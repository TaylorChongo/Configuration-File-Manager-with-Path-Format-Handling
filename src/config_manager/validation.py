"""Validate raw data against the TypedDict schemas in ``schemas.py``."""

from collections.abc import Mapping
from typing import Any, cast

from config_manager.schemas import (
    SUPPORTED_VALUE_TYPES,
    ConfigDocument,
    ConfigEntry,
    ConfigMetadata,
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


def _issue(location: str, message: str) -> ValidationIssue:
    return {"location": location, "message": message}


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _value_matches(value: object, value_type: str) -> bool:
    # bool is a subclass of int, so it must be excluded from int/float explicitly
    if isinstance(value, bool):
        return value_type == "bool"
    match value_type:
        case "str":
            return isinstance(value, str)
        case "int":
            return isinstance(value, int)
        case "float":
            return isinstance(value, int | float)  # 4 is accepted as 4.0
    return False


def _check_required_str(
    raw: Mapping[str, Any], field: str, location: str
) -> list[ValidationIssue]:
    if field not in raw:
        return [_issue(f"{location}.{field}", "is required")]
    if not _is_non_empty_str(raw[field]):
        return [_issue(f"{location}.{field}", "must be a non-empty string")]
    return []


def _check_optional_str(
    raw: Mapping[str, Any], field: str, location: str
) -> list[ValidationIssue]:
    if field in raw and not isinstance(raw[field], str):
        return [_issue(f"{location}.{field}", "must be a string")]
    return []


def validate_entry(raw: object, location: str = "entry") -> list[ValidationIssue]:
    """Return issues for a single entry (empty list when valid)."""
    if not isinstance(raw, Mapping):
        return [_issue(location, "must be an object")]

    issues = [
        *_check_required_str(raw, "section", location),
        *_check_required_str(raw, "key", location),
    ]
    value_type = raw.get("type")
    if "type" not in raw:
        issues.append(_issue(f"{location}.type", "is required"))
    elif not isinstance(value_type, str) or value_type not in SUPPORTED_VALUE_TYPES:
        expected = ", ".join(sorted(SUPPORTED_VALUE_TYPES))
        issues.append(
            _issue(f"{location}.type", f"unsupported type {value_type!r} (expected {expected})")
        )
        value_type = None  # can't check the value against an unknown type

    if "value" not in raw:
        issues.append(_issue(f"{location}.value", "is required"))
    elif value_type is not None and not _value_matches(raw["value"], value_type):
        value = raw["value"]
        issues.append(
            _issue(
                f"{location}.value",
                f"expected {value_type}, got {type(value).__name__} {value!r}",
            )
        )
    issues.extend(_check_optional_str(raw, "description", location))
    return issues


def is_valid_entry(raw: object) -> bool:
    """Predicate suitable for ``filter()``."""
    return not validate_entry(raw)


def _validate_metadata(raw: object) -> list[ValidationIssue]:
    if not isinstance(raw, Mapping):
        return [_issue("metadata", "must be an object")]
    return [
        *_check_required_str(raw, "name", "metadata"),
        *_check_required_str(raw, "version", "metadata"),
        *_check_optional_str(raw, "description", "metadata"),
    ]


def _validate_entries(raw: object) -> list[ValidationIssue]:
    if not isinstance(raw, list):
        return [_issue("entries", "must be a list")]
    issues: list[ValidationIssue] = []
    first_seen: dict[tuple[str, str], int] = {}
    for index, entry in enumerate(raw):
        location = f"entries[{index}]"
        entry_issues = validate_entry(entry, location)
        issues.extend(entry_issues)
        if entry_issues:
            continue
        name = (entry["section"], entry["key"])
        if name in first_seen:
            issues.append(
                _issue(
                    location,
                    f"duplicate key '{name[0]}.{name[1]}' "
                    f"(first defined at entries[{first_seen[name]}])",
                )
            )
        else:
            first_seen[name] = index
    return issues


def _clean_entry(raw: Mapping[str, Any]) -> ConfigEntry:
    entry = cast(ConfigEntry, dict(raw))
    if entry["type"] == "float":
        entry["value"] = float(entry["value"])
    return entry


def validate_document(raw: object) -> ConfigDocument:
    """Validate and return ``raw`` as a ``ConfigDocument`` or raise ``ConfigValidationError``.

    Every problem is collected before raising, so one error lists them all.
    The returned document is a copy; integer values of ``float`` entries become floats.
    """
    if not isinstance(raw, Mapping):
        raise ConfigValidationError([_issue("document", "must be an object")])

    issues: list[ValidationIssue] = []
    for field, check in (("metadata", _validate_metadata), ("entries", _validate_entries)):
        if field in raw:
            issues.extend(check(raw[field]))
        else:
            issues.append(_issue(field, "is required"))
    if issues:
        raise ConfigValidationError(issues)

    return {
        "metadata": cast(ConfigMetadata, dict(raw["metadata"])),
        "entries": [_clean_entry(entry) for entry in raw["entries"]],
    }


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
