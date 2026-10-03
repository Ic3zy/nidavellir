from IR_gen.irs import *
from .c_nodes import *
from .intrinsics_c_handlers import IntrinsicHandler
from .header_generator import HeaderGenerator
from .c_types import *
from .extra_c_includes import EXTRA_C_INCLUDES
from semantic.symbol_table import SymbolTableManager


class CExprTranslator:
    @classmethod
    def translate(cls, value):
        if isinstance(value, int):
            return CNumber(value)

        if isinstance(value, float):
            return CNumber(value)

        if isinstance(value, str):
            return CString(value)

        raise Exception(f"Unsupported expression value: {type(value).__name__}")


class CTypeTranslator:
    INT_TYPES = {
        "u8": CTInt(False, 1),
        "i8": CTInt(True, 1),
        "u16": CTInt(False, 2),
        "i16": CTInt(True, 2),
        "u32": CTInt(False, 4),
        "i32": CTInt(True, 4),
        "u64": CTInt(False, 8),
        "i64": CTInt(True, 8),
    }

    FLOAT_TYPES = {
        "f32": CTFloat(4),
        "f64": CTFloat(8),
    }

    TYPES = {
        **INT_TYPES,
        **FLOAT_TYPES,
        "bool": CTInt(False, 1),
        "None": CTVoid(),
        "str": CTString(),
    }

    @classmethod
    def translate(cls, type_name: str) -> CType:
        try:
            return cls.TYPES[type_name]
        except KeyError:
            raise Exception(f"Unsupported C translation for type: {type_name}")


class C_Gen:
    def __init__(self, LIRs, module_name=None):
        self.LIRs = LIRs
        self.c_nodes = []

    def name_maper(self, name):
        if name[0] == "%":
            name = "v" + name[1:]
        return name

    def process_FunctionLIR(self, lir):
        name = lir.name
        args = lir.args
        body = lir.body
        return_type = CTypeTranslator.translate(lir.type)

        args_nodes = []
        for arg in args:
            args_nodes.append(CVariable(arg.name))

        body_nodes = []
        for b in body:
            body_nodes.append(self.process(b))

        return CFunction(name, name, args_nodes, body_nodes, return_type)

    def process_ConstLIR(self, lir):
        lir_name = self.name_maper(lir.name)

        val = CExprTranslator.translate(lir.value)

        type = CTypeTranslator.translate(lir.type)
        return CAssign(lir_name, val, type)

    def process_AddLIR(self, lir):
        name = self.name_maper(lir.name)
        type = CTypeTranslator.translate(lir.type)
        left = lir.left_id
        right = lir.right_id

        left_val = self.name_maper(left)
        left = CVariable(left_val)
        right_val = self.name_maper(right)
        right = CVariable(right_val)

        bin_op = CBinaryOp(left, right, "+")

        return CAssign(name, bin_op, type)

    def process_StoreLIR(self, lir):
        name = lir.name
        type = CTypeTranslator.translate(lir.type)
        val_name = self.name_maper(lir.value)
        value = CVariable(val_name)
        return CAssign(name, value, type)

    def process_ReturnLIR(self, lir):
        value = lir.value
        if value is None:
            return CReturn(CNone())

        val_name = self.name_maper(value)
        value = CVariable(val_name)
        return CReturn(value)

    def process(self, lir):
        name = lir.__class__.__name__
        func = getattr(self, f"process_{name}", None)
        if func is None:
            raise Exception(f"No function named {name}")

        return func(lir)

    def get_code_string(self):
        includes = ["#include <Nida_core.h>"]
        for include in EXTRA_C_INCLUDES:
            includes.append(f"#include {include}")
        includes_str = "\n".join(includes)

        c_code = includes_str + "\n"
        for idx, c_node in enumerate(self.c_nodes):
            if idx == 0:
                c_code += "\n" + c_node.str()
            else:
                c_code += ";\n" + c_node.str()

        return c_code

    def gen_from_list(self, lirs):
        for lir in lirs:
            res = self.process(lir)
            if res is not None:
                self.c_nodes.append(res)

        return self.get_code_string()
