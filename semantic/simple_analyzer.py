from .intrinsics import INTRINSIC_HANDLERS
from .symbol_table import SymbolTableManager
from nida_ast.base import *

VALID_RETURN_EXPRESSIONS = (
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
    def __init__(self, stm):
        self.stm = stm
        self.body_parse_waiter_funcs = []
        self.current_class_name = None

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
            self.stm.define_var(arg.target, arg.type_annotation)

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
        if self.stm.lookup_var(node.name) is None:
            self.error(node, f"Variable '{node.name}' is not defined")
        return self.stm.lookup_var(node.name)

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
        if isinstance(node.target, SelfAST):
            root_name = "self"
        elif isinstance(node.target, VariableAST):
            root_name = node.target.name
            self.eval_VariableAST(node.target)
        else:
            self.visit_expression(node.target)
            root_name = None

        if self.current_class_name is not None and root_name == "self":
            chain = getattr(node, "chain", [])

            if not chain:
                return None

            root_field = chain[0]
            existing_field = self.stm.lookup_field(self.current_class_name, root_field)

            if not existing_field:
                self.error(
                    node,
                    f"Member '{root_field}' is not defined in class '{self.current_class_name}'",
                )

            return existing_field

        return None

    def eval_CallAST(self, node):
        target = node.target

        bpwf = self.get_target_in_bpwf(target)
        if bpwf is not None:
            self.body_parse_waiter_funcs.remove(bpwf)
            self._parse_body(bpwf[0], bpwf[1], bpwf[2], bpwf[3])
        is_chain = node.chain
        if is_chain:
            if (
                self.current_class_name is None
                and target != "self"
                and not self.stm.lookup_var(target)
            ):
                self.error(node, f"Variable '{target}' is not defined")
        else:
            is_class = False
            func = self.stm.lookup_func(target)
            if func is None:
                func = self.stm.lookup_class(target)
                is_class = True

            if func is None:
                self.error(node, f"Function '{target}' not defined")

        args = node.args
        if not is_chain:
            if not func.get("is_variadic", False) and len(args) != len(func["params"]):
                self.error(
                    node,
                    f"{'Function' if not is_class else 'Class'} '{target}' takes {len(func['params'])} arguments",
                )

        for arg in args:
            self.visit_expression(arg)

    def stmt_ClassAST(self, node):
        self.stm.define_class(node.name, node)
        self.current_class_name = node.name
        self.stm.enter_scope(scope_name=node.name, is_func=False)

        try:
            for n in node.body:
                self.visit_statement(n)
        finally:
            self.stm.exit_scope()
            self.current_class_name = None

    def stmt_PassAST(self, node):
        pass

    def stmt_AssignAST(self, node):
        chain = getattr(node, "chain", [])

        if self.current_class_name is not None:
            if node.target == "self" and len(chain) == 1:
                self.stm.define_field(
                    class_name=self.current_class_name,
                    field_name=chain[0],
                    field_type=node.type_annotation,
                    ast_node=node,
                )

            elif node.target != "self" and not self.stm.current_scope.is_func:
                self.stm.define_field(
                    class_name=self.current_class_name,
                    field_name=node.target,
                    field_type=node.type_annotation,
                    ast_node=node,
                )

            elif node.target == "self" and len(chain) > 1:
                last_class = self.stm.lookup_class(self.current_class_name)

                for idx, ch in enumerate(chain):
                    if ch in last_class["fields"]:
                        ast = last_class["fields"][ch]["ast"]
                        value = ast.value

                        is_last_in_chain = idx == len(chain) - 1

                        if not is_last_in_chain:
                            if not isinstance(value, CallAST):
                                type_str = getattr(ast, "type_annotation", "primitive")
                                self.error(
                                    node,
                                    f"Cannot perform member chain access '{'.'.join(chain)}': "
                                    f"'{ch}' is of type '{type_str}', not a class instance.",
                                )
                                break

                            tr = value.target
                            last_class = self.stm.lookup_class(tr)
                            if not last_class:
                                self.error(
                                    node,
                                    f"Class '{tr}' referenced by '{ch}' is not defined.",
                                )
                                break
                    else:
                        curr_class_name = last_class.get(
                            "name", self.current_class_name
                        )
                        self.error(
                            node,
                            f"Member '{ch}' is not defined in class '{curr_class_name}'",
                        )
                        break

            else:
                self.stm.define_var(node.target, node.type_annotation)

        else:
            self.stm.define_var(node.target, node.type_annotation)

        if node.value is not None:
            self.visit_expression(node.value)

    def stmt_ReturnAST(self, node):
        if not self.stm.current_scope.is_func:
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
        is_intrinsic = node.name in INTRINSIC_HANDLERS
        if is_intrinsic:
            self.error(
                node, f"Cannot redefine built-in intrinsic function '{node.name}'"
            )

        self.stm.enter_scope(scope_name=f"func_{node.name}", is_func=True)
        self.stm.define_func(node.name, node.type, node.args, node)
        args = node.args
        in_self = False

        if self.current_class_name is not None:
            in_self = None

            if args and isinstance(args[0], SelfAST):
                # in_self = args[0]
                in_self = args.pop(0)

            if in_self is None:
                self.error(
                    node,
                    f"Method '{node.name}' in class '{self.current_class_name}' must take 'self' as its first parameter",
                )

        if node.name == "__init__":
            self._parse_body(
                self.stm.current_scope,
                node.body,
                node.args,
                self.current_class_name,
            )

            self.stm.define_class_required_params(self.current_class_name, node.args)
        else:
            self.body_parse_waiter_funcs.append(
                (
                    self.stm.current_scope,
                    node.body,
                    node.args,
                    self.current_class_name,
                )
            )

        self.stm.exit_scope()

    def stmt_CallAST(self, node):
        self.eval_CallAST(node)

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


class SimpleAnalyzer:
    def __init__(self, ast_tree):
        self.ast_tree = ast_tree
        self.stm = SymbolTableManager()
        self.sav = SimpleASTVisitor(self.stm)

    def analyze_all(self):
        for node in self.ast_tree:
            self.sav.visit_statement(node)

        while self.sav.body_parse_waiter_funcs:
            func = self.sav.body_parse_waiter_funcs.pop(0)
            self.sav._parse_body(func[0], func[1], func[2], func[3])
