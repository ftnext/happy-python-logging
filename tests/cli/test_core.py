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
