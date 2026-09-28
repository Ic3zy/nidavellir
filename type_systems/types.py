class Type:
    pass


class DynamicType(Type):
    pass


class BoolType(Type):
    pass


class IntType(Type):
    def __init__(self, signed=False, byte_size=DynamicType):
        self.signed = signed
        self.byte_size = byte_size
        self.is_dynamic = byte_size == DynamicType


class FloatType(Type):
    def __init__(self, byte_size=DynamicType):
        self.byte_size = byte_size
        self.is_dynamic = byte_size == DynamicType


class StringType(Type):
    def __init__(self):
        pass


class ArrayType(Type):
    def __init__(self, element_type, size=DynamicType):
        self.element_type = element_type
        self.size = size
        self.is_dynamic = size == DynamicType
