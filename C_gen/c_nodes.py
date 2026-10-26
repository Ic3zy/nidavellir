from .c_types import CTFuncRef


class CNode:
    def __str__(self):
        raise NotImplementedError

    def str(self):
        return str(self)

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
    def __init__(self, target, value, type, re_assign=False):
        self.target = target
        self.value = value
        self.re_assign = re_assign
        self.type = type

    def __str__(self):
        if isinstance(self.value, CNone) and not self.value.is_str:
            val_str = ""
        else:
            val_str = str(self.value)

        if self.re_assign:
            eq_sign = " = " if val_str else ""
            return f"{self.target}{eq_sign}{val_str}".strip()

        if isinstance(self.type, CTFuncRef):
            declaration = self.type.declare(self.target)
            eq_sign = " = " if val_str else ""
            return f"{declaration}{eq_sign}{val_str}".strip()

        type_prefix = f"{self.type} "
        eq_sign = " = " if val_str else ""
        return f"{type_prefix}{self.target}{eq_sign}{val_str}".strip()


class CNumber(CNode):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class CCall(CNode):
    def __init__(self, target, args):
        self.target = target
        self.args = args

    def __str__(self):
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.target}({args_str})"


class CFunction(CNode):
    def __init__(self, name, c_name, args, body, type, is_static):
        self.name = name
        self.c_name = c_name
        self.args = args
        self.body = body
        self.type = type
        self.is_static = is_static

    def __str__(self):
        body_str = "".join(
            f"{str(b)}{';' if not isinstance(b, CBlock) else ''}\n" for b in self.body
        )
        args_str = ", ".join(str(a) for a in self.args)
        static_str = "static " if self.is_static else ""

        return (
            f"{static_str}{str(self.type)} {self.c_name}({args_str}) {{\n{body_str}}}"
        )


class CReturn(CNode):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return f"return {str(self.value)}"


class CImport(CNode):
    def __init__(self, module):
        self.module = module

    def __str__(self):
        return f'#include "{self.module}.h"'


class CString(CNode):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return f'"{self.value}"'


class CVariable(CNode):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


class CArg(CNode):
    def __init__(self, name, type):
        self.name = name
        self.type = type

    def __str__(self):
        return f"{self.type} {self.name}"


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

    def __str__(self):
        formatted_op = self.format_op(self.op)
        left_str = str(self.left)
        right_str = str(self.right)

        if formatted_op == "is":
            return f"((void*)({left_str}) == (void*)({right_str}))"
        if formatted_op == "is not":
            return f"((void*)({left_str}) != (void*)({right_str}))"

        return f"{left_str} {formatted_op} {right_str}"


class CElif(CNode):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

    def __str__(self):
        body_str = "".join(f"{str(b)};\n" for b in self.body)
        return f"else if ({str(self.cond)}) {{\n{body_str}}}"


class CIf(CNode):
    def __init__(self, cond, body, elifs, else_body):
        self.cond = cond
        self.body = body
        self.elifs = elifs
        self.else_body = else_body

    def __str__(self):
        def format_stmt(stmt):
            s = str(stmt)
            return f"{s}\n" if s.endswith(";") else f"{s};\n"

        body_str = "".join(format_stmt(b) for b in self.body)
        parts = [f"if ({str(self.cond)}) {{\n{body_str}}}"]

        if self.elifs:
            parts.append("\n".join(str(e) for e in self.elifs))

        if self.else_body:
            else_body_str = "".join(format_stmt(b) for b in self.else_body)
            parts.append(f"else {{\n{else_body_str}}}")

        return "\n".join(parts)


class CGroup(CNode):
    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return f"({str(self.expr)})"


class CBlock(CNode):
    def __init__(self, body):
        self.body = body

    def __str__(self):
        total = len(self.body)
        return "".join(
            f"{str(stmt)};\n" if i < total - 1 else str(stmt)
            for i, stmt in enumerate(self.body)
        )


class CFor(CNode):
    def __init__(self, target, range, body):
        self.target = target
        self.range = range
        self.body = body

    def __str__(self):
        body_str = "".join(f"{str(b)};\n" for b in self.body)
        return f"for (int {self.target} = 0; {self.target} < {self.range}; {self.target}++) {{\n{body_str}}}"


class CWhile(CNode):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

    def __str__(self):
        body_str = "".join(f"{str(b)};\n" for b in self.body)
        return f"while ({str(self.cond)}) {{\n{body_str}}}"


class CBoolean(CNode):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "true" if self.value else "false"


class CNone(CNode):
    def __init__(self, is_str=True):
        self.is_str = is_str

    def __str__(self):
        return "Nida_None" if self.is_str else ""


class CBlock(CNode):
    def __init__(self, name, body):
        self.name = name
        self.body = body

    def __str__(self):
        body_str = "".join(f"{str(b)};\n" for b in self.body)
        return f"{self.name}:\n{body_str}"


class CGoto(CNode):
    def __init__(self, block):
        self.block = block

    def __str__(self):
        return f"goto {self.block}"


class CGlobal(CNode):
    def __init__(self, name, type, initializer):
        self.name = name
        self.type = type
        self.initializer = initializer

    def __str__(self):
        return f"{self.type} {self.name}"


class CStruct(CNode):
    """A C struct definition."""

    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

    def __str__(self):
        field_str = "".join(f"    {str(f)};\n" for f in self.fields)
        return f"typedef struct {{\n{field_str}}} {self.name}"


class CFieldDecl(CNode):
    def __init__(self, name, type):
        self.name = name
        self.type = type

    def __str__(self):
        return f"{self.type} {self.name}"


class CFieldAccess(CNode):
    def __init__(self, target, field):
        self.target = target
        self.field = field

    def __str__(self):
        return f"{self.target}->{self.field}"


class CFieldStore(CNode):
    def __init__(self, target, field, value):
        self.target = target
        self.field = field
        self.value = value

    def __str__(self):
        return f"{self.target}->{self.field} = {self.value}"


class CNew(CNode):
    def __init__(self, class_name):
        self.class_name = class_name

    def __str__(self):
        return f"({self.class_name} *)calloc(1, sizeof({self.class_name}))"


class CUnaryOp(CNode):
    def __init__(self, name, op, value, type=None):
        self.name = name
        self.op = op
        self.value = value
        self.type = type

    def __str__(self):
        return f"{self.type} {self.name} = {self.op}{self.value}"


class CCast:
    def __init__(self, target_type, value):
        self.target_type = target_type
        self.value = value

    def __str__(self):
        return f"({self.target_type.str()}){self.value.str()}"
