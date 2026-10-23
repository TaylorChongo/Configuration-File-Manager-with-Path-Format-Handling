"""Tests for JsonHandler read/write."""

import json
from pathlib import Path

import pytest

from config_manager.handlers import JsonHandler
from config_manager.schemas import ConfigDocument


@pytest.fixture
def handler() -> JsonHandler:
    return JsonHandler()


def test_read_sample(
    handler: JsonHandler, samples_dir: Path, sample_document: ConfigDocument
) -> None:
    assert handler.read(samples_dir / "app_config.json") == sample_document


def test_round_trip(
    handler: JsonHandler, tmp_path: Path, sample_document: ConfigDocument
) -> None:
    target = tmp_path / "out.json"
    handler.write(sample_document, target)
    assert handler.read(target) == sample_document


def test_write_creates_parent_dirs(
    handler: JsonHandler, tmp_path: Path, sample_document: ConfigDocument
) -> None:
    target = tmp_path / "nested" / "dir" / "out.json"
    handler.write(sample_document, target)
    assert target.is_file()


def test_write_is_pretty_printed(
    handler: JsonHandler, tmp_path: Path, sample_document: ConfigDocument
) -> None:
    target = tmp_path / "out.json"
    handler.write(sample_document, target)
    text = target.read_text(encoding="utf-8")
    assert text.startswith('{\n  "metadata"')
    assert text.endswith("\n")


def test_read_missing_file_raises(handler: JsonHandler, tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        handler.read(tmp_path / "missing.json")


def test_read_malformed_json_raises(handler: JsonHandler, tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        handler.read(bad)


def test_read_non_object_raises(handler: JsonHandler, tmp_path: Path) -> None:
    bad = tmp_path / "list.json"
    bad.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match="must be an object"):
        handler.read(bad)
