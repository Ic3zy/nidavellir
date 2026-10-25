from ..types import *
from semantic.analyzer.symbol_types import *


def detect_type(value: str):
    try:
        int(value)
        return int
    except ValueError:
        try:
            float(value)
            return float
        except ValueError:
            return str


class AutoTypeDefEngine:
    def __init__(self, sym_tree):
        self.sym_tree = sym_tree

    def process_BooleanSymbol(self, sym):
        sym.type = BooleanType()

    def process_NumberSymbol(self, sym):
        val = detect_type(sym.value)

        with TypeUpdate(sym):
            if val is int:
                sym.type = IntType()
            elif val is float:
                sym.type = FloatType()
            else:
                raise Exception(sym, f"Cannot determine type of number {sym.value}")

    def process_VariableSymbol(self, sym):
        if sym.type is None:
            lk_type = sym.lookup.type
            if lk_type is None:
                self.process(sym.lookup)
                lk_type = sym.lookup.type

            if lk_type is None:
                raise Exception(sym.lookup.ast_node)
                raise Exception(sym, "Cannot determine type of variable")

            with TypeUpdate(sym):
                sym.type = lk_type

    def process_StringSymbol(self, sym):
        pass

    def process_AssignSymbol(self, sym):
        if sym.type is None and sym.value is not None:
            self.process(sym.value)
            with TypeUpdate(sym):
                sym.type = sym.value.type
                if sym.type is None:
                    raise Exception(sym, "Cannot determine type of assigned value")

        if sym.chain:
            base = sym.base_sym
            if base.type is None:
                self.process(base)

            self._resolve_chain(base.type, sym.chain, sym)

    def process_DefinitionSymbol(self, sym):
        if sym.type is None:
            self.process(sym.value)
            with TypeUpdate(sym):
                sym.type = sym.value.type
                if sym.type is None:
                    raise Exception(sym, "Cannot determine type of assigned value")

    def process_BinaryOpSymbol(self, sym):
        right = sym.right_sym
        left = sym.left_sym
        if right.type is None:
            self.process(right)

        if left.type is None:
            self.process(left)

        if right.type is None or left.type is None:
            raise Exception(sym, "Cannot determine type of binary operation")

        if type(left.type) != type(right.type):
            raise Exception(
                sym,
                f"Incompatible operand types: {left.type} and {right.type}",
            )

        with TypeUpdate(sym):
            sym.type = left.type
            if sym.type is None:
                raise Exception(sym, "Cannot determine type of binary operation")

    def process_UnaryOpSymbol(self, sym):
        right = sym.right_sym
        if right.type is None:
            self.process(right)

        if right.type is None:
            raise Exception(sym, "Cannot determine type of unary operation")

        with TypeUpdate(sym):
            sym.type = right.type

    def _infer_returns(self, body: list):
        returns = []

        for node in body:
            if isinstance(node, ReturnSymbol):
                returns.append(node)
            elif hasattr(node, "body"):
                returns.extend(self._infer_returns(node.body))

        return returns

    def process_FunctionSymbol(self, sym: FunctionSymbol):
        self._process_FunctionSymbol(sym)

    def _process_FunctionSymbol(self, sym):
        arg_types = {}

        for call in sym.uses:
            if not isinstance(call, (CallSymbol, ConstructorCallSymbol)):
                continue

            offset = getattr(call, "arg_offset", 0)

            for idx, arg in enumerate(call.args):
                if arg.type is None:
                    self.process(arg)

                arg_type = arg.type
                if arg_type is None:
                    raise Exception(
                        sym,
                        f"Cannot infer argument type at position {idx} "
                        f"in call {call.name}",
                    )

                if (previous_type := arg_types.get(idx + offset)) is not None:
                    if arg_type != previous_type:
                        raise Exception(
                            sym,
                            f"Incompatible argument types in call {call.name}: "
                            f"{arg_type} and {previous_type}",
                        )

                arg_types[idx + offset] = arg_type
        for idx, arg in enumerate(sym.args):
            if arg.type is None:
                arg_type = arg_types.get(idx)
                if arg_type is None:
                    continue

                with TypeUpdate(arg):
                    arg.type = arg_type

        self.process_from_list(sym.body)

        inferred_type = None
        for node in self._infer_returns(sym.body):
            if inferred_type is None:
                inferred_type = node.type
                continue

            if type(node.type) != type(inferred_type):
                raise Exception(
                    f"Incompatible return types in function '{sym.name}': "
                    f"{inferred_type} and {node.type}",
                )
            inferred_type = node.type

        if inferred_type is not None:
            with TypeUpdate(sym):
                sym.type = inferred_type
        elif sym.type is None:
            with TypeUpdate(sym):
                sym.type = NoneType()

    def process_ReturnSymbol(self, sym):
        if sym.value is None:
            return

        if sym.value.type is None:
            self.process(sym.value)

        if sym.value.type is None:
            raise Exception(sym, "Cannot determine type of return value")

        with TypeUpdate(sym):
            sym.type = sym.value.type

    def process_CallSymbol(self, sym):
        if getattr(sym, "is_list_method", False):
            self.process_from_list(sym.args)
            return

        lk = sym.lookup
        self._process_FunctionSymbol(lk)

        if sym.type is None:
            if sym.lookup.type is None:
                self.process(sym.lookup)

            if sym.lookup.type is None:
                raise Exception(sym, "Cannot determine type of call")

            with TypeUpdate(sym):
                sym.type = sym.lookup.type

        for arg in sym.args:
            self.process(arg)

    def process_ConstructorCallSymbol(self, sym):
        for arg in sym.args:
            self.process(arg)

        with TypeUpdate(sym):
            sym.type = sym.lookup.type

    def process_ClassSymbol(self, sym):
        self.process_from_list(sym.body)

        for method in sym.method_syms.values():
            self._process_FunctionSymbol(method)

    def process_SelfSymbol(self, sym):
        if sym.class_name is None:
            raise Exception(sym, "'self' is only valid inside a class")

        with TypeUpdate(sym):
            sym.type = ClassType(sym.class_name)

    def process_FieldAccessSymbol(self, sym):
        target = sym.target
        if target.type is None:
            self.process(target)

        self._resolve_chain(target.type, sym.chain, sym)

    def _resolve_chain(self, base_type, chain, sym):
        for name in chain:
            if not isinstance(base_type, ClassType):
                raise Exception(
                    sym,
                    f"Cannot access member '{name}' on non-class type '{base_type}'",
                )

            class_sym = self._find_class(base_type.name)
            if class_sym is None:
                raise Exception(sym, f"Class '{base_type.name}' is not defined")

            field_ast = class_sym.fields.get(name)
            if field_ast is None:
                raise Exception(
                    sym, f"Member '{name}' is not defined in class '{base_type.name}'"
                )

            base_type = self._field_type(class_sym, field_ast)
            if base_type is None:
                raise Exception(
                    sym,
                    f"Cannot determine type of member '{name}' "
                    f"in class '{base_type.name}'",
                )

        with TypeUpdate(sym):
            sym.type = base_type

    def _find_class(self, name):
        for sym in self.sym_tree:
            if isinstance(sym, ClassSymbol) and sym.name == name:
                return sym

        return None

    def _field_type(self, class_sym, field_ast):
        if field_ast.type is not None:
            return resolve_type(field_ast.type)

        if field_ast.value is not None:
            value_sym = field_ast.value
            if value_sym.type is not None:
                return value_sym.type

            self.process(value_sym)
            if value_sym.type is not None:
                return value_sym.type

        return None

    def process_IntrinsicCallSymbol(self, sym):
        args = sym.args
        intrinsic = sym.intrinsic
        self.process_from_list(args)
        if sym.type is None:
            if intrinsic.type is None:
                raise Exception(sym, "Cannot determine type of intrinsic call")

            with TypeUpdate(sym):
                sym.type = intrinsic.type

        if not intrinsic.params.check(args):
            raise Exception(f"Invalid arguments for intrinsic '{intrinsic.name}'")

    def process_IfSymbol(self, sym):
        self.process(sym.cond)

        for stmt in sym.body:
            self.process(stmt)

        for elif_sym in sym.elifs:
            self.process(elif_sym.cond)

            for stmt in elif_sym.body:
                self.process(stmt)

        if sym.else_body is not None:
            for stmt in sym.else_body:
                self.process(stmt)

    def process_ListLiteralSymbol(self, sym):
        for element_sym in sym.elements:
            self.process(element_sym)

        if sym.type is None:
            with TypeUpdate(sym):
                sym.type = ListType()

    def process(self, sym):
        method_name = f"process_{type(sym).__name__}"
        visitor = getattr(self, method_name, None)
        if visitor is None:
            raise Exception(sym, f"No visitor method '{method_name}' for symbol")
        return visitor(sym)

    def process_from_list(self, syms):
        for sym in syms:
            self.process(sym)

    def run(self):
        self.process_from_list(self.sym_tree)
