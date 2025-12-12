import ast

LineNumber = int
ColumnOffset = int
ErrorMessage = str


class ConfigureRootLoggerChecker(ast.NodeVisitor):
    def __init__(self) -> None:
        self.errors: list[tuple[LineNumber, ColumnOffset, ErrorMessage]] = []
        self.logging_aliases: set[str] = set()
        self.imported_names: set[str] = set()
        self.imported_aliases: dict[str, str] = {}  # alias -> original_name

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            if alias.name == "logging":
                self.logging_aliases.add(alias.asname or "logging")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.module == "logging":
            for alias in node.names:
                name = alias.asname or alias.name
                self.imported_names.add(name)
                if alias.asname:
                    self.imported_aliases[alias.asname] = alias.name
        self.generic_visit(node)

    def _is_logging_attribute_basic_config_call(self, node: ast.Call) -> bool:
        return (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in self.logging_aliases
            and node.func.attr == "basicConfig"
        )

    def _is_imported_basic_config_call(self, node: ast.Call) -> bool:
        if not isinstance(node.func, ast.Name):
            return False

        func_name = node.func.id
        if func_name == "basicConfig":
            return True

        # エイリアスの場合、元の関数名を確認
        original_name = self.imported_aliases.get(func_name)
        return original_name == "basicConfig"

    def _is_imported_logging_direct_call(self, node: ast.Call) -> bool:
        if not isinstance(node.func, ast.Name):
            return False

        func_name = node.func.id
        if func_name not in self.imported_names:
            return False

        # basicConfigは除外
        if func_name == "basicConfig":
            return False

        # エイリアスの場合、元の関数名を確認
        original_name = self.imported_aliases.get(func_name, func_name)
        return original_name in {"debug", "info", "warning", "error", "critical", "exception", "log"}

    def _is_basic_config_call(self, node: ast.Call) -> bool:
        return self._is_logging_attribute_basic_config_call(node) or self._is_imported_basic_config_call(node)

    def _is_logging_direct_call(self, node: ast.Call) -> bool:
        return (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in self.logging_aliases
            and node.func.attr in {"debug", "info", "warning", "error", "critical", "exception", "log"}
        ) or self._is_imported_logging_direct_call(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if self._is_basic_config_call(node):
            self.errors.append(
                (
                    node.lineno,
                    node.col_offset,
                    "HPL101 Don't configure the root logger in your library",
                )
            )
        elif self._is_logging_direct_call(node):
            self.errors.append(
                (
                    node.lineno,
                    node.col_offset,
                    "HPL102 Don't use the root logger directly in your library",
                )
            )

        self.generic_visit(node)
