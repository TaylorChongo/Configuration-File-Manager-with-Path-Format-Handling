"""Tests for CsvHandler read/write/streaming."""

import types
from pathlib import Path

import pytest

from config_manager.handlers import CsvHandler
from config_manager.schemas import ConfigDocument


@pytest.fixture
def handler() -> CsvHandler:
    return CsvHandler()


def write_csv(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_read_sample(
    handler: CsvHandler, samples_dir: Path, sample_document: ConfigDocument
) -> None:
    assert handler.read(samples_dir / "app_config.csv") == sample_document


def test_round_trip(handler: CsvHandler, tmp_path: Path, sample_document: ConfigDocument) -> None:
    target = tmp_path / "out.csv"
    handler.write(sample_document, target)
    assert handler.read(target) == sample_document


def test_write_matches_sample_file(
    handler: CsvHandler, tmp_path: Path, samples_dir: Path, sample_document: ConfigDocument
) -> None:
    target = tmp_path / "out.csv"
    handler.write(sample_document, target)
    expected = (samples_dir / "app_config.csv").read_text(encoding="utf-8")
    assert target.read_text(encoding="utf-8") == expected


def test_write_creates_parent_dirs(
    handler: CsvHandler, tmp_path: Path, sample_document: ConfigDocument
) -> None:
    target = tmp_path / "nested" / "out.csv"
    handler.write(sample_document, target)
    assert target.is_file()


def test_write_quotes_commas(handler: CsvHandler, tmp_path: Path) -> None:
    doc: ConfigDocument = {
        "metadata": {"name": "app", "version": "1.0.0"},
        "entries": [{"section": "s", "key": "k", "value": "a, b", "type": "str",
                     "description": 'say "hi"'}],
    }
    target = tmp_path / "out.csv"
    handler.write(doc, target)
    assert handler.read(target) == doc


def test_iter_entries_is_generator(handler: CsvHandler, samples_dir: Path) -> None:
    result = handler.iter_entries(samples_dir / "app_config.csv")
    assert isinstance(result, types.GeneratorType)
    first = next(result)
    assert first == {"section": "database", "key": "host", "value": "localhost", "type": "str",
                     "description": "Database host"}
    result.close()


def test_empty_description_is_omitted(handler: CsvHandler, samples_dir: Path) -> None:
    entries = list(handler.iter_entries(samples_dir / "app_config.csv"))
    assert "description" not in entries[2]  # pool_timeout


def test_read_metadata_ignores_lines_without_equals(handler: CsvHandler, tmp_path: Path) -> None:
    path = write_csv(tmp_path / "a.csv", "# just a note\n# name = app \n# version=1.0=beta\n"
                                         "section,key,value,type\n")
    assert handler.read_metadata(path) == {"name": "app", "version": "1.0=beta"}


def test_no_metadata(handler: CsvHandler, tmp_path: Path) -> None:
    path = write_csv(tmp_path / "a.csv", "section,key,value,type\ns,k,1,int\n")
    doc = handler.read(path)
    assert not doc["metadata"]
    assert doc["entries"] == [{"section": "s", "key": "k", "value": 1, "type": "int"}]


def test_bad_value_reports_row(handler: CsvHandler, tmp_path: Path) -> None:
    path = write_csv(tmp_path / "a.csv", "# name=x\nsection,key,value,type\n"
                                         "s,a,1,int\ns,b,oops,int\n")
    with pytest.raises(ValueError, match=r"line 4: cannot convert 'oops' to int"):
        handler.read(path)


def test_missing_columns_raises(handler: CsvHandler, tmp_path: Path) -> None:
    path = write_csv(tmp_path / "a.csv", "section,key\ns,k\n")
    with pytest.raises(ValueError, match="missing CSV columns: type, value"):
        handler.read(path)
