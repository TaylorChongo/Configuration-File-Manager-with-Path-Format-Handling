"""Convert config files between formats via the shared ``ConfigDocument`` model."""

from pathlib import Path

from config_manager.handlers import get_handler
from config_manager.pipeline import Transform
from config_manager.schemas import ConfigDocument


def convert(source: Path, target: Path, *, transform: Transform | None = None) -> Path:
    """Read ``source``, optionally transform entries, write ``target``.

    Handlers are chosen from each path's suffix (``handlers.get_handler``).
    Both suffixes are checked before anything is read, and ``source`` is never
    overwritten.
    """
    reader = get_handler(source)
    writer = get_handler(target)
    if source.resolve() == target.resolve():
        raise ValueError(f"Source and target are the same file: {source}")

    document = reader.read(source)
    if transform is not None:
        document = ConfigDocument(
            metadata=document["metadata"],
            entries=list(transform(document["entries"])),
        )
    writer.write(document, target)
    return target
