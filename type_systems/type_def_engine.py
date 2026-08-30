from nida_ast.base import *
from .symbol_types import *

from .tree_builder import SymbolTreeBuilder
from .symbol_types import CallSymbol


def number_to_type(min_val: int, max_val: int) -> str:
    I64_MIN, I64_MAX = -9_223_372_036_854_775_808, 9_223_372_036_854_775_807
    U64_MAX = 18_446_744_073_709_551_615

    # if min_val < I64_MIN or max_val > U64_MAX:
    #     return "dynamic_int"

    if min_val >= 0:
        if max_val <= 255:
            return "u8"
        elif max_val <= 65_535:
            return "u16"
        elif max_val <= 4_294_967_295:
            return "u32"
        elif max_val <= U64_MAX:
            return "u64"

    else:
        if min_val >= -128 and max_val <= 127:
            return "i8"
        elif min_val >= -32_768 and max_val <= 32_767:
            return "i16"
        elif min_val >= -2_147_483_648 and max_val <= 2_147_483_647:
            return "i32"
        elif min_val >= I64_MIN and max_val <= I64_MAX:
            return "i64"

    # return "dynamic_int"
    raise ValueError("Invalid number range. Note: dynamic_int is not supported yet")


class TypeInference:
    def extract_number_value(self, ast_node) -> int | None:
        if isinstance(ast_node, NumberAST):
            raw_val = ast_node.value
            if isinstance(raw_val, str):
                val = int(raw_val, 0)
                ast_node.value = val
                return val
            return raw_val
        return None

    def infer_from_symbol_history(self, symbol) -> str | None:
        values = []

        if hasattr(symbol.ast_node, "value"):
            val = self.extract_number_value(symbol.ast_node.value)
            if val is not None:
                values.append(val)

        stack = getattr(symbol, "used_stack", [])
        for node in stack:
            if isinstance(node, CallSymbol):
                continue

            ast_node = node.ast_node
            if isinstance(ast_node, AssignAST):
                target_node = ast_node.value
            else:
                target_node = ast_node

            val = self.extract_number_value(target_node)
            if val is not None:
                values.append(val)

        if not values:
            return None

        min_val = min(values)
        max_val = max(values)

        return number_to_type(min_val, max_val)

    def process_number(self, symbol):
        type = self.infer_from_symbol_history(symbol)
        if type is not None:
            symbol.type = type

            symbol.ast_node.type_annotation = type

    def process_function(self, symbol):
        if symbol.return_type is not None:
            return

        if symbol.returns is None:
            return  # not return statement


