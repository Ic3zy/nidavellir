from .intrinsics import INTRINSIC_HANDLERS


class Scope:
    def __init__(
        self, name="block", parent=None, is_func=False, is_if=False, class_name=None
    ):
        self.name = name
        self.parent = parent
        self.is_func = is_func
        self.is_if = is_if

        self.class_name = class_name

        self.variables = {}
        self.functions = {}
        self.classes = {}
        self.types = {}
        self.modules = {}

    def define_var(self, name, symbol_obj):
        self.variables[name] = symbol_obj

    def lookup_class(self, name):
        if name in self.classes:
            return self.classes[name]
        if self.parent:
            return self.parent.lookup_class(name)

    def lookup_func(self, name):
        if name in self.functions:
            return self.functions[name]
        if self.parent:
            return self.parent.lookup_func(name)

    def lookup_module(self, name):  # EKLENDİ
        if name in self.modules:
            return self.modules[name]
        if self.parent:
            return self.parent.lookup_module(name)

    def lookup_var_local(self, name):
        if name in self.variables:
            return self.variables[name]

    def lookup_var(self, name):
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.lookup_var(name)


class SymbolTableManager:
    def __init__(self):
        self.global_scope = Scope(name="global", parent=None)
        self.current_scope = self.global_scope

    def enter_scope(
        self, scope_name="block", is_func=False, is_if=False, class_name=None
    ):
        new_scope = Scope(
            name=scope_name,
            parent=self.current_scope,
            is_func=is_func,
            is_if=is_if,
            class_name=class_name,
        )
        self.current_scope = new_scope

    def exit_scope(self):
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent

    def define_var(self, name, var_type):
        var_symbol = {"name": name, "type": var_type}
        self.current_scope.define_var(name, var_symbol)

    def define_class(self, name, ast_node):
        class_symbol = {"name": name, "params": [], "fields": {}, "ast": ast_node}
        self.global_scope.classes[name] = class_symbol

    def lookup_field(self, class_name, field_name):
        class_symbol = self.lookup_class(class_name)
        if class_symbol and field_name in class_symbol["fields"]:
            return class_symbol["fields"][field_name]
        return None

    def define_field(self, class_name, field_name, field_type, ast_node=None):
        class_symbol = self.global_scope.classes.get(class_name)
        if class_symbol:
            class_symbol["fields"][field_name] = {
                "name": field_name,
                "type": field_type,
                "ast": ast_node,
            }

    def define_class_required_params(self, class_name, params):
        class_symbol = self.global_scope.classes.get(class_name)
        if class_symbol:
            class_symbol["params"] = params

    def lookup_class(self, name):
        return self.current_scope.lookup_class(name)

    def lookup_var(self, name):
        return self.current_scope.lookup_var(name)

    def define_func(self, name, return_type, params, ast_node, c_name=None):
        func_symbol = {
            "name": name,
            "return_type": return_type,
            "params": params,
            "ast": ast_node,
            "is_variadic": False,
            "module": None,
            "c_name": c_name,
        }
        self.global_scope.functions[name] = func_symbol

    def define_imported_func(
        self, name, return_type, params, module_name, is_variadic=False
    ):
        func_symbol = {
            "name": name,
            "return_type": return_type,
            "params": params,
            "ast": None,
            "is_variadic": is_variadic,
            "is_external": True,
            "module": module_name,
        }
        self.global_scope.functions[name] = func_symbol

    def define_module(self, alias_or_name, real_module_name):
        self.current_scope.modules[alias_or_name] = real_module_name

    def lookup_func(self, name):
        if name in INTRINSIC_HANDLERS:
            return INTRINSIC_HANDLERS[name]

        return self.global_scope.lookup_func(name)
