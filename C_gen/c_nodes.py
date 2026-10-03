class CNode:
    def str(self):
        raise NotImplementedError

    def _format_item(self, item, indent=0):
        if isinstance(item, CNode):
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


class CAssign(CNode):
    def __init__(self, target, value, val_type, re_assign=False):
        self.target = target
        self.value = value
        self.re_assign = re_assign
        self.val_type = val_type

    def str(self):
        if isinstance(self.value, CNone) and not self.value.is_str:
            val_str = ""
        else:
            val_str = self.value.str()

        type_prefix = f"{self.val_type.str()} " if not self.re_assign else ""
        eq_sign = " = " if val_str else ""
        return f"{type_prefix}{self.target}{eq_sign}{val_str}".strip()


class CNumber(CNode):
    def __init__(self, value):
        self.value = value

    def str(self):
        return str(self.value)


class CCall(CNode):
    def __init__(self, target, args):
        self.target = target
        self.args = args

    def str(self):
        args_str = ", ".join(a.str() for a in self.args)
        return f"{self.target}({args_str})"


class CFunction(CNode):
    def __init__(self, name, c_name, args, body, return_type):
        self.name = name
        self.c_name = c_name
        self.args = args
        self.body = body
        self.return_type = return_type

    def str(self):
        body_str = "".join(f"{b.str()};\n" for b in self.body)
        args_str = ", ".join(a.str() for a in self.args)
        return f"{self.return_type.str()} {self.c_name}({args_str}) {{\n{body_str}}}"


class CReturn(CNode):
    def __init__(self, value):
        self.value = value

    def str(self):
        return f"return {self.value.str()}"


class CImport(CNode):
    def __init__(self, module):
        self.module = module

    def str(self):
        return f'#include "{self.module}.h"'


class CString(CNode):
    def __init__(self, value):
        self.value = value

    def str(self):
        return f'"{self.value}"'


class CVariable(CNode):
    def __init__(self, name):
        self.name = name

    def str(self):
        return self.name


class CBinaryOp(CNode):
    def __init__(self, left, right, op):
        self.left = left
        self.right = right
        self.op = op

    def format_op(self, op):
        if op == "and":
            return "&&"
        if op == "or":
            return "||"
        return op

    def str(self):
        formatted_op = self.format_op(self.op)
        left_str = self.left.str()
        right_str = self.right.str()

        if formatted_op == "is":
            return f"((void*)({left_str}) == (void*)({right_str}))"
        if formatted_op == "is not":
            return f"((void*)({left_str}) != (void*)({right_str}))"

        return f"{left_str} {formatted_op} {right_str}"


class CElif(CNode):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

    def str(self):
        body_str = "".join(f"{b.str()};\n" for b in self.body)
        return f"else if ({self.cond.str()}) {{\n{body_str}}}"


class CIf(CNode):
    def __init__(self, cond, body, elifs, else_body):
        self.cond = cond
        self.body = body
        self.elifs = elifs
        self.else_body = else_body

    def str(self):
        def format_stmt(stmt):
            s = stmt.str()
            return f"{s}\n" if s.endswith(";") else f"{s};\n"

        body_str = "".join(format_stmt(b) for b in self.body)
        parts = [f"if ({self.cond.str()}) {{\n{body_str}}}"]

        if self.elifs:
            parts.append("\n".join(e.str() for e in self.elifs))

        if self.else_body:
            else_body_str = "".join(format_stmt(b) for b in self.else_body)
            parts.append(f"else {{\n{else_body_str}}}")

        return "\n".join(parts)


class CGroup(CNode):
    def __init__(self, expr):
        self.expr = expr

    def str(self):
        return f"({self.expr.str()})"


class CBlock(CNode):
    def __init__(self, body):
        self.body = body

    def str(self):
        total = len(self.body)
        return "".join(
            f"{stmt.str()};\n" if i < total - 1 else stmt.str()
            for i, stmt in enumerate(self.body)
        )


class CFor(CNode):
    def __init__(self, target, range, body):
        self.target = target
        self.range = range
        self.body = body

    def str(self):
        body_str = "".join(f"{b.str()};\n" for b in self.body)
        return f"for (int {self.target} = 0; {self.target} < {self.range}; {self.target}++) {{\n{body_str}}}"


class CWhile(CNode):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

    def str(self):
        body_str = "".join(f"{b.str()};\n" for b in self.body)
        return f"while ({self.cond.str()}) {{\n{body_str}}}"


class CBoolean(CNode):
    def __init__(self, value):
        self.value = value

    def str(self):
        return "true" if self.value else "false"


class CNone(CNode):
    def __init__(self, is_str=True):
        self.is_str = is_str

    def str(self):
        return "Nida_None" if self.is_str else ""
