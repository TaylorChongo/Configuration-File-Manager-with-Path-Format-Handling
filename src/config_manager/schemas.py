"""TypedDict schemas describing a configuration document.

A config document is format-agnostic: every handler reads into and writes
from these structures, which is what makes lossless conversion possible.

    ConfigDocument
    ├── metadata: ConfigMetadata   (name, version, optional description)
    └── entries:  list[ConfigEntry] (section, key, value, type, ...)
"""

from typing import Literal, NotRequired, TypedDict

ValueType = Literal["str", "int", "float", "bool"]
ConfigValue = str | int | float | bool

SUPPORTED_VALUE_TYPES: frozenset[str] = frozenset({"str", "int", "float", "bool"})


class ConfigEntry(TypedDict):
    """A single key/value setting inside a section."""

    section: str
    key: str
    value: ConfigValue
    type: ValueType
    description: NotRequired[str]


class ConfigMetadata(TypedDict):
    """Information about the config document itself."""

    name: str
    version: str
    description: NotRequired[str]


class ConfigDocument(TypedDict):
    """Top-level structure shared by all formats."""

    metadata: ConfigMetadata
    entries: list[ConfigEntry]


class ValidationIssue(TypedDict):
    """A single problem found while validating a document or entry."""

    location: str
    message: str
