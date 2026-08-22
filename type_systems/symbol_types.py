from .tree_utils import render_attrs


class Symbol:
    def __repr__(self) -> str:
        return "\n".join(render_attrs(self))


class GlobalScope(Symbol):
    pass


class VariableSymbol(Symbol):
    def __init__(self, name: str, type_annotation: str):
        self.name = name
        self.type = type_annotation
        self.used_stack = []


class FunctionSymbol(Symbol):
    def __init__(self, name: str, return_type: str, params: list, is_variadic=False):
        self.name = name
        self.return_type = return_type
        self.params = params
        self.call_stack = []
        self.is_variadic = is_variadic


class ClassSymbol(Symbol):
    def __init__(self, name: str, params: list, scope):
        self.name = name
        self.params = params
        self.scope = scope
        self.call_stack = []
