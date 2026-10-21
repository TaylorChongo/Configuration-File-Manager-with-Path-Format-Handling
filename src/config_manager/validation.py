"""Validate raw data against the TypedDict schemas in ``schemas.py``."""

from typing import Any

from config_manager.schemas import (
    ConfigDocument,
    ConfigEntry,
    ConfigValue,
    ValidationIssue,
    ValueType,
)


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
    """Convert a string read from CSV/XML into its declared Python type."""
    # TODO (Day 3-4): "bool" -> accept true/false/1/0/yes/no
    raise NotImplementedError


def entry_to_strings(entry: ConfigEntry) -> dict[str, str]:
    """Flatten an entry to strings for text formats (CSV/XML)."""
    # TODO (Day 3-4)
    raise NotImplementedError
