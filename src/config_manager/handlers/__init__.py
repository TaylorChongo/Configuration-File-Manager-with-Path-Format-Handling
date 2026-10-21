"""Format handlers and a registry that picks one by file extension."""

from pathlib import Path

from config_manager.handlers.csv_handler import CsvHandler
from config_manager.handlers.json_handler import JsonHandler
from config_manager.handlers.xml_handler import XmlHandler
from config_manager.protocols import FormatHandler

HANDLERS: tuple[FormatHandler, ...] = (JsonHandler(), CsvHandler(), XmlHandler())


def get_handler(path: Path) -> FormatHandler:
    """Return the handler registered for ``path``'s suffix."""
    suffix = path.suffix.lower()
    for handler in HANDLERS:
        if suffix in handler.extensions:
            return handler
    raise ValueError(f"Unsupported config format: {suffix!r}")


__all__ = ["CsvHandler", "JsonHandler", "XmlHandler", "HANDLERS", "get_handler"]
