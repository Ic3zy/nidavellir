class FunctionAST:
    def __init__(self, name, args, body):
        self.name = name
        self.args = args
        self.body = body

    def generate_code(self):
        pass

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

class ReturnAST:
    def __init__(self, value):
        self.value = value

class AssignAST:
    def __init__(self, name, value):
        self.name = name
        self.value = value

class BinaryAST:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right
