from IR_gen.irs import *
from .c_nodes import *
from .intrinsics_c_handlers import IntrinsicHandler
from semantic.symbol_table import SymbolTableManager


class C_Gen:
    def __init__(self, IRs):
        self.IRs = IRs
        self.stm = SymbolTableManager()
        self.C_code = []
        self.ih = IntrinsicHandler()

    def gen_AssignIR(self, ir):
        target = ir.target

        value = ir.value
        value_node = self.gen(value)
        if value_node is None:
            raise Exception("No value node")

        val_type = ir.val_type
        lk = self.stm.lookup_var(target)
        self.stm.define_var(target, val_type)
        if lk is not None:
            ir.re_assign = True
        else:
            ir.re_assign = False
        return CAssign(target, value_node, val_type, re_assign=ir.re_assign)

    def gen_NumberIR(self, ir):
        value = ir.value
        return CNumber(value)

    def gen_FunctionIR(self, ir):
        name = ir.name
        is_main_func = ir.is_main_func
        if is_main_func:
            c_name = "main"
        else:
            c_name = f"Nidavellir_Func_{name}"

        args = ir.args
        body = ir.body_irs
        return_type = ir.return_type

        body_nodes = []
        for b in body:
            body_nodes.append(self.gen(b))

        args_nodes = []
        for a in args:
            args_nodes.append(self.gen(a))

        self.stm.define_func(name, 0, 0, 0, c_name)

        return CFunction(name, c_name, args_nodes, body_nodes, return_type)

    def gen_ReturnIR(self, ir):
        value = ir.value
        value_node = self.gen(value)
        if value_node is None:
            raise Exception("No value node")

        return CReturn(value_node)

    def gen_IRImport(self, ir):
        # TODO: impl
        return CImport(ir.module)

    def gen_CallIR(self, ir):
        target = ir.target
        args = ir.args
        args_nodes = []
        for arg in args:
            args_nodes.append(self.gen(arg))

        # TODO: impl

        func = self.stm.lookup_func(target)
        if func is None:
            return CCall(target, args_nodes)

        c_name = func.get("c_name")
        if c_name is None:
            is_default_func = func.get("is_default_function")
            if is_default_func:
                irs = self.ih.run_intrinsic_handler(ir)
                print(irs)
                top_c_nodes = []
                for ir in irs:
                    res = self.gen(ir)
                    top_c_nodes.append(res)

                return CBlock(top_c_nodes)
            else:
                raise Exception("No c_name")

        return CCall(c_name, args_nodes)

    def gen_StringLiteralIR(self, ir):
        return CString(ir.value)

    def gen_VariableIR(self, ir):
        return CVariable(ir.name)

    def gen_BinaryOpIR(self, ir):
        left = ir.left
        right = ir.right

        left_node = self.gen(left)
        right_node = self.gen(right)

        op = ir.op

        return CBinaryOp(left_node, right_node, op)

    def gen_ElifIR(self, ir):
        cond = ir.cond
        body = ir.body

        cond_node = self.gen(cond)
        body_nodes = []
        for b in body:
            body_nodes.append(self.gen(b))

        return CElif(cond_node, body_nodes)

    def gen_IfIR(self, ir):
        cond = ir.cond
        body = ir.body
        elifs = ir.elifs
        else_body = ir.else_body

        cond_node = self.gen(cond)
        elifs_nodes = []
        body_nodes = []
        else_body_nodes = []

        for b in body:
            body_nodes.append(self.gen(b))

        for e in elifs:
            elifs_nodes.append(self.gen(e))

        if else_body is not None:
            for b in else_body.body:
                else_body_nodes.append(self.gen(b))

        return CIf(cond_node, body_nodes, elifs_nodes, else_body_nodes)

    def gen_GroupIR(self, ir):
        expr = ir.expr
        expr_node = self.gen(expr)
        return CGroup(expr_node)

    def gen_ForIR(self, ir):
        target = ir.target
        source = ir.source
        body = ir.body

        body_nodes = []
        for b in body:
            body_nodes.append(self.gen(b))

        range = None

        if isinstance(source, CallIR):
            target_fn = source.target
            if target_fn == "range" and isinstance(source.args[0], NumberIR):
                range = source.args[0].value
                range = int(range)
            else:
                raise NotImplementedError(
                    f"For loop source '{target_fn}' is not implemented"
                )
        else:
            raise NotImplementedError(
                f"For loop source '{type(source).__name__}' is not implemented"
            )

        return CFor(target.name, range, body_nodes)

    def gen_WhileIR(self, ir):
        cond = ir.cond
        body = ir.body
        cond_node = self.gen(cond)
        body_nodes = []
        for b in body:
            body_nodes.append(self.gen(b))

        return CWhile(cond_node, body_nodes)

    def gen_BooleanIR(self, ir):
        value = ir.value
        return CBoolean(value)

    def gen_NoneIR(self, ir):
        return CNone()

    def gen(self, ir):
        name = ir.__class__.__name__
        func = getattr(self, f"gen_{name}")
        if func is None:
            raise Exception(f"No function named {name}")

        return func(ir)

    def gen_from_list(self, IRs):
        for ir in IRs:
            res = self.gen(ir)
            self.C_code.append(res)

        print("\n\n\n C code final: ", c_code := self.get_final_c_code())

        return c_code

    def get_used_intrinsics_includes(self):
        used_includes = ["#include <Nida_core.h>"]
        for intrinsic in self.ih.used_intrinsics:
            used_includes.append(f"#include <{intrinsic}.h>")

        return "\n".join(used_includes)

    def get_final_c_code(self):
        c_code = self.get_used_intrinsics_includes()
        for c_node in self.C_code:
            c_code += "\n" + c_node.str()

        return c_code
