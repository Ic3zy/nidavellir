class LIR:
    def _format_item(self, item, indent=0):
        if isinstance(item, LIR):
            return item._format(indent)
        elif isinstance(item, list):
            return "\n".join([self._format_item(i, indent + 1) for i in item])
        else:
            return repr(item)

    def _format(self, indent=0):
        indent_str = ("  ") * (indent + 1)
        indent_str_parent = ("  ") * indent

        lines = []

        class_args = self.__dict__.items()
        class_name = self.__class__.__name__
        lines.append(f"{indent_str_parent}{class_name}:")

        for key, value in class_args:
            field_prefix = f"{key}: {self._format_item(value, indent + 1)}"
            lines.append(f"{indent_str}{field_prefix}")

        return "\n" + "\n".join(lines) + "\n"

    def __repr__(self):
        return self._format()


class ConstLIR(LIR):
    def __init__(self, name, type, value):
        self.name = name
        self.type = type
        self.value = value


class StoreLIR(LIR):
    def __init__(self, name, type, value):
        self.name = name
        self.type = type
        self.value = value


class LoadLIR(LIR):
    def __init__(self, name, type):
        self.name = name
        self.type = type


class FunctionLIR(LIR):
    def __init__(self, name, args, body):
        self.name = name
        self.args = args
        self.body = body


class ReturnLIR(LIR):
    def __init__(self, value):
        self.value = value
