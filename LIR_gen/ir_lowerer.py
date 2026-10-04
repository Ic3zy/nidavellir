from IR_gen.irs import *
from .lirs import *
from type_systems.types import *


class LIRs(list):
    def __init__(self, *args):
        super().__init__()

        for arg in args:
            self.append(arg)

    def append(self, item):
        if isinstance(item, list):
            super().extend(item)
        else:
            super().append(item)


class Value_Id:
    def __init__(self, parrent=None):
        self.value = -1
        self.parrent = parrent

    def new(self):
        self.value += 1
        return self.value

    def current(self):
        return self.value


class IRLowerer:
    def __init__(self, hirs):
        self.hir = hirs
        self.lir = LIRs()

        self.value_id = Value_Id()

    def enter_new_value_scope(self):
        parrent = (
            self.value_id if self.value_id.parrent is None else self.value_id.parrent
        )
        self.value_id = Value_Id(parrent)

    def exit_value_scope(self):
        if self.value_id.parrent is None:
            raise Exception("No parent value scope")

        self.value_id = self.value_id.parrent

    def get_value_id(self):
        id = self.value_id.new()
        return f"%{id}"

    def get_current_value_id(self):
        return f"%{self.value_id.current()}"

    def process_VariableIR(self, hir):
        name = hir.name
        type_str = str(hir.type)

        const_id = self.get_value_id()
        lirs = LIRs()
        lirs.append(LoadLIR(const_id, name, type_str))

        return lirs

    def process_NumberIR(self, hir):
        val = hir.value
        if val is not None and isinstance(val, str):
            val = int(val)

        const_id = self.get_value_id()
        type = hir.type

        type_str = str(type)

        return ConstLIR(const_id, type_str, val)

    def process_ReturnIR(self, hir):
        lirs = LIRs()
        val = hir.value
        if val is None:
            return ReturnLIR(None)

        val_lirs = self.process(val)
        ret_lir = ReturnLIR(self.get_current_value_id())

        lirs.append(val_lirs)
        lirs.append(ret_lir)

        return lirs

    def process_AssignIR(self, hir):
        lirs = LIRs()

        target = hir.target
        value = hir.value
        type = hir.type
        type_str = str(type)

        value_lirs = self.process(value)
        lirs.append(value_lirs)

        const_id = self.get_current_value_id()

        lirs.append(StoreLIR(target, type_str, const_id))
        return lirs

    def process_FunctionIR(self, hir):
        name = hir.name
        args = hir.args
        type = hir.type
        type_str = str(type)
        body = hir.body_irs
        body_lir = LIRs()
        for hir in body:
            res = self.process(hir)
            if res is not None:
                body_lir.append(res)

        return FunctionLIR(name, args, type_str, body_lir)

    def process_IntrinsicIR(self, hir):
        return self.process_CallIR(hir)

    def process_GroupIR(self, hir):
        return self.process(hir.expr)

    def process_CallIR(self, hir):
        is_not_return = isinstance(hir.type, NoneType) or hir.type is None

        type = str(hir.type)
        target = hir.target
        args = hir.args

        lirs = LIRs()
        arg_ids = []

        for arg in args:
            lir = self.process(arg)

            lirs.append(lir)
            arg_ids.append(self.get_current_value_id())

        if is_not_return:
            nonetype = str(NoneType())
            const_lir = ConstLIR(self.get_value_id(), nonetype, None)
            lirs.append(const_lir)

            call_lir = CallLIR(None, type, target, arg_ids)
        else:
            call_lir = CallLIR(self.get_value_id(), type, target, arg_ids)

        lirs.append(call_lir)

        return lirs

    def _op_to_lir(self, type, left_id, right_id, op):
        match op:
            case "+":
                return AddLIR(self.get_value_id(), type, left_id, right_id)
            case "-":
                return SubLIR(self.get_value_id(), type, left_id, right_id)
            case "*":
                return MulLIR(self.get_value_id(), type, left_id, right_id)
            case "/":
                return DivLIR(self.get_value_id(), type, left_id, right_id)
            case "%":
                return ModLIR(self.get_value_id(), type, left_id, right_id)
            case _:
                raise Exception(f"No LIR for op {op}")

    def process_BinaryOpIR(self, hir):
        left = hir.left
        right = hir.right
        type = str(hir.type)
        op = hir.op

        lirs = LIRs()

        left_lir = self.process(left)
        left_id = self.get_current_value_id()
        right_lir = self.process(right)
        right_id = self.get_current_value_id()

        lirs.append(left_lir)
        lirs.append(right_lir)

        op_lir = self._op_to_lir(type, left_id, right_id, op)
        lirs.append(op_lir)
        return lirs

    def process_BooleanIR(self, hir):
        value = hir.value
        if value:
            return ConstLIR(self.get_value_id(), "bool", 1)
        else:
            return ConstLIR(self.get_value_id(), "bool", 0)

    def process_BlockIR(self, hir):
        lirs = self.process_from_list(hir.body)
        return lirs

    def process(self, hir):
        name = hir.__class__.__name__
        func = getattr(self, f"process_{name}", None)
        if func is None:
            raise Exception(f"No process function for {name}")

        return func(hir)

    def process_from_list(self, hirs):
        lirs = LIRs()
        for hir in hirs:
            res = self.process(hir)
            if res is not None:
                lirs.append(res)

        return lirs

    def run(self):
        lirs = self.process_from_list(self.hir)
        self.lir = lirs

        print(self.lir)

        return self.lir
