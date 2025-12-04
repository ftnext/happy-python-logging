import ast
from unittest.mock import ANY

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
