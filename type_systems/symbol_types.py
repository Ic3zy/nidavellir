from .types import resolve_type, StringType, NoneType


class Symbol:
    pass

    def set_type_to_AST(self):
        pass


class AssignSymbol(Symbol):
    def __init__(self, name, type, value, ast_node):
        self.name = name
        self.type = resolve_type(type)
        self.value = value

        self.ast_node = ast_node

        self.parent_assign = None

        self.uses = []

    def set_type_to_AST(self):
        self.ast_node.type = self.type
        if self.parent_assign is not None:
            self.parent_assign.type = self.type
            if hasattr(self.parent_assign, "set_type_to_AST"):
                self.parent_assign.set_type_to_AST()


class NumberSymbol(Symbol):
    def __init__(self, value, ast_node):
        self.value = value
        self.ast_node = ast_node

        self.type = None

    def set_type_to_AST(self):
        self.ast_node.type = self.type


class StringSymbol(Symbol):
    def __init__(self, value, ast_node):
        self.value = value
        self.ast_node = ast_node

        self.type = StringType()

    def set_type_to_AST(self):
        self.ast_node.type = self.type


class NoneSymbol(Symbol):
    def __init__(self, ast_node):
        self.ast_node = ast_node

        self.type = NoneType()

    def set_type_to_AST(self):
        self.ast_node.type = self.type


class FunctionSymbol(Symbol):
    def __init__(self, name, type, args, ast_node, is_variadic=False):
        self.name = name
        self.type = resolve_type(type)
        self.args = args
        self.ast_node = ast_node
        self.is_variadic = is_variadic

        self.body = []

        self.uses = []
        self.returned = []

    def set_type_to_AST(self):
        self.ast_node.type = self.type


class ReturnSymbol(Symbol):
    def __init__(self, value, ast_node):
        self.value = value
        self.ast_node = ast_node


class CallSymbol(Symbol):
    def __init__(self, name, args, lookup, ast_node):
        self.name = name
        self.args = args
        self.lookup = lookup
        self.ast_node = ast_node

        self.type = None

    def set_type_to_AST(self):
        self.ast_node.type = self.type


class VariableSymbol(Symbol):
    def __init__(self, name, lookup, ast_node):
        self.name = name
        self.lookup = lookup
        self.ast_node = ast_node

        self.type = None

    def set_type_to_AST(self):
        self.ast_node.type = self.type


class BinaryOpSymbol(Symbol):
    def __init__(self, op, left_sym, right_sym, ast_node=None):
        self.op = op
        self.left_sym = left_sym
        self.right_sym = right_sym
        self.ast_node = ast_node

        self.type = None

        self.max_val = None
        self.min_val = None

    def set_type_to_AST(self):
        self.ast_node.type = self.type


class ForSymbol(Symbol):
    def __init__(self, target, source, body, loop_count, ast_node):
        self.target = target
        self.source = source
        self.ast_node = ast_node
        self.body = body
        self.loop_count = loop_count

        self.type = None


class IfSymbol(Symbol):
    def __init__(self, cond, body, elifs, else_body, ast_node):
        self.cond = cond
        self.body = body

        self.elifs = elifs
        self.else_body = else_body

        self.ast_node = ast_node


class ElifSymbol(Symbol):
    def __init__(self, cond, body, ast_node):
        self.cond = cond
        self.body = body
        self.ast_node = ast_node
