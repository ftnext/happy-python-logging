import ast
from unittest.mock import ANY

from happy_python_logging.lint.core import ConfigureRootLoggerChecker


class TestConfigureRootLoggerChecker:
    def test_HPL101(self):  # noqa: N802
        code = """\
import logging

def awesome():
    logging.basicConfig(level=logging.DEBUG)
"""
        checker = ConfigureRootLoggerChecker()
        checker.visit(ast.parse(code))

        assert len(checker.errors) == 1
        assert checker.errors[0] == (4, 4, ANY)
        assert checker.errors[0][2].startswith("HPL101")
