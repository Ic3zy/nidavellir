from .symbol_types import *


class Scope:
    def __init__(self, name=None, type=None, parent=None):
        self.name = name
        self.type = type
        self.parent = parent

        self.functions = {}
        self.classes = {}
        self.assigns = {}

    def define_func(self, name, return_type, params):
        if name in self.functions:
            raise Exception(f"Function '{name}' already defined")

        func = {
            "name": name,
            "return_type": return_type,
            "params": params,
            "call_stack": [],
        }

        self.functions[name] = func

    def lookup_func(self, name):
        if name in self.functions:
            return self.functions[name]

        if self.parent:
            return self.parent.lookup_func(name)

    def define_class(self, name, params):
        if name in self.classes:
            raise Exception(f"Class '{name}' already defined")

        class_symbol = {
            "name": name,
            "params": params,
            "fields": {},
            "call_stack": [],
        }

        self.classes[name] = class_symbol

    def lookup_class(self, name):
        if name in self.classes:
            return self.classes[name]

        if self.parent:
            return self.parent.lookup_class(name)

    def define_assign(self, name, type):
        if name in self.assigns:
            raise Exception(f"Variable '{name}' already defined")

        assign = {"name": name, "type": type}
        self.assigns[name] = assign

    def lookup_assign(self, name):
        if name in self.assigns:
            return self.assigns[name]

        if self.parent:
            return self.parent.lookup_assign(name)


class ScopeManager:
    def __init__(self):
        self.global_scope = Scope(name="global", parent=None)
        self.current_scope = self.global_scope

    def enter_scope(self, scope_name="block", type=None):
        new_scope = Scope(name=scope_name, type=type, parent=self.current_scope)
        self.current_scope = new_scope

    def exit_scope(self):
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent

    def define_func(self, name, return_type, params):
        self.current_scope.define_func(name, return_type, params)

    def lookup_func(self, name):
        return self.current_scope.lookup_func(name)

    def define_class(self, name, params):
        self.current_scope.define_class(name, params)

    def lookup_class(self, name):
        return self.current_scope.lookup_class(name)

    def define_assign(self, name, type):
        self.current_scope.define_assign(name, type)

    def lookup_assign(self, name):
        return self.current_scope.lookup_assign(name)
