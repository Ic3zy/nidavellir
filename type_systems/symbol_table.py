from .symbol_types import *


class Scope:
    def __init__(self, parent=None, scope_type=None):
        self.parent = parent
        self.symbols = {}
        self.children = []
        self.scope_type = scope_type

    def add_symbol(self, symbol):
        if symbol.name in self.symbols:
            raise SyntaxError(f"Symbol {symbol.name} already exists in scope")
        self.symbols[symbol.name] = symbol

    def get_symbol(self, name):
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent is not None:
            return self.parent.get_symbol(name)
        else:
            raise SyntaxError(f"Symbol {name} not found in scope")


class ScopeManager:
    def __init__(self):
        self.global_scope = Scope(scope_type=GlobalScope)
        self.current_scope = self.global_scope

    def enter_scope(self, scope_type=None):
        new_scope = Scope(parent=self.current_scope, scope_type=scope_type)
        self.current_scope.children.append(new_scope)
        self.current_scope = new_scope

    def exit_scope(self):
        if self.current_scope.parent is not None:
            self.current_scope = self.current_scope.parent

        else:
            raise SyntaxError("Cannot exit global scope")

    def add_symbol(self, symbol):
        self.current_scope.add_symbol(symbol)

    def get_symbol(self, name):
        return self.current_scope.get_symbol(name)

    def print_scopes(self, scope=None):
        if scope is None:
            scope = self.global_scope

        print(f"Scope: {scope.symbols}")

        for sc in scope.children:
            if sc is None:
                print("None")
            self.print_scopes(scope=sc)
