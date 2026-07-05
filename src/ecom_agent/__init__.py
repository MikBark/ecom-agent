"""Package entrypoint."""


def main() -> None:
    """Start the server without importing runtime dependencies on package import."""
    from ecom_agent.server import main as run_server  # noqa: PLC0415

    run_server()


__all__ = ["main"]
