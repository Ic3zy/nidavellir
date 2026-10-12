from ..types import *
from ..tree_gen.symbol_types import *


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
                raise Exception(sym, "Cannot determine type of variable")

            with TypeUpdate(sym):
                sym.type = lk_type

    def process_StringSymbol(self, sym):
        pass

    def process_AssignSymbol(self, sym):
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

    def _infer_returns(self, body: list):
        returns = []

        for node in body:
            if isinstance(node, ReturnSymbol):
                returns.append(node)

        return returns

    def process_FunctionSymbol(self, sym):
        arg_types = {}

        for call in sym.uses:
            if not isinstance(call, CallSymbol):
                continue

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

                if (previous_type := arg_types.get(idx)) is not None:
                    if arg_type != previous_type:
                        raise Exception(
                            sym,
                            f"Incompatible argument types in call {call.name}: "
                            f"{arg_type} and {previous_type}",
                        )

                arg_types[idx] = arg_type

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
            if inferred_type is not None and node.type != inferred_type:
                raise Exception(
                    sym,
                    f"Incompatible return types in function {sym.name}: "
                    f"{inferred_type} and {node.type}",
                )
            inferred_type = node.type

        if inferred_type is not None:
            with TypeUpdate(sym):
                sym.type = inferred_type

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
        if sym.type is None:
            if sym.lookup.type is None:
                self.process(sym.lookup)

            if sym.lookup.type is None:
                raise Exception(sym, "Cannot determine type of call")

            with TypeUpdate(sym):
                sym.type = sym.lookup.type

        for arg in sym.args:
            self.process(arg)

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
