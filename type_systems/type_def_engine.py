from .symbol_table import ScopeManager
from .symbol_types import *


class TypeDefEngine:
    def __init__(self, ast_tree):
        self.ast_tree = ast_tree
        self.sm = ScopeManager()

    def error(self, node, message):
        line = getattr(node, "line", None)
        col = getattr(node, "column", None)
        loc = f" [Line {line}:{col}]" if line is not None else ""
        raise SyntaxError(f"Nidavellir Error{loc}: {message}")

    def eval_VariableAST(self, ast):
        pass

    def eval_NumberAST(self, ast):
        pass

    def stmt_PassAST(self, ast):
        pass

    def stmt_FunctionAST(self, ast):
        self.sm.add_symbol(FunctionSymbol(ast.name, None, ast.args))
        self.sm.enter_scope()
        for param in ast.args:
            self.sm.add_symbol(VariableSymbol(param.name, param.type))

        for stmt in ast.body:
            self.visit_statement(stmt)

        self.sm.exit_scope()

    def stmt_CallAST(self, ast):
        func = self.sm.get_symbol(ast.target)
        if not isinstance(func, FunctionSymbol):
            self.error(ast, f"Cannot call non-function symbol {ast.target}")

        if len(ast.args) != len(func.params):
            self.error(ast, f"Function {ast.target} takes {len(func.params)} arguments")

    def stmt_AssignAST(self, ast):
        self.sm.add_symbol(VariableSymbol(ast.target, ast.type_annotation))

    def visit_statement(self, node):
        method_name = f"stmt_{type(node).__name__}"
        visitor = getattr(self, method_name, None)
        if visitor is None:
            self.error(
                node,
                f"Standalone expression '{type(node).__name__}' is not a valid statement",
            )
        return visitor(node)

    def visit_expression(self, node):
        method_name = f"eval_{type(node).__name__}"
        visitor = getattr(self, method_name, None)
        if visitor is None:
            self.error(node, f"Invalid expression context for '{type(node).__name__}'")
        return visitor(node)

    def run(self):
        for node in self.ast_tree:
            self.visit_statement(node)

        self.sm.print_scopes()
