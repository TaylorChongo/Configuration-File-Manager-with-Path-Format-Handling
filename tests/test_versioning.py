"""Tests for timestamped config backups."""

import re
import shutil
from pathlib import Path

import pytest

from config_manager import versioning
from config_manager.paths import discover_configs
from config_manager.versioning import (
    list_versions,
    restore_version,
    save_version,
    versions_dir,
)


@pytest.fixture
def config(samples_dir: Path, tmp_path: Path) -> Path:
    target = tmp_path / "app_config.json"
    shutil.copy(samples_dir / target.name, target)
    return target


@pytest.fixture
def frozen_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every save happen at the same instant."""
    monkeypatch.setattr(versioning, "_timestamp", lambda: "20261023T101500000000Z")


def test_save_version_copies_file(config: Path) -> None:
    saved = save_version(config)
    assert saved.parent == config.parent / ".versions" / "app_config"
    assert re.fullmatch(r"app_config\.\d{8}T\d{12}Z\.json", saved.name)
    assert saved.read_bytes() == config.read_bytes()


def test_save_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        save_version(tmp_path / "missing.json")


def test_list_versions_oldest_first(config: Path) -> None:
    saved = []
    for version in ("1", "2", "3"):
        config.write_text(version, encoding="utf-8")
        saved.append(save_version(config))
    assert list_versions(config) == saved
    assert [p.read_text(encoding="utf-8") for p in list_versions(config)] == ["1", "2", "3"]


def test_same_instant_saves_keep_order(config: Path, frozen_clock: None) -> None:
    saved = [save_version(config) for _ in range(12)]
    assert len(set(saved)) == 12
    assert saved[1].name == "app_config.20261023T101500000000Z-1.json"
    assert list_versions(config) == saved  # -10 sorts after -9


def test_list_versions_empty(config: Path) -> None:
    assert list_versions(config) == []


def test_list_versions_ignores_other_files(config: Path, samples_dir: Path) -> None:
    xml = config.with_suffix(".xml")  # same stem, so it shares the versions dir
    shutil.copy(samples_dir / "app_config.xml", xml)
    json_version = save_version(config)
    xml_version = save_version(xml)
    (versions_dir(config) / "notes.txt").write_text("junk", encoding="utf-8")

    assert list_versions(config) == [json_version]
    assert list_versions(xml) == [xml_version]


def test_versions_are_hidden_from_discovery(config: Path) -> None:
    save_version(config)
    assert list(discover_configs(config.parent)) == [config]


def test_restore_version(config: Path) -> None:
    original = config.read_bytes()
    old = save_version(config)
    config.write_text("edited", encoding="utf-8")

    restore_version(config, old)

    assert config.read_bytes() == original
    versions = list_versions(config)
    assert len(versions) == 2
    assert versions[-1].read_text(encoding="utf-8") == "edited"  # current saved first
    assert [p.name for p in config.parent.iterdir()] == [".versions", "app_config.json"]


def test_restore_when_file_was_deleted(config: Path) -> None:
    original = config.read_bytes()
    old = save_version(config)
    config.unlink()
    restore_version(config, old)
    assert config.read_bytes() == original


def test_restore_rejects_other_files_version(config: Path, tmp_path: Path) -> None:
    other = tmp_path / "other.json"
    shutil.copy(config, other)
    foreign = save_version(other)
    with pytest.raises(ValueError, match="is not a saved version"):
        restore_version(config, foreign)


def test_restore_rejects_arbitrary_file(config: Path, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="is not a saved version"):
        restore_version(config, tmp_path / "random.json")


def test_restore_missing_version_raises(config: Path) -> None:
    ghost = versions_dir(config) / "app_config.20200101T000000000000Z.json"
    with pytest.raises(FileNotFoundError):
        restore_version(config, ghost)
