from semantic import INTRINSIC_HANDLERS
from nida_ast.base import *
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
        var = self.sm.lookup(ast.name)
        if var is None:
            self.error(ast, f"Variable '{ast.name}' is not defined")

        return var

    def eval_NumberAST(self, ast):
        pass

    def eval_CallAST(self, ast):
        self.stmt_CallAST(ast)

    def inference_class_params(self, ast):
        params = []
        for node in ast.body:
            if isinstance(node, FunctionAST):
                for arg in node.args:
                    type = arg.type_annotation
                    target = arg.target
                    params.append({"type": type, "name": target})

        return params

    def stmt_ClassAST(self, ast):
        print(ast)
        params = self.inference_class_params(ast)
        self.sm.add_symbol(ClassSymbol(ast.name, params))
        self.sm.enter_scope()
        for node in ast.body:
            self.visit_statement(node)

        self.sm.exit_scope()

    def stmt_PassAST(self, ast):
        pass

    def stmt_FunctionAST(self, ast):
        self.sm.add_symbol(FunctionSymbol(ast.name, None, ast.args))
        self.sm.enter_scope()
        for param in ast.args:
            self.sm.add_symbol(VariableSymbol(param.target, param.type_annotation))

        for stmt in ast.body:
            self.visit_statement(stmt)

        self.sm.exit_scope()

    def transform_Intrinsic_to_Symbol(self, node):
        return FunctionSymbol(
            node["name"],
            node["return_type"],
            node["params"],
            is_variadic=node["is_variadic"],
        )

    def stmt_CallAST(self, ast):
        func_name = ast.target
        if func_name in INTRINSIC_HANDLERS:
            temp = INTRINSIC_HANDLERS[func_name]
            func = self.transform_Intrinsic_to_Symbol(temp)
        else:
            func = self.sm.get_symbol(ast.target)

        if isinstance(func, FunctionSymbol):
            if len(ast.args) != len(func.params) and not func.is_variadic:
                self.error(
                    ast, f"Function {ast.target} takes {len(func.params)} arguments"
                )

            for arg in ast.args:
                var = self.visit_expression(arg)
                if not isinstance(var, VariableSymbol):
                    self.error(arg, f"Cannot pass non-variable symbol {arg.name}")

                var.used_stack.append(ast)
        elif isinstance(func, ClassSymbol):
            if len(ast.args) != len(func.params):
                self.error(ast, f"Class {ast.target} takes 1 argument")

        func.call_stack.append(ast)

    def stmt_AssignAST(self, ast):
        self.sm.add_symbol(VariableSymbol(ast.target, ast.type_annotation))
        self.visit_expression(ast.value)

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
