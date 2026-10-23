"""Validate raw data against the TypedDict schemas in ``schemas.py``."""

from typing import Any

from config_manager.schemas import (
    ConfigDocument,
    ConfigEntry,
    ConfigValue,
    ValidationIssue,
    ValueType,
)

_TRUE_STRINGS: frozenset[str] = frozenset({"true", "1", "yes"})
_FALSE_STRINGS: frozenset[str] = frozenset({"false", "0", "no"})


class ConfigValidationError(ValueError):
    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues
        super().__init__("; ".join(f"{i['location']}: {i['message']}" for i in issues))


def validate_entry(raw: dict[str, Any], location: str = "entry") -> list[ValidationIssue]:
    """Return issues for a single entry (empty list when valid)."""
    # TODO (Day 5-6): required keys, type in SUPPORTED_VALUE_TYPES, value matches type
    raise NotImplementedError


def is_valid_entry(raw: dict[str, Any]) -> bool:
    """Predicate suitable for ``filter()``."""
    return not validate_entry(raw)


def validate_document(raw: dict[str, Any]) -> ConfigDocument:
    """Validate and return ``raw`` as a ``ConfigDocument`` or raise ``ConfigValidationError``."""
    # TODO (Day 5-6)
    raise NotImplementedError


def coerce_value(value: str, value_type: ValueType) -> ConfigValue:
    """Convert a string read from CSV/XML into its declared Python type.

    Raises ``ValueError`` if ``value`` can't be read as ``value_type``.
    """
    try:
        match value_type:
            case "str":
                return value
            case "int":
                return int(value)
            case "float":
                return float(value)
            case "bool":
                text = value.strip().lower()
                if text in _TRUE_STRINGS:
                    return True
                if text in _FALSE_STRINGS:
                    return False
                raise ValueError
    except ValueError:
        raise ValueError(f"cannot convert {value!r} to {value_type}") from None
    raise ValueError(f"unsupported type {value_type!r}")


def entry_to_strings(entry: ConfigEntry) -> dict[str, str]:
    """Flatten an entry to strings for text formats (CSV/XML).

    Booleans become ``"true"``/``"false"``; a missing description becomes ``""``.
    """
    value = entry["value"]
    return {
        "section": entry["section"],
        "key": entry["key"],
        "value": str(value).lower() if isinstance(value, bool) else str(value),
        "type": entry["type"],
        "description": entry.get("description", ""),
    }
