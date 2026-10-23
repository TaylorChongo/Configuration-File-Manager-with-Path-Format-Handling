"""Tests for converting config files between formats."""

from pathlib import Path

import pytest

from config_manager.converter import convert
from config_manager.handlers import get_handler
from config_manager.pipeline import compose, normalise_keys, select_section
from config_manager.schemas import ConfigDocument

FORMATS = ("json", "csv", "xml")


@pytest.mark.parametrize("target_fmt", FORMATS)
@pytest.mark.parametrize("source_fmt", FORMATS)
def test_convert_every_pair_is_lossless(
    source_fmt: str,
    target_fmt: str,
    samples_dir: Path,
    tmp_path: Path,
    sample_document: ConfigDocument,
) -> None:
    target = tmp_path / f"out.{target_fmt}"
    result = convert(samples_dir / f"app_config.{source_fmt}", target)
    assert result == target
    assert get_handler(target).read(target) == sample_document


@pytest.mark.parametrize(("source_fmt", "target_fmt"), [("json", "xml"), ("xml", "csv")])
def test_convert_output_matches_sample_file(
    source_fmt: str, target_fmt: str, samples_dir: Path, tmp_path: Path
) -> None:
    target = tmp_path / f"out.{target_fmt}"
    convert(samples_dir / f"app_config.{source_fmt}", target)
    expected = (samples_dir / f"app_config.{target_fmt}").read_text(encoding="utf-8")
    assert target.read_text(encoding="utf-8") == expected


def test_convert_applies_transform(samples_dir: Path, tmp_path: Path) -> None:
    target = tmp_path / "database.csv"
    convert(
        samples_dir / "app_config.json",
        target,
        transform=compose(normalise_keys, select_section("database")),
    )
    doc = get_handler(target).read(target)
    assert doc["metadata"]["name"] == "app"
    assert [e["key"] for e in doc["entries"]] == ["host", "port", "pool_timeout"]


def test_convert_creates_target_dirs(samples_dir: Path, tmp_path: Path) -> None:
    target = tmp_path / "out" / "nested" / "app.xml"
    convert(samples_dir / "app_config.json", target)
    assert target.is_file()


def test_convert_rejects_unsupported_target_before_reading(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unsupported config format: '.yaml'"):
        convert(tmp_path / "missing.json", tmp_path / "out.yaml")


def test_convert_rejects_same_file(samples_dir: Path) -> None:
    source = samples_dir / "app_config.json"
    with pytest.raises(ValueError, match="same file"):
        convert(source, source)


def test_convert_missing_source_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        convert(tmp_path / "missing.json", tmp_path / "out.xml")
    assert not (tmp_path / "out.xml").exists()
