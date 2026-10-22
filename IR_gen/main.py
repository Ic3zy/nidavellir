from .irs import *
from .ir_passer import IRPasser
from nida_ast.base import *
from type_systems.types import ClassType, Type, resolve_type


class IRGen:
    def __init__(self, asts, ctx):
        self.asts = asts
        self.ctx = ctx
        self.f_alloc = ctx["f_alloc"]

        self.IRs = []

    def gen_PassAST(self, ast):
        return PassIR()

    def gen_AssignAST(self, ast):
        target = ast.target
        value = ast.value
        var_type = ast.type
        chain = getattr(ast, "chain", []) or []

        if isinstance(value, UnaryOpAST):
            val_res = self._gen_unary_op(target, value)
        elif value is None:
            val_res = NoneIR(air=True)
        else:
            val_res = self.gen(value)

        if hasattr(val_res, "type") and val_res.type is None:
            val_res.type = var_type

        return AssignIR(
            target,
            val_res,
            var_type,
            re_assign=ast.is_re_assign,
            chain=chain,
            base_type=self._type_of(getattr(ast, "base_type", None)),
            chain_types=[self._type_of(t) for t in getattr(ast, "chain_types", [])],
        )

    def _type_of(self, type_val):
        """A type written as a name ('int', 'Point') becomes a type object."""
        if type_val is None or isinstance(type_val, Type):
            return type_val

        resolved = resolve_type(type_val)

        if resolved is not None:
            return resolved

        return type_val

    def gen_FieldAccessAST(self, ast):
        target_ir = self.gen(ast.target)
        chain = getattr(ast, "chain", []) or []
        chain_types = getattr(ast, "chain_types", []) or []

        return FieldAccessIR(
            target_ir,
            chain,
            self._type_of(ast.type),
            [self._type_of(t) for t in chain_types],
        )

    def gen_SelfAST(self, ast):
        return VariableIR("self", ast.type)

    def gen_ReturnAST(self, ast):
        value = ast.value
        res = self.gen(value)
        return ReturnIR(res)

    def gen_CallAST(self, ast):
        target = ast.target_function_name
        if target is not None:
            target = self.f_alloc.name_of(target)
        else:
            target = ast.target

        args = ast.args
        type = ast.type

        args_irs = []
        for arg in args:
            args_irs.append(self.gen(arg))

        if ast.chain:
            receiver = self._gen_receiver(ast)
            args_irs.insert(0, receiver)

        ir = CallIR(target, args_irs, type)
        return ir

    def _gen_receiver(self, ast):
        receiver_type = getattr(ast, "receiver_type", None)
        receiver_chain = getattr(ast, "receiver_chain", None) or []

        if not receiver_chain:
            return VariableIR(ast.target, receiver_type)

        base_type = getattr(ast, "receiver_base_type", None)
        target_ir = VariableIR(ast.target, base_type)

        chain_types = list(getattr(ast, "receiver_chain_types", None) or [])

        return FieldAccessIR(
            target_ir,
            list(receiver_chain),
            receiver_type,
            chain_types,
        )

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
        name = ast.func_id
        if name is None:
            raise Exception(f"No func_id for function {ast}")
        name = self.f_alloc.name_of(name)

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

        ir = FunctionIR(decs, name, args_irs, ir_body, type, ast_name=ast.name)

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

    def gen_UnaryOpAST(self, ast):
        op = ast.op
        value = ast.right
        type = ast.type

        value_ir = self.gen(value)
        return UnaryOpIR(op, value_ir, type)

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

        return ClassIR(name, new_body, self._class_fields(ast))

    def _class_fields(self, ast):
        """The fields of a class: [(name, type)] in declaration order."""
        fields = []

        for field_name, field_ast in ast.fields.items():
            info_tuple = [field_name]
            field_type = field_ast.type

            if field_type is None and field_ast.value is not None:
                field_type = field_ast.value.type

            info_tuple.append(field_type)

            value_ir = None

            if getattr(field_ast, "value", None) is not None:
                value_ir = self.gen(field_ast.value)

            info_tuple.append(value_ir)

            fields.append(tuple(info_tuple))

        return fields

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
