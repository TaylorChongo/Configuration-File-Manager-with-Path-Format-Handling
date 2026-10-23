"""JSON reader/writer.

File layout::

    {"metadata": {...}, "entries": [{"section": ..., "key": ..., ...}, ...]}
"""

import json
from collections.abc import Iterator
from pathlib import Path

from config_manager.schemas import ConfigDocument, ConfigEntry
from config_manager.validation import validate_document


class JsonHandler:
    extensions: tuple[str, ...] = (".json",)

    def read(self, path: Path) -> ConfigDocument:
        with path.open(encoding="utf-8") as fh:
            return validate_document(json.load(fh))

    def write(self, document: ConfigDocument, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(document, fh, indent=2, ensure_ascii=False)
            fh.write("\n")

    def iter_entries(self, path: Path) -> Iterator[ConfigEntry]:
        # TODO (Day 7): JSON isn't line-oriented; yield from read()["entries"]
        # or support JSON Lines (.jsonl) for true streaming
        raise NotImplementedError
