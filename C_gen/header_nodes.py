class HeaderNode:
    pass


class Hifndef(HeaderNode):
    def __init__(self, name):
        self.name = name

    def name_map(self):
        return f"NIDAVELLIR_{self.name.upper()}_H"

    def str(self):
        self.name = self.name_map()
        return f"#ifndef {self.name}\n#define {self.name}"


class Hendif(HeaderNode):
    def __init__(self):
        pass

    def str(self):
        return "#endif"


class HImport(HeaderNode):
    def __init__(self, file_name, is_system=False):
        self.file_name = file_name
        self.is_system = is_system

    def str(self):
        return f"#include <{self.file_name}>"


class HFunction(HeaderNode):
    def __init__(self, name, args, return_type):
        self.name = name
        self.args = args
        self.return_type = return_type

    def str(self):
        args_str = ""
        for a in self.args:
            args_str += f"{a.str()}, "

        return f"{self.return_type} {self.name}({args_str})"
