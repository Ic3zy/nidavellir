TYPE_RANK = {
    "bool": 0,
    "u8": 1,
    "i8": 2,
    "u16": 3,
    "i16": 4,
    "u32": 5,
    "i32": 6,
    "u64": 7,
    "i64": 8,
    "f32": 9,
    "f64": 10,
    "dyn_int": 11,
}


def get_type_rank(target_type) -> int:
    return TYPE_RANK.get(str(target_type), -1)


def resolve_type(type_val):
    if type_val is None or isinstance(type_val, Type):
        return type_val

    if isinstance(type_val, str):
        match type_val:
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
            case "dyn_int":
                return IntType(signed=True)
            case "f32":
                return FloatType(byte_size=4)
            case "f64":
                return FloatType(byte_size=8)
            case "dyn_float":
                return FloatType()
            case "str":
                return StringType()
            case "None" | "void":
                return NoneType()
            case "dynamic":
                return DynamicType()
            case _:
                return type_val

    return type_val


class Infinity:
    def __repr__(self):
        return "∞ (Nida_Infinity)"


class Type:
    def __str__(self):
        return self.__class__.__name__


class DynamicType(Type):
    def __str__(self):
        return "dynamic"


class BoolType(Type):
    def __str__(self):
        return "bool"


class IntType(Type):
    I64_MIN, I64_MAX = -9_223_372_036_854_775_808, 9_223_372_036_854_775_807
    U64_MAX = 18_446_744_073_709_551_615

    def __init__(
        self,
        arg1=None,
        arg2=None,
        signed=True,
        byte_size=DynamicType,
        min_val=None,
        max_val=None,
    ):
        if isinstance(arg1, int) and isinstance(arg2, int):
            self.min_val = arg1
            self.max_val = arg2
            self.signed, self.byte_size = self._infer_bounds(arg1, arg2)
        elif min_val is not None and max_val is not None:
            self.min_val = min_val
            self.max_val = max_val
            self.signed, self.byte_size = self._infer_bounds(min_val, max_val)
        else:
            self.min_val = min_val
            self.max_val = max_val
            self.signed = arg1 if (arg1 is not None and not isinstance(arg1, int)) else signed
            self.byte_size = arg2 if (arg2 is not None and not isinstance(arg2, int)) else byte_size

        self.is_dynamic = (
            self.byte_size == DynamicType
            or self.byte_size == Infinity
            or self.byte_size is None
        )

    @property
    def rank(self) -> int:
        return TYPE_RANK.get(str(self), -1)

    @staticmethod
    def _infer_bounds(min_val: int, max_val: int):
        if min_val >= 0:
            if max_val <= 255:
                return False, 1
            if max_val <= 65_535:
                return False, 2
            if max_val <= 4_294_967_295:
                return False, 4
            if max_val <= IntType.U64_MAX:
                return False, 8
        else:
            if min_val >= -128 and max_val <= 127:
                return True, 1
            if min_val >= -32_768 and max_val <= 32_767:
                return True, 2
            if min_val >= -2_147_483_648 and max_val <= 2_147_483_647:
                return True, 4
            if min_val >= IntType.I64_MIN and max_val <= IntType.I64_MAX:
                return True, 8

        return True, Infinity

    def __str__(self):
        if self.is_dynamic:
            return "dyn_int"

        prefix = "i" if self.signed else "u"
        return f"{prefix}{self.byte_size * 8}"

    def __eq__(self, other):
        if isinstance(other, IntType):
            return self.signed == other.signed and self.byte_size == other.byte_size
        if isinstance(other, str):
            return str(self) == other
        return False

    def __hash__(self):
        return hash((self.signed, self.byte_size))


class FloatType(Type):
    def __init__(self, byte_size=DynamicType):
        self.byte_size = byte_size
        self.is_dynamic = byte_size == DynamicType

    def __str__(self):
        if self.is_dynamic:
            return "dyn_float"

        return f"f{self.byte_size * 8}"


class StringType(Type):
    def __init__(self):
        pass

    def __str__(self):
        return "str"


class ArrayType(Type):
    def __init__(self, element_type, size=DynamicType):
        self.element_type = element_type
        self.size = size
        self.is_dynamic = size == DynamicType

    def __str__(self):
        if self.is_dynamic:
            return f"{self.element_type}[]"

        return f"{self.element_type}[{self.size}]"


class NoneType(Type):
    def __str__(self):
        return "None"
