from __future__ import annotations

import argparse
import sys

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
    # Keep `script` as the raw user-typed string (no `type=Path`) so
    # `python ./x.py`-style invocations preserve `./` in `sys.argv[0]`.
    run_parser.add_argument("script", help="Path to the Python script")
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
    # Keep `script` as the raw user-typed string (no `type=Path`) so
    # `python ./x.py`-style invocations preserve `./` in `sys.argv[0]`.
    run_parser.add_argument("script", help="Path to the Python script")

    return parser


def _is_wrapper_help_request(run_argv: list[str]) -> bool:
    """True if argv (after the `run` token) asks for wrapper help.

    The user wants wrapper help when `-h`/`--help` appears in the wrapper-side
    portion of argv (i.e. before any script-like positional, and before any
    `--` separator). With a script present, `-h`/`--help` is forwarded to the
    script instead.
    """
    has_help = False
    i = 0
    while i < len(run_argv):
        arg = run_argv[i]
        if arg == "--":
            # `--` terminates wrapper option parsing; subsequent `--help`
            # belongs to the script side, never the wrapper.
            return has_help
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


def extract_run_script_args(
    argv: list[str], parser: argparse.ArgumentParser
) -> list[str]:
    """Find the script positional in `argv`, validate wrapper typos, and
    return the args forwarded to the script (preserving `--`).

    Mirrors what `main()` does for the `run` subcommand so tests can build
    the same Namespace shape via :func:`build_parser` + this helper without
    diverging from the real CLI path.

    Raises ``SystemExit`` (via ``parser.error``) on typos or missing script.
    """
    # Locate the `script` positional in argv by walking the wrapper
    # portion. Track unknown wrapper-side flags by their argv position
    # (not value) so a script_arg that happens to equal `"run"` or a
    # `--log-config` value isn't mistaken for a typo.
    run_idx = argv.index("run")
    script_idx: int | None = None
    unknown_wrapper: list[str] = []
    saw_separator = False
    i = run_idx + 1
    while i < len(argv):
        arg = argv[i]
        if arg == "--":
            # argparse positional separator: next token (if any) is script.
            saw_separator = True
            i += 1
            if i < len(argv):
                script_idx = i
            break
        if arg in _LOG_CONFIG_FLAGS:
            i += 2
            continue
        if arg.startswith("--log-config=") or arg.startswith("--log_config="):
            i += 1
            continue
        if arg.startswith("-"):
            unknown_wrapper.append(arg)
            i += 1
            continue
        script_idx = i
        break
    if script_idx is None:
        parser.error("script is required")

    # Top-level parser has no flags of its own, so anything before `run` is
    # a stray wrapper arg (e.g. `happy-python-logging --bogus run …`).
    bad = list(argv[:run_idx]) + unknown_wrapper
    if bad:
        parser.error(f"unrecognized arguments: {' '.join(bad)}")

    script_args = list(argv[script_idx + 1 :])
    if saw_separator:
        # User explicitly ended wrapper option parsing with `--` before the
        # script, so argparse didn't consume any `--log-config` after it —
        # forward everything verbatim.
        return script_args
    # `--log-config` after the script was already consumed by argparse into
    # `args.log_config`; drop those tokens so we don't ALSO forward them to
    # the script. Stop at `--`: everything after it is verbatim.
    j = 0
    while j < len(script_args):
        arg = script_args[j]
        if arg == "--":
            break
        if arg in _LOG_CONFIG_FLAGS:
            del script_args[j : j + 2]
            continue
        if arg.startswith("--log-config=") or arg.startswith("--log_config="):
            del script_args[j]
            continue
        j += 1
    return script_args


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if argv and argv[0] == "run" and _is_wrapper_help_request(argv[1:]):
        _build_run_parser().print_help()
        return 0

    parser = build_parser()
    args, remaining = parser.parse_known_args(argv)

    if args.command == "run":
        args.script_args = extract_run_script_args(argv, parser)
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
