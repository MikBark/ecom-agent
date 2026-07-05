"""Reject escaped physical newlines inside Python string literals."""

import sys
import tokenize
from collections.abc import Iterable
from pathlib import Path

_ESCAPED_NEWLINES = (bytes((92, 10)), bytes((92, 13, 10)))


def python_files(roots: Iterable[Path]) -> Iterable[Path]:
    """Yield maintained Python files below the supplied roots."""
    for root in roots:
        if root.is_file() and root.suffix == ".py":
            yield root
        elif root.is_dir():
            yield from root.rglob("*.py")


def escaped_newline_lines(path: Path) -> Iterable[int]:
    """Yield lines containing escaped newlines within string tokens."""
    with path.open("rb") as source:
        for token in tokenize.tokenize(source.readline):
            if token.type != tokenize.STRING:
                continue
            raw = token.string.encode()
            for escaped_newline in _ESCAPED_NEWLINES:
                offset = 0
                while (index := raw.find(escaped_newline, offset)) >= 0:
                    yield token.start[0] + raw[:index].count(b"\n")
                    offset = index + len(escaped_newline)


def main() -> int:
    """Report forbidden string continuations and return nonzero when found."""
    failed = False
    roots = (Path(argument) for argument in sys.argv[1:])
    for path in python_files(roots):
        for line in escaped_newline_lines(path):
            failed = True
            print(f"{path}:{line}: escaped newline in string literal is forbidden")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
