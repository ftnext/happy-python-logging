from __future__ import annotations

import argparse
import sys
from pathlib import Path

from happy_python_logging.cli.run import run_command
from happy_python_logging.cli.snippets import SNIPPETS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="happy-python-logging",
        description="happy-python-logging CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    snippet_parser = subparsers.add_parser("snippet", help="Print a code snippet")
    snippet_parser.add_argument(
        "name",
        choices=sorted(SNIPPETS),
        help="Name of the snippet to print",
    )

    run_parser = subparsers.add_parser(
        "run",
        help="(experimental) Run a Python script with quick logging configuration",
        allow_abbrev=False,
        # Don't intercept `-h`/`--help` after the script — they belong to the script.
        add_help=False,
    )
    run_parser.add_argument(
        "--log-config",
        "--log_config",
        dest="log_config",
        default=None,
        help='RUST_LOG-style spec, e.g. "httpx=debug,urllib3=info" (also via PYTHON_LOG env var)',
    )
    run_parser.add_argument("script", type=Path, help="Path to the Python script")
    # script_args is collected via parse_known_args in main(), so any flags after
    # the script path (other than our own --log-config) flow through to the script.

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, remaining = parser.parse_known_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    if args.command == "run":
        args.script_args = remaining
        return run_command(args)

    if remaining:
        parser.error(f"unrecognized arguments: {' '.join(remaining)}")

    if args.command == "snippet":
        sys.stdout.write(SNIPPETS[args.name])
        return 0

    return 1


def cli() -> None:
    """Entry point for the ``happy-python-logging`` command."""
    raise SystemExit(main())
