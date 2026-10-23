"""Command-line entry point: ``config-manager <command> ...``."""

import argparse
import sys
import xml.etree.ElementTree as ET
from collections.abc import Callable, Sequence
from pathlib import Path

from config_manager.converter import convert
from config_manager.handlers import get_handler
from config_manager.paths import ConfigTreeIterator, inspect_file
from config_manager.validation import ConfigValidationError
from config_manager.versioning import list_versions, restore_version, save_version


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="config-manager", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    discover = sub.add_parser("discover", help="list config files under a directory")
    discover.add_argument("root")

    validate = sub.add_parser("validate", help="validate a config file")
    validate.add_argument("path")

    convert = sub.add_parser("convert", help="convert between formats")
    convert.add_argument("source")
    convert.add_argument("target")

    version = sub.add_parser("version", help="save / list / restore config versions")
    version.add_argument("action", choices=["save", "list", "restore"])
    version.add_argument("path")
    version.add_argument(
        "-n", "--number", type=int, help="version to restore, as numbered by 'version list'"
    )

    return parser


def _discover(args: argparse.Namespace) -> int:
    root = Path(args.root)
    paths = list(ConfigTreeIterator(root))
    for path in paths:
        info = inspect_file(path)
        print(f"{info.size_bytes:>10,} B  {info.modified:%Y-%m-%d %H:%M}  {path}")
    print(f"{len(paths)} config file(s) under {root}")
    return 0


def _validate(args: argparse.Namespace) -> int:
    path = Path(args.path)
    document = get_handler(path).read(path)
    print(f"{path}: valid ({len(document['entries'])} entries)")
    return 0


def _convert(args: argparse.Namespace) -> int:
    source, target = Path(args.source), Path(args.target)
    convert(source, target)
    print(f"Converted {source} -> {target}")
    return 0


def _version(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if args.action == "save":
        print(f"Saved {save_version(path)}")
        return 0

    versions = list_versions(path)
    if args.action == "list":
        if not versions:
            print(f"No saved versions of {path}")
        for number, version in enumerate(versions, start=1):
            print(f"{number:>3}  {version.name}")
        return 0

    if args.number is None:
        raise ValueError("restore needs --number N (see 'version list')")
    if not 1 <= args.number <= len(versions):
        raise ValueError(f"no version {args.number}; {path} has {len(versions)} saved")
    restore_version(path, versions[args.number - 1])
    print(f"Restored {path} from {versions[args.number - 1].name}")
    return 0


COMMANDS: dict[str, Callable[[argparse.Namespace], int]] = {
    "discover": _discover,
    "validate": _validate,
    "convert": _convert,
    "version": _version,
}


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return COMMANDS[args.command](args)
    except ConfigValidationError as exc:
        print("error: invalid config:", file=sys.stderr)
        for issue in exc.issues:
            print(f"  {issue['location']}: {issue['message']}", file=sys.stderr)
    except (OSError, ValueError, ET.ParseError) as exc:
        print(f"error: {exc}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
