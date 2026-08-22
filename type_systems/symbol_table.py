from .symbol_types import *
from .tree_utils import render_node


class Scope:
    def __init__(self, parent=None, scope_type=None):
        self.parent = parent
        self.symbols = {}
        self.children = []
        self.scope_type = scope_type

    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent is not None:
            return self.parent.lookup(name)
        return None

    def add_symbol(self, symbol):
        if symbol.name in self.symbols:
            existing = self.symbols[symbol.name]

            if isinstance(existing, VariableSymbol) and isinstance(
                symbol, VariableSymbol
            ):
                if hasattr(symbol, "used_stack"):
                    existing.used_stack.append(symbol)
                return
            else:
                raise SyntaxError(
                    f"Symbol {symbol.name} already exists in scope and cannot be redefined"
                )

        self.symbols[symbol.name] = symbol
        return symbol

    def get_symbol(self, name):
        sym = self.lookup(name)
        if sym is None:
            raise SyntaxError(f"Symbol '{name}' not found in scope")
        return sym


class ScopeManager:
    def __init__(self):
        self.global_scope = Scope(scope_type=GlobalScope)
        self.current_scope = self.global_scope

    def enter_scope(self, scope_type=None, attach_to_parent=True):
        new_scope = Scope(parent=self.current_scope, scope_type=scope_type)
        if attach_to_parent:
            self.current_scope.children.append(new_scope)

        self.current_scope = new_scope

    def exit_scope(self):
        if self.current_scope.parent is not None:
            self.current_scope = self.current_scope.parent
        else:
            raise SyntaxError("Cannot exit global scope")

    def lookup(self, name):
        return self.current_scope.lookup(name)

    def add_symbol(self, symbol):
        self.current_scope.add_symbol(symbol)

    def get_symbol(self, name):
        return self.current_scope.get_symbol(name)

    def print_scopes(self, scope=None, prefix="", is_last=True, is_root=True):
        if scope is None:
            scope = self.global_scope

        scope_name = scope.scope_type.__name__ if scope.scope_type else "Scope"

        if is_root:
            print(scope_name)
            child_prefix = ""
        else:
            branch = "└── " if is_last else "├── "
            print(prefix + branch + scope_name)
            child_prefix = prefix + ("    " if is_last else "│   ")

        entries = [("symbol", name, symbol) for name, symbol in scope.symbols.items()]
        entries += [("scope", None, child) for child in scope.children]

        for index, (kind, name, value) in enumerate(entries):
            entry_last = index == len(entries) - 1

            if kind == "symbol":
                for line in render_node(name, value, child_prefix, entry_last):
                    print(line)
            else:
                self.print_scopes(
                    scope=value, prefix=child_prefix, is_last=entry_last, is_root=False
                )
