# NOTE: Technical debt has accumulated on this analyzer layer.
# The current priority is to build a working prototype (MVP), not perfect architecture.

from .intrinsics import INTRINSICS
from .symbol_table import SymbolTableManager
from nida_ast.base import *
from type_systems.types import resolve_type, ClassType, Type

VALID_RETURN_EXPRESSIONS = (
    NoneAST,
    VariableAST,
    NumberAST,
    StringAST,
    BooleanAST,
    ListAST,
    CallAST,
    IndexAccessAST,
    BinaryOpAST,
    UnaryOpAST,
    FieldAccessAST,
)


class SimpleASTVisitor:
    def __init__(self, stm, ctx):
        self.stm = stm
        self.ctx = ctx
        self.f_alloc = ctx["f_alloc"]

        self.body_parse_waiter_funcs = []
        self.module_scopes = {}
        self.current_class_name = None

        self.function_id = 0

    def error(self, node, message):
        line = getattr(node, "line", None)
        col = getattr(node, "column", None)
        loc = f" [Line {line}:{col}]" if line is not None else ""
        raise SyntaxError(f"Nidavellir Error{loc}: {message}")

    def generic_visit(self, node):
        self.error(node, f"Unexpected node: {type(node).__name__}")

    def _parse_body(self, scope, body, args, class_name=None):
        saved_scope = self.stm.current_scope
        saved_class = self.current_class_name

        self.stm.current_scope = scope
        self.current_class_name = class_name

        for arg in args:
            self.stm.define_var(arg.target, arg.type)

        for node in body:
            self.visit_statement(node)

        self.stm.current_scope = saved_scope
        self.current_class_name = saved_class

    def get_target_in_bpwf(self, target):
        for func_data in self.body_parse_waiter_funcs:
            scope, _, _, class_name = func_data
            if class_name == self.current_class_name and scope.name == f"func_{target}":
                return func_data
        return None

    def eval_VariableAST(self, node):
        symbol = self.stm.lookup_var(node.name)
        if symbol is None:
            self.error(node, f"Variable '{node.name}' is not defined")

        if node.type is None and symbol.get("type") is not None:
            node.type = symbol["type"]

        return symbol

    def eval_UnaryOpAST(self, node):
        pass

    def eval_NumberAST(self, node):
        pass

    def eval_StringAST(self, node):
        pass

    def eval_BooleanAST(self, node):
        pass

    def eval_BinaryOpAST(self, node):
        self.visit_expression(node.left)
        self.visit_expression(node.right)

    def eval_FieldAccessAST(self, node):
        target = node.target
        chain = getattr(node, "chain", [])

        if isinstance(target, SelfAST):
            class_name = self.get_current_class_name()

            if class_name is None:
                self.error(node, "'self' is only valid inside a class")

            base_class = class_name
        elif isinstance(target, VariableAST):
            self.eval_VariableAST(target)

            base_class = self._class_of(target)
        else:
            self.visit_expression(target)

            base_class = self._class_of(target)

        # The type of every step in the chain, so the backend knows the type
        # of the intermediate values too.
        chain_types = []

        for member in chain:
            if base_class is None:
                self.error(
                    node,
                    f"Cannot access member '{member}' on a non-class value",
                )

            field = self.stm.lookup_field(base_class, member)

            if field is None:
                method = self.stm.lookup_class(base_class)
                if method is not None and member in method.methods:
                    base_class = None
                    chain_types.append(None)
                    continue

                self.error(
                    node,
                    f"Member '{member}' is not defined in class '{base_class}'",
                )

            field_type = self._type_of_field(field)

            chain_types.append(field_type)
            base_class = self._class_of(field)

        node.chain_types = chain_types

        return None

    def _type_of_field(self, field):
        if isinstance(field, dict):
            field_type = field.get("type")
            ast_node = field.get("ast")
        else:
            field_type = getattr(field, "type", None)
            ast_node = field

        if field_type is not None:
            return self._resolve(field_type)

        value = getattr(ast_node, "value", None)

        return self._resolve(getattr(value, "type", None))

    def _resolve(self, type_val):
        if type_val is None or isinstance(type_val, Type):
            return type_val

        resolved = resolve_type(type_val)

        if resolved is not None:
            return resolved

        if isinstance(type_val, str) and self.stm.lookup_class(type_val) is not None:
            return ClassType(type_val)

        return type_val

    def _define_self_field(self, node, class_name, chain):
        if class_name is None or node.target != "self" or not chain:
            return

        class_symbol = self.stm.lookup_class(class_name)

        if class_symbol is None:
            return

        class_symbol.ast_node.fields.setdefault(chain[0], node)

    def _check_chain(self, node, base, chain):
        if base == "self":
            class_name = self.get_current_class_name()

            if class_name is None:
                self.error(node, "'self' is only valid inside a class")
        else:
            symbol = self.stm.lookup_var(base)

            if symbol is None:
                self.error(node, f"Variable '{base}' is not defined")

            class_name = self._class_of(symbol)

        chain_types = []

        for member in chain:
            if class_name is None:
                self.error(
                    node,
                    f"Cannot access member '{member}' on a non-class value",
                )

            field = self.stm.lookup_field(class_name, member)

            if field is None:
                class_symbol = self.stm.lookup_class(class_name)

                if class_symbol is not None and member in class_symbol.methods:
                    class_name = None
                    chain_types.append(None)
                    continue

                self.error(
                    node,
                    f"Member '{member}' is not defined in class '{class_name}'",
                )

            chain_types.append(self._type_of_field(field))
            class_name = self._class_of(field)

        return chain_types

    def _base_type(self, node, base):
        """The type of the object a member chain is accessed on."""
        if base == "self":
            class_name = self.get_current_class_name()

            return ClassType(class_name) if class_name is not None else None

        symbol = self.stm.lookup_var(base)

        if symbol is None:
            return None

        return symbol.get("type")

    def _class_of(self, node):
        if isinstance(node, dict):
            node_type = node.get("type")
        elif isinstance(node, AssignAST):
            if node.value is not None:
                node_type = getattr(node.value, "type", None)
            else:
                node_type = getattr(node, "type", None)
        else:
            node_type = getattr(node, "type", None)

        if isinstance(node_type, ClassType):
            return node_type.name

        if isinstance(node_type, str):
            if self.stm.lookup_class(node_type) is not None:
                return node_type

            symbol = self.stm.lookup_var(getattr(node, "name", None))
            if symbol is not None:
                symbol_type = symbol.get("type")
                if isinstance(symbol_type, ClassType):
                    return symbol_type.name

        return None

    def process_intrinsic_call(self, node):
        name = node.target
        args = node.args
        intrinsic = INTRINSICS[name]

        intr_call = IntrinsicCallAST(intrinsic, name, args)
        node.__class__ = intr_call.__class__
        node.__dict__.clear()
        node.__dict__.update(intr_call.__dict__)

        return self.visit_expression(node)

    def eval_IntrinsicCallAST(self, node):
        args = node.args

        if not node.intrinsic.params.check_arg_count(len(args)):
            self.error(
                node,
                f"Invalid arguments for intrinsic '{node.intrinsic.name}': "
                f"{[arg.type for arg in args]}",
            )

        for arg in args:
            self.visit_expression(arg)

    def stmt_IntrinsicCallAST(self, node):
        return self.eval_IntrinsicCallAST(node)

    def eval_CallAST(self, node):
        target = node.target

        bpwf = self.get_target_in_bpwf(target)
        if bpwf is not None:
            self.body_parse_waiter_funcs.remove(bpwf)
            self._parse_body(bpwf[0], bpwf[1], bpwf[2], bpwf[3])

        is_chain = node.chain
        chain = node.chain or []
        is_class = False
        is_intrinsic = False

        if is_chain:
            method_name = chain[0]
            rest_chain = chain[1:]

            if target == "self":
                class_name = self.get_current_class_name()

                if class_name is None:
                    self.error(node, "'self' is only valid inside a class")
            else:
                symbol = self.stm.lookup_var(target)

                if symbol is None:
                    self.error(node, f"Variable '{target}' is not defined")

                class_name = self._class_of(symbol)

                if class_name is None:
                    self.error(
                        node,
                        f"Cannot call method '{method_name}' on a non-class value",
                    )

            target_class = self.stm.lookup_class(class_name)
            if target_class is None:
                self.error(node, f"Class '{class_name}' is not defined")

            target_func = target_class.methods.get(method_name)
            if target_func is None:
                self.error(node, f"Method '{method_name}' is not defined")

            bpwf = self.get_target_in_bpwf(method_name)
            if bpwf is not None:
                self.body_parse_waiter_funcs.remove(bpwf)
                self._parse_body(bpwf[0], bpwf[1], bpwf[2], bpwf[3])

            node.target_function = target_func
            node.type = target_func.type
            node.receiver_type = ClassType(class_name)

            if rest_chain:
                self._check_chain(node, target, rest_chain)

        else:
            if target in INTRINSICS:
                return self.process_intrinsic_call(node)

            func = self.stm.lookup_func(target)

            if func is None:
                func = self.stm.lookup_class(target)
                is_class = True

            if func is None:
                self.error(node, f"Function '{target}' not defined")

            node.target_function = func.ast_node

            if is_class:
                node.type = ClassType(target)
            else:
                node.type = func.return_type
        args = node.args

        if not is_chain and not is_class:
            is_variadic = (
                func.get("is_variadic", False)
                if isinstance(func, dict)
                else getattr(func, "is_variadic", False)
            )
            params = func.params

            if not is_variadic and len(args) != len(params):
                self.error(
                    node,
                    f"{'Intrinsic' if is_intrinsic else 'Function' if not is_class else 'Class'} '{target}' takes {len(params)} arguments ({len(args)} given)",
                )

        for arg in args:
            self.visit_expression(arg)

        return node

    def eval_GroupAST(self, node):
        expr = node.expr
        self.visit_expression(expr)

    def eval_NoneAST(self, node):
        pass

    def eval_SelfAST(self, node):
        class_name = self.get_current_class_name()

        if class_name is None:
            self.error(node, "'self' is only valid inside a class")

        node.type = ClassType(class_name)

        return class_name

    def stmt_PassAST(self, node):
        pass

    def stmt_DefinitionAST(self, node):
        lk = self.stm.lookup_var(node.target)
        if lk is not None:
            raise SyntaxError(f"Definition of variable '{node.target}' already exists")

        self.visit_expression(node.value)
        self.stm.define_var(node.target, node.type)

    def stmt_ClassAST(self, node):
        self.stm.define_class(node.name, node)
        self.stm.enter_scope(scope_name=node.name, is_func=False, class_name=node.name)

        self.current_class_name = node.name

        try:
            for n in node.body:
                if isinstance(n, FunctionAST):
                    node.methods[n.name] = n
                elif isinstance(n, AssignAST):
                    node.fields[n.target] = n
                else:
                    self.error(n, f"Invalid class body item '{type(n).__name__}'")

                self.visit_statement(n)

            for method in node.methods.values():
                for stmt in method.body:
                    if isinstance(stmt, AssignAST) and stmt.chain:
                        node.fields.setdefault(stmt.chain[0], stmt)
        finally:
            self.stm.exit_scope()
            self.current_class_name = None

    def get_current_class_name(self):
        curr = self.stm.current_scope
        while curr is not None:
            if curr.class_name is not None:
                return curr.class_name
            curr = curr.parent

        return None

    def stmt_AssignAST(self, node):
        chain = getattr(node, "chain", [])
        class_name = self.get_current_class_name()

        # if class_name is not None:
        #     if node.target == "self" and len(chain) == 1:
        #         self.stm.define_field(
        #             class_name=class_name,
        #             field_name=chain[0],
        #             field_type=node.type,
        #             ast_node=node,
        #         )

        #     elif node.target != "self" and not self.stm.current_scope.is_func:
        #         self.stm.define_var(node.target, node.type)

        #     elif node.target == "self" and len(chain) > 1:
        #         last_class = self.stm.lookup_class(class_name)

        #         for idx, ch in enumerate(chain):
        #             if ch in last_class["fields"]:
        #                 ast = last_class["fields"][ch]["ast"]
        #                 value = ast.value

        #                 is_last_in_chain = idx == len(chain) - 1

        #                 if not is_last_in_chain:
        #                     if not isinstance(value, CallAST):
        #                         type_str = getattr(ast, "type", "primitive")
        #                         self.error(
        #                             node,
        #                             f"Cannot perform member chain access '{'.'.join(chain)}': "
        #                             f"'{ch}' is of type '{type_str}', not a class instance.",
        #                         )
        #                         break

        #                     tr = value.target
        #                     last_class = self.stm.lookup_class(tr)
        #                     if not last_class:
        #                         self.error(
        #                             node,
        #                             f"Class '{tr}' referenced by '{ch}' is not defined.",
        #                         )
        #                         break
        #             else:
        #                 curr_class_name = last_class.get("name", class_name)
        #                 self.error(
        #                     node,
        #                     f"Member '{ch}' is not defined in class '{curr_class_name}'",
        #                 )
        #                 break

        #     else:
        #         self.stm.define_var(node.target, node.type)

        # else:
        lookups = self.stm.lookup_var(node.target)
        if lookups:
            node.is_re_assign = True

        if node.chain:
            if node.value is not None:
                self.visit_expression(node.value)

            self._define_self_field(node, class_name, chain)

            node.chain_types = self._check_chain(node, node.target, chain)
            node.base_type = self._base_type(node, node.target)

            last_type = node.chain_types[-1] if node.chain_types else None

            node.type = last_type if last_type is not None else node.type

            var_type = node.base_type if node.base_type is not None else node.type
        else:
            if node.value is not None:
                self.visit_expression(node.value)

                if node.type is None and node.value.type is not None:
                    node.type = node.value.type

            var_type = node.type

        self.stm.define_var(node.target, var_type)

    def stmt_ReturnAST(self, node):
        scope = self.stm.current_scope

        while scope is not None and not scope.is_func:
            scope = scope.parent

        if scope is None:
            self.error(node, "Return statement outside of function")

        if node.value is None:
            return

        if not isinstance(node.value, VALID_RETURN_EXPRESSIONS):
            self.error(
                node,
                f"Invalid return expression: '{type(node.value).__name__}' cannot be returned",
            )

        self.visit_expression(node.value)

    def stmt_FunctionAST(self, node):
        class_name = self.get_current_class_name()

        self.stm.enter_scope(
            scope_name=f"func_{node.name}", is_func=True, class_name=class_name
        )

        if node.func_id is None:
            node.func_id = self.f_alloc.alloc()

        self.stm.define_func(node.name, node.func_id, node.type, node.args, node)
        args = node.args
        in_self = False

        if class_name is not None:
            in_self = None

            if args and isinstance(args[0], SelfAST):
                in_self = args[0]

                in_self.type = ClassType(class_name)

            if in_self is None:
                self.error(
                    node,
                    f"Method '{node.name}' in class '{class_name}' must take 'self' as its first parameter",
                )

        if node.name == "__init__":
            self._parse_body(
                self.stm.current_scope,
                node.body,
                node.args,
                class_name,
            )

            self.stm.define_class_required_params(class_name, node.args)
        else:
            self.body_parse_waiter_funcs.append(
                (
                    self.stm.current_scope,
                    node.body,
                    node.args,
                    class_name,
                )
            )

        self.stm.exit_scope()

    def stmt_CallAST(self, node):
        self.eval_CallAST(node)

    def stmt_IfAST(self, node: IfAST):
        self.stm.enter_scope(scope_name="if", is_if=True)
        self.visit_expression(node.cond)

        for n in node.body:
            self.visit_statement(n)

        self.stm.exit_scope()

        for elif_node in node.elifs:
            self.stm.enter_scope(scope_name="elif", is_if=True)
            self.visit_expression(elif_node.cond)

            for n in elif_node.body:
                self.visit_statement(n)

            self.stm.exit_scope()

        if isinstance(node.else_body, BlockAST):
            self.stm.enter_scope(scope_name="else", is_if=True)

            for n in node.else_body.body:
                self.visit_statement(n)

            self.stm.exit_scope()

    def stmt_WhileAST(self, node):
        self.stm.enter_scope(scope_name="while", is_func=False)

        self.visit_expression(node.cond)

        for n in node.body:
            self.visit_statement(n)

        self.stm.exit_scope()

    def stmt_ForAST(self, node):

        if not isinstance(node.target, AssignAST):
            self.error(
                f"Invalid 'for' loop target '{type(node.target).__name__}'. "
                f"Expected a variable declaration (e.g., 'for i in sequence').",
                node=node.target,
            )

        if node.target.value is not None:
            self.error(
                f"For loop iterator variable cannot have an initial value assignment. "
                f"Use 'for {node.target.name} in ...' instead of 'for {node.target.name} = {node.target.value} ...'.",
                node=node.target,
            )

        self.visit_statement(node.target)
        self.stm.enter_scope(scope_name="for", is_func=False)

        self.visit_expression(node.source)

        for n in node.body:
            self.visit_statement(n)

        self.stm.exit_scope()

    def stmt_ImportAST(self, node):
        # TODO: refactor
        name = node.module
        module_scope = self.stm.enter_scope(
            scope_name="imp", is_func=False, link_to_parent=False
        )
        module = node.resolved_module

        if module is None:
            return

        for ast in module.asts:
            print(ast)
            self.visit_statement(ast)

        funcs = {}
        classes = {}
        for sym in node.symbols:
            func_name = sym["name"]
            alias = sym.get("alias")

            is_class = False
            lk = self.stm.lookup_func(func_name)
            if lk is None:
                lk = self.stm.lookup_class(func_name)
                is_class = True

            if lk is None:
                self.error(node, f"Symbol '{func_name}' is not defined")

            if is_class:
                classes[func_name if alias is None else alias] = lk
            else:
                funcs[func_name if alias is None else alias] = lk
        c_scp = self.stm.current_scope
        self.stm.exit_scope()
        self.module_scopes[name] = module_scope

        for name, lk in funcs.items():
            p = c_scp.parent
            if p is not None and p.name == "imp":
                self.stm.define_imported_func(name, lk)
            else:
                self.stm.define_imported_func(name, lk, is_global=True)

        for name, lk in classes.items():
            p = c_scp.parent
            if p is not None and p.name == "imp":
                self.stm.define_imported_class(name, lk)
            else:
                self.stm.define_imported_class(name, lk, is_global=True)

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


class SimpleAnalyzer:
    def __init__(self, ast_tree, ctx):
        self.ast_tree = ast_tree
        self.ctx = ctx
        self.stm = SymbolTableManager()
        self.sav = SimpleASTVisitor(self.stm, self.ctx)

    def analyze_all(self):
        for node in self.ast_tree:
            self.sav.visit_statement(node)

        while self.sav.body_parse_waiter_funcs:
            func = self.sav.body_parse_waiter_funcs.pop(0)
            self.sav._parse_body(func[0], func[1], func[2], func[3])

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
