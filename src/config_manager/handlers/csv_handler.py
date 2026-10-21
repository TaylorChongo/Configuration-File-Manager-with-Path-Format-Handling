"""CSV reader/writer using ``csv.DictReader`` / ``csv.DictWriter``.

One row per entry. Header: ``section,key,value,type,description``.
Document metadata is stored in leading ``#`` comment lines::

    # name=app
    # version=1.0.0
    section,key,value,type,description
    database,host,localhost,str,Database host
"""

from collections.abc import Iterator
from pathlib import Path

from config_manager.schemas import ConfigDocument, ConfigEntry

FIELDNAMES: tuple[str, ...] = ("section", "key", "value", "type", "description")


class CsvHandler:
    extensions: tuple[str, ...] = (".csv",)

    def read(self, path: Path) -> ConfigDocument:
        # TODO (Day 3-4): parse metadata comments, then list(self.iter_entries(path))
        raise NotImplementedError

    def write(self, document: ConfigDocument, path: Path) -> None:
        # TODO (Day 3-4): write metadata comments, then DictWriter rows
        raise NotImplementedError

    def iter_entries(self, path: Path) -> Iterator[ConfigEntry]:
        # TODO (Day 7): generator — open with newline="", skip comments,
        # yield one coerced ConfigEntry per DictReader row
        raise NotImplementedError
