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

        value_str = value_node.str()

        val_type = ir.val_type

        return CAssign(target, value_str, val_type)

    def gen_NumberIR(self, ir):
        value = ir.value
        return CNumber(value)

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

        print("\n\n\n C code final: ", self.get_final_c_code())

    def get_final_c_code(self):
        c_code = ""
        for c_node in self.C_code:
            c_code += c_node.str()

        return c_code
