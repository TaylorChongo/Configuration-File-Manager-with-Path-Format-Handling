"""JSON reader/writer.

File layout::

    {"metadata": {...}, "entries": [{"section": ..., "key": ..., ...}, ...]}
"""

from collections.abc import Iterator
from pathlib import Path

from config_manager.schemas import ConfigDocument, ConfigEntry


class JsonHandler:
    extensions: tuple[str, ...] = (".json",)

    def read(self, path: Path) -> ConfigDocument:
        # TODO (Day 1-2): open with `with path.open(encoding="utf-8")`, json.load, validate
        raise NotImplementedError

    def write(self, document: ConfigDocument, path: Path) -> None:
        # TODO (Day 1-2): mkdir parents, json.dump with indent=2
        raise NotImplementedError

    def iter_entries(self, path: Path) -> Iterator[ConfigEntry]:
        # TODO (Day 7): JSON isn't line-oriented; yield from read()["entries"]
        # or support JSON Lines (.jsonl) for true streaming
        raise NotImplementedError
