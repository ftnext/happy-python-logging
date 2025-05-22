import logging
import os
import sys
import tempfile

from happy_python_logging.app import configureLogger


def assert_console_handler(actual: logging.Handler) -> None:
    assert isinstance(actual, logging.StreamHandler)
    assert actual.stream is sys.stderr


def assert_file_handler(actual: logging.Handler, expected_filename: str) -> None:
    assert isinstance(actual, logging.FileHandler)
    assert actual.baseFilename == os.path.abspath(expected_filename)


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


def test_configureLogger_with_filename():
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_filename = temp_file.name

    try:
        actual = configureLogger(
            "awesome_file", level=logging.INFO, format="%(levelname)s: %(message)s", filename=temp_filename
        )

        assert actual.level == logging.INFO
        assert len(actual.handlers) == 1
        assert_file_handler(actual.handlers[0], temp_filename)
        assert_formatter(actual.handlers[0].formatter, "%(levelname)s: %(message)s")

        # Test that logging actually works
        test_message = "Test log message to file"
        actual.info(test_message)

        with open(temp_filename, "r") as f:
            log_content = f.read()
            assert f"INFO: {test_message}" in log_content

    finally:
        # Clean up the temporary file
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)
