from IR_gen.irs import *
from semantic.intrinsics import INTRINSIC_HANDLERS


class IntrinsicHandler:
    def __init__(self):
        self.used_intrinsics = []

    def print_handler(self, ir):
        self.used_intrinsics.append("print")
        args = ir.args

        chunks = []

        temp_args = []
        arg_c = 0
        top_c = 0
        for arg in args:
            arg_c += 1
            temp_args.append(arg)
            if arg_c == 4:
                is_last = (top_c * 4) == len(args)
                temp_args.append(BooleanIR(is_last))
                c_call_node = CallIR("_Nida_print_a4", temp_args)
                chunks.append(c_call_node)
                temp_args = []
                arg_c = 0
                top_c += 1

        if temp_args:
            extra_args = [BooleanIR(True)]
            temp_args.extend(extra_args)
            c_call_node = CallIR(
                f"_Nida_print_a{len(temp_args)-len(extra_args)}", temp_args
            )
            chunks.append(c_call_node)

        return chunks

    def run_intrinsic_handler(self, ir):
        name = ir.target
        func = getattr(self, f"{name}_handler", None)
        if func is None:
            raise Exception(f"No function named {name}")

        return func(ir)
