from __future__ import annotations

import builtins
import importlib.machinery
import logging
import os
import sys
import types
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

_VALID_LEVEL_NAMES = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
# RUST_LOG-style aliases mapped to Python's level names.
_LEVEL_ALIASES = {"WARN": "WARNING"}

_DEFAULT_FORMAT = "%(asctime)s | %(levelname)s (%(name)s) | %(filename)s:%(funcName)s:%(lineno)d - %(message)s"


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


def run_script(script: str, script_args: Sequence[str]) -> None:
    # Keep `script` as the raw user-typed token so `sys.argv[0]` matches
    # `python <token>` (e.g. `./x.py` stays `./x.py`, not normalized to
    # `x.py`). Filesystem operations go through `Path` locally.
    script_path = Path(script)
    if not script_path.is_file():
        msg = f"script not found: {script}"
        raise SystemExit(msg)

    old_argv = sys.argv[:]
    old_sys_path = sys.path[:]
    old_main = sys.modules.get("__main__")

    try:
        # Mimic `python script.py`:
        #   sys.argv[0]            = user-given path (possibly relative,
        #                            possibly a symlink) — exactly what was
        #                            typed
        #   __file__               = absolute path so `Path(__file__)`-based
        #                            resource lookups don't break after the
        #                            script chdirs (symlinks NOT followed)
        #   sys.path[0]            = absolute path of the *real* script's
        #                            containing directory (symlinks ARE
        #                            followed, so `import helper` resolves
        #                            in the directory next to the real file)
        #   sys.modules['__main__'] = a fresh module so `import __main__`
        #                            inside the script resolves to itself
        # `runpy.run_path` would tie `sys.argv[0]` and `__file__` to the same
        # value (via `_ModifiedArgv0`), so we install a `__main__` module
        # and exec into its `__dict__` directly to keep them independent.
        absolute_script = script_path.absolute()
        sys.argv = [script, *script_args]

        script_dir = str(script_path.resolve().parent)
        if sys.path:
            sys.path[0] = script_dir
        else:
            sys.path.insert(0, script_dir)

        # `python script.py` sets `__main__.__loader__` to a real
        # `SourceFileLoader`, which scripts use for e.g.
        # `__loader__.get_data(__file__)`. Match that.
        loader = importlib.machinery.SourceFileLoader(
            "__main__", str(absolute_script)
        )
        main_module = types.ModuleType("__main__")
        main_module.__file__ = str(absolute_script)
        main_module.__loader__ = loader
        main_module.__package__ = None
        main_module.__spec__ = None
        main_module.__cached__ = None
        # `python script.py` seeds `__builtins__` with the `builtins` module
        # (not its `__dict__`); seed it ourselves before exec, otherwise
        # Python's automatic injection installs the dict and code like
        # `__builtins__.__name__` breaks.
        main_module.__dict__["__builtins__"] = builtins
        sys.modules["__main__"] = main_module

        source = absolute_script.read_bytes()
        code = compile(source, str(absolute_script), "exec")
        exec(  # noqa: S102 - executing user-supplied script is the point
            code, main_module.__dict__
        )

    finally:
        sys.argv = old_argv
        sys.path[:] = old_sys_path
        if old_main is not None:
            sys.modules["__main__"] = old_main
        else:
            sys.modules.pop("__main__", None)


def run_command(args, env: Mapping[str, str] | None = None) -> int:
    if env is None:
        env = os.environ

    log_config: str | None = args.log_config
    if log_config is None:
        log_config = env.get("PYTHON_LOG")

    try:
        if log_config:
            # `parse_log_config` raises `SystemExit` on invalid levels; catch
            # it here too so library-style callers of `run_command` get a
            # consistent exit-code return instead of a propagated exception.
            specs = parse_log_config(log_config)
            configure_logging(specs)

        run_script(args.script, args.script_args)
    except SystemExit as e:
        if e.code is None:
            return 0
        if isinstance(e.code, int):
            return e.code
        sys.stderr.write(f"{e.code}\n")
        return 1
    finally:
        # Only tear down the handler we installed. `logging.shutdown()` would
        # close every handler in the process, breaking library-style callers
        # that had their own handlers in place before run_command was invoked.
        root = logging.getLogger()
        for handler in list(root.handlers):
            if isinstance(handler, _RunHandler):
                root.removeHandler(handler)
                handler.close()

    return 0
