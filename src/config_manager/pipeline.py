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


def normalise_keys(entries: Iterable[ConfigEntry]) -> Iterator[ConfigEntry]:
    # TODO (Day 3-4): map() — strip + lower-case section/key
    raise NotImplementedError


def select_section(section: str) -> Transform:
    """Return a transform keeping only entries in ``section``."""
    # TODO (Day 3-4): filter() with a closure
    raise NotImplementedError
