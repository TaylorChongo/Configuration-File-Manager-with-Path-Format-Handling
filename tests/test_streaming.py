"""Tests for iter_entries() generators across all handlers."""

import tracemalloc
import types
from collections.abc import Callable
from pathlib import Path

import pytest

from config_manager.handlers import HANDLERS, XmlHandler, get_handler
from config_manager.protocols import FormatHandler
from config_manager.schemas import ConfigDocument


@pytest.mark.parametrize("handler", HANDLERS, ids=lambda h: type(h).__name__)
def test_iter_entries_matches_read(
    handler: FormatHandler, samples_dir: Path, sample_document: ConfigDocument
) -> None:
    path = samples_dir / f"app_config{handler.extensions[0]}"
    result = handler.iter_entries(path)
    assert isinstance(result, types.GeneratorType)
    assert list(result) == sample_document["entries"]


@pytest.mark.parametrize("handler", HANDLERS, ids=lambda h: type(h).__name__)
def test_closing_early_releases_file(handler: FormatHandler, samples_dir: Path,
                                     tmp_path: Path) -> None:
    path = tmp_path / f"app_config{handler.extensions[0]}"
    path.write_bytes((samples_dir / path.name).read_bytes())
    entries = handler.iter_entries(path)
    next(entries)
    entries.close()  # type: ignore[attr-defined]
    path.unlink()  # fails on Windows if the file were still open


# --- XML specifics ----------------------------------------------------------


def write_xml(path: Path, body: str) -> Path:
    path.write_text(f'<config name="x" version="1">{body}</config>', encoding="utf-8")
    return path


def test_xml_skips_nested_and_other_elements(tmp_path: Path) -> None:
    path = write_xml(
        tmp_path / "a.xml",
        '<description>d</description>'
        '<entry section="s" key="a" type="int">1</entry>'
        '<group><entry section="s" key="nested" type="int">2</entry></group>'
        '<entry section="s" key="b" type="bool">true</entry>',
    )
    assert [e["key"] for e in XmlHandler().iter_entries(path)] == ["a", "b"]
    assert [e["key"] for e in XmlHandler().read(path)["entries"]] == ["a", "b"]


def test_xml_wrong_root_raises(tmp_path: Path) -> None:
    path = tmp_path / "a.xml"
    path.write_text("<settings/>", encoding="utf-8")
    with pytest.raises(ValueError, match="root element must be <config>"):
        next(XmlHandler().iter_entries(path))


def test_xml_bad_value_reports_entry(tmp_path: Path) -> None:
    path = write_xml(
        tmp_path / "a.xml",
        '<entry section="s" key="a" type="int">1</entry>'
        '<entry section="s" key="b" type="int">x</entry>',
    )
    entries = XmlHandler().iter_entries(path)
    assert next(entries)["key"] == "a"
    with pytest.raises(ValueError, match="entry 2: cannot convert 'x' to int"):
        next(entries)


# --- memory ------------------------------------------------------------------


def peak_bytes(fn: Callable[[], object]) -> int:
    tracemalloc.start()
    try:
        fn()
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


@pytest.mark.slow
@pytest.mark.parametrize("suffix", [".csv", ".xml"])
def test_streaming_uses_less_memory(suffix: str, tmp_path: Path) -> None:
    document: ConfigDocument = {
        "metadata": {"name": "big", "version": "1"},
        "entries": [
            {"section": "s", "key": f"k{i}", "value": i, "type": "int",
             "description": f"setting {i}"}
            for i in range(20_000)
        ],
    }
    path = tmp_path / f"big{suffix}"
    handler = get_handler(path)
    handler.write(document, path)
    del document

    full = peak_bytes(lambda: handler.read(path))
    streamed = peak_bytes(lambda: sum(1 for _ in handler.iter_entries(path)))
    assert streamed * 10 < full
