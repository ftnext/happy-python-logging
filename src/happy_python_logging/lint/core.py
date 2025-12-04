import ast

LineNumber = int
ColumnOffset = int
ErrorMessage = str


class ConfigureRootLoggerChecker(ast.NodeVisitor):
    def __init__(self) -> None:
        self.errors: list[tuple[LineNumber, ColumnOffset, ErrorMessage]] = []
        self.logging_aliases: set[str] = set()
        self.imported_names: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            if alias.name == "logging":
                self.logging_aliases.add(alias.asname or "logging")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.module == "logging":
            for alias in node.names:
                self.imported_names.add(alias.asname or alias.name)
        self.generic_visit(node)

    def _is_logging_attribute_basic_config_call(self, node: ast.Call) -> bool:
        return (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in self.logging_aliases
            and node.func.attr == "basicConfig"
        )

    def _is_imported_basic_config_call(self, node: ast.Call) -> bool:
        return isinstance(node.func, ast.Name) and node.func.id in self.imported_names

    def _is_basic_config_call(self, node: ast.Call) -> bool:
        return self._is_logging_attribute_basic_config_call(node) or self._is_imported_basic_config_call(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if self._is_basic_config_call(node):
            self.errors.append(
                (
                    node.lineno,
                    node.col_offset,
                    "HPL101 Don't configure the root logger in your library",
                )
            )

        self.generic_visit(node)
