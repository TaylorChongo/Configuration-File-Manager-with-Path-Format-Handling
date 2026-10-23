"""CSV reader/writer using ``csv.DictReader`` / ``csv.DictWriter``.

One row per entry. Header: ``section,key,value,type,description``.
Document metadata is stored in leading ``#`` comment lines::

    # name=app
    # version=1.0.0
    section,key,value,type,description
    database,host,localhost,str,Database host
"""

import csv
from collections.abc import Iterator
from itertools import takewhile
from pathlib import Path
from typing import cast

from config_manager.schemas import ConfigDocument, ConfigEntry, ConfigMetadata, ValueType
from config_manager.validation import coerce_value, entry_to_strings, validate_document

FIELDNAMES: tuple[str, ...] = ("section", "key", "value", "type", "description")
REQUIRED_FIELDS: frozenset[str] = frozenset({"section", "key", "value", "type"})


def _is_comment(line: str) -> bool:
    return line.startswith("#")


class CsvHandler:
    extensions: tuple[str, ...] = (".csv",)

    def read(self, path: Path) -> ConfigDocument:
        return validate_document(
            {"metadata": self.read_metadata(path), "entries": list(self.iter_entries(path))}
        )

    def read_metadata(self, path: Path) -> ConfigMetadata:
        """Parse the leading ``# key=value`` comment lines."""
        metadata: dict[str, str] = {}
        with path.open(encoding="utf-8", newline="") as fh:
            for line in takewhile(_is_comment, fh):
                key, sep, value = line[1:].strip().partition("=")
                if sep:
                    metadata[key.strip()] = value.strip()
        return cast(ConfigMetadata, metadata)

    def write(self, document: ConfigDocument, path: Path) -> None:
        # Checked before opening, so an existing file is never left half-written
        for key, value in document["metadata"].items():
            if isinstance(value, str) and ("\n" in value or "\r" in value):
                raise ValueError(f"CSV metadata '{key}' cannot contain line breaks")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as fh:
            for key, value in document["metadata"].items():
                fh.write(f"# {key}={value}\n")
            writer = csv.DictWriter(fh, fieldnames=FIELDNAMES, lineterminator="\n")
            writer.writeheader()
            writer.writerows(map(entry_to_strings, document["entries"]))

    def iter_entries(self, path: Path) -> Iterator[ConfigEntry]:
        """Yield one coerced entry per row, reading the file lazily."""
        with path.open(encoding="utf-8", newline="") as fh:
            # Skip leading comments with readline/tell so their count is known for error lines
            comment_lines, start = 0, fh.tell()
            while _is_comment(fh.readline()):
                comment_lines, start = comment_lines + 1, fh.tell()
            fh.seek(start)
            reader = csv.DictReader(fh)
            missing = REQUIRED_FIELDS - set(reader.fieldnames or ())
            if missing:
                raise ValueError(f"{path}: missing CSV columns: {', '.join(sorted(missing))}")
            for row in reader:
                value_type = cast(ValueType, row["type"])
                try:
                    value = coerce_value(row["value"], value_type)
                except ValueError as exc:
                    line = comment_lines + reader.line_num
                    raise ValueError(f"{path}, line {line}: {exc}") from None
                entry: ConfigEntry = {
                    "section": row["section"],
                    "key": row["key"],
                    "value": value,
                    "type": value_type,
                }
                if row.get("description"):
                    entry["description"] = row["description"]
                yield entry
