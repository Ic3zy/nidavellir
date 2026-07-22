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
    def __init__(self, value):
        self.value = value

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

class ReturnAST:
    def __init__(self, value):
        self.value = value

class AssignAST:
    def __init__(self, target, value):
        self.target = target
        self.value = value

class ExpressionAST:
    def __init__(self, target):
        self.target = target