import ast
from collections.abc import Generator
from typing import Any

from happy_python_logging import __about__
from happy_python_logging.lint.core import ConfigureRootLoggerChecker


class HappyPythonLoggingPlugin:
    name = "flake8-happy-python-logging"
    version = __about__.__version__

    def __init__(self, tree: ast.AST) -> None:
        self._tree = tree

    def run(self) -> Generator[tuple[int, int, str, type[Any]], None, None]:
        checker = ConfigureRootLoggerChecker()
        checker.visit(self._tree)

        for lineno, col_offset, msg in checker.errors:
            yield (lineno, col_offset, msg, type(self))
