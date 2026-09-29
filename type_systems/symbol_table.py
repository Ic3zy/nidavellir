from .symbol_types import *
from nida_ast.base import *


class Scope:
    def __init__(self, parent=None, scope_type=None):
        self.parent = parent
        self.symbols = {}
        self.scope_type = scope_type

    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent is not None:
            return self.parent.lookup(name)
        return None

    def add_symbol(self, symbol):
        if symbol.name in self.symbols:
            raise SyntaxError(
                f"Symbol {symbol.name} already exists in scope and cannot be redefined"
            )

        self.symbols[symbol.name] = symbol
        return symbol


class SymbolTableManager:
    def __init__(self):
        self.global_scope = Scope()
        self.current_scope = self.global_scope
