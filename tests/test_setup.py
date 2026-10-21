"""Smoke tests confirming the project skeleton is wired up correctly."""

from pathlib import Path

import pytest

from config_manager.handlers import HANDLERS, get_handler
from config_manager.protocols import FormatHandler


def test_sample_files_exist(samples_dir: Path) -> None:
    for suffix in (".json", ".csv", ".xml"):
        assert (samples_dir / f"app_config{suffix}").is_file()


@pytest.mark.parametrize("handler", HANDLERS, ids=lambda h: type(h).__name__)
def test_handlers_satisfy_protocol(handler: FormatHandler) -> None:
    assert isinstance(handler, FormatHandler)


@pytest.mark.parametrize("name", ["a.json", "a.csv", "a.XML"])
def test_get_handler_by_suffix(name: str) -> None:
    assert get_handler(Path(name)) is not None


def test_get_handler_rejects_unknown_suffix() -> None:
    with pytest.raises(ValueError):
        get_handler(Path("a.yaml"))
