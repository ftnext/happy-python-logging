import logging

import pytest

from happy_python_logging.lib.filters import NotFilter, OrFilter


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

    def test_or_operator_with_logging_filter(self):
        # OrFilter | logging.Filter
        combined = OrFilter("spam") | logging.Filter("ham")

        # "spam" prefix should pass
        assert combined.filter(logging.makeLogRecord({"name": "spam"}))
        assert combined.filter(logging.makeLogRecord({"name": "spam.eggs"}))

        # "ham" name should pass
        assert combined.filter(logging.makeLogRecord({"name": "ham"}))
        assert combined.filter(logging.makeLogRecord({"name": "ham.eggs"}))

        # Neither should be rejected
        assert not combined.filter(logging.makeLogRecord({"name": "other"}))
        assert not combined.filter(logging.makeLogRecord({"name": "foo.bar"}))

    def test_ror_operator_with_logging_filter(self):
        # logging.Filter | OrFilter (reverse order)
        combined = logging.Filter("ham") | OrFilter("spam")

        # Same behavior as __or__
        assert combined.filter(logging.makeLogRecord({"name": "spam"}))
        assert combined.filter(logging.makeLogRecord({"name": "spam.eggs"}))
        assert combined.filter(logging.makeLogRecord({"name": "ham"}))
        assert combined.filter(logging.makeLogRecord({"name": "ham.eggs"}))
        assert not combined.filter(logging.makeLogRecord({"name": "other"}))

    def test_or_operator_immutability(self):
        # Original OrFilter should not be modified
        original = OrFilter("spam")
        log_filter = logging.Filter("ham")

        combined = original | log_filter

        # Original should still have only "spam"
        assert original.prefixes == ["spam"]
        # Combined should have both
        assert "spam" in combined.prefixes
        assert "ham" in combined.prefixes

    def test_or_operator_with_invalid_type(self):
        or_filter = OrFilter("spam")

        with pytest.raises(TypeError, match="OrFilter can only be combined with logging.Filter instances"):
            or_filter | "invalid"

        with pytest.raises(TypeError, match="OrFilter can only be combined with logging.Filter instances"):
            or_filter | 123

    def test_or_operator_with_empty_name(self):
        or_filter = OrFilter("spam")
        empty_filter = logging.Filter("")

        with pytest.raises(ValueError, match="Cannot combine OrFilter with a logging.Filter that has an empty name"):
            or_filter | empty_filter

        # Test __ror__ as well
        with pytest.raises(ValueError, match="Cannot combine OrFilter with a logging.Filter that has an empty name"):
            empty_filter | or_filter

    def test_multiple_filters(self):
        # Chain multiple logging.Filters
        combined = OrFilter("lib1") | logging.Filter("app") | logging.Filter("service")

        assert combined.filter(logging.makeLogRecord({"name": "lib1.module"}))
        assert combined.filter(logging.makeLogRecord({"name": "app"}))
        assert combined.filter(logging.makeLogRecord({"name": "service.api"}))
        assert not combined.filter(logging.makeLogRecord({"name": "other"}))


class TestNotFilter:
    @pytest.fixture
    def handler_under_test(self):
        # Invert a standard logging.Filter
        return NotFilter(logging.Filter("spam"))

    @pytest.mark.parametrize("name", ["other", "ham", "foo.spam"])
    def test_pass(self, name, handler_under_test):
        # logging.Filter("spam") rejects these, so NotFilter passes them
        record = logging.makeLogRecord({"name": name})
        assert handler_under_test.filter(record)

    @pytest.mark.parametrize("name", ["spam", "spam.eggs"])
    def test_reject(self, name, handler_under_test):
        # logging.Filter("spam") passes these, so NotFilter rejects them
        record = logging.makeLogRecord({"name": name})
        assert not handler_under_test.filter(record)

    def test_wraps_or_filter(self):
        # NotFilter can wrap an OrFilter (duck-typed, not a logging.Filter)
        combined = NotFilter(OrFilter("spam", "ham.egg"))

        # Names OrFilter would pass are now rejected
        assert not combined.filter(logging.makeLogRecord({"name": "spam"}))
        assert not combined.filter(logging.makeLogRecord({"name": "ham.egg"}))
        # Names OrFilter would reject are now passed
        assert combined.filter(logging.makeLogRecord({"name": "ham"}))
        assert combined.filter(logging.makeLogRecord({"name": "quux"}))

    def test_double_negation(self):
        # NotFilter(NotFilter(...)) restores the original behavior
        combined = NotFilter(NotFilter(logging.Filter("spam")))

        assert combined.filter(logging.makeLogRecord({"name": "spam"}))
        assert combined.filter(logging.makeLogRecord({"name": "spam.eggs"}))
        assert not combined.filter(logging.makeLogRecord({"name": "other"}))
