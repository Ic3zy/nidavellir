from .tree_utils import render_attrs


class Symbol:
    def __repr__(self) -> str:
        return "\n".join(render_attrs(self))


class GlobalScope(Symbol):
    pass


class VariableSymbol(Symbol):
    def __init__(self, name: str, type_annotation: str, ast_node):
        self.name = name
        self.type = type_annotation
        self.ast_node = ast_node
        self.used_stack = []

        self.call_symbol = None


class FunctionSymbol(Symbol):
    def __init__(
        self, name: str, return_type: str, params: list, ast_node, is_variadic=False
    ):
        self.name = name
        self.return_type = return_type
        self.params = params
        self.ast_node = ast_node
        self.call_stack = []
        self.is_variadic = is_variadic
        self.returns = None


class ClassSymbol(Symbol):
    def __init__(self, name: str, params: list, scope, ast_node):
        self.name = name
        self.params = params
        self.scope = scope
        self.ast_node = ast_node
        self.call_stack = []


class CallSymbol(Symbol):
    def __init__(self, name: str, params: list, func, ast_node):
        self.name = name
        self.params = params
        self.sym_params = []
        self.func = func
        self.ast_node = ast_node


class BinaryOpSymbol(Symbol):
    def __init__(self, op, left_sym, right_sym, ast_node=None):
        self.op = op
        self.left_sym = left_sym
        self.right_sym = right_sym
        self.ast_node = ast_node
        self.inferred_type = None


class NumberSymbol(Symbol):
    def __init__(self, value, ast_node):
        self.value = value
        self.ast_node = ast_node
        self.type = None
        self.name = "Number"
