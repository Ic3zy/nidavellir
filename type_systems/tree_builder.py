from .symbol_table import SymbolTableManager
from .tree_printer import render_node
from .symbol_types import *
from nida_ast.base import *


class SymbolTreeBuilder:
    def __init__(self, ast_tree):
        self.ast_tree = ast_tree
        self.stm = SymbolTableManager()
        self.st = []

        self.run()

    def error(self, node, message):
        line = getattr(node, "line", None)
        col = getattr(node, "column", None)
        loc = f" [Line {line}:{col}]" if line is not None else ""
        raise SyntaxError(f"Nidavellir Error{loc}: {message}")

    def eval_VariableAST(self, ast):
        var = self.stm.lookup(ast.name)
        if var is None:
            self.error(ast, f"Variable '{ast.name}' is not defined")

        return VariableSymbol(ast.name, var, ast)

    def eval_AssignAST(self, ast):
        return self.stmt_AssignAST(ast)

    def eval_NumberAST(self, ast):
        return NumberSymbol(ast.value, ast)

    def eval_BinaryOpAST(self, ast):
        left_sym = self.process_eval(ast.left)
        right_sym = self.process_eval(ast.right)

        return BinaryOpSymbol(ast.op, left_sym, right_sym, ast)

    def eval_StringAST(self, ast):
        return StringSymbol(ast.value, ast)

    def eval_NoneAST(self, ast):
        return NoneSymbol(ast)

    def eval_CallAST(self, ast):
        return self.stmt_CallAST(ast)

    def stmt_PassAST(self, ast):
        pass

    def stmt_AssignAST(self, ast):
        val = ast.value
        val_sym = None
        if val is not None:
            val_sym = self.process_eval(ast.value)

        final_sym = AssignSymbol(ast.target, ast.type_annotation, val_sym, ast)

        target_lookup = self.stm.lookup(ast.target)
        if target_lookup is not None:
            target_lookup.uses.append(final_sym)
        else:
            self.stm.add_symbol(final_sym)
            return final_sym

    def stmt_FunctionAST(self, ast):
        lookup = self.stm.lookup(ast.name)
        if lookup is not None:
            self.error(ast, f"Function '{ast.name}' already exists")

        fn_sym = FunctionSymbol(ast.name, ast.type, None, ast)
        self.stm.add_symbol(fn_sym)
        self.stm.enter_scope()

        params = []
        for param in ast.args:
            res = self.process_eval(param)
            if res is not None:
                params.append(res)

        fn_sym.args = params

        res = self.process_from_list(ast.body)
        fn_sym.body = res
        fn_sym.returned.extend([r for r in res if isinstance(r, ReturnSymbol)])

        self.stm.exit_scope()

        return fn_sym

    def stmt_ReturnAST(self, ast):
        val = ast.value
        if val is not None:
            val = self.process_eval(ast.value)

        return ReturnSymbol(val, ast)

    def stmt_CallAST(self, ast):
        func_name = ast.target
        # TODO: impl intrinsic

        lookup = self.stm.lookup(func_name)
        if lookup is None:
            self.error(ast, f"Function '{func_name}' is not defined")

        params = []
        for arg in ast.args:
            res = self.process_eval(arg)
            if res is not None:
                params.append(res)

        sym = CallSymbol(func_name, params, lookup, ast)
        lookup.uses.append(sym)

        return sym

    def process_eval(self, ast):
        method_name = f"eval_{type(ast).__name__}"
        visitor = getattr(self, method_name, None)
        if visitor is None:
            self.error(ast, f"No function named {method_name}")
        return visitor(ast)

    def process_stmt(self, ast):
        method_name = f"stmt_{type(ast).__name__}"
        visitor = getattr(self, method_name, None)
        if visitor is None:
            self.error(ast, f"No function named {method_name}")
        return visitor(ast)

    def process_from_list(self, asts):
        st = []
        for ast in asts:
            res = self.process_stmt(ast)
            if res is not None:
                st.append(res)

        return st

    def run(self):
        res = self.process_from_list(self.ast_tree)
        self.st.extend(res)
        # raise Exception(self.print_scopes())

    def print_scopes(self, st=None):
        print("SymbolTree")
        st = st or self.st
        lines = render_node("st", st, prefix="", is_last=True)
        for line in lines:
            print(line)

    def print_ast_tree(self):
        print(self.ast_tree)
