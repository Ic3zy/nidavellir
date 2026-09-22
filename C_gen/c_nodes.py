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
        return f"{self.val_type if not self.re_assign else ''} {self.target} = {self.value};"


class CNumber(CNode):
    def __init__(self, value):
        self.value = value

    def str(self):
        return f"{self.value}"
