class FunctionAST:
    def __init__(self, name, args, body):
        self.name = name
        self.args = args
        self.body = body

    def generate_code(self):
        pass

class ElseAST:
    def __init__(self, body):
        self.body = body

class ElifAST:
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

class IfAST:
    def __init__(self, cond, body, elifs, else_body):
        self.cond = cond
        self.body = body
        self.elifs = elifs
        self.else_body = else_body

class NumberAST:
    def __init__(self, value, data_type=None):
        self.value = value
        self.data_type = data_type

class StringAST:
    def __init__(self, value):
        self.value = value

class VariableAST:
    def __init__(self, name):
        self.name = name

class IndexAccessAST:
    def __init__(self, target, index):
        self.target = target
        self.index = index

class MemberAccessAST:
    def __init__(self, target, member):
        self.target = target
        self.member = member

class CallAST:
    def __init__(self, callee, args):
        self.callee = callee
        self.args = args

class ChainAccessAST:
    def __init__(self, base, chain, args=None):
        self.base = base
        self.chain = chain
        self.args = args

class ReturnAST:
    def __init__(self, value):
        self.value = value

class AssignAST:
    def __init__(self, target, chain, value):
        self.target = target
        self.chain = chain
        self.value = value

class VarAssignAST:
    def __init__(self, target, type, value):
        self.target = target
        self.value = value
        self.type = type

class ExpressionAST:
    def __init__(self, target):
        self.target = target

class BinaryExprAST:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class UnaryExprAST:
    def __init__(self, op, right):
        self.op = op
        self.right = right

class WhileAST:
    def __init__(self, conditions, body):
        self.conditions = conditions
        self.body = body

class ForAST:
    def __init__(self, target, source, body):
        self.target = target
        self.source = source
        self.body = body

class ListAST:
    def __init__(self, body):
        self.body = body