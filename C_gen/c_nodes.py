class CNode:
    def str(self):
        raise NotImplementedError


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

        return f"{self.val_type if not self.re_assign else ''} {self.target} {"=" if val_str else ""} {val_str}"


class CNumber(CNode):
    def __init__(self, value):
        self.value = value

    def str(self):
        return f"{self.value}"


class CCall(CNode):
    def __init__(self, target, args):
        self.target = target
        self.args = args

    def str(self):
        args_str = ""

        args_count = len(self.args)
        for c_a in range(args_count):
            a = self.args[c_a]
            is_last = c_a == args_count - 1
            args_str += f"{a.str()}, " if not is_last else f"{a.str()}"

        return f"{self.target}({args_str})"


class CFunction(CNode):
    def __init__(self, name, c_name, args, body, return_type):
        self.name = name
        self.c_name = c_name
        self.args = args
        self.body = body
        self.return_type = return_type

    def str(self):
        body = []
        for b in self.body:
            body.append(b.str())
            body.append(";\n")

        body_str = "".join(body)

        args = []
        c = 0
        for a in self.args:
            args.append(a.str())
            if c < len(self.args) - 1:
                args.append(", ")
            c += 1

        args_str = "".join(args)

        return f"{self.return_type} {self.c_name}({args_str}) {{\n{body_str}}}"


class CReturn(CNode):
    def __init__(self, value):
        self.value = value

    def str(self):
        return f"return {self.value.str()}"


class CImport(CNode):
    def __init__(self, module):
        self.module = module

    def str(self):
        return f"#include <{self.module}.h>"


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
        elif op == "or":
            return "||"
        else:
            return op

    def str(self):
        formatted_op = self.format_op(self.op)
        if formatted_op == "is":
            return f"((void*)({self.left.str()}) == (void*)({self.right.str()}))"
        elif formatted_op == "is not":
            return f"((void*)({self.left.str()}) != (void*)({self.right.str()}))"
        else:
            return f"{self.left.str()} {self.format_op(self.op)} {self.right.str()}"


class CElif(CNode):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

    def str(self):
        body = []
        for b in self.body:
            body.append(b.str())
            body.append(";\n")

        body_str = "".join(body)
        return f"else if ({self.cond.str()}) {{\n{body_str}}}"


class CIf(CNode):
    def __init__(self, cond, body, elifs, else_body):
        self.cond = cond
        self.body = body
        self.elifs = elifs
        self.else_body = else_body

    def str(self):
        body_str = "".join(
            f"{b.str()};\n" if not b.str().endswith(";") else f"{b.str()}\n"
            for b in self.body
        )

        else_body_str = "".join(
            f"{b.str()};\n" if not b.str().endswith(";") else f"{b.str()}\n"
            for b in self.else_body
        )

        elifs_str = "\n".join(e.str() for e in self.elifs)

        parts = [f"if ({self.cond.str()}) {{\n{body_str}}}"]

        if self.elifs:
            parts.append(elifs_str)

        if self.else_body:
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
        result = []
        total = len(self.body)
        for i, stmt in enumerate(self.body):
            stmt_str = stmt.str()
            if i < total - 1:
                result.append(f"{stmt_str};\n")
            else:
                result.append(stmt_str)
        return "".join(result)


class CFor(CNode):
    def __init__(self, target, range, body):
        self.target = target
        self.range = range
        self.body = body

    def str(self):
        body_str = "".join(b.str() + ";\n" for b in self.body)
        fr = f"for (int {self.target} = 0; {self.target} < {self.range}; {self.target}++) {{\n{body_str}}}"
        return fr


class CWhile(CNode):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

    def str(self):
        body_str = "".join(b.str() + ";\n" for b in self.body)
        fr = f"while ({self.cond.str()}) {{\n{body_str}}}"
        return fr


class CBoolean(CNode):
    def __init__(self, value):
        self.value = value

    def str(self):
        if self.value is True:
            return "true"
        else:
            return "false"


class CNone(CNode):
    def __init__(self, is_str=True):
        self.is_str = is_str

    def str(self):
        if self.is_str:
            return "Nida_None"
        else:
            return ""
