from __future__ import annotations

import argparse
import sys
from pathlib import Path

from happy_python_logging.cli.run import run_command
from happy_python_logging.cli.snippets import SNIPPETS

_LOG_CONFIG_FLAGS = ("--log-config", "--log_config")
_HELP_FLAGS = ("-h", "--help")


def _build_run_parser() -> argparse.ArgumentParser:
    """The `run` subparser as a standalone parser, used both inside `build_parser`
    and to print help when the user types `run --help` without a script."""
    run_parser = argparse.ArgumentParser(
        prog="happy-python-logging run",
        description="(experimental) Run a Python script with quick logging configuration.",
        allow_abbrev=False,
        # `-h`/`--help` after the script must flow through to the script;
        # wrapper help is handled manually in `main()`.
        add_help=False,
    )
    run_parser.add_argument(
        *_LOG_CONFIG_FLAGS,
        dest="log_config",
        default=None,
        help='RUST_LOG-style spec, e.g. "httpx=debug,urllib3=info" (also via PYTHON_LOG env var)',
    )
    run_parser.add_argument("script", type=Path, help="Path to the Python script")
    # script_args is collected via parse_known_args in main(); any flags after
    # the script path (other than our own --log-config) flow through to the script.
    return run_parser


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

    # Mirror _build_run_parser's args so the top-level parser knows about them too.
    run_parser = subparsers.add_parser(
        "run",
        help="(experimental) Run a Python script with quick logging configuration",
        allow_abbrev=False,
        add_help=False,
    )
    run_parser.add_argument(
        *_LOG_CONFIG_FLAGS,
        dest="log_config",
        default=None,
        help='RUST_LOG-style spec, e.g. "httpx=debug,urllib3=info" (also via PYTHON_LOG env var)',
    )
    run_parser.add_argument("script", type=Path, help="Path to the Python script")

    return parser


def _is_wrapper_help_request(run_argv: list[str]) -> bool:
    """True if argv (after the `run` token) asks for wrapper help.

    The user wants wrapper help when `-h`/`--help` appears in the wrapper-side
    portion of argv (i.e. before any script-like positional). With a script
    present, `-h`/`--help` is forwarded to the script instead.
    """
    has_help = False
    i = 0
    while i < len(run_argv):
        arg = run_argv[i]
        if arg in _HELP_FLAGS:
            has_help = True
            i += 1
            continue
        if arg in _LOG_CONFIG_FLAGS:
            i += 2
            continue
        if arg.startswith("--log-config=") or arg.startswith("--log_config="):
            i += 1
            continue
        if arg.startswith("-"):
            i += 1
            continue
        # First positional → script path. From here on, everything is script
        # territory, so any earlier `-h`/`--help` was wrapper-side.
        return has_help
    return has_help


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if argv and argv[0] == "run" and _is_wrapper_help_request(argv[1:]):
        _build_run_parser().print_help()
        return 0

    parser = build_parser()
    args, remaining = parser.parse_known_args(argv)

    if args.command == "run":
        # Args that appeared before `run` in argv can't be script args; if they
        # weren't consumed, they're top-level typos.
        run_idx = argv.index("run")
        pre_run = set(argv[:run_idx])
        bad = [a for a in remaining if a in pre_run]
        if bad:
            parser.error(f"unrecognized arguments: {' '.join(bad)}")
        args.script_args = remaining
        return run_command(args)

    # For any non-`run` invocation, leftover args (e.g. `--bogus`) are a typo
    # we should surface, not silently absorb.
    if remaining:
        parser.error(f"unrecognized arguments: {' '.join(remaining)}")

    if args.command is None:
        parser.print_help()
        return 1

    if args.command == "snippet":
        sys.stdout.write(SNIPPETS[args.name])
        return 0

    return 1


def cli() -> None:
    """Entry point for the ``happy-python-logging`` command."""
    raise SystemExit(main())
