from .types import *


def type_lowering(type_str: str):
    match type_str:
        case "bool":
            return BoolType()

        case "u8":
            return IntType(signed=False, byte_size=1)
        case "i8":
            return IntType(signed=True, byte_size=1)
        case "u16":
            return IntType(signed=False, byte_size=2)
        case "i16":
            return IntType(signed=True, byte_size=2)
        case "u32":
            return IntType(signed=False, byte_size=4)
        case "i32":
            return IntType(signed=True, byte_size=4)
        case "u64":
            return IntType(signed=False, byte_size=8)
        case "i64":
            return IntType(signed=True, byte_size=8)
        case "i128":
            return IntType(signed=True, byte_size=16)
        case "u128":
            return IntType(signed=False, byte_size=16)
        case "dynamic_int":
            return IntType()

        case "f32":
            return FloatType(byte_size=4)
        case "f64":
            return FloatType(byte_size=8)

        case "str":
            return StringType()

        case _:
            raise SyntaxError(f"Invalid type {type_str}")


class TypeLowering:
    def __init__(self, ast_tree):
        self.ast_tree = ast_tree

    def default_pass(self, ast):
        pass

    def process_FunctionAST(self, ast):
        return_type = ast.type
        if return_type is None:
            raise SyntaxError(f"Cannot infer type of {ast.name}")

        ast.type = type_lowering(return_type)

        for arg in ast.args:
            self.process(arg)

    def process_AssignAST(self, ast):
        type = ast.type_annotation
        if type is None:
            raise SyntaxError(f"Cannot infer type of {ast.name}")

        ast.type_annotation = type_lowering(type)

    def process(self, ast):
        method_name = f"process_{type(ast).__name__}"
        visitor = getattr(self, method_name, None) or self.default_pass

        return visitor(ast)

    def run(self):
        for node in self.ast_tree:
            self.process(node)

        # raise Exception(self.ast_tree)
