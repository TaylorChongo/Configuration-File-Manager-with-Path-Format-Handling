"""Convert config files between formats via the shared ``ConfigDocument`` model."""

from pathlib import Path

from config_manager.pipeline import Transform


def convert(source: Path, target: Path, *, transform: Transform | None = None) -> Path:
    """Read ``source``, optionally transform entries, write ``target``.

    Handlers are chosen from each path's suffix (``handlers.get_handler``).
    """
    # TODO (Day 3-4)
    raise NotImplementedError
