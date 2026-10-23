"""Tests for XmlHandler read/write."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from config_manager.handlers import XmlHandler
from config_manager.schemas import ConfigDocument
from config_manager.validation import ConfigValidationError


@pytest.fixture
def handler() -> XmlHandler:
    return XmlHandler()


def write_xml(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_read_sample(
    handler: XmlHandler, samples_dir: Path, sample_document: ConfigDocument
) -> None:
    assert handler.read(samples_dir / "app_config.xml") == sample_document


def test_round_trip(handler: XmlHandler, tmp_path: Path, sample_document: ConfigDocument) -> None:
    target = tmp_path / "out.xml"
    handler.write(sample_document, target)
    assert handler.read(target) == sample_document


def test_write_matches_sample_file(
    handler: XmlHandler, tmp_path: Path, samples_dir: Path, sample_document: ConfigDocument
) -> None:
    target = tmp_path / "out.xml"
    handler.write(sample_document, target)
    expected = (samples_dir / "app_config.xml").read_text(encoding="utf-8")
    assert target.read_text(encoding="utf-8") == expected


def test_write_creates_parent_dirs(
    handler: XmlHandler, tmp_path: Path, sample_document: ConfigDocument
) -> None:
    target = tmp_path / "nested" / "out.xml"
    handler.write(sample_document, target)
    assert target.is_file()


def test_write_escapes_special_characters(handler: XmlHandler, tmp_path: Path) -> None:
    doc: ConfigDocument = {
        "metadata": {"name": "a&b", "version": "1.0.0", "description": "<tags> & more"},
        "entries": [{"section": "s", "key": "k", "value": "x < y & \"z\"", "type": "str",
                     "description": "it's \"quoted\""}],
    }
    target = tmp_path / "out.xml"
    handler.write(doc, target)
    ET.parse(target)  # still well-formed
    assert handler.read(target) == doc


def test_empty_string_value(handler: XmlHandler, tmp_path: Path) -> None:
    doc: ConfigDocument = {
        "metadata": {"name": "app", "version": "1.0.0"},
        "entries": [{"section": "s", "key": "k", "value": "", "type": "str"}],
    }
    target = tmp_path / "out.xml"
    handler.write(doc, target)
    assert handler.read(target) == doc


def test_wrong_root_raises(handler: XmlHandler, tmp_path: Path) -> None:
    path = write_xml(tmp_path / "a.xml", "<settings/>")
    with pytest.raises(ValueError, match="root element must be <config>, got <settings>"):
        handler.read(path)


def test_missing_attribute_raises(handler: XmlHandler, tmp_path: Path) -> None:
    path = write_xml(tmp_path / "a.xml", '<config><entry section="s" type="int">1</entry></config>')
    with pytest.raises(ValueError, match="entry 1: missing attributes: key"):
        handler.read(path)


def test_bad_value_reports_entry(handler: XmlHandler, tmp_path: Path) -> None:
    path = write_xml(
        tmp_path / "a.xml",
        '<config><entry section="s" key="a" type="int">1</entry>'
        '<entry section="s" key="b" type="bool">maybe</entry></config>',
    )
    with pytest.raises(ValueError, match="entry 2: cannot convert 'maybe' to bool"):
        handler.read(path)


def test_malformed_xml_raises(handler: XmlHandler, tmp_path: Path) -> None:
    path = write_xml(tmp_path / "a.xml", "<config><entry>")
    with pytest.raises(ET.ParseError):
        handler.read(path)


def test_read_requires_metadata(handler: XmlHandler, tmp_path: Path) -> None:
    path = write_xml(tmp_path / "a.xml", '<config version="1"/>')
    with pytest.raises(ConfigValidationError, match="metadata.name: is required"):
        handler.read(path)
