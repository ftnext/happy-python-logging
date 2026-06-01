import logging
from typing import Protocol


class _Filterer(Protocol):
    def filter(self, record: logging.LogRecord) -> bool: ...


class OrFilter:
    def __init__(self, *prefixes: str) -> None:
        self.prefixes = list(prefixes)

    def filter(self, record: logging.LogRecord) -> bool:
        return any(record.name.startswith(prefix) for prefix in self.prefixes)

    def __or__(self, other) -> "OrFilter":
        if not isinstance(other, logging.Filter):
            msg = "OrFilter can only be combined with logging.Filter instances"
            raise TypeError(msg)
        if not other.name:
            msg = "Cannot combine OrFilter with a logging.Filter that has an empty name"
            raise ValueError(msg)
        return OrFilter(*self.prefixes, other.name)

    def __ror__(self, other) -> "OrFilter":
        if not isinstance(other, logging.Filter):
            msg = "OrFilter can only be combined with logging.Filter instances"
            raise TypeError(msg)
        if not other.name:
            msg = "Cannot combine OrFilter with a logging.Filter that has an empty name"
            raise ValueError(msg)
        return OrFilter(other.name, *self.prefixes)


class NotFilter:
    def __init__(self, filter: _Filterer) -> None:
        self.filter_ = filter

    def filter(self, record: logging.LogRecord) -> bool:
        return not self.filter_.filter(record)
