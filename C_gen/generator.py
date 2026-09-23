from IR_gen.irs import *
from .c_nodes import *


class C_Gen:
    def __init__(self, IRs):
        self.IRs = IRs
        self.C_code = []

    def gen_AssignIR(self, ir):
        target = ir.target

        value = ir.value
        value_node = self.gen(value)
        if value_node is None:
            raise Exception("No value node")

        val_type = ir.val_type

        return CAssign(target, value_node, val_type)

    def gen_NumberIR(self, ir):
        value = ir.value
        return CNumber(value)

    def gen_FunctionIR(self, ir):
        name = ir.name
        args = ir.args
        body = ir.body_irs
        return_type = ir.return_type

        body_nodes = []
        for b in body:
            body_nodes.append(self.gen(b))

        args_nodes = []
        for a in args:
            args_nodes.append(self.gen(a))

        return CFunction(name, args_nodes, body_nodes, return_type)

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

        return CCall(target, args_nodes)

    def gen_StringLiteralIR(self, ir):
        return CString(ir.value)

    def gen_VariableIR(self, ir):
        return CVariable(ir.name)

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

    def get_final_c_code(self):
        c_code = ""
        for c_node in self.C_code:
            c_code += "\n" + c_node.str()

        return c_code
