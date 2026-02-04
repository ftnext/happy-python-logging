import logging

from happy_python_logging import getLoggerForLibrary


class TestGetLoggerForLibrary:
    def test_default_adds_null_handler(self):
        """Test that by default (backward compatibility), NullHandler is added."""
        sut = getLoggerForLibrary("mylib")

        assert len(sut.handlers) == 1
        assert isinstance(sut.handlers[0], logging.NullHandler)

    def test_with_handler_true_adds_null_handler(self):
        """Test that with_handler=True explicitly adds NullHandler."""
        sut = getLoggerForLibrary("mylib.explicit", with_handler=True)

        assert len(sut.handlers) == 1
        assert isinstance(sut.handlers[0], logging.NullHandler)

    def test_with_handler_false_does_not_add_handler(self):
        """Test that with_handler=False does not add any handler."""
        sut = getLoggerForLibrary("mylib.no_handler", with_handler=False)

        assert len(sut.handlers) == 0
