from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

_VALID_LEVEL_NAMES = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
# RUST_LOG-style aliases mapped to Python's level names.
_LEVEL_ALIASES = {"WARN": "WARNING"}

_DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


class _RunHandler(logging.StreamHandler):
    """StreamHandler installed by ``happy-python-logging run`` (marker subclass)."""


def _parse_level(level: str) -> int:
    name = level.strip().upper()
    name = _LEVEL_ALIASES.get(name, name)
    if name not in _VALID_LEVEL_NAMES:
        msg = f"invalid log level: {level!r}"
        raise SystemExit(msg)
    return logging.getLevelName(name)


def parse_log_config(spec: str) -> list[tuple[str, int]]:
    result: list[tuple[str, int]] = []
    for raw in spec.split(","):
        item = raw.strip()
        if not item:
            continue
        if "=" in item:
            name, _, level = item.partition("=")
            result.append((name.strip(), _parse_level(level)))
        else:
            result.append(("", _parse_level(item)))
    return result


def configure_logging(specs: Sequence[tuple[str, int]]) -> None:
    root = logging.getLogger()
    if not any(isinstance(h, _RunHandler) for h in root.handlers):
        handler = _RunHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
        root.addHandler(handler)

    for name, level in specs:
        logging.getLogger(name).setLevel(level)


def run_script(script: Path, script_args: Sequence[str]) -> None:
    if not script.is_file():
        msg = f"script not found: {script}"
        raise SystemExit(msg)

    old_argv = sys.argv[:]
    old_sys_path = sys.path[:]

    try:
        # Mimic `python script.py`:
        #   sys.argv[0]   = user-given path (possibly relative, possibly a
        #                   symlink) — exactly what was typed
        #   __file__      = absolute path so `Path(__file__)`-based resource
        #                   lookups don't break after the script chdirs
        #   sys.path[0]   = absolute path of the script's containing directory
        # `runpy.run_path` would tie `sys.argv[0]` and `__file__` to the same
        # value (via `_ModifiedArgv0`), so we exec the compiled code with an
        # explicit module-globals dict to keep them independent.
        # Symlinks are NOT followed (`absolute()` vs `resolve()`).
        absolute_script = script.absolute()
        sys.argv = [str(script), *script_args]

        script_dir = str(absolute_script.parent)
        if sys.path:
            sys.path[0] = script_dir
        else:
            sys.path.insert(0, script_dir)

        source = absolute_script.read_bytes()
        code = compile(source, str(absolute_script), "exec")
        exec(  # noqa: S102 - executing user-supplied script is the point
            code,
            {
                "__name__": "__main__",
                "__file__": str(absolute_script),
                "__doc__": None,
                "__package__": None,
                "__loader__": None,
                "__spec__": None,
            },
        )

    finally:
        sys.argv = old_argv
        sys.path[:] = old_sys_path


def run_command(args, env: Mapping[str, str] | None = None) -> int:
    if env is None:
        env = os.environ

    log_config: str | None = args.log_config
    if log_config is None:
        log_config = env.get("PYTHON_LOG")

    if log_config:
        specs = parse_log_config(log_config)
        configure_logging(specs)

    try:
        run_script(args.script, args.script_args)
    except SystemExit as e:
        if e.code is None:
            return 0
        if isinstance(e.code, int):
            return e.code
        sys.stderr.write(f"{e.code}\n")
        return 1
    finally:
        logging.shutdown()

    return 0
