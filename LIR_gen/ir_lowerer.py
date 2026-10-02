from IR_gen.irs import *
from .lirs import *


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
        self.lir = []

        self.value_id = Value_Id()

        self.run()

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

    def process_NumberIR(self, hir):
        const_id = self.get_value_id()
        type = hir.type

        type_str = str(type)

        return ConstLIR(const_id, type_str, hir.value)

    def process_ReturnIR(self, hir):
        lirs = []
        val = hir.value
        if val is None:
            return ReturnLIR(None)

        val_lirs = self.process(val)
        ret_lir = ReturnLIR(self.get_current_value_id())

        lirs.append(val_lirs)
        lirs.append(ret_lir)

        return lirs

    def process_AssignIR(self, hir):
        lirs = []

        target = hir.target
        value = hir.value
        type = hir.val_type

        type_str = str(type)

        value_lirs = self.process(value)
        if isinstance(value_lirs, list):
            lirs.extend(value_lirs)
        else:
            lirs.append(value_lirs)

        const_id = self.get_current_value_id()

        lirs.append(StoreLIR(target, type_str, const_id))
        return lirs

    def process_FunctionIR(self, hir):
        name = hir.name
        args = hir.args
        body = hir.body_irs
        body_lir = []
        for hir in body:
            res = self.process(hir)
            if res is not None:
                body_lir.append(res)

        return FunctionLIR(name, args, body_lir)

    def process(self, hir):
        name = hir.__class__.__name__
        func = getattr(self, f"process_{name}", None)
        if func is None:
            raise Exception(f"No process function for {name}")

        return func(hir)

    def process_from_list(self, hirs):
        lirs = []
        for hir in hirs:
            res = self.process(hir)
            if res is not None:
                if isinstance(res, list):
                    lirs.extend(res)
                else:
                    lirs.append(res)

        return lirs

    def run(self):
        lirs = self.process_from_list(self.hir)
        self.lir = lirs

        raise Exception(self.lir)

        return self.lir
