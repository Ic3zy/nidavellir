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
        return f"{self.val_type if not self.re_assign else ''} {self.target} = {self.value.str()}"


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
        return f"{self.target}({self.args})"


class CFunction(CNode):
    def __init__(self, name, args, body, return_type):
        self.name = name
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
        for a in self.args:
            args.append(a.str())
            args.append(", ")

        args_str = "".join(args)

        return f"{self.return_type} {self.name}({args_str}) {{\n{body_str}}}"


class CReturn(CNode):
    def __init__(self, value):
        self.value = value

    def str(self):
        return f"return {self.value.str()}"
