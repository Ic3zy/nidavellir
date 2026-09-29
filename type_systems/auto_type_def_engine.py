from .integer_systems import int_type
from .symbol_types import *
from .tree_builder import SymbolTreeBuilder


class TypeDefHelper:
    @staticmethod
    def _to_int(val) -> int:
        return int(val, 0) if isinstance(val, str) else int(val)

    @classmethod
    def infer_int_range(cls, sym):
        uses = sym.uses
        if not uses:
            return None, None

        range_list = []

        if isinstance(sym.value, NumberSymbol):
            range_list.append(cls._to_int(sym.value.value))

        for use in uses:
            val_node = use.value if hasattr(use, "value") else use

            if isinstance(val_node, NumberSymbol):
                range_list.append(cls._to_int(val_node.value))
            else:
                raise SyntaxError(
                    f"Cannot infer integer range of '{use.name}' ({type(use).__name__})"
                )

        return min(range_list), max(range_list)


class AutoTypeDefEngine:
    def __init__(self, ast_tree):
        self.stb = SymbolTreeBuilder(ast_tree)
        self.sym_tree = self.stb.st
        self.run()

    def error(self, sym, message):
        line = getattr(sym, "line", None)
        col = getattr(sym, "column", None)
        loc = f" [Line {line}:{col}]" if line is not None else ""
        raise SyntaxError(f"Nidavellir Error{loc}: {message}")

    def eval_NumberSymbol(self, sym):
        val = int(sym.value, 0) if isinstance(sym.value, str) else int(sym.value)
        sym.type = int_type(val, val)
        return sym

    def eval_VariableSymbol(self, sym):
        if sym.type is None:
            self.process_eval(sym.lookup)
            sym.type = sym.lookup.type

        if sym.type is None:
            self.error(sym, f"Cannot infer type of variable '{sym.name}'")

        return sym

    def stmt_AssignSymbol(self, sym):
        val = sym.value

        if val.type is None:
            self.process_eval(val)

        val_type = None

        if sym.uses:
            is_int = False
            for use in sym.uses:
                self.process_stmt(use)
                use_type = use.type

                if isinstance(use_type, int_type):
                    is_int = True
                elif is_int and not isinstance(use_type, int_type):
                    self.error(use, f"Cannot infer type of {use.name}")

            if is_int:
                min_val, max_val = TypeDefHelper.infer_int_range(sym)
                val_type = int_type(min_val, max_val)

        if val_type is None:
            val_type = val.type

        if val_type is None:
            self.error(sym, f"Cannot infer type of '{sym.name}'")

        sym.type = val_type
        return sym

    def process_stmt(self, sym):
        method_name = f"stmt_{type(sym).__name__}"
        visitor = getattr(self, method_name, None)
        if visitor is None:
            self.error(sym, f"No visitor method '{method_name}' for symbol")

        return visitor(sym)

    def process_eval(self, sym):
        method_name = f"eval_{type(sym).__name__}"
        visitor = getattr(self, method_name, None)
        if visitor is None:
            self.error(sym, f"No evaluator method '{method_name}' for symbol")

        return visitor(sym)

    def run(self):
        for sym in self.sym_tree:
            self.process_stmt(sym)

        raise Exception(self.stb.print_scopes())
