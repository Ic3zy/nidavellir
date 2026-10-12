from ..types import *
from ..tree_gen.symbol_types import *


class AutoTypeDefEngine:
    def __init__(self, sym_tree):
        self.sym_tree = sym_tree

    def process_AssignSymbol(self, sym):
        pass

    def process_CallSymbol(self, sym):
        pass

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
