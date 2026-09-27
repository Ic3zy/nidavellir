from .c_nodes import *
from .header_nodes import *


class HeaderGenerator:
    def __init__(self, header_name, c_code):
        self.header_name = header_name
        self.c_code = c_code

    def gen_CFunction(self, node):
        name = node.name
        args = node.args
        return_type = node.return_type
        return HFunction(name, args, return_type)

    def gen(self, node):
        name = node.__class__.__name__
        func = getattr(self, f"gen_{name}")
        if func is not None:
            return func(node)

    def generate_default_header_dependencies(self):
        return Hifndef(self.header_name)

    def gen_all(self):
        header_nodes = [self.generate_default_header_dependencies()]
        for c_node in self.c_code:
            res = self.gen(c_node)
            if res is not None:
                header_nodes.append(res)

        header_nodes.append(Hendif())

        return header_nodes

    def header_node_to_str(self, node):
        header_str = ""
        for n in node:
            header_str += n.str()
            if isinstance(n, HFunction):
                header_str += ";\n"

            header_str += "\n"

        return header_str

    def gen_Header(self):
        header_nodes = self.gen_all()
        header_str = self.header_node_to_str(header_nodes)
        return header_str
