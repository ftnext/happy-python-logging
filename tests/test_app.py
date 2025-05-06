import logging
import sys

from happy_python_logging.app import configureLogger


def assert_console_handler(actual: logging.Handler) -> None:
    assert isinstance(actual, logging.StreamHandler)
    assert actual.stream is sys.stderr


def assert_formatter(actual: logging.Formatter, expected_format: str) -> None:
    assert actual._fmt == expected_format


def test_basicConfigForLogger():
    actual = configureLogger(
        "awesome", level=logging.DEBUG, format="%(message)s"
    )

    assert actual.level == logging.DEBUG
    assert len(actual.handlers) == 1
    assert_console_handler(actual.handlers[0])
    assert_formatter(actual.handlers[0].formatter, "%(message)s")
