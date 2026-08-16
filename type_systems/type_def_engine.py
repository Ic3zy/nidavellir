from .symbol_table import ScopeManager
from .symbol_types import *


class TypeDefEngine:
    def __init__(self, ast_tree):
        self.ast_tree = ast_tree
        self.sm = ScopeManager()

    def eval_VariableAST(self, ast):
        pass

    def eval_NumberAST(self, ast):
        number = ast.value
        if number is None:
            return "int"

        number = int(number)

        if -(2**7) <= number <= 2**7 - 1:
            return "int8"

        if -(2**15) <= number <= 2**15 - 1:
            return "int16"

        if -(2**31) <= number <= 2**31 - 1:
            return "int32"

        if -(2**63) <= number <= 2**63 - 1:
            return "int64"

        if -(2**127) <= number <= 2**127 - 1:
            return "int128"

        if 0 <= number <= 2**128 - 1:
            return "uint128"

        raise Exception("Integer literal is too large")

    def eval_CallAST(self, ast):
        pass

    def stmt_FunctionAST(self, ast):
        pass

    def stmt_CallAST(self, ast):
        print(ast)

    def stmt_AssignAST(self, ast):
        if ast.type_annotation is None:
            type = self.visit_expression(ast.value)
            if type is None:
                self.error(ast, "Cannot infer type of expression")
            else:
                ast.type_annotation = type
        else:
            self.sm.define_assign(ast.target, ast.type_annotation)

        print(ast)

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
