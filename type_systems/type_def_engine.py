from nida_ast.base import *
from .tree_builder import SymbolTreeBuilder
from .symbol_types import CallSymbol


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
            raise SyntaxError(f"Cannot infer type of {symbol.func.name}")

        return symbol.func.return_type

    def process_FunctionSymbol(self, symbol):
        returns = symbol.returns
        if returns is None:
            return

        sym = returns["symbol"]
        if sym.type is None:
            self.process(sym)

        if sym.type is None:
            raise SyntaxError(f"Cannot infer type of {sym.name}")

        symbol.return_type = sym.type

    def process_VariableSymbol(self, symbol):
        if isinstance(symbol.ast_node, AssignAST):
            self.process_assign(symbol)
        else:
            print(f"Variable {symbol.name} is not assigned")

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
