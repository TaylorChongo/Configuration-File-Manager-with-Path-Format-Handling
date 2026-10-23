"""Tests for converting values between strings and Python types."""

from typing import Any

import pytest

from config_manager.schemas import ConfigDocument, ConfigEntry
from config_manager.validation import coerce_value, entry_to_strings


@pytest.mark.parametrize(
    ("text", "value_type", "expected"),
    [
        ("localhost", "str", "localhost"),
        ("", "str", ""),
        ("5432", "int", 5432),
        (" 42 ", "int", 42),
        ("-7", "int", -7),
        ("30.5", "float", 30.5),
        ("1e3", "float", 1000.0),
        ("4", "float", 4.0),
        ("true", "bool", True),
        ("True", "bool", True),
        ("YES", "bool", True),
        ("1", "bool", True),
        ("false", "bool", False),
        (" no ", "bool", False),
        ("0", "bool", False),
    ],
)
def test_coerce_value(text: str, value_type: Any, expected: object) -> None:
    result = coerce_value(text, value_type)
    assert result == expected
    assert type(result) is type(expected)


@pytest.mark.parametrize(
    ("text", "value_type"),
    [
        ("abc", "int"),
        ("5.0", "int"),
        ("", "int"),
        ("fast", "float"),
        ("maybe", "bool"),
        ("2", "bool"),
        ("", "bool"),
    ],
)
def test_coerce_value_rejects_bad_input(text: str, value_type: Any) -> None:
    with pytest.raises(ValueError, match=f"cannot convert {text!r} to {value_type}"):
        coerce_value(text, value_type)


def test_coerce_value_rejects_unknown_type() -> None:
    with pytest.raises(ValueError, match="unsupported type 'enum'"):
        coerce_value("fast", "enum")  # type: ignore[arg-type]


def test_entry_to_strings() -> None:
    entry: ConfigEntry = {
        "section": "database", "key": "port", "value": 5432, "type": "int",
        "description": "Database port",
    }
    assert entry_to_strings(entry) == {
        "section": "database", "key": "port", "value": "5432", "type": "int",
        "description": "Database port",
    }


@pytest.mark.parametrize(("value", "expected"), [(True, "true"), (False, "false")])
def test_entry_to_strings_bool_is_lowercase(value: bool, expected: str) -> None:
    entry: ConfigEntry = {"section": "server", "key": "debug", "value": value, "type": "bool"}
    assert entry_to_strings(entry)["value"] == expected


def test_entry_to_strings_missing_description_is_empty() -> None:
    entry: ConfigEntry = {"section": "server", "key": "workers", "value": 4, "type": "int"}
    assert entry_to_strings(entry)["description"] == ""


def test_round_trip_through_strings(sample_document: ConfigDocument) -> None:
    for entry in sample_document["entries"]:
        flat = entry_to_strings(entry)
        assert coerce_value(flat["value"], entry["type"]) == entry["value"]
