from .irs import *
from .ir_passer import IRPasser
from nida_ast.base import *


class IRGen:
    def __init__(self, asts):
        self.asts = asts
        self.IRs = []

    def gen_PassAST(self, ast):
        return IR()

    def gen_AssignAST(self, ast):
        target = ast.target
        value = ast.value
        if isinstance(value, UnaryOpAST):
            val_res = self._gen_unary_op(target, value)
        else:
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

    def gen_BlockAST(self, ast):
        body = ast.body
        body_irs = []
        for n in body:
            body_irs.append(self.gen(n))

        return BlockIR(body_irs)

    def gen_ElifAST(self, ast):
        cond = ast.cond
        body = ast.body

        cond_ir = self.gen(cond)
        body_irs = []
        for n in body:
            body_irs.append(self.gen(n))

        return ElifIR(cond_ir, body_irs)

    def gen_IfAST(self, ast):
        cond = ast.cond
        body = ast.body
        elifs = ast.elifs
        else_body = ast.else_body

        cond_ir = self.gen(cond)
        body_irs = []
        for n in body:
            body_irs.append(self.gen(n))

        elifs_irs = []
        for elif_ast in elifs:
            elif_ir = self.gen(elif_ast)
            elifs_irs.append(elif_ir)

        else_body_irs = self.gen(else_body) if else_body is not None else None

        return IfIR(cond_ir, body_irs, elifs_irs, else_body_irs)

    def gen_GroupAST(self, ast):
        expr = ast.expr
        expr_ir = self.gen(expr)
        return GroupIR(expr_ir)

    def gen_ForAST(self, ast):
        target = ast.target
        source = ast.source
        body = ast.body

        target_ir = VariableIR(target.target)
        source_ir = self.gen(source)
        body_irs = []
        for n in body:
            body_irs.append(self.gen(n))

        return ForIR(target_ir, source_ir, body_irs)

    def _gen_unary_op(self, target, ast):
        op = ast.op
        right = ast.right

        right_ir = self.gen(right)
        return BinaryOpIR(left=VariableIR(target), op=op, right=right_ir)

    def gen(self, ast):
        name = ast.__class__.__name__
        if name == "NoneType":
            raise Exception(f"No function named {ast}")

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
