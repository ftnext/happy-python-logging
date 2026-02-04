import argparse
import sys

from happy_python_logging.cli.snippets import SNIPPETS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="happy",
        description="happy-python-logging CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    snippet_parser = subparsers.add_parser("snippet", help="Print a code snippet")
    snippet_parser.add_argument(
        "name",
        choices=sorted(SNIPPETS),
        help="Name of the snippet to print",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    if args.command == "snippet":
        sys.stdout.write(SNIPPETS[args.name])
        return 0

    return 1


def cli() -> None:
    """Entry point for the ``happy`` command."""
    raise SystemExit(main())
