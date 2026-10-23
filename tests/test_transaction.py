"""Tests for the ConfigTransaction context manager."""

import shutil
from pathlib import Path

import pytest

from config_manager.handlers import get_handler
from config_manager.handlers.json_handler import JsonHandler
from config_manager.schemas import ConfigDocument
from config_manager.transaction import ConfigTransaction
from config_manager.validation import ConfigValidationError


@pytest.fixture(params=["json", "csv", "xml"])
def config_file(request: pytest.FixtureRequest, samples_dir: Path, tmp_path: Path) -> Path:
    """A writable copy of a sample config, in each format."""
    target = tmp_path / f"app_config.{request.param}"
    shutil.copy(samples_dir / target.name, target)
    return target


@pytest.fixture
def json_file(samples_dir: Path, tmp_path: Path) -> Path:
    target = tmp_path / "app_config.json"
    shutil.copy(samples_dir / target.name, target)
    return target


def leftovers(path: Path) -> list[str]:
    """Files in the directory other than the config itself (e.g. temp files)."""
    return sorted(p.name for p in path.parent.iterdir() if p != path)


def test_commit_saves_changes(config_file: Path, sample_document: ConfigDocument) -> None:
    with ConfigTransaction(config_file) as doc:
        doc["metadata"]["version"] = "1.1.0"
        doc["entries"].append({"section": "cache", "key": "ttl", "value": 60, "type": "int"})

    saved = get_handler(config_file).read(config_file)
    assert saved["metadata"]["version"] == "1.1.0"
    assert saved["entries"] == [
        *sample_document["entries"],
        {"section": "cache", "key": "ttl", "value": 60, "type": "int"},
    ]
    assert leftovers(config_file) == []


def test_exception_rolls_back(config_file: Path) -> None:
    before = config_file.read_bytes()
    with pytest.raises(RuntimeError, match="boom"), ConfigTransaction(config_file) as doc:
        doc["metadata"]["version"] = "9.9.9"
        raise RuntimeError("boom")
    assert config_file.read_bytes() == before
    assert leftovers(config_file) == []


def test_invalid_edit_is_rejected(json_file: Path) -> None:
    before = json_file.read_bytes()
    invalid = pytest.raises(ConfigValidationError, match=r"entries\[1\].value")
    with invalid, ConfigTransaction(json_file) as doc:
        doc["entries"][1]["value"] = "not-a-port"
    assert json_file.read_bytes() == before
    assert leftovers(json_file) == []


def test_failed_write_keeps_original(json_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken_write(self: JsonHandler, document: ConfigDocument, path: Path) -> None:
        path.write_text('{"half": ', encoding="utf-8")  # partial output, then crash
        raise OSError("disk full")

    before = json_file.read_bytes()
    monkeypatch.setattr(JsonHandler, "write", broken_write)
    with pytest.raises(OSError, match="disk full"), ConfigTransaction(json_file) as doc:
        doc["metadata"]["version"] = "1.1.0"
    assert json_file.read_bytes() == before
    assert leftovers(json_file) == []


def test_no_changes_skips_write(json_file: Path) -> None:
    mtime = json_file.stat().st_mtime_ns
    with ConfigTransaction(json_file) as doc:
        assert doc["metadata"]["name"] == "app"
    assert json_file.stat().st_mtime_ns == mtime


def test_document_is_a_copy(json_file: Path) -> None:
    transaction = ConfigTransaction(json_file)
    with transaction as doc:
        doc["entries"].clear()
        # the file on disk isn't touched until the block exits
        assert len(JsonHandler().read(json_file)["entries"]) == 6
    assert JsonHandler().read(json_file)["entries"] == []


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError), ConfigTransaction(tmp_path / "missing.json"):
        pass


def test_unsupported_format_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unsupported config format"):
        ConfigTransaction(tmp_path / "a.yaml")
