"""Command-line entry point: ``config-manager <command> ...``."""

import argparse
from collections.abc import Sequence


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

    version = sub.add_parser("version", help="save / list config versions")
    version.add_argument("action", choices=["save", "list"])
    version.add_argument("path")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    # TODO: dispatch args.command to paths / validation / converter / versioning
    print(f"{args.command}: not implemented yet")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