class SymbolProcessor:
    tyinf = TypeInference()

    TYPE_RANK = {
        "bool": 0,
        "i8": 1,
        "u8": 1,
        "i16": 2,
        "u16": 2,
        "i32": 3,
        "u32": 3,
        "i64": 4,
        "u64": 4,
        "f32": 5,
        "f64": 6,
    }

    def promote_types(self, t1: str, t2: str) -> str:
        if t1 == t2:
            return t1

        r1 = self.TYPE_RANK.get(t1, 0)
        r2 = self.TYPE_RANK.get(t2, 0)

        return t1 if r1 >= r2 else t2

    def are_types_compatible(self, t1: str, t2: str) -> bool:
        if t1 == t2:
            return True
        return t1 in self.TYPE_RANK and t2 in self.TYPE_RANK

    def process_assign(self, symbol):
        ast = symbol.ast_node

        if ast.type_annotation is None:
            value = ast.value
            if isinstance(value, NumberAST):
                type = self.tyinf.process_number(symbol)
                if type is not None:
                    ast.type_annotation = type
                    symbol.type = type
            elif isinstance(value, CallAST):
                call_sym = symbol.call_symbol
                if call_sym is None:
                    raise Exception("Cannot infer type of call")

                type = self.process_call(call_sym)
                if type is not None:
                    ast.type_annotation = type
                    symbol.type = type

            else:
                print(f"Cannot infer type of {value} \n {symbol}")

    def process_call(self, symbol):
        if symbol.func.return_type is None:
            self.process(symbol.func)

        if symbol.func.return_type is None:
            raise SyntaxError(f"Cannot infer type of {symbol.func.name} \n {symbol}")

        return symbol.func.return_type

    def call_stack_analysis(self, symbol: FunctionSymbol):
        call_stack = symbol.call_stack
        if not call_stack:
            return []

        # detected_types = [i.type for i in call_stack[0].sym_params]
        detected_types = []

        for call in call_stack[0].sym_params:
            type = call.type
            if type is None:
                self.process(call)

            type = call.type

            if type is None:
                raise SyntaxError(f"Cannot infer type of {call.name}, \n {call}")

            detected_types.append(type)

        for call_idx, call in enumerate(call_stack[1:], start=1):
            current_types = [i.type for i in call.sym_params]

            if len(current_types) != len(detected_types):
                raise TypeError(
                    f"Call stack mismatch in '{symbol.name}' at call #{call_idx}: "
                    f"Expected {len(detected_types)} args, got {len(current_types)}."
                )

            for arg_idx, (expected, current) in enumerate(
                zip(detected_types, current_types)
            ):
                if expected != current:
                    raise TypeError(
                        f"Type mismatch in '{symbol.name}' at call #{call_idx}, arg #{arg_idx}: "
                        f"Expected '{expected}', got '{current}'."
                    )

        return detected_types

    def process_BinaryOpSymbol(self, symbol):
        left_sym = symbol.left_sym
        right_sym = symbol.right_sym

        if left_sym is None or right_sym is None:
            raise SyntaxError(f"Invalid operands for binary operator '{symbol.op}'")

        left_type = getattr(left_sym, "type", None) or getattr(
            left_sym, "inferred_type", None
        )
        if left_type is None:
            self.process(left_sym)
            left_type = getattr(left_sym, "type", None) or getattr(
                left_sym, "inferred_type", None
            )

        right_type = getattr(right_sym, "type", None) or getattr(
            right_sym, "inferred_type", None
        )
        if right_type is None:
            self.process(right_sym)
            right_type = getattr(right_sym, "type", None) or getattr(
                right_sym, "inferred_type", None
            )

        if left_type is None and right_type is None:
            raise SyntaxError(
                f"Cannot infer type for binary operation '{symbol.op}' - "
                f"neither left ({getattr(left_sym, 'name', left_sym)}) nor right ({getattr(right_sym, 'name', right_sym)}) is typed."
            )

        if symbol.op in ("==", "!=", "<", ">", "<=", ">=", "&&", "||"):
            if (
                left_type
                and right_type
                and not self.are_types_compatible(left_type, right_type)
            ):
                raise SyntaxError(
                    f"Type mismatch in comparison '{symbol.op}': {left_type} vs {right_type}"
                )

            symbol.inferred_type = "bool"
            symbol.type = "bool"
            return

        if left_type is not None and right_type is not None:
            inferred = self.promote_types(left_type, right_type)
            symbol.inferred_type = inferred
            symbol.type = inferred
            return

        known_type = left_type if left_type is not None else right_type

        symbol.inferred_type = known_type
        symbol.type = known_type

    def is_called(self, symbol):
        if isinstance(symbol, FunctionSymbol) and len(symbol.call_stack) > 0:
            return True

        return False

    def process_FunctionSymbol(self, symbol):
        types = self.call_stack_analysis(symbol)

        returns = symbol.returns
        if returns is None:
            return

        if self.is_called(symbol):
            for i in range(len(symbol.params)):
                if i >= len(types):
                    raise TypeError(
                        f"Return type mismatch in '{symbol.name}': Expected {len(types)} args, got {len(symbol.params)}."
                    )

                type = types[i]
                symbol.params[i]["symbol"].type = type

            sym = returns["symbol"]
            if sym is None:
                print(symbol)
                raise SyntaxError(f"Cannot infer type of {symbol.name}")

            if isinstance(sym, VariableSymbol):
                if sym.type is None:
                    self.process(sym)

                if sym.type is None:
                    raise SyntaxError(f"Cannot infer type of {sym.name}")

            elif isinstance(sym, BinaryOpSymbol):
                self.process(sym)

            symbol.return_type = (
                sym.type if isinstance(sym, VariableSymbol) else sym.inferred_type
            )

    def process_VariableSymbol(self, symbol):
        if isinstance(symbol.ast_node, AssignAST):
            self.process_assign(symbol)
        else:
            print(f"Variable {symbol.name} is not assigned")

    def process_NumberSymbol(self, symbol):
        val = symbol.value
        if isinstance(val, str):
            val = int(val, 0)

        type = number_to_type(val, val)
        if type is None:
            raise SyntaxError(f"Cannot infer type of number {val}")

        symbol.type = type

    def process(self, symbol):
        method_name = f"process_{type(symbol).__name__}"
        visitor = getattr(self, method_name, None)
        if visitor is None:
            raise SyntaxError(f"Invalid symbol type {type(symbol).__name__}")

        return visitor(symbol)


class TypeDefEngine:
    def __init__(self, ast_tree):
        self.ast_tree = ast_tree
        self.processor = SymbolProcessor()
        self.stb = SymbolTreeBuilder(ast_tree)
        self.stb.run()

    def process_symbol(self, symbol):
        self.processor.process(symbol)

    def process_symbols(self, node):
        for symbol in node.symbols.values():
            self.process_symbol(symbol)

    def process_node(self, node):
        if isinstance(node, list):
            self.process_children(node)
            return

        method_name = f"process_{type(node).__name__}"

        symbols = node.symbols
        if symbols is not None:
            self.process_symbols(node)

        if node.children:
            self.process_children(node)

    def process_children(self, node):
        for child in node.children:
            self.process_node(child)

    def run(self):
        current_scope = self.stb.sm.current_scope
        self.process_node(current_scope)

        self.stb.print_scopes()
