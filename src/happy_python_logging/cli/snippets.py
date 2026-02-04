ORFILTER_SNIPPET = """\
class OrFilter:
    def __init__(self, *prefixes: str) -> None:
        self.prefixes = list(prefixes)

    def filter(self, record) -> bool:
        return any(record.name.startswith(prefix) for prefix in self.prefixes)
"""

SNIPPETS = {
    "orfilter": ORFILTER_SNIPPET,
}
