"""Tests for the map()/filter() transformation pipeline."""

from collections.abc import Iterable, Iterator

from config_manager.pipeline import compose, normalise_keys, select_section
from config_manager.schemas import ConfigDocument, ConfigEntry


def entry(section: str, key: str) -> ConfigEntry:
    return {"section": section, "key": key, "value": 1, "type": "int"}


def keys(entries: Iterable[ConfigEntry]) -> list[str]:
    return [e["key"] for e in entries]


def test_normalise_keys() -> None:
    result = list(normalise_keys([entry("  Database ", " Max_Conn"), entry("SERVER", "Port")]))
    assert [(e["section"], e["key"]) for e in result] == [
        ("database", "max_conn"),
        ("server", "port"),
    ]


def test_normalise_keys_keeps_other_fields() -> None:
    original: ConfigEntry = {"section": "DB", "key": "Host", "value": "Localhost", "type": "str",
                             "description": "Keep Me"}
    (result,) = normalise_keys([original])
    assert result == {"section": "db", "key": "host", "value": "Localhost", "type": "str",
                      "description": "Keep Me"}


def test_normalise_keys_does_not_mutate_input() -> None:
    original = entry("DB", "Host")
    list(normalise_keys([original]))
    assert original == entry("DB", "Host")


def test_select_section(sample_document: ConfigDocument) -> None:
    result = select_section("database")(sample_document["entries"])
    assert keys(result) == ["host", "port", "pool_timeout"]


def test_select_section_no_match(sample_document: ConfigDocument) -> None:
    assert list(select_section("missing")(sample_document["entries"])) == []


def test_select_section_is_case_sensitive() -> None:
    assert list(select_section("database")([entry("Database", "host")])) == []


def test_transforms_are_lazy() -> None:
    consumed: list[str] = []

    def source() -> Iterator[ConfigEntry]:
        for name in ("a", "b", "c"):
            consumed.append(name)
            yield entry("s", name)

    pipeline = compose(normalise_keys, select_section("s"))
    result = iter(pipeline(source()))
    assert consumed == []  # nothing read until we iterate
    next(result)
    assert consumed == ["a"]


def test_compose_normalise_then_select() -> None:
    entries = [entry("Database", "Host"), entry("server", "port"), entry(" DATABASE", "Port")]
    pipeline = compose(normalise_keys, select_section("database"))
    assert keys(pipeline(entries)) == ["host", "port"]


def test_compose_order_matters() -> None:
    entries = [entry("Database", "Host")]
    pipeline = compose(select_section("database"), normalise_keys)
    assert list(pipeline(entries)) == []  # filtered before normalising


def test_compose_with_no_steps_is_identity(sample_document: ConfigDocument) -> None:
    entries = sample_document["entries"]
    assert list(compose()(entries)) == entries
