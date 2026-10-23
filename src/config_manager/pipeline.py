"""Functional transformation pipeline built from ``map()`` and ``filter()``."""

from collections.abc import Callable, Iterable, Iterator
from functools import reduce

from config_manager.schemas import ConfigEntry

Transform = Callable[[Iterable[ConfigEntry]], Iterable[ConfigEntry]]


def compose(*steps: Transform) -> Transform:
    """Chain ``steps`` left-to-right into a single lazy transform."""
    return lambda entries: reduce(lambda acc, step: step(acc), steps, entries)


def filter_valid(entries: Iterable[ConfigEntry]) -> Iterator[ConfigEntry]:
    # TODO (Day 5-6): filter(is_valid_entry, entries)
    raise NotImplementedError


def _normalise_entry(entry: ConfigEntry) -> ConfigEntry:
    normalised = entry.copy()  # never mutate the caller's entry
    normalised["section"] = entry["section"].strip().lower()
    normalised["key"] = entry["key"].strip().lower()
    return normalised


def normalise_keys(entries: Iterable[ConfigEntry]) -> Iterator[ConfigEntry]:
    """Strip whitespace and lower-case each entry's section and key."""
    return map(_normalise_entry, entries)


def select_section(section: str) -> Transform:
    """Return a transform keeping only entries in ``section`` (exact match).

    Compose after ``normalise_keys`` for a case-insensitive match.
    """
    return lambda entries: filter(lambda entry: entry["section"] == section, entries)
