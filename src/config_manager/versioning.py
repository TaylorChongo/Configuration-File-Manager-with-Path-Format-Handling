"""Timestamped config backups stored in a ``.versions/`` directory beside the file."""

from pathlib import Path

VERSIONS_DIRNAME = ".versions"


def versions_dir(path: Path) -> Path:
    return path.parent / VERSIONS_DIRNAME / path.stem


def save_version(path: Path) -> Path:
    """Copy ``path`` into its versions dir as ``<stem>.<UTC timestamp><suffix>``."""
    # TODO (Day 5-6)
    raise NotImplementedError


def list_versions(path: Path) -> list[Path]:
    """Return saved versions, oldest first."""
    # TODO (Day 5-6)
    raise NotImplementedError


def restore_version(path: Path, version: Path) -> None:
    """Overwrite ``path`` with ``version`` (saving the current file first)."""
    # TODO (Day 5-6)
    raise NotImplementedError
