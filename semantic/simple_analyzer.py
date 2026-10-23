from .intrinsics import INTRINSICS
from .symbol_table import SymbolTableManager
from nida_ast.base import *
from type_systems.types import *


class SimpleASTVisitor:
    def __init__(self, stm, ctx):
        self.stm = stm
        self.ctx = ctx
        self.f_alloc = ctx["f_alloc"]

        self.module_scopes = {}

        self.function_id = 0

    def stmt_AssignAST(self, node):
        pass

    def visit_statement(self, node):
        method_name = f"stmt_{type(node).__name__}"
        visitor = getattr(self, method_name, None)
        if visitor is None:
            raise Exception(
                node,
                f"Standalone expression '{type(node).__name__}' is not a valid statement",
            )
        return visitor(node)


class SimpleAnalyzer:
    def __init__(self, ast_tree, ctx):
        self.ast_tree = ast_tree
        self.ctx = ctx
        self.stm = SymbolTableManager()
        self.sav = SimpleASTVisitor(self.stm, self.ctx)

    def analyze_all(self):
        for node in self.ast_tree:
            self.sav.visit_statement(node)

        for node in self.ast_tree:
            normalize_ast_types(node, self.stm.global_scope.classes)

        for module in self._imported_modules():
            for node in module.asts:
                normalize_ast_types(node, self.stm.global_scope.classes)

    def _imported_modules(self):
        modules = []
        seen = set()

        def visit(node):
            module = getattr(node, "resolved_module", None)

            if module is None or id(module) in seen:
                return

            seen.add(id(module))
            modules.append(module)

            for child in module.asts:
                visit(child)

        for node in self.ast_tree:
            visit(node)

        return modules


def normalize_ast_types(node, classes={}):
    if node is None:
        return

    if hasattr(node, "type") and node.type is not None:
        node.type = _normalize_type(node.type, classes)

    for attr in ("body", "args", "elifs"):
        val = getattr(node, attr, None)
        if isinstance(val, list):
            for item in val:
                normalize_ast_types(item, classes)
        elif val is not None and not isinstance(val, (str, int, float, bool)):
            normalize_ast_types(val, classes)

    for attr in (
        "value",
        "target",
        "cond",
        "left",
        "right",
        "expr",
        "else_body",
        "source",
        "chain",
    ):
        val = getattr(node, attr, None)
        if val is not None and not isinstance(val, (str, int, float, bool)):
            normalize_ast_types(val, classes)

    types = getattr(node, "chain_types", None)

    if isinstance(types, list):
        node.chain_types = [_normalize_type(t, classes) for t in types]

    base_type = getattr(node, "base_type", None)
    if base_type is not None:
        node.base_type = _normalize_type(base_type, classes)


def _normalize_type(type_val, classes):
    if type_val is None or isinstance(type_val, Type):
        return type_val

    new_type = resolve_type(type_val)

    if new_type is None:
        if type_val in classes:
            new_type = ClassType(type_val)
        else:
            raise TypeError(
                f"Unknown type '{type_val}'. The type is not defined or imported."
            )

    return new_type
