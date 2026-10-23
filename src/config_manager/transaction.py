"""Custom context manager for atomic config updates.

Usage::

    with ConfigTransaction(Path("samples/app_config.json")) as doc:
        doc["metadata"]["version"] = "1.1.0"
    # written atomically on success; original untouched if the block raises
"""

import copy
import os
import tempfile
from pathlib import Path
from types import TracebackType
from typing import Literal

from config_manager.handlers import get_handler
from config_manager.protocols import FormatHandler
from config_manager.schemas import ConfigDocument
from config_manager.validation import validate_document


class ConfigTransaction:
    """Edit a config file in memory and save it all-or-nothing.

    On a clean exit the edited document is validated, written to a hidden temp
    file in the same directory, then swapped in with ``Path.replace`` (atomic on
    the same filesystem). If the block raises, validation fails or the write
    fails, the original file is left untouched and the temp file is removed.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self._handler: FormatHandler = get_handler(path)
        self._original: ConfigDocument | None = None
        self._document: ConfigDocument | None = None

    def __enter__(self) -> ConfigDocument:
        self._original = self._handler.read(self.path)
        self._document = copy.deepcopy(self._original)
        return self._document

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[False]:
        document, original = self._document, self._original
        self._document = self._original = None
        if exc_type is None and document is not None and document != original:
            self._commit(validate_document(document))
        return False  # never swallow exceptions from the with-block

    def _commit(self, document: ConfigDocument) -> None:
        fd, name = tempfile.mkstemp(
            dir=self.path.parent, prefix=f".{self.path.name}.", suffix=".tmp"
        )
        os.close(fd)
        temp = Path(name)
        try:
            self._handler.write(document, temp)
            temp.replace(self.path)
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
