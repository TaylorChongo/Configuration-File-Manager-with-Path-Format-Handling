"""Timestamped config backups stored in a ``.versions/`` directory beside the file.

    samples/app_config.json
    samples/.versions/app_config/app_config.20261023T101500123456Z.json
    samples/.versions/app_config/app_config.20261023T101500123456Z-1.json  (same instant)
"""

import os
import re
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

VERSIONS_DIRNAME = ".versions"
TIMESTAMP_FORMAT = "%Y%m%dT%H%M%S%fZ"


def versions_dir(path: Path) -> Path:
    return path.parent / VERSIONS_DIRNAME / path.stem


def _timestamp() -> str:
    return datetime.now(UTC).strftime(TIMESTAMP_FORMAT)


def _version_pattern(path: Path) -> re.Pattern[str]:
    """Match ``<stem>.<timestamp>[-<n>]<suffix>`` for ``path``, capturing timestamp and n."""
    return re.compile(
        rf"{re.escape(path.stem)}\.(\d{{8}}T\d{{12}}Z)(?:-(\d+))?{re.escape(path.suffix)}"
    )


def save_version(path: Path) -> Path:
    """Copy ``path`` into its versions dir as ``<stem>.<UTC timestamp><suffix>``."""
    if not path.is_file():
        raise FileNotFoundError(f"No such file: {path}")
    directory = versions_dir(path)
    directory.mkdir(parents=True, exist_ok=True)

    base = f"{path.stem}.{_timestamp()}"
    target = directory / f"{base}{path.suffix}"
    counter = 0
    while target.exists():  # two saves within the clock's resolution
        counter += 1
        target = directory / f"{base}-{counter}{path.suffix}"
    shutil.copy2(path, target)
    return target


def list_versions(path: Path) -> list[Path]:
    """Return saved versions, oldest first."""
    directory = versions_dir(path)
    if not directory.is_dir():
        return []
    pattern = _version_pattern(path)
    keyed: list[tuple[str, int, Path]] = []
    for candidate in directory.iterdir():
        match = pattern.fullmatch(candidate.name)
        if match and candidate.is_file():
            keyed.append((match[1], int(match[2] or 0), candidate))
    return [candidate for *_, candidate in sorted(keyed)]


def restore_version(path: Path, version: Path) -> None:
    """Overwrite ``path`` with ``version`` (saving the current file first)."""
    in_versions_dir = version.parent.resolve() == versions_dir(path).resolve()
    if not (in_versions_dir and _version_pattern(path).fullmatch(version.name)):
        raise ValueError(f"{version} is not a saved version of {path}")
    if not version.is_file():
        raise FileNotFoundError(f"No such version: {version}")

    if path.exists():
        save_version(path)
    # copy beside the target, then swap in atomically so path is never half-written
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    os.close(fd)
    temp = Path(name)
    try:
        shutil.copy2(version, temp)
        temp.replace(path)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
