from __future__ import annotations

import logging
import os
import runpy
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

_VALID_LEVEL_NAMES = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}

_DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


class _RunHandler(logging.StreamHandler):
    """StreamHandler installed by ``happy-python-logging run`` (marker subclass)."""


def _parse_level(level: str) -> int:
    name = level.strip().upper()
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
    script = script.resolve()

    if not script.is_file():
        msg = f"script not found: {script}"
        raise SystemExit(msg)

    old_argv = sys.argv[:]
    old_sys_path = sys.path[:]

    try:
        sys.argv = [str(script), *script_args]

        if sys.path:
            sys.path[0] = str(script.parent)
        else:
            sys.path.insert(0, str(script.parent))

        runpy.run_path(str(script), run_name="__main__")

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
