"""Contract tests every FormatHandler must pass, run against each format.

Uses a deliberately awkward document (unicode, delimiters, markup characters,
line breaks, edge-case numbers) to check that no format loses or mangles data.
"""

from pathlib import Path

import pytest

from config_manager.converter import convert
from config_manager.handlers import HANDLERS, get_handler
from config_manager.protocols import FormatHandler
from config_manager.schemas import ConfigDocument

SUFFIXES = [handler.extensions[0] for handler in HANDLERS]


@pytest.fixture
def tricky_document() -> ConfigDocument:
    return {
        "metadata": {
            "name": "café ☕ app",
            "version": "2.0.0-beta+1",
            "description": 'Commas, "quotes", <tags> & ampersands = fun',
        },
        "entries": [
            {"section": "text", "key": "unicode", "value": "naïve — 日本語 🚀", "type": "str"},
            {"section": "text", "key": "delimiters", "value": 'a,b;"c"\t|d', "type": "str",
             "description": "csv, quoting"},
            {"section": "text", "key": "markup", "value": "<b>x</b> & y > z", "type": "str",
             "description": "<xml> & 'quotes'"},
            {"section": "text", "key": "multiline", "value": "line 1\nline 2", "type": "str"},
            {"section": "text", "key": "padded", "value": "  spaced  ", "type": "str"},
            {"section": "text", "key": "empty", "value": "", "type": "str"},
            {"section": "text", "key": "hash", "value": "# not a comment", "type": "str"},
            {"section": "text", "key": "looks_numeric", "value": "007", "type": "str"},
            {"section": "numbers", "key": "negative", "value": -42, "type": "int"},
            {"section": "numbers", "key": "big", "value": 2**63, "type": "int"},
            {"section": "numbers", "key": "precise", "value": 0.1 + 0.2, "type": "float"},
            {"section": "numbers", "key": "tiny", "value": 1e-12, "type": "float"},
            {"section": "numbers", "key": "negative_zero", "value": -0.0, "type": "float"},
            {"section": "flags", "key": "on", "value": True, "type": "bool"},
            {"section": "flags", "key": "off", "value": False, "type": "bool"},
        ],
    }


@pytest.fixture(params=HANDLERS, ids=lambda h: type(h).__name__)
def handler(request: pytest.FixtureRequest) -> FormatHandler:
    handler: FormatHandler = request.param
    return handler


def path_for(handler: FormatHandler, directory: Path, stem: str = "config") -> Path:
    return directory / f"{stem}{handler.extensions[0]}"


def test_satisfies_protocol(handler: FormatHandler) -> None:
    assert isinstance(handler, FormatHandler)
    assert all(ext.startswith(".") and ext == ext.lower() for ext in handler.extensions)


def test_registered_for_its_extensions(handler: FormatHandler) -> None:
    for ext in handler.extensions:
        assert get_handler(Path(f"file{ext.upper()}")) is handler


def test_round_trip_is_lossless(
    handler: FormatHandler, tmp_path: Path, tricky_document: ConfigDocument
) -> None:
    path = path_for(handler, tmp_path)
    handler.write(tricky_document, path)
    assert handler.read(path) == tricky_document


def test_types_survive_round_trip(
    handler: FormatHandler, tmp_path: Path, tricky_document: ConfigDocument
) -> None:
    path = path_for(handler, tmp_path)
    handler.write(tricky_document, path)
    for before, after in zip(tricky_document["entries"], handler.read(path)["entries"],
                             strict=True):
        assert type(after["value"]) is type(before["value"]), before["key"]


def test_iter_entries_matches_written(
    handler: FormatHandler, tmp_path: Path, tricky_document: ConfigDocument
) -> None:
    path = path_for(handler, tmp_path)
    handler.write(tricky_document, path)
    assert list(handler.iter_entries(path)) == tricky_document["entries"]


def test_empty_entries(handler: FormatHandler, tmp_path: Path) -> None:
    document: ConfigDocument = {"metadata": {"name": "empty", "version": "0"}, "entries": []}
    path = path_for(handler, tmp_path)
    handler.write(document, path)
    assert handler.read(path) == document
    assert list(handler.iter_entries(path)) == []


def test_write_overwrites_existing(
    handler: FormatHandler, tmp_path: Path, tricky_document: ConfigDocument,
    sample_document: ConfigDocument,
) -> None:
    path = path_for(handler, tmp_path)
    handler.write(tricky_document, path)
    handler.write(sample_document, path)
    assert handler.read(path) == sample_document


def test_write_creates_parent_dirs(
    handler: FormatHandler, tmp_path: Path, sample_document: ConfigDocument
) -> None:
    path = path_for(handler, tmp_path / "a" / "b")
    handler.write(sample_document, path)
    assert handler.read(path) == sample_document


def test_read_missing_file(handler: FormatHandler, tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        handler.read(path_for(handler, tmp_path))


@pytest.mark.parametrize("target_suffix", SUFFIXES)
@pytest.mark.parametrize("source_suffix", SUFFIXES)
def test_conversion_is_lossless(
    source_suffix: str, target_suffix: str, tmp_path: Path, tricky_document: ConfigDocument
) -> None:
    source = tmp_path / f"source{source_suffix}"
    target = tmp_path / f"target{target_suffix}"
    get_handler(source).write(tricky_document, source)
    convert(source, target)
    assert get_handler(target).read(target) == tricky_document
