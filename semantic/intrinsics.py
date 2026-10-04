from nida_ast.base import IntrinsicAST
from utils import SysArgs


def not_implemented(*a, **k):
    raise NotImplementedError("Intrinsic not implemented", a, k)


# TODO: Move intrinsic implementation out of semantic and into HIR generation.
# Semantic should only validate/resolve the intrinsic and produce IntrinsicAST.
# HIR generator should invoke the intrinsic implementer and receive HIR nodes.
def print_intrinsic(Hir):
    from IR_gen.irs import CallIR, BooleanIR, BlockIR

    if SysArgs.no_print:
        return []

    # TODO: impl
    # self.used_intrinsics.append("print")
    SysArgs.add_extra_c_include("<print.h>")
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


INTRINSIC_HANDLERS = {
    "list": {
        "name": "list",
        "return_type": "List",
        "params": [("size", "Any_int"), ("type", "type")],
        "handler": not_implemented,
        "is_variadic": False,
    },
    "print": {
        "name": "print",
        "return_type": "None",
        "params": [],
        "handler": print_intrinsic,
        "is_variadic": True,
        "is_default_function": True,
    },
    "range": {
        "name": "range",
        "return_type": "List",
        "params": [("size", "Any_int")],
        "handler": not_implemented,
        "is_variadic": False,
    },
}
