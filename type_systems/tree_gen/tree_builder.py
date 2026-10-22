from .symbol_table import SymbolTableManager
from .tree_printer import render_node
from .symbol_types import *
from nida_ast.base import *
from type_systems.types import resolve_type, ClassType, ListType, NoneType


class SymbolTreeBuilder:
    def __init__(self, ast_tree):
        self.ast_tree = ast_tree
        self.stm = SymbolTableManager()
        self.st = []
        self.class_syms = {}

        self.visited_imports = set()

        self.current_class_name = None

        self.run()

    def error(self, node, message):
        line = getattr(node, "line", None)
        col = getattr(node, "column", None)
        loc = f" [Line {line}:{col}]" if line is not None else ""
        raise SyntaxError(f"Nidavellir Error{loc}: {message}")

    def resolve(self, type_val):
        resolved = resolve_type(type_val)

        if resolved is None and isinstance(type_val, str):
            if isinstance(self.stm.lookup(type_val), ClassSymbol):
                return ClassType(type_val)

        return resolved

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

    def eval_GroupAST(self, ast):
        return self.process_eval(ast.expr)

    def eval_StringAST(self, ast):
        return StringSymbol(ast.value, ast)

    def eval_NoneAST(self, ast):
        return NoneSymbol(ast)

    def eval_CallAST(self, ast):
        return self.stmt_CallAST(ast)

    def eval_IntrinsicAST(self, ast):
        self.stmt_intrinsic(ast.name, ast.type, ast.args)
        return self.stmt_CallAST(ast)

    def eval_BooleanAST(self, ast):
        return BooleanSymbol(ast.value, ast)

    def eval_UnaryOpAST(self, ast):
        right_sym = self.process_eval(ast.right)

        return UnaryOpSymbol(ast.op, right_sym, ast)

    def eval_ListLiteralAST(self, ast):
        elements = []

        for e in ast.elements:
            element_sym = self.process_eval(e)
            elements.append(element_sym)

        return ListLiteralSymbol(elements, ast)

    def stmt_PassAST(self, ast):
        pass

    def stmt_AssignAST(self, ast):
        val = ast.value
        val_sym = None
        if val is not None:
            val_sym = self.process_eval(ast.value)

        final_sym = AssignSymbol(ast.target, ast.type, val_sym, ast)

        if final_sym.type is None:
            final_sym.type = self.resolve(ast.type)

        target_lookup = self.stm.current_scope.symbols.get(ast.target)
        if target_lookup is not None:
            final_sym.parent_assign = target_lookup
            target_lookup.uses.append(final_sym)
        elif ast.target != "self":
            self.stm.add_symbol(final_sym)

        if ast.chain:
            final_sym.chain = ast.chain

            base_type = getattr(ast, "base_type", None)

            if base_type is not None:
                final_sym.type = self.resolve(base_type)

            if ast.target == "self":
                final_sym.base_sym = SelfSymbol(ast, self.current_class_name)
            else:
                final_sym.base_sym = self.stm.lookup(ast.target)

        return final_sym

    def stmt_IntrinsicAST(self, ast):
        pass

    def stmt_IntrinsicCallAST(self, ast):
        name = ast.intrinsic.name
        args = ast.args
        intrinsic = ast.intrinsic

        n_args = self.process_call_args(args, intrinsic, name, is_intrinsic=True)

        return IntrinsicCallSymbol(intrinsic, name, n_args, ast)

    def eval_IntrinsicCallAST(self, ast):
        return self.stmt_IntrinsicCallAST(ast)

    def stmt_DefinitionAST(self, ast):
        lk = self.stm.lookup(ast.target)
        if lk is not None:
            raise SyntaxError(f"Definition of variable '{ast.target}' already exists")

        val = ast.value
        val_sym = self.process_eval(val)

        self.stm.add_symbol(d := DefinitionSymbol(ast.target, ast.type, val_sym, ast))
        return d

    def stmt_FunctionAST(self, ast):
        fn_sym = self.stm.lookup(ast.name)

        if fn_sym is None:
            fn_sym = FunctionSymbol(ast.name, ast.type, None, ast)
            self.stm.add_symbol(fn_sym)

        fn_sym.ast_node = ast
        fn_sym.type = self.resolve(ast.type)

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

    def process_call_args(self, args, lookup, func_name, is_intrinsic=False, skip=0):
        params = []
        arg_symbols = self._arg_symbols(lookup)[skip:]

        for idx, arg in enumerate(args):
            res = self.process_eval(arg)

            lookup_func_arg = None
            if not is_intrinsic:
                if idx >= len(arg_symbols):
                    self.error(arg, f"Too many arguments for function '{func_name}'")

                lookup_func_arg = arg_symbols[idx]

            if res is not None:
                params.append(res)

            if lookup_func_arg is not None and res is not None and not is_intrinsic:
                lookup_func_arg.uses.append(res)

        return params

    def _arg_symbols(self, lookup):
        if isinstance(lookup, ClassSymbol):
            init_sym = lookup.method_syms.get("__init__")

            if init_sym is None:
                return []

            return init_sym.args or []

        return getattr(lookup, "args", None) or []

    def stmt_CallAST(self, ast):
        func_name = ast.target

        if ast.chain:
            return self._method_call(ast)

        lookup = self.stm.lookup(func_name)

        if lookup is None:
            self.error(ast, f"Function '{func_name}' is not defined")

        skip = 1 if isinstance(lookup, ClassSymbol) else 0

        params = self.process_call_args(ast.args, lookup, func_name, skip=skip)

        if isinstance(lookup, ClassSymbol):
            sym = ConstructorCallSymbol(func_name, params, lookup, ast)
            sym.type = lookup.type
            lookup.uses.append(sym)

            init_sym = lookup.method_syms.get("__init__")

            if init_sym is not None:
                init_sym.uses.append(sym)

            return sym

        sym = CallSymbol(func_name, params, lookup, ast)
        lookup.uses.append(sym)

        return sym

    def _method_call(self, ast):
        chain = ast.chain

        if ast.target == "self":
            base = None
            class_name = self.current_class_name
        else:
            base = self.stm.lookup(ast.target)

            if base is None:
                self.error(ast, f"Variable '{ast.target}' is not defined")

            class_name = base.type.name if isinstance(base.type, ClassType) else None

        if class_name is None and isinstance(getattr(base, "type", None), ListType):
            return self._list_method_call(ast, base)

        if class_name is None:
            self.error(ast, f"Cannot call method '{chain[0]}' on a non-class value")

        field_chain = chain[:-1]
        method_name = chain[-1]

        for field_name in field_chain:
            class_sym = self._find_class(class_name)
            if class_sym is None:
                self.error(ast, f"Class '{class_name}' is not defined")

            field_ast = class_sym.fields.get(field_name)

            if field_ast is None:
                self.error(
                    ast, f"Member '{field_name}' is not defined in class '{class_name}'"
                )

            field_class = self._field_class(field_ast)

            if field_class is None:
                self.error(
                    ast,
                    f"Cannot call method on field '{field_name}' of non-class type",
                )

            class_name = field_class

        class_sym = self._find_class(class_name)
        if class_sym is None:
            self.error(ast, f"Class '{class_name}' is not defined")

        method_ast = class_sym.methods.get(method_name)
        if method_ast is None:
            self.error(ast, f"Method '{method_name}' is not defined")

        lookup = class_sym.method_syms.get(method_name)

        if lookup is None:
            lookup = FunctionSymbol(method_name, method_ast.type, None, method_ast)
            lookup.args = [None] * len(method_ast.args)

        params = self.process_call_args(ast.args, lookup, method_name, skip=1)

        sym = CallSymbol(method_name, params, lookup, ast)
        sym.receiver_chain = list(field_chain)
        sym.arg_offset = 1
        lookup.uses.append(sym)

        return sym

    def _list_method_call(self, ast, base):
        chain = ast.chain
        method_name = chain[-1]

        if method_name != "append":
            self.error(ast, f"List has no method '{method_name}'")

        params = self.process_call_args(ast.args, None, method_name, is_intrinsic=True)

        sym = CallSymbol(method_name, params, base, ast)
        sym.type = NoneType()
        sym.is_list_method = True
        base.uses.append(sym)

        return sym

    def _field_class(self, field_ast):
        field_type = getattr(field_ast, "type", None)

        if field_type is None:
            value = getattr(field_ast, "value", None)
            field_type = getattr(value, "type", None)

        if isinstance(field_type, ClassType):
            return field_type.name

        if isinstance(field_type, str) and self._find_class(field_type) is not None:
            return field_type

        return None

    def _find_class(self, name):
        return self.class_syms.get(name)

    def stmt_ForAST(self, ast):
        self.stm.enter_scope()
        target = self.process_stmt(ast.target)
        source = ast.source
        loop_count = None
        if isinstance(source, (CallAST, IntrinsicAST, IntrinsicCallAST)):
            target_fn = getattr(source, "target", getattr(source, "name", None))
            args = getattr(source, "args", [])
            if target_fn == "range" and args and isinstance(args[0], NumberAST):
                loop_count = args[0].value
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

    def stmt_ElifAST(self, ast):
        cond = ast.cond
        body = ast.body

        cond_sym = self.process_eval(cond)
        body_sym = self.process_from_list(body)

        return ElifSymbol(cond_sym, body_sym, ast)

    def stmt_IfAST(self, ast):
        cond = ast.cond
        body = ast.body

        elifs = ast.elifs
        else_body = ast.else_body

        cond_sym = self.process_eval(cond)
        body_sym = self.process_from_list(body)
        elifs_sym = self.process_from_list(elifs)

        if else_body is not None:
            else_body = self.process_from_list(else_body.body)

        return IfSymbol(cond_sym, body_sym, elifs_sym, else_body, ast)

    def stmt_WhileAST(self, ast):
        cond = ast.cond
        body = ast.body

        cond_sym = self.process_eval(cond)
        body_sym = self.process_from_list(body)

        return WhileSymbol(cond_sym, body_sym, ast)

    def stmt_ImportAST(self, ast):
        module = ast.resolved_module

        if module is None:
            return

        if module in self.visited_imports:
            return

        self.visited_imports.add(module)

        st = self.process_from_list(module.asts)
        self.st.extend(st)

    def stmt_ClassAST(self, ast):
        name = ast.name

        class_sym = self.stm.lookup(name)

        if class_sym is None:
            class_sym = ClassSymbol(name, ast)
            self.stm.add_symbol(class_sym)

        class_sym.ast_node = ast
        self.class_syms[name] = class_sym

        self.stm.enter_scope()

        self.current_class_name = name

        for b in ast.body:
            res = self.process_stmt(b)
            if res is not None:
                class_sym.body.append(res)

            if isinstance(b, AssignAST):
                if b.chain:
                    class_sym.fields[b.chain[0]] = b
                else:
                    class_sym.fields[b.target] = b
            elif isinstance(b, FunctionAST):
                class_sym.methods[b.name] = b
                class_sym.method_syms[b.name] = res

                for stmt in b.body:
                    if isinstance(stmt, AssignAST) and stmt.chain:
                        class_sym.fields.setdefault(stmt.chain[0], stmt)

        self.current_class_name = None

        self.stm.exit_scope()

        return class_sym

    def eval_FieldAccessAST(self, ast):
        target = ast.target
        chain = ast.chain

        target_sym = self.process_eval(target)

        return FieldAccessSymbol(target_sym, chain, ast)

    def eval_SelfAST(self, ast):
        return SelfSymbol(ast, self.current_class_name)

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
        self.declare(self.ast_tree)

        res = self.process_from_list(self.ast_tree)
        self.st.extend(res)
        # raise Exception(self.print_scopes())

    def declare(self, asts):
        for ast in asts:
            if isinstance(ast, FunctionAST):
                if self.stm.lookup(ast.name) is None:
                    fn_sym = FunctionSymbol(ast.name, ast.type, None, ast)
                    fn_sym.args = [None] * len(ast.args)
                    self.stm.add_symbol(fn_sym)

            elif isinstance(ast, ClassAST):
                if self.stm.lookup(ast.name) is None:
                    self.stm.add_symbol(ClassSymbol(ast.name, ast))

    def print_scopes(self, st=None):
        print("SymbolTree")
        st = st or self.st
        lines = render_node("st", st, prefix="", is_last=True)
        for line in lines:
            print(line)

    def print_ast_tree(self):
        print(self.ast_tree)
