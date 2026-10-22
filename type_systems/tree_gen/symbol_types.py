from ..types import resolve_type, StringType, NoneType, ClassType


class Symbol:
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

        self.chain = []
        self.base_sym = None

    def set_type_to_AST(self):
        self.ast_node.type = self.type
        if self.parent_assign is not None and not self.chain:
            self.parent_assign.type = self.type
            self.parent_assign.set_type_to_AST()


class DefinitionSymbol(Symbol):
    def __init__(self, name, type, value, ast_node):
        self.name = name
        self.type = resolve_type(type)
        self.value = value
        self.ast_node = ast_node

        self.parent_assign = None

        self.uses = []

    def set_type_to_AST(self):
        self.ast_node.type = self.type


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

        self.receiver_chain = []

        self.arg_offset = 0

        self.type = None

    def set_type_to_AST(self):
        self.ast_node.type = self.type


class IntrinsicCallSymbol(Symbol):
    def __init__(self, intrinsic, name, args, ast_node):
        self.intrinsic = intrinsic
        self.name = name
        self.args = args
        self.ast_node = ast_node

        self.type = None


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


class UnaryOpSymbol(Symbol):
    def __init__(self, op, right_sym, ast_node=None):
        self.op = op
        self.right_sym = right_sym
        self.ast_node = ast_node

        self.type = None

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


class WhileSymbol(Symbol):
    def __init__(self, cond, body, ast_node):
        self.cond = cond
        self.body = body
        self.ast_node = ast_node


class BooleanSymbol(Symbol):
    def __init__(self, value, ast_node):
        self.value = value
        self.ast_node = ast_node
        self.type = None


class ClassSymbol(Symbol):
    def __init__(self, name, ast_node):
        self.name = name
        self.ast_node = ast_node

        self.body = []

        self.fields = {}
        self.methods = {}

        self.method_syms = {}

        self.uses = []

        self.type = ClassType(name)

    def set_type_to_AST(self):
        self.ast_node.type = self.type


class FieldAccessSymbol(Symbol):
    def __init__(self, target, chain, ast_node):
        self.target = target
        self.chain = chain
        self.ast_node = ast_node

        self.type = None

    def set_type_to_AST(self):
        self.ast_node.type = self.type


class SelfSymbol(Symbol):
    def __init__(self, ast_node, class_name=None):
        self.ast_node = ast_node
        self.class_name = class_name

        self.type = None

    def set_type_to_AST(self):
        if hasattr(self.ast_node, "chain"):
            return

        self.ast_node.type = self.type


class ConstructorCallSymbol(Symbol):
    def __init__(self, name, args, lookup, ast_node):
        self.name = name
        self.args = args
        self.lookup = lookup
        self.ast_node = ast_node

        self.arg_offset = 1

        self.type = None

    def set_type_to_AST(self):
        self.ast_node.type = self.type
