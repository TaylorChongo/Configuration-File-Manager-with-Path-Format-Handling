"""Tests for schema validation."""

import json
from pathlib import Path
from typing import Any

import pytest

from config_manager.schemas import ConfigDocument
from config_manager.validation import (
    ConfigValidationError,
    is_valid_entry,
    validate_document,
    validate_entry,
)


def valid_entry(**overrides: Any) -> dict[str, Any]:
    return {"section": "s", "key": "k", "value": 1, "type": "int", **overrides}


def locations(issues: list[Any]) -> list[str]:
    return [issue["location"] for issue in issues]


# --- validate_entry -------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "value_type"),
    [("x", "str"), ("", "str"), (1, "int"), (-5, "int"), (1.5, "float"), (4, "float"),
     (True, "bool"), (False, "bool")],
)
def test_valid_entries(value: object, value_type: str) -> None:
    assert validate_entry(valid_entry(value=value, type=value_type)) == []


@pytest.mark.parametrize(
    ("value", "value_type"),
    [(1, "str"), ("1", "int"), (1.5, "int"), (True, "int"), (False, "float"),
     ("1.5", "float"), (1, "bool"), ("true", "bool"), (None, "str")],
)
def test_value_must_match_type(value: object, value_type: str) -> None:
    issues = validate_entry(valid_entry(value=value, type=value_type), "e")
    assert locations(issues) == ["e.value"]
    assert issues[0]["message"].startswith(f"expected {value_type}, got")


@pytest.mark.parametrize("field", ["section", "key", "value", "type"])
def test_required_fields(field: str) -> None:
    raw = valid_entry()
    del raw[field]
    assert validate_entry(raw, "e") == [{"location": f"e.{field}", "message": "is required"}]


@pytest.mark.parametrize("bad", ["", "   ", 5, None])
def test_section_and_key_must_be_non_empty_strings(bad: object) -> None:
    issues = validate_entry(valid_entry(section=bad, key=bad), "e")
    assert locations(issues) == ["e.section", "e.key"]


@pytest.mark.parametrize("bad_type", ["enum", "INT", 3, None])
def test_unsupported_type(bad_type: object) -> None:
    issues = validate_entry(valid_entry(type=bad_type), "e")
    assert locations(issues) == ["e.type"]  # value isn't checked against an unknown type
    assert "unsupported type" in issues[0]["message"]


def test_description_must_be_string() -> None:
    assert locations(validate_entry(valid_entry(description=3), "e")) == ["e.description"]


def test_entry_must_be_object() -> None:
    assert validate_entry(["not", "a", "dict"], "e") == [
        {"location": "e", "message": "must be an object"}
    ]


def test_reports_every_problem() -> None:
    issues = validate_entry({"section": "", "value": "x", "type": "int"}, "e")
    assert locations(issues) == ["e.section", "e.key", "e.value"]


def test_is_valid_entry() -> None:
    assert is_valid_entry(valid_entry())
    assert not is_valid_entry(valid_entry(value="x"))


# --- validate_document ----------------------------------------------------


def test_valid_document(sample_document: ConfigDocument) -> None:
    result = validate_document(sample_document)
    assert result == sample_document
    assert result is not sample_document  # returns a copy


def test_converts_int_to_float() -> None:
    doc = validate_document({
        "metadata": {"name": "a", "version": "1"},
        "entries": [valid_entry(value=4, type="float")],
    })
    assert isinstance(doc["entries"][0]["value"], float)


def test_invalid_fixture_lists_every_issue(fixtures_dir: Path) -> None:
    raw = json.loads((fixtures_dir / "invalid_config.json").read_text(encoding="utf-8"))
    with pytest.raises(ConfigValidationError) as info:
        validate_document(raw)
    assert locations(info.value.issues) == [
        "metadata.version", "entries[0].value", "entries[1].key", "entries[2].type",
    ]
    assert "entries[0].value: expected int, got str 'not-a-number'" in str(info.value)


def test_document_must_be_object() -> None:
    with pytest.raises(ConfigValidationError, match="document: must be an object"):
        validate_document([1, 2, 3])


def test_metadata_and_entries_required() -> None:
    with pytest.raises(ConfigValidationError) as info:
        validate_document({})
    assert locations(info.value.issues) == ["metadata", "entries"]


@pytest.mark.parametrize(
    ("raw", "location"),
    [
        ({"metadata": "x", "entries": []}, "metadata"),
        ({"metadata": {"name": "a", "version": "1"}, "entries": {}}, "entries"),
        ({"metadata": {"name": "", "version": "1"}, "entries": []}, "metadata.name"),
        ({"metadata": {"name": "a", "version": "1", "description": 1}, "entries": []},
         "metadata.description"),
    ],
)
def test_bad_structure(raw: dict[str, Any], location: str) -> None:
    with pytest.raises(ConfigValidationError) as info:
        validate_document(raw)
    assert locations(info.value.issues) == [location]


def test_duplicate_keys() -> None:
    raw = {
        "metadata": {"name": "a", "version": "1"},
        "entries": [valid_entry(), valid_entry(section="other"), valid_entry(value=2)],
    }
    with pytest.raises(ConfigValidationError, match=r"entries\[2\]: duplicate key 's.k' "
                                                    r"\(first defined at entries\[0\]\)"):
        validate_document(raw)


def test_error_is_a_value_error() -> None:
    with pytest.raises(ValueError):
        validate_document({})
