from nida_ast.base import *
from .tree_builder import SymbolTreeBuilder


def number_to_type(min_val: int, max_val: int) -> str:
    I64_MIN, I64_MAX = -9_223_372_036_854_775_808, 9_223_372_036_854_775_807
    U64_MAX = 18_446_744_073_709_551_615

    if min_val < I64_MIN or max_val > U64_MAX:
        return "dynamic_int"

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
            target_node = node.value if isinstance(node, AssignAST) else node
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


class SymbolProcessor:
    tyinf = TypeInference()

    def process_assign(self, symbol):
        print(f"Assign {symbol.name} to {symbol.type}")
        print(symbol.ast_node)
        ast = symbol.ast_node

        if ast.type_annotation is None:
            value = ast.value
            if isinstance(value, NumberAST):
                type = self.tyinf.process_number(symbol)
                if type is not None:
                    ast.type_annotation = type
            else:
                print(f"Cannot infer type of {value}")

        print(symbol.ast_node)

    def process_VariableSymbol(self, symbol):
        if isinstance(symbol.ast_node, AssignAST):
            self.process_assign(symbol)
        else:
            print(f"Variable {symbol.name} is not assigned")
            print(symbol.ast_node)

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
        print(method_name)

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
