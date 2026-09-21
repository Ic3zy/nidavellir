from .irs import *
from nida_ast import *


class IRGen:
    def __init__(self, asts):
        self.asts = asts
        self.IRs = []

    def gen_PassAST(self, ast):
        return IR()

    def gen_AssignAST(self, ast):
        target = ast.target
        value = ast.value
        type_annotation = ast.type_annotation
        return AssignIR(target, value, type_annotation)

    def gen_ReturnAST(self, ast):
        value = ast.value
        res = self.gen(value)
        return ReturnIR(res)

    def gen_CallAST(self, ast):
        target = ast.target
        args = ast.args
        return CallIR(target, args)

    def gen_NumberAST(self, ast):
        return IR()

    def gen_VariableAST(self, ast):
        name = ast.name
        return VariableIR(name)

    def gen_BinaryOpAST(self, ast):
        left = ast.left
        left_ir = self.gen(left)
        right = ast.right
        right_ir = self.gen(right)
        op = ast.op
        return BinaryOpIR(left_ir, right_ir, op)

    def gen_FunctionAST(self, ast):
        decs = ast.decorators
        name = ast.name
        args = ast.args
        body = ast.body
        type = ast.type

        ir = FunctionIR(decs, name, args, body, type)

        for arg in body:
            res = self.gen(arg)
            self.IRs.append(res)
            ir.body_irs.append(res)

        return ir

    def gen(self, ast):
        name = ast.__class__.__name__
        func = getattr(self, f"gen_{name}")
        if func is None:
            raise Exception(f"No function named {name}")

        res = func(ast)
        return res

    def gen_from_list(self, asts):
        for ast in asts:
            res = self.gen(ast)
            self.IRs.append(res)

        print(self.IRs)
