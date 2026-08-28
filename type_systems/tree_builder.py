from semantic import INTRINSIC_HANDLERS
from nida_ast.base import *
from .symbol_table import ScopeManager
from .symbol_types import *


class SymbolTreeBuilder:
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
        return self.stmt_CallAST(ast)

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
        params = self.inference_class_params(ast)
        self.sm.add_symbol(ClassSymbol(ast.name, params, None, ast))
        self.sm.enter_scope(attach_to_parent=False)

        sym = self.sm.lookup(ast.name)
        sym.scope = self.sm.current_scope

        for node in ast.body:
            self.visit_statement(node)

        self.sm.exit_scope()

    def stmt_PassAST(self, ast):
        pass

    def stmt_FunctionAST(self, ast):
        fn_sym = FunctionSymbol(ast.name, None, ast.args, ast)
        self.sm.add_symbol(fn_sym)
        self.sm.enter_scope()

        params = []
        for param in ast.args:
            sym = VariableSymbol(param.target, param.type_annotation, param)
            params.append({"name": param.target, "symbol": sym})

            self.sm.add_symbol(sym)

        ret = None
        var = None
        for stmt in ast.body:
            if isinstance(stmt, ReturnAST):
                ret = self.visit_statement(stmt)
                if isinstance(ret, VariableAST):
                    var = self.sm.lookup(ret.name)
                    if var is None:
                        self.error(ret, f"Variable '{ret.name}' is not defined")

                continue

            self.visit_statement(stmt)

        fn_sym.returns = {"symbol": var, "ast_node": ret}
        fn_sym.params = params
        self.sm.exit_scope()

    def stmt_ReturnAST(self, ast):
        return ast.value

    def transform_Intrinsic_to_Symbol(self, node):
        return FunctionSymbol(
            node["name"],
            node["return_type"],
            node["params"],
            None,  # ast_node
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
            sym = CallSymbol(ast.target, ast.args, func, ast)
            if len(ast.args) != len(func.params) and not func.is_variadic:
                self.error(
                    ast, f"Function {ast.target} takes {len(func.params)} arguments"
                )

            for arg in ast.args:
                var = self.visit_expression(arg)
                if not isinstance(var, VariableSymbol):
                    self.error(arg, f"Cannot pass non-variable symbol {arg.name}")

                sym.sym_params.append(var)

                var.used_stack.append(sym)

        elif isinstance(func, ClassSymbol):
            if len(ast.args) != len(func.params):
                self.error(ast, f"Class {ast.target} takes 1 argument")
        else:
            self.error(ast, f"Cannot call {ast.target}")

        func.call_stack.append(sym or ast)
        return sym or ast

    def stmt_AssignAST(self, ast):
        var_sym = VariableSymbol(ast.target, ast.type_annotation, ast)
        self.sm.add_symbol(var_sym)

        value = ast.value
        sym = None
        if isinstance(value, CallAST):
            sym = self.stmt_CallAST(value)
        else:
            self.visit_expression(ast.value)

        var_sym.call_symbol = sym

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

    def print_scopes(self):
        self.sm.print_scopes()
