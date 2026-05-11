from __future__ import annotations

import argparse
import logging
from typing import TYPE_CHECKING

import pytest

from happy_python_logging.cli.core import build_parser, extract_run_script_args, main
from happy_python_logging.cli.run import (
    _RunHandler,
    configure_logging,
    parse_log_config,
    run_command,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def reset_root_logger():
    root = logging.getLogger()
    saved_level = root.level
    saved_handlers = root.handlers[:]
    root.handlers = []
    try:
        yield root
    finally:
        root.handlers = saved_handlers
        root.setLevel(saved_level)


class TestParseLogConfig:
    def test_single_logger(self):
        assert parse_log_config("httpx=debug") == [("httpx", logging.DEBUG)]

    def test_multiple_loggers(self):
        assert parse_log_config("httpx=debug,urllib3=info") == [
            ("httpx", logging.DEBUG),
            ("urllib3", logging.INFO),
        ]

    def test_global_level(self):
        assert parse_log_config("INFO") == [("", logging.INFO)]

    def test_case_insensitive_level(self):
        assert parse_log_config("httpx=DeBuG") == [("httpx", logging.DEBUG)]

    def test_warn_alias_for_warning(self):
        assert parse_log_config("httpx=warn") == [("httpx", logging.WARNING)]

    def test_invalid_level_raises(self):
        with pytest.raises(SystemExit):
            parse_log_config("httpx=bogus")


@pytest.mark.usefixtures("reset_root_logger")
class TestConfigureLogging:
    def test_sets_levels(self):
        configure_logging([("httpx", logging.DEBUG), ("urllib3", logging.INFO)])
        assert logging.getLogger("httpx").level == logging.DEBUG
        assert logging.getLogger("urllib3").level == logging.INFO

    def test_adds_one_stream_handler(self):
        configure_logging([("httpx", logging.DEBUG)])
        configure_logging([("urllib3", logging.INFO)])
        own_handlers = [h for h in logging.getLogger().handlers if isinstance(h, _RunHandler)]
        assert len(own_handlers) == 1


@pytest.mark.usefixtures("reset_root_logger")
class TestRunCommand:
    def _parse(self, *argv: str):
        """Parse argv the same way main() does."""
        full = ["run", *argv]
        parser = build_parser()
        ns, _ = parser.parse_known_args(full)
        ns.script_args = extract_run_script_args(full, parser)
        return ns

    def _make_args(self, script: Path, log_config: str | None = None):
        argv = []
        if log_config is not None:
            argv += ["--log-config", log_config]
        argv += [str(script)]
        return self._parse(*argv)

    def test_propagates_script_exit_code(self, tmp_path):
        script = tmp_path / "exit7.py"
        script.write_text("import sys\nsys.exit(7)\n")
        args = self._make_args(script)
        assert run_command(args, env={}) == 7

    def test_zero_when_script_finishes(self, tmp_path):
        script = tmp_path / "ok.py"
        script.write_text("x = 1\n")
        args = self._make_args(script)
        assert run_command(args, env={}) == 0

    def test_log_config_sets_level(self, tmp_path):
        script = tmp_path / "ok.py"
        script.write_text("x = 1\n")
        args = self._make_args(script, log_config="httpx=debug")
        run_command(args, env={})
        assert logging.getLogger("httpx").level == logging.DEBUG

    def test_python_log_env_fallback(self, tmp_path):
        script = tmp_path / "ok.py"
        script.write_text("x = 1\n")
        args = self._make_args(script)
        run_command(args, env={"PYTHON_LOG": "urllib3=info"})
        assert logging.getLogger("urllib3").level == logging.INFO

    def test_cli_arg_takes_precedence_over_env(self, tmp_path):
        script = tmp_path / "ok.py"
        script.write_text("x = 1\n")
        args = self._make_args(script, log_config="httpx=debug")
        run_command(args, env={"PYTHON_LOG": "httpx=warning"})
        assert logging.getLogger("httpx").level == logging.DEBUG

    def test_log_config_after_script(self, tmp_path):
        script = tmp_path / "ok.py"
        script.write_text("x = 1\n")
        args = self._parse(str(script), "--log-config", "httpx=debug")
        run_command(args, env={})
        assert logging.getLogger("httpx").level == logging.DEBUG
        assert args.script_args == []

    @pytest.mark.parametrize(
        "argv",
        [
            ["run", "--help"],
            ["run", "-h"],
            ["run", "--log-config", "httpx=debug", "--help"],
        ],
    )
    def test_help_without_script_prints_wrapper_help(self, capsys, argv):
        exit_code = main(argv)
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "happy-python-logging run" in out
        assert "--log-config" in out

    @pytest.mark.parametrize("flag", ["-h", "--help"])
    def test_forwards_help_flags(self, tmp_path, flag):
        # `-h`/`--help` after the script must reach the script, not trigger
        # the wrapper's argparse help and exit.
        script = tmp_path / "ok.py"
        script.write_text("x = 1\n")
        args = self._parse(str(script), flag)
        assert args.script_args == [flag]

    def test_does_not_abbreviate_log_config(self, tmp_path):
        # --log-c is a prefix of --log-config; it must not be captured here,
        # so the script receives it intact.
        script = tmp_path / "ok.py"
        script.write_text("x = 1\n")
        args = self._parse(str(script), "--log-c", "value")
        assert args.log_config is None
        assert args.script_args == ["--log-c", "value"]

    def test_forwards_script_args(self, tmp_path):
        script = tmp_path / "echo.py"
        script.write_text(
            "import sys, pathlib\n"
            "pathlib.Path(sys.argv[0] + '.argv').write_text(repr(sys.argv[1:]))\n"
        )
        args = self._parse(str(script), "--flag", "value", "positional")
        run_command(args, env={})
        recorded = (script.parent / (script.name + ".argv")).read_text()
        assert recorded == "['--flag', 'value', 'positional']"

    def test_missing_script_returns_nonzero(self, tmp_path, capsys):
        args = argparse.Namespace(
            log_config=None,
            script=str(tmp_path / "does_not_exist.py"),
            script_args=[],
        )
        exit_code = run_command(args, env={})
        assert exit_code == 1
        assert "script not found" in capsys.readouterr().err

    def test_invalid_log_config_returns_nonzero(self, tmp_path, capsys):
        # `parse_log_config` raises SystemExit on invalid levels; `run_command`
        # must normalize that into a return-code, same as `script not found`,
        # so library-style callers don't see an unwrapped exception.
        script = tmp_path / "ok.py"
        script.write_text("x = 1\n")
        args = self._parse(str(script), "--log-config", "httpx=bogus")
        exit_code = run_command(args, env={})
        assert exit_code == 1
        assert "invalid log level" in capsys.readouterr().err

    def test_does_not_close_caller_logging_handlers(self, tmp_path):
        # `run_command` should clean up only the `_RunHandler` it adds, not
        # call `logging.shutdown()`, which would close every handler in the
        # process and break library-style callers that had their own
        # `FileHandler` etc. already in place.
        class _FlagHandler(logging.Handler):
            def __init__(self):
                super().__init__()
                self.closed = False

            def close(self):
                self.closed = True
                super().close()

            def emit(self, record):  # pragma: no cover - not exercised
                pass

        caller = _FlagHandler()
        logging.getLogger().addHandler(caller)
        try:
            script = tmp_path / "ok.py"
            script.write_text("x = 1\n")
            args = self._make_args(script, log_config="httpx=debug")
            run_command(args, env={})
            assert not caller.closed
            assert caller in logging.getLogger().handlers
            # Our own handler is gone again.
            own = [
                h
                for h in logging.getLogger().handlers
                if isinstance(h, _RunHandler)
            ]
            assert own == []
        finally:
            logging.getLogger().removeHandler(caller)

    def test_symlink_path_not_resolved(self, tmp_path):
        # Match `python link.py`: `__file__` / `argv[0]` should reflect the
        # path the user invoked, not the symlink target.
        real = tmp_path / "real.py"
        real.write_text(
            "import pathlib, sys\n"
            "pathlib.Path(sys.argv[0] + '.seen').write_text(\n"
            "    repr({'argv0': sys.argv[0], 'file': __file__})\n"
            ")\n"
        )
        link = tmp_path / "link.py"
        link.symlink_to(real)
        args = self._parse(str(link))
        run_command(args, env={})
        recorded = (link.parent / (link.name + ".seen")).read_text()
        assert recorded == repr({"argv0": str(link), "file": str(link)})

    def test_relative_script_path_yields_absolute_file(self, tmp_path, monkeypatch):
        # Match `python foo.py`: `argv[0]` keeps the user-given relative path,
        # but `__file__` is the absolute path of the script.
        script = tmp_path / "x.py"
        script.write_text(
            "import pathlib, sys\n"
            "pathlib.Path(__file__ + '.seen').write_text(\n"
            "    repr({'argv0': sys.argv[0], 'file': __file__})\n"
            ")\n"
        )
        monkeypatch.chdir(tmp_path)
        args = self._parse("x.py")
        run_command(args, env={})
        recorded = (tmp_path / "x.py.seen").read_text()
        assert recorded == repr({"argv0": "x.py", "file": str(tmp_path / "x.py")})

    def test_import_main_resolves_to_script(self, tmp_path):
        # `python script.py` makes `sys.modules['__main__']` the script
        # itself, so `import __main__` from inside the script sees the
        # script's globals (e.g. `__main__.__file__`).
        script = tmp_path / "self_introspect.py"
        script.write_text(
            "import __main__, pathlib\n"
            "pathlib.Path(__file__ + '.seen').write_text(__main__.__file__)\n"
        )
        args = self._parse(str(script))
        run_command(args, env={})
        recorded = (script.parent / (script.name + ".seen")).read_text()
        assert recorded == str(script)

    def test_main_loader_supports_get_data(self, tmp_path):
        # `python script.py` sets `__main__.__loader__` to a real
        # `SourceFileLoader`, so `__loader__.get_data(__file__)` works.
        script = tmp_path / "uses_loader.py"
        script.write_text(
            "import pathlib\n"
            "data = __loader__.get_data(__file__)\n"
            "pathlib.Path(__file__ + '.seen').write_bytes(data)\n"
        )
        args = self._parse(str(script))
        run_command(args, env={})
        recorded = (script.parent / (script.name + ".seen")).read_bytes()
        assert recorded == script.read_bytes()

    def test_main_cached_is_defined(self, tmp_path):
        # `python script.py` defines `__cached__` as None on `__main__`;
        # scripts that reference it must not crash with NameError.
        script = tmp_path / "reads_cached.py"
        script.write_text(
            "import pathlib\n"
            "pathlib.Path(__file__ + '.seen').write_text(repr(__cached__))\n"
        )
        args = self._parse(str(script))
        run_command(args, env={})
        recorded = (script.parent / (script.name + ".seen")).read_text()
        assert recorded == "None"

    def test_main_builtins_is_module(self, tmp_path):
        # `python script.py` sets `__builtins__` to the `builtins` MODULE on
        # `__main__`, not its dict — `__builtins__.__name__` must work.
        script = tmp_path / "reads_builtins.py"
        script.write_text(
            "import pathlib\n"
            "pathlib.Path(__file__ + '.seen').write_text(__builtins__.__name__)\n"
        )
        args = self._parse(str(script))
        run_command(args, env={})
        recorded = (script.parent / (script.name + ".seen")).read_text()
        assert recorded == "builtins"

    def test_dot_slash_prefix_preserved_in_argv(self, tmp_path, monkeypatch):
        # `python ./x.py` keeps `./x.py` in `sys.argv[0]`. The wrapper must
        # not normalize the token via `Path` and drop the `./` prefix.
        script = tmp_path / "x.py"
        script.write_text(
            "import sys, pathlib\n"
            "pathlib.Path(__file__ + '.seen').write_text(sys.argv[0])\n"
        )
        monkeypatch.chdir(tmp_path)
        args = self._parse("./x.py")
        run_command(args, env={})
        recorded = (tmp_path / "x.py.seen").read_text()
        assert recorded == "./x.py"

    def test_sys_path_uses_real_script_directory(self, tmp_path):
        # `python link.py` sets `sys.path[0]` to the REAL script's directory
        # (symlinks resolved), so a sibling module next to the real file can
        # be imported. The symlink's parent directory may not contain it.
        real_dir = tmp_path / "realdir"
        real_dir.mkdir()
        (real_dir / "helper.py").write_text("MARKER = 'real'\n")
        real_script = real_dir / "real.py"
        real_script.write_text(
            "import helper, pathlib, sys\n"
            "pathlib.Path(sys.argv[0] + '.seen').write_text(helper.MARKER)\n"
        )
        link_dir = tmp_path / "linkdir"
        link_dir.mkdir()
        link = link_dir / "link.py"
        link.symlink_to(real_script)
        args = self._parse(str(link))
        run_command(args, env={})
        recorded = (link.parent / (link.name + ".seen")).read_text()
        assert recorded == "real"
