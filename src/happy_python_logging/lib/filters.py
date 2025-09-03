import logging


class OrFilter:
    def __init__(self, *prefixes: str) -> None:
        self.prefixes = list(prefixes)

    def filter(self, record: logging.LogRecord) -> bool:
        return any(record.name.startswith(prefix) for prefix in self.prefixes)
