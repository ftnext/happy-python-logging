import ast
from unittest.mock import ANY

import pytest

from happy_python_logging.lint.core import ConfigureRootLoggerChecker


class TestConfigureRootLoggerChecker:
    class TestHPL101:
        def test_import(self):
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

        def test_import_as(self):
            code = """\
import logging as log

def awesome():
    log.basicConfig(level=logging.DEBUG)
"""
            checker = ConfigureRootLoggerChecker()
            checker.visit(ast.parse(code))

            assert len(checker.errors) == 1
            assert checker.errors[0] == (4, 4, ANY)
            assert checker.errors[0][2].startswith("HPL101")

        def test_import_from(self):
            code = """\
from logging import basicConfig

def awesome():
    basicConfig(level=logging.DEBUG)
"""
            checker = ConfigureRootLoggerChecker()
            checker.visit(ast.parse(code))

            assert len(checker.errors) == 1
            assert checker.errors[0] == (4, 4, ANY)
            assert checker.errors[0][2].startswith("HPL101")

        def test_import_from_as(self):
            code = """\
from logging import basicConfig as loggingBasicConfig

def awesome():
    loggingBasicConfig(level=logging.DEBUG)
"""
            checker = ConfigureRootLoggerChecker()
            checker.visit(ast.parse(code))

            assert len(checker.errors) == 1
            assert checker.errors[0] == (4, 4, ANY)
            assert checker.errors[0][2].startswith("HPL101")

    class TestHPL102:
        @pytest.mark.parametrize("function", ["debug", "info", "warning", "error", "critical"])
        def test_import(self, function):
            code = f"""\
import logging

def awesome():
    logging.{function}("message")
"""
            checker = ConfigureRootLoggerChecker()
            checker.visit(ast.parse(code))

            assert len(checker.errors) == 1
            assert checker.errors[0] == (4, 4, ANY)
            assert checker.errors[0][2].startswith("HPL102")

        def test_import_as(self):
            code = """\
import logging as log

def awesome():
    log.debug("message")
"""
            checker = ConfigureRootLoggerChecker()
            checker.visit(ast.parse(code))

            assert len(checker.errors) == 1
            assert checker.errors[0] == (4, 4, ANY)
            assert checker.errors[0][2].startswith("HPL102")

        def test_import_from(self):
            code = """\
from logging import debug

def awesome():
    debug("message")
"""
            checker = ConfigureRootLoggerChecker()
            checker.visit(ast.parse(code))

            assert len(checker.errors) == 1
            assert checker.errors[0] == (4, 4, ANY)
            assert checker.errors[0][2].startswith("HPL102")

        def test_import_from_as(self):
            code = """\
from logging import debug as dbg

def awesome():
    dbg("message")
"""
            checker = ConfigureRootLoggerChecker()
            checker.visit(ast.parse(code))

            assert len(checker.errors) == 1
            assert checker.errors[0] == (4, 4, ANY)
            assert checker.errors[0][2].startswith("HPL102")
