import logging

from happy_python_logging import getLoggerForLibrary


def test_getLoggerForLibrary():  # noqa: N802
    sut = getLoggerForLibrary("mylib")

    assert len(sut.handlers) == 1
    assert isinstance(sut.handlers[0], logging.NullHandler)
