"""Optional, fail-open Langfuse instrumentation."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Literal

from langfuse import Langfuse

from ecom_agent.config import ObservabilityMode, Settings

logger = logging.getLogger(__name__)

ObservationType = Literal["span", "agent", "tool", "chain", "generation"]


class Observation:
    """Safe wrapper around one Langfuse observation."""

    def __init__(
        self,
        delegate: Any | None,
        *,
        include_error_messages: bool,
    ) -> None:
        self._delegate = delegate
        self._include_error_messages = include_error_messages

    def update(self, **values: Any) -> None:
        """Update an observation without allowing telemetry to break the request."""
        if self._delegate is None:
            return
        try:
            self._delegate.update(**values)
        except Exception:
            logger.warning("failed to update Langfuse observation", exc_info=True)

    def fail(self, exc: BaseException) -> None:
        """Mark an observation as failed with mode-appropriate detail."""
        error_type = type(exc).__name__
        status = error_type
        if self._include_error_messages and str(exc):
            status = f"{error_type}: {exc}"
        self.update(
            level="ERROR",
            status_message=status,
            metadata={"error_type": error_type},
        )


class Observability:
    """Creates nested observations or behaves as a zero-cost no-op."""

    def __init__(self, mode: ObservabilityMode, client: Any | None = None) -> None:
        self.mode = mode
        self._client = client

    @property
    def captures_content(self) -> bool:
        """Whether prompts and application payloads may be exported."""
        return self.mode == "full"

    def content(self, value: Any) -> Any | None:
        """Return content only in full-capture mode."""
        return value if self.captures_content else None

    @contextmanager
    def observe(
        self,
        *,
        name: str,
        as_type: ObservationType = "span",
        input_data: Any | None = None,
        metadata: dict[str, Any] | None = None,
        model: str | None = None,
    ) -> Iterator[Observation]:
        """Create a current observation while preserving application exceptions."""
        started = self._start_observation(
            name=name,
            as_type=as_type,
            input_data=input_data,
            metadata=metadata,
            model=model,
        )
        if started is None:
            yield Observation(None, include_error_messages=self.captures_content)
            return

        manager, observation = started
        try:
            yield observation
        except BaseException as exc:
            observation.fail(exc)
            self._close_observation(manager, exc)
            raise
        else:
            self._close_observation(manager)

    def _start_observation(
        self,
        *,
        name: str,
        as_type: ObservationType,
        input_data: Any | None,
        metadata: dict[str, Any] | None,
        model: str | None,
    ) -> tuple[Any, Observation] | None:
        if self._client is None:
            return None
        try:
            manager = self._client.start_as_current_observation(
                name=name,
                as_type=as_type,
                input=input_data,
                metadata=metadata,
                model=model,
            )
            delegate = manager.__enter__()
        except Exception:
            logger.warning("failed to start Langfuse observation", exc_info=True)
            return None
        return manager, Observation(
            delegate, include_error_messages=self.captures_content
        )

    def _close_observation(self, manager: Any, exc: BaseException | None = None) -> None:
        try:
            if exc is None or not self.captures_content:
                manager.__exit__(None, None, None)
            else:
                manager.__exit__(type(exc), exc, exc.__traceback__)
        except Exception:
            logger.warning("failed to close Langfuse observation", exc_info=True)

    def update_current_generation(
        self, *, model: str, usage_details: dict[str, Any]
    ) -> None:
        """Attach provider-reported usage to the active generation."""
        if self._client is None:
            return
        try:
            self._client.update_current_generation(
                model=model, usage_details=usage_details
            )
        except Exception:
            logger.warning("failed to record Langfuse token usage", exc_info=True)

    def shutdown(self) -> None:
        """Flush queued observations during graceful process shutdown."""
        if self._client is None:
            return
        try:
            self._client.shutdown()
        except Exception:
            logger.warning("failed to shut down Langfuse", exc_info=True)


def build_observability(settings: Settings) -> Observability:
    """Build the configured Langfuse client, or a no-op observer."""
    if settings.observability_mode == "off":
        return Observability("off")

    public_key = settings.langfuse_public_key
    secret_key = settings.langfuse_secret_key
    if public_key is None or secret_key is None:  # guarded by Settings validation
        raise ValueError("Langfuse credentials are required")
    client = Langfuse(
        public_key=public_key.get_secret_value(),
        secret_key=secret_key.get_secret_value(),
        base_url=settings.langfuse_base_url,
    )
    return Observability(settings.observability_mode, client)


__all__ = ["Observability", "Observation", "build_observability"]
