"""Protocol defining the interface every format handler must satisfy."""

from collections.abc import Iterator
from pathlib import Path
from typing import Protocol, runtime_checkable

from config_manager.schemas import ConfigDocument, ConfigEntry


@runtime_checkable
class FormatHandler(Protocol):
    """Structural interface for JSON / CSV / XML handlers.

    Any class providing these members is a valid handler; no inheritance needed.
    """

    #: File extensions this handler owns, e.g. ``(".json",)``.
    extensions: tuple[str, ...]

    def read(self, path: Path) -> ConfigDocument:
        """Load the whole document into memory."""
        ...

    def write(self, document: ConfigDocument, path: Path) -> None:
        """Serialise ``document`` to ``path``."""
        ...

    def iter_entries(self, path: Path) -> Iterator[ConfigEntry]:
        """Yield entries one at a time without loading the full file."""
        ...
