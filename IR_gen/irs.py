class IR:
    def tree_repr(self, indent="", is_last=True):
        if self.__class__.__name__ == "VariableIR":
            return f"{indent}{'└── ' if is_last else '├── '}VariableIR({repr(getattr(self, 'name', ''))})"
        if self.__class__.__name__ == "NumberIR":
            return f"{indent}{'└── ' if is_last else '├── '}NumberIR({repr(getattr(self, 'value', ''))})"

        marker = "└── " if is_last else "├── "
        lines = [f"{indent}{marker}{self.__class__.__name__}"]

        children = []
        for k, v in self.__dict__.items():
            if k in ("decs", "val_type", "body") and not v:
                continue
            if k == "body":
                continue
            children.append((k, v))

        child_indent = indent + ("    " if is_last else "│   ")

        for i, (key, val) in enumerate(children):
            is_last_child = i == len(children) - 1
            c_marker = "└── " if is_last_child else "├── "

            if isinstance(val, IR):
                lines.append(f"{child_indent}{c_marker}{key}:")
                lines.append(
                    val.tree_repr(
                        indent=child_indent + ("    " if is_last_child else "│   "),
                        is_last=True,
                    )
                )
            elif isinstance(val, list):
                if not val:
                    lines.append(f"{child_indent}{c_marker}{key}: []")
                    continue
                lines.append(f"{child_indent}{c_marker}{key}:")
                list_indent = child_indent + ("    " if is_last_child else "│   ")
                for j, item in enumerate(val):
                    is_last_item = j == len(val) - 1
                    if isinstance(item, IR):
                        lines.append(
                            item.tree_repr(indent=list_indent, is_last=is_last_item)
                        )
                    else:
                        item_marker = "└── " if is_last_item else "├── "
                        lines.append(f"{list_indent}{item_marker}{repr(item)}")
            else:
                lines.append(f"{child_indent}{c_marker}{key}: {repr(val)}")

        return "\n".join(lines)

    def __repr__(self):
        return self.tree_repr()


class AssignIR(IR):
    def __init__(self, target, value, type=None):
        self.target = target
        self.value = value
        self.val_type = type


class FunctionIR(IR):
    def __init__(self, decs, name, args, body, return_type=None, is_main_func=False):
        self.decs = decs
        self.name = name
        self.args = args
        self.body = body
        self.return_type = return_type

        self.is_main_func = is_main_func

        self.body_irs = []


class ReturnIR(IR):
    def __init__(self, value, val_type=None):
        self.value = value
        self.val_type = None


class BinaryOpIR(IR):
    def __init__(self, left, right, op):
        self.left = left
        self.right = right
        self.op = op


class VariableIR(IR):
    def __init__(self, name):
        self.name = name


class CallIR(IR):
    def __init__(self, target, args):
        self.target = target
        self.args = args
        self.val_type = None


class NumberIR(IR):
    def __init__(self, value):
        self.value = value
        self.val_type = None


class ClassIR(IR):
    def __init__(self, name, body):
        self.name = name
        self.body = body


class StringLiteralIR(IR):
    def __init__(self, value):
        self.value = value


class IRImport:
    def __init__(
        self,
        module: str,
        symbols: list[str] = None,
        alias: str = None,
    ):
        self.module = module
        self.symbols = symbols or []
        self.alias = alias
