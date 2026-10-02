from .symbol_table import SymbolTableManager
from .tree_printer import render_node
from .symbol_types import *
from nida_ast.base import *
from semantic import INTRINSIC_HANDLERS as INTRINSICS


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
            final_sym.parent_assign = target_lookup
            target_lookup.uses.append(final_sym)
        else:
            self.stm.add_symbol(final_sym)

        return final_sym

    def stmt_intrinsic(self, name, type, args, is_variadic=False):
        fn_sym = FunctionSymbol(name, type, args, None, is_variadic)
        self.stm.add_symbol(fn_sym)
        return fn_sym

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

        is_intrinsic = func_name in INTRINSICS

        lookup = self.stm.lookup(func_name)
        if lookup is None and is_intrinsic:
            intrinsic = INTRINSICS[func_name]
            ret = self.stmt_intrinsic(
                func_name,
                intrinsic["return_type"],
                intrinsic["params"],
                intrinsic["is_variadic"],
            )
            lookup = ret
        if lookup is None:
            self.error(ast, f"Function '{func_name}' is not defined")

        params = []
        for idx, arg in enumerate(ast.args):
            res = self.process_eval(arg)
            if is_intrinsic:
                continue

            if idx >= len(lookup.args):
                self.error(arg, f"Too many arguments for function '{func_name}'")

            lookup_func_arg = lookup.args[idx]

            if res is not None:
                params.append(res)

            if lookup_func_arg is not None and res is not None:
                lookup_func_arg.uses.append(res)

        sym = CallSymbol(func_name, params, lookup, ast)
        lookup.uses.append(sym)

        return sym

    def stmt_ForAST(self, ast):
        self.stm.enter_scope()
        target = self.process_stmt(ast.target)
        source = ast.source
        loop_count = None
        if isinstance(source, CallAST):
            target_fn = source.target
            if target_fn == "range" and isinstance(source.args[0], NumberAST):
                loop_count = source.args[0].value
                loop_count = int(loop_count)
            else:
                raise NotImplementedError(
                    f"For loop source '{target_fn}' is not implemented"
                )
        else:
            raise NotImplementedError(
                f"For loop source '{type(source).__name__}' is not implemented"
            )

        target.uses.append(NumberSymbol(0, ast))
        target.uses.append(NumberSymbol(loop_count, ast))

        body = []
        for b in ast.body:
            body.append(self.process_stmt(b))

        self.stm.exit_scope()

        # raise Exception(ast)
        return ForSymbol(target, source, body, loop_count, ast)

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
