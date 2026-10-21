"""Custom context manager for atomic config updates.

Usage::

    with ConfigTransaction(Path("samples/app_config.json")) as doc:
        doc["metadata"]["version"] = "1.1.0"
    # written atomically on success; original untouched if the block raises
"""

from pathlib import Path
from types import TracebackType

from config_manager.schemas import ConfigDocument


class ConfigTransaction:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._document: ConfigDocument | None = None

    def __enter__(self) -> ConfigDocument:
        # TODO (Day 5-6): load via handler, deep-copy for editing
        raise NotImplementedError

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        # TODO (Day 5-6): on success write to a temp file then Path.replace();
        # on error discard changes and clean up temp file. Return False to re-raise.
        raise NotImplementedError
