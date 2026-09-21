class IR:
    pass


class AssignIR(IR):
    def __init__(self, target, value, type=None):
        self.target = target
        self.value = value
        self.val_type = type


class FunctionIR(IR):
    def __init__(self, decs, name, args, body, return_type=None):
        self.decs = decs
        self.name = name
        self.args = args
        self.body = body
        self.return_type = return_type

        self.body_irs = []


class ReturnIR(IR):
    def __init__(self, value, val_type=None):
        self.value = value
        self.val_type = None


class BinaryOpIR(IR):
    def __init__(self, left, right, op):
        self.left = left
        self.right = right
        self.op = op


class VariableIR(IR):
    def __init__(self, name):
        self.name = name


class CallIR(IR):
    def __init__(self, target, args):
        self.target = target
        self.args = args
        self.val_type = None
