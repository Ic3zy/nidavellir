class Symbol:
    pass


class AssignSymbol(Symbol):
    def __init__(self, name, type, value, ast_node):
        self.name = name
        self.type = type
        self.value = value

        self.ast_node = ast_node

        self.uses = []


class NumberSymbol(Symbol):
    def __init__(self, value, ast_node):
        self.value = value
        self.ast_node = ast_node

        self.type = None


class FunctionSymbol(Symbol):
    def __init__(self, name, return_type, args, ast_node, is_variadic=False):
        self.name = name
        self.return_type = return_type
        self.args = args
        self.ast_node = ast_node
        self.is_variadic = is_variadic

        self.uses = []
        self.returned = []


class ReturnSymbol(Symbol):
    def __init__(self, value, ast_node):
        self.value = value
        self.ast_node = ast_node


class CallSymbol(Symbol):
    def __init__(self, name, args, func, ast_node):
        self.name = name
        self.args = args
        self.func = func
        self.ast_node = ast_node

        self.return_type = None


class VariableSymbol(Symbol):
    def __init__(self, name, lookup, ast_node):
        self.name = name
        self.lookup = lookup
        self.ast_node = ast_node

    @property
    def type(self):
        return self.lookup.type


class BinaryOpSymbol(Symbol):
    def __init__(self, op, left_sym, right_sym, ast_node=None):
        self.op = op
        self.left_sym = left_sym
        self.right_sym = right_sym
        self.ast_node = ast_node

        self.type = None
