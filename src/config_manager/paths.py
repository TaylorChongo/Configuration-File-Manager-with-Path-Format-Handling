"""pathlib-based file discovery and inspection helpers."""

import os
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

SUPPORTED_SUFFIXES: frozenset[str] = frozenset({".json", ".csv", ".xml"})


@dataclass(frozen=True, slots=True)
class FileInfo:
    path: Path
    size_bytes: int
    modified: datetime
    readable: bool
    writable: bool


def _is_hidden(path: Path, root: Path) -> bool:
    """True if any part of ``path`` below ``root`` starts with a dot (e.g. ``.versions``)."""
    return any(part.startswith(".") for part in path.relative_to(root).parts)


def discover_configs(root: Path, *, recursive: bool = True) -> Iterator[Path]:
    """Yield supported config files under ``root`` (``rglob`` or ``glob``).

    Hidden files and directories (``.versions``, ``.venv``, ...) are skipped.
    Raises ``NotADirectoryError`` immediately if ``root`` is not a directory.
    """
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")
    candidates = root.rglob("*") if recursive else root.glob("*")
    return (
        path
        for path in candidates
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_SUFFIXES
        and not _is_hidden(path, root)
    )


def inspect_file(path: Path) -> FileInfo:
    """Return existence-checked size, mtime and permission info for ``path``."""
    if not path.is_file():
        raise FileNotFoundError(f"No such file: {path}")
    stat = path.stat()
    return FileInfo(
        path=path,
        size_bytes=stat.st_size,
        modified=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
        readable=os.access(path, os.R_OK),
        writable=os.access(path, os.W_OK),
    )


def ensure_dir(path: Path) -> Path:
    """Create ``path`` (and parents) if missing and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


class ConfigTreeIterator:
    """Custom iterator over config files in a directory tree, sorted by path."""

    def __init__(self, root: Path) -> None:
        self._root = root
        # discover_configs checks ``root`` now; the tree is only walked on first next()
        self._pending: Iterator[Path] | None = discover_configs(root)
        self._paths: list[Path] = []
        self._index = 0

    def __iter__(self) -> "ConfigTreeIterator":
        return self

    def __next__(self) -> Path:
        if self._pending is not None:
            self._paths = sorted(self._pending)
            self._pending = None
        if self._index >= len(self._paths):
            raise StopIteration
        path = self._paths[self._index]
        self._index += 1
        return path
