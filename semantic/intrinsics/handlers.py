from utils import SysArgs
from IR_gen.irs import *


def print_intrinsic(Hir):

    if SysArgs.no_print:
        return []

    SysArgs.add_extra_c_include("print.h")
    args = Hir.args

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
            c_call_node.imported_func_call = True

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
        c_call_node.imported_func_call = True

        chunks.append(c_call_node)

    return BlockIR(chunks)


def range_intrinsic(Hir):
    args = Hir.args
    arg_c = len(args)

    start = None
    end = None
    step = None

    if arg_c == 1:
        start = NumberIR(0)
        end = args[0]
        step = NumberIR(1)
    elif arg_c == 2:
        start = args[0]
        end = args[1]
        step = NumberIR(1)
    elif arg_c == 3:
        start = args[0]
        end = args[1]
        step = args[2]
    else:
        raise Exception("Range intrinsic takes 1, 2 or 3 arguments")

    return RangeIR(start, end, step)


def input_intrinsic(Hir):
    SysArgs.add_extra_c_include("input.h")
    return CallIR("Nida_input", Hir.args)
