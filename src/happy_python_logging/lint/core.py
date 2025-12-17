import ast

LineNumber = int
ColumnOffset = int
ErrorMessage = str

LOGGING_FUNCTION_NAMES = {"debug", "info", "warning", "error", "critical", "exception", "log"}


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

    def _get_original_func_name_if_alias(self, alias_name: str) -> str:
        return self.imported_aliases.get(alias_name, alias_name)

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

        original_name = self._get_original_func_name_if_alias(func_name)
        return original_name == "basicConfig"

    def _is_basic_config_call(self, node: ast.Call) -> bool:
        return self._is_logging_attribute_basic_config_call(node) or self._is_imported_basic_config_call(node)

    def _is_aliased_logging_function_call(self, node: ast.Call) -> bool:
        if not isinstance(node.func, ast.Name):
            return False

        func_name = node.func.id
        if func_name not in self.imported_names:
            return False

        if func_name == "basicConfig":
            return False

        original_name = self._get_original_func_name_if_alias(func_name)
        return original_name in LOGGING_FUNCTION_NAMES

    def _is_logging_attribute_function_call(self, node: ast.Call) -> bool:
        return (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in self.logging_aliases
            and node.func.attr in LOGGING_FUNCTION_NAMES
        )

    def _is_logging_function_call(self, node: ast.Call) -> bool:
        return self._is_logging_attribute_function_call(node) or self._is_aliased_logging_function_call(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if self._is_basic_config_call(node):
            self.errors.append(
                (
                    node.lineno,
                    node.col_offset,
                    "HPL101 Don't configure the root logger in your library",
                )
            )
        elif self._is_logging_function_call(node):
            self.errors.append(
                (
                    node.lineno,
                    node.col_offset,
                    "HPL102 Don't use the logging function (and configure the root logger) in your library",
                )
            )

        self.generic_visit(node)
