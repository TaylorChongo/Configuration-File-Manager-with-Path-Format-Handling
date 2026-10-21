"""pathlib-based file discovery and inspection helpers."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SUPPORTED_SUFFIXES: frozenset[str] = frozenset({".json", ".csv", ".xml"})


@dataclass(frozen=True, slots=True)
class FileInfo:
    path: Path
    size_bytes: int
    modified: datetime
    readable: bool
    writable: bool


def discover_configs(root: Path, *, recursive: bool = True) -> Iterator[Path]:
    """Yield supported config files under ``root`` (``rglob`` or ``glob``)."""
    # TODO (Day 1-2)
    raise NotImplementedError


def inspect_file(path: Path) -> FileInfo:
    """Return existence-checked size, mtime and permission info for ``path``."""
    # TODO (Day 1-2): path.stat(), os.access(path, os.R_OK / os.W_OK)
    raise NotImplementedError


def ensure_dir(path: Path) -> Path:
    """Create ``path`` (and parents) if missing and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


class ConfigTreeIterator:
    """Custom iterator over config files in a directory tree, sorted by path."""

    def __init__(self, root: Path) -> None:
        self._root = root
        # TODO (Day 1-2): collect/sort lazily, track position

    def __iter__(self) -> "ConfigTreeIterator":
        return self

    def __next__(self) -> Path:
        raise NotImplementedError
