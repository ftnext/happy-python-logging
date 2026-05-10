from io import StringIO
from unittest.mock import patch

import pytest

from happy_python_logging.cli.core import main
from happy_python_logging.cli.snippets import ORFILTER_SNIPPET


class TestSnippetCommand:
    def test_orfilter(self):
        stdout = StringIO()
        with patch("sys.stdout", stdout):
            exit_code = main(["snippet", "orfilter"])

        assert exit_code == 0
        assert stdout.getvalue() == ORFILTER_SNIPPET

    def test_invalid_name(self):
        with pytest.raises(SystemExit):
            main(["snippet", "nonexistent"])


class TestNoCommand:
    def test_returns_nonzero(self):
        exit_code = main([])
        assert exit_code == 1

    def test_unknown_top_level_arg_errors(self):
        with pytest.raises(SystemExit) as excinfo:
            main(["--bogus"])
        assert excinfo.value.code == 2

    def test_unknown_arg_before_run_errors(self):
        # `--bogus` precedes `run`, so it must not be silently forwarded as a
        # script argument; treat it as a top-level typo like `snippet` does.
        with pytest.raises(SystemExit) as excinfo:
            main(["--bogus", "run", "script.py"])
        assert excinfo.value.code == 2

    def test_typo_before_script_errors(self):
        # `--log-confg` is a typo of --log-config and sits between `run` and
        # the script positional. Without rejecting it, `httpx=debug` would be
        # mis-parsed as the script path.
        with pytest.raises(SystemExit) as excinfo:
            main(["run", "--log-confg", "httpx=debug", "script.py"])
        assert excinfo.value.code == 2


class TestRunForwarding:
    def test_preserves_double_dash_in_script_args(self, tmp_path, capsys):
        # `--` should reach the script verbatim so scripts that need a literal
        # `--` (or use it as their own separator) behave like `python script.py
        # -- --flag`.
        script = tmp_path / "echo.py"
        script.write_text(
            "import sys, pathlib\n"
            "pathlib.Path(sys.argv[0] + '.argv').write_text(repr(sys.argv[1:]))\n"
        )
        exit_code = main(["run", str(script), "--", "--flag"])
        assert exit_code == 0
        recorded = (script.parent / (script.name + ".argv")).read_text()
        assert recorded == "['--', '--flag']"
