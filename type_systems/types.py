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

    def __init__(self, signed=False, byte_size=DynamicType):
        self.signed = signed
        self.byte_size = byte_size
        self.is_dynamic = byte_size == DynamicType

    def __str__(self):
        if self.is_dynamic:
            return "dyn_int"

        prefix = "i" if self.signed else "u"
        return f"{prefix}{self.byte_size * 8}"


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
