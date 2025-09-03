import logging

import pytest

from happy_python_logging.lib.filters import OrFilter


class TestOrFilter:
    @pytest.fixture
    def handler_under_test(self):
        return OrFilter("spam", "ham.egg")

    @pytest.mark.parametrize("name", ["spam", "ham.egg", "spam.ham"])
    def test_pass(self, name, handler_under_test):
        record = logging.makeLogRecord({"name": name})
        assert handler_under_test.filter(record)

    @pytest.mark.parametrize("name", ["ham", "ham.spam", "quux", "foo.ham.egg"])
    def test_reject(self, name, handler_under_test):
        record = logging.makeLogRecord({"name": name})
        assert not handler_under_test.filter(record)
