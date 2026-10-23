"""Tests for pathlib discovery and inspection helpers."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from config_manager.paths import discover_configs, inspect_file


@pytest.fixture
def config_tree(tmp_path: Path) -> Path:
    """Build a small tree of config and non-config files."""
    files = [
        "a.json",
        "b.CSV",
        "notes.txt",
        "sub/c.xml",
        "sub/deeper/d.json",
        "sub/readme.md",
        ".versions/a/a.20260101T000000Z.json",
        ".hidden.json",
    ]
    for name in files:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
    (tmp_path / "folder.json").mkdir()  # a directory with a config-like name
    return tmp_path


def names(paths: list[Path], root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in paths}


def test_discover_recursive(config_tree: Path) -> None:
    found = list(discover_configs(config_tree))
    assert names(found, config_tree) == {"a.json", "b.CSV", "sub/c.xml", "sub/deeper/d.json"}


def test_discover_non_recursive(config_tree: Path) -> None:
    found = list(discover_configs(config_tree, recursive=False))
    assert names(found, config_tree) == {"a.json", "b.CSV"}


def test_discover_samples(samples_dir: Path) -> None:
    found = names(list(discover_configs(samples_dir, recursive=False)), samples_dir)
    assert found == {"app_config.json", "app_config.csv", "app_config.xml"}


def test_discover_is_lazy(config_tree: Path) -> None:
    result = discover_configs(config_tree)
    assert iter(result) is result  # an iterator, not a list


def test_discover_rejects_missing_root(tmp_path: Path) -> None:
    with pytest.raises(NotADirectoryError):
        discover_configs(tmp_path / "missing")


def test_discover_rejects_file_root(tmp_path: Path) -> None:
    file = tmp_path / "a.json"
    file.write_text("{}", encoding="utf-8")
    with pytest.raises(NotADirectoryError):
        discover_configs(file)


def test_inspect_file(tmp_path: Path) -> None:
    path = tmp_path / "a.json"
    path.write_text('{"x": 1}', encoding="utf-8")
    info = inspect_file(path)
    assert info.path == path
    assert info.size_bytes == path.stat().st_size
    assert info.readable
    assert info.writable
    assert info.modified.tzinfo is UTC
    assert abs(datetime.now(UTC) - info.modified) < timedelta(minutes=1)


def test_inspect_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        inspect_file(tmp_path / "missing.json")


def test_inspect_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        inspect_file(tmp_path)
