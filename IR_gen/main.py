from .irs import *
from .ir_passer import IRPasser
from nida_ast.base import *
from type_systems.types import ClassType

# from semantic import INTRINSIC_HANDLERS


class IRGen:
    def __init__(self, asts, ctx):
        self.asts = asts
        self.ctx = ctx

        self.IRs = []

    def gen_PassAST(self, ast):
        return PassIR()

    def gen_AssignAST(self, ast):
        target = ast.target
        value = ast.value
        var_type = ast.type

        if isinstance(value, UnaryOpAST):
            val_res = self._gen_unary_op(target, value)
        elif value is None:
            val_res = NoneIR(air=True)
        else:
            val_res = self.gen(value)

        if hasattr(val_res, "type") and val_res.type is None:
            val_res.type = var_type

        return AssignIR(target, val_res, var_type, re_assign=ast.is_re_assign)

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
        target = ast.target_function_name or ast.target
        # target = ast.target_function_name
        # if target is None and isinstance(ast.target, ClassType):
        #     target = ast.target
        # else:
        #     raise Exception(f"No IR generated for {ast}")

        args = ast.args
        type = ast.type

        args_irs = []
        for arg in args:
            args_irs.append(self.gen(arg))

        ir = CallIR(target, args_irs, type)
        return ir

    def gen_IntrinsicCallAST(self, ast):
        name = ast.intrinsic.name
        args = ast.args
        type = ast.type
        intrinsic = ast.intrinsic

        n_args = []
        for arg in args:
            n_args.append(self.gen(arg))

        ir = IntrinsicCallIR(intrinsic, name, n_args, type)
        handler = intrinsic.handler
        new_ir = handler(ir)
        return new_ir

    def gen_StringAST(self, ast):
        return StringLiteralIR(ast.value)

    def gen_NumberAST(self, ast):
        return NumberIR(ast.value, ast.type)

    def gen_VariableAST(self, ast):
        name = ast.name
        type = ast.type
        return VariableIR(name, type)

    def gen_BinaryOpAST(self, ast):
        left = ast.left
        left_ir = self.gen(left)
        right = ast.right
        right_ir = self.gen(right)
        op = ast.op
        type = ast.type
        return BinaryOpIR(left_ir, right_ir, op, type)

    def gen_FunctionAST(self, ast):
        decs = ast.decorators
        name = ast.local_id
        args = ast.args
        body = ast.body
        type = ast.type
        args_irs = []
        for arg in args:
            args_irs.append(self.gen(arg))

        ir_body = []

        for b in body:
            res = self.gen(b)
            ir_body.append(res)

        ir = FunctionIR(decs, name, args_irs, ir_body, type)

        return ir

    def gen_ImportAST(self, ast):
        module_name = ast.module
        symbols = ast.symbols
        alias = ast.alias

        body = []
        module = ast.resolved_module

        for n in module.asts:
            body.append(self.gen(n))

        module.hirs = body

        return IRImport(
            module=module_name,
            symbols=symbols,
            alias=alias,
            resolved_module=module,
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

        target_ir = self.gen(target)
        source_ir = self.gen(source)
        body_irs = []
        for n in body:
            body_irs.append(self.gen(n))

        return ForIR(target_ir, source_ir, body_irs)

    def gen_WhileAST(self, ast):
        cond = ast.cond
        body = ast.body

        body_irs = []
        for n in body:
            body_irs.append(self.gen(n))

        cond_ir = self.gen(cond)
        return WhileIR(cond_ir, body_irs)

    def gen_BooleanAST(self, ast):
        value = ast.value
        return BooleanIR(value)

    def gen_NoneAST(self, ast):
        return NoneIR()

    def gen_DefinitionAST(self, ast):
        target = ast.target
        value = ast.value
        type = ast.type

        value_ir = self.gen(value)
        return DefinitionIR(target, value_ir, type)

    def process_class_body(self, body):
        new_body = []

        for n in body:
            if isinstance(n, AssignAST):
                res = self.gen(n)
                if res is None:
                    raise Exception(f"No IR generated for {n}")

                new_body.append(res)

            elif isinstance(n, FunctionAST):
                res = self.gen(n)
                if res is None:
                    raise Exception(f"No IR generated for {n}")

                new_body.append(res)

            else:
                raise Exception(f"No IR generated for {n}")

        return new_body

    def gen_ClassAST(self, ast):
        name = ast.name
        body = ast.body

        new_body = self.process_class_body(body)

        return ClassIR(name, new_body)

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

        # raise Exception(self.IRs)

        ir_passer = IRPasser(self.IRs, self.ctx)
        self.IRs = ir_passer.run()

        return self.IRs

    def run(self):
        return self.gen_from_list(self.asts)
