from __future__ import annotations

import argparse
import logging
from typing import TYPE_CHECKING

import pytest

from happy_python_logging.cli.core import build_parser
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
    def _make_args(self, script: Path, log_config: str | None = None):
        parser = build_parser()
        argv = ["run"]
        if log_config is not None:
            argv += ["--log-config", log_config]
        argv += [str(script)]
        return parser.parse_args(argv)

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

    def test_missing_script_returns_nonzero(self, tmp_path, capsys):
        args = argparse.Namespace(
            log_config=None,
            script=tmp_path / "does_not_exist.py",
            script_args=[],
        )
        exit_code = run_command(args, env={})
        assert exit_code == 1
        assert "script not found" in capsys.readouterr().err
