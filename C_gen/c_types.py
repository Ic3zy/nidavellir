from .extra_c_includes import EXTRA_C_INCLUDES


class CType:
    pass


class CTVoid(CType):
    def str(self):
        return "void"


class CTInt(CType):
    def __init__(self, signed=False, byte_size=None):
        self.signed = signed
        self.byte_size = byte_size

    def str(self):
        if self.byte_size is None:
            return "int"

        if "<stdint.h>" not in EXTRA_C_INCLUDES:
            EXTRA_C_INCLUDES.append("<stdint.h>")

        int_str = "uint" if not self.signed else "int"

        if self.byte_size == 1:
            return f"{int_str}8_t"
        elif self.byte_size == 2:
            return f"{int_str}16_t"
        elif self.byte_size == 4:
            return f"{int_str}32_t"
        elif self.byte_size == 8:
            return f"{int_str}64_t"
        else:
            raise Exception("Invalid byte size")


class CTFloat(CType):
    def __init__(self, byte_size=None):
        self.byte_size = byte_size

    def str(self):
        if self.byte_size is None:
            return "float"

        if self.byte_size == 4:
            return "float"
        elif self.byte_size == 8:
            return "double"
        else:
            raise Exception("Invalid byte size")


class CTString(CType):
    def str(self):
        return "Nida_Str"
