import ast

LineNumber = int
ColumnOffset = int
ErrorMessage = str


class ConfigureRootLoggerChecker(ast.NodeVisitor):
    def __init__(self) -> None:
        self.errors: list[tuple[LineNumber, ColumnOffset, ErrorMessage]] = []
        self.logging_aliases: set[str] = {"logging"}

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            if alias.name == "logging":
                self.logging_aliases.add(alias.asname or "logging")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in self.logging_aliases
            and node.func.attr == "basicConfig"
        ):
            self.errors.append(
                (
                    node.lineno,
                    node.col_offset,
                    "HPL101 Don't configure the root logger in your library",
                )
            )

        self.generic_visit(node)
