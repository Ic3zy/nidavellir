from .irs import *
from .ir_passer import IRPasser
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
        val_res = self.gen(value)

        type_annotation = ast.type_annotation
        return AssignIR(target, val_res, type_annotation)

    def gen_ReturnAST(self, ast):
        value = ast.value
        res = self.gen(value)
        return ReturnIR(res)

    def gen_ClassAST(self, ast):
        name = ast.name
        body = ast.body

        body_irs = []
        for n in body:
            body_irs.append(self.gen(n))

        return ClassIR(name, body_irs)

    def gen_CallAST(self, ast):
        target = ast.target
        args = ast.args

        args_irs = []
        for arg in args:
            args_irs.append(self.gen(arg))

        return CallIR(target, args_irs)

    def gen_StringAST(self, ast):
        return StringLiteralIR(ast.value)

    def gen_NumberAST(self, ast):
        return NumberIR(ast.value)

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

        args_irs = []
        for arg in args:
            args_irs.append(self.gen(arg))

        ir = FunctionIR(decs, name, args_irs, body, type)

        for arg in body:
            res = self.gen(arg)
            ir.body_irs.append(res)

        return ir

    def gen_ImportAST(self, ast):
        module_name = ast.module
        symbols = ast.symbols
        alias = ast.alias

        return IRImport(
            module=module_name,
            symbols=symbols,
            alias=alias,
        )

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

        ir_passer = IRPasser(self.IRs)
        self.IRs = ir_passer.run()

        return self.IRs
