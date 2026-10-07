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


class BlockBox:
    def __init__(self, block, parent=None):
        self.block = block
        self.parent = parent


class BlockManager:
    def __init__(self):
        self.blocks = []
        self.current = None
        self.block_id = Value_Id()

    def create_block(self, name=None):
        bname = name if name else f"B{self.block_id.new()}"
        block = BlockLIR(bname)
        box = BlockBox(block, self.current)
        self.blocks.append(box)
        return block

    def new_block(self, name=None):
        block = self.create_block(name)
        self.switch_to(block)
        return block

    def switch_to(self, block):
        for box in self.blocks:
            if box.block is block or box.block.name == getattr(block, "name", block):
                self.current = box
                return box
        box = BlockBox(block, self.current)
        self.blocks.append(box)
        self.current = box
        return box

    def is_terminated(self):
        return self.current is not None and self.current.block.terminator is not None

    def emit(self, lir):
        if self.current is None:
            raise Exception("No active block")

        if self.current.block.terminator is not None:
            return

        if isinstance(lir, list):
            for item in lir:
                self.emit(item)
        elif lir is not None:
            self.current.block.body.append(lir)

    def terminate(self, terminator):
        if self.current is None:
            raise Exception("No active block")

        if self.current.block.terminator is not None:
            return

        self.current.block.terminator = terminator
        self.current.block.body.append(terminator)

    def branch(self, condition, true_block, false_block=None):
        true_name = true_block.name if hasattr(true_block, "name") else true_block
        false_name = false_block.name if hasattr(false_block, "name") else false_block
        self.terminate(BranchLIR(condition, true_name, false_name))

    def jump(self, target_block):
        target_name = (
            target_block.name if hasattr(target_block, "name") else target_block
        )
        self.terminate(JumpLIR(target_name))


class IRLowerer:
    def __init__(self, hirs):
        self.hir = hirs
        self.blocks = BlockManager()
        self.value_id = Value_Id()
        self.lir = []

    def enter_new_value_scope(self):
        self.value_id = Value_Id(self.value_id)

    def exit_value_scope(self):
        if self.value_id.parrent is None:
            raise Exception("No parent value scope")

        self.value_id = self.value_id.parrent

    def get_value_id(self):
        id = self.value_id.new()
        return f"%{id}"

    def get_current_value_id(self):
        return f"%{self.value_id.current()}"

    def get_block_id(self):
        id = self.value_id.new()
        return f"B{id}"

    def get_current_block_id(self):
        return f"B{self.value_id.current()}"

    def process_StringLiteralIR(self, hir):
        lirs = LIRs()
        const_lir = ConstLIR(self.get_value_id(), "str", hir.value)
        self.blocks.emit(const_lir)
        lirs.append(const_lir)
        return lirs

    def process_VariableIR(self, hir):
        name = hir.name
        type_str = str(hir.type)

        const_id = self.get_value_id()
        lirs = LIRs()
        load_lir = LoadLIR(const_id, name, type_str)
        lirs.append(load_lir)
        self.blocks.emit(load_lir)

        return lirs

    def process_NumberIR(self, hir):
        val = hir.value
        if val is not None and isinstance(val, str):
            val = int(val)

        const_id = self.get_value_id()
        type_str = str(hir.type)
        const_lir = ConstLIR(const_id, type_str, val)
        self.blocks.emit(const_lir)

        return const_lir

    def process_ReturnIR(self, hir):
        lirs = LIRs()
        val = hir.value
        if val is None:
            ret_lir = ReturnLIR(None)
            self.blocks.terminate(ret_lir)
            return ret_lir

        val_lirs = self.process(val)
        ret_lir = ReturnLIR(self.get_current_value_id())

        lirs.append(val_lirs)
        lirs.append(ret_lir)
        self.blocks.terminate(ret_lir)

        return lirs

    def process_AssignIR(self, hir):
        lirs = LIRs()

        target = hir.target
        value = hir.value
        type_str = str(hir.type)
        is_reassign = hir.re_assign

        value_lirs = self.process(value)

        as_lir = None

        if is_reassign:
            const_id = self.get_current_value_id()
            store_lir = StoreLIR(target, type_str, const_id)
            self.blocks.emit(store_lir)
            as_lir = store_lir
        else:
            const_id = self.get_current_value_id()
            declare_lir = DeclareLIR(target, type_str, const_id)
            self.blocks.emit(declare_lir)
            as_lir = declare_lir

        lirs.append(value_lirs)
        lirs.append(as_lir)
        return lirs

    def process_args(self, args):
        args_lir = LIRs()
        arg_loads = LIRs()

        for arg in args:
            value_id = self.get_value_id()
            type_str = str(arg.type)

            args_lir.append(ArgLIR(value_id, type_str))
            arg_loads.append(LoadLIR(arg.target, value_id, type_str))

        return args_lir, arg_loads

    def process_FunctionIR(self, hir):
        self.enter_new_value_scope()

        name = hir.name
        args = hir.args
        type_str = str(hir.type)
        body = hir.body_irs

        prev_blocks = self.blocks
        self.blocks = BlockManager()

        self.blocks.new_block()

        args_lir, arg_load = self.process_args(args)
        self.blocks.emit(arg_load)

        for stmt in body:
            self.process(stmt)

        if self.blocks.current and not self.blocks.is_terminated():
            self.blocks.terminate(ReturnLIR(None))

        fn_blocks = [box.block for box in self.blocks.blocks]

        self.blocks = prev_blocks
        self.exit_value_scope()

        return FunctionLIR(name, args_lir, type_str, fn_blocks)

    def process_IntrinsicIR(self, hir):
        return self.process_CallIR(hir)

    def process_GroupIR(self, hir):
        return self.process(hir.expr)

    def process_CallIR(self, hir):
        is_not_return = isinstance(hir.type, NoneType) or hir.type is None

        type_str = str(hir.type)
        target = hir.target
        args = hir.args

        lirs = LIRs()
        arg_ids = []

        for arg in args:
            lir = self.process(arg)
            arg_ids.append(self.get_current_value_id())

        if is_not_return:
            nonetype = str(NoneType())
            const_lir = ConstLIR(self.get_value_id(), nonetype, None)
            self.blocks.emit(const_lir)
            lirs.append(const_lir)

            call_lir = CallLIR(None, type_str, target, arg_ids)
        else:
            call_lir = CallLIR(self.get_value_id(), type_str, target, arg_ids)

        self.blocks.emit(call_lir)
        lirs.append(call_lir)

        return lirs

    def _op_to_lir(self, type_str, left_id, right_id, op):
        match op:
            case "+":
                return AddLIR(self.get_value_id(), type_str, left_id, right_id)
            case "-":
                return SubLIR(self.get_value_id(), type_str, left_id, right_id)
            case "*":
                return MulLIR(self.get_value_id(), type_str, left_id, right_id)
            case "/":
                return DivLIR(self.get_value_id(), type_str, left_id, right_id)
            case "%":
                return ModLIR(self.get_value_id(), type_str, left_id, right_id)
            case ">":
                return GtLIR(self.get_value_id(), type_str, left_id, right_id)
            case "<":
                return LtLIR(self.get_value_id(), type_str, left_id, right_id)
            case _:
                raise Exception(f"No LIR for op {op}")

    def process_BinaryOpIR(self, hir):
        left = hir.left
        right = hir.right
        type_str = str(hir.type)
        op = hir.op

        lirs = LIRs()

        left_lir = self.process(left)
        left_id = self.get_current_value_id()
        right_lir = self.process(right)
        right_id = self.get_current_value_id()

        op_lir = self._op_to_lir(type_str, left_id, right_id, op)
        self.blocks.emit(op_lir)

        lirs.append(left_lir)
        lirs.append(right_lir)
        lirs.append(op_lir)
        return lirs

    def process_BooleanIR(self, hir):
        value = hir.value
        val = 1 if value else 0
        const_lir = ConstLIR(self.get_value_id(), "bool", val)
        self.blocks.emit(const_lir)
        return const_lir

    def process_BlockIR(self, hir):
        lirs = self.process_from_list(hir.body)
        return lirs

    def process_IfIR(self, hir):
        merge_block = self.blocks.create_block()

        has_else_path = bool(hir.elifs) or hir.else_body is not None
        false_target = self.blocks.create_block() if has_else_path else merge_block

        self.process(hir.cond)
        cond_id = self.get_current_value_id()

        then_block = self.blocks.create_block()
        self.blocks.branch(cond_id, then_block, false_target)

        self.blocks.switch_to(then_block)
        self._lower_branch_body(hir.body, merge_block)

        if has_else_path:
            self._lower_else_chain(hir.elifs, hir.else_body, false_target, merge_block)

        self.blocks.switch_to(merge_block)

    def process_WhileIR(self, hir):
        is_always_true = isinstance(hir.cond, BooleanIR) and hir.cond.value

        cond_block = self.blocks.create_block()
        loop_block = self.blocks.create_block()
        merge_block = self.blocks.create_block()

        self.blocks.jump(cond_block)

        self.blocks.switch_to(cond_block)

        self.process(hir.cond)

        if not is_always_true:
            cond_id = self.get_current_value_id()

            self.blocks.branch(
                cond_id,
                loop_block,
                merge_block,
            )
        else:
            self.blocks.jump(loop_block)

        self.blocks.switch_to(loop_block)

        self.process_from_list(hir.body)

        if not self.blocks.is_terminated():
            self.blocks.jump(cond_block)

        self.blocks.switch_to(merge_block)

    def process_ForIR(self, hir):
        # The First block
        target = hir.target.target
        target_reassign = hir.target.re_assign
        target_type = str(hir.target.type)
        source = hir.source

        source.start.type = hir.target.type
        source.end.type = hir.target.type
        source.step.type = hir.target.type

        if not isinstance(source, RangeIR):
            raise NotImplementedError("Only range-based for loops are supported")

        condition_block = self.blocks.create_block()
        loop_block = self.blocks.create_block()
        merge_block = self.blocks.create_block()

        self.process(source.start)
        if target_reassign:
            self.blocks.emit(StoreLIR(target, target_type, self.get_current_value_id()))
        else:
            self.blocks.emit(
                DeclareLIR(target, target_type, self.get_current_value_id())
            )
        self.blocks.jump(condition_block)

        # The condition block

        self.blocks.switch_to(condition_block)
        self.blocks.emit(LoadLIR(self.get_value_id(), target, target_type))
        loaded_id = self.get_current_value_id()
        self.process(source.end)
        end_id = self.get_current_value_id()
        self.blocks.emit(LtLIR(self.get_value_id(), target_type, loaded_id, end_id))
        self.blocks.branch(self.get_current_value_id(), loop_block, merge_block)

        # The loop block
        self.blocks.switch_to(loop_block)

        self.process_from_list(hir.body)

        self.process(source.step)
        step_id = self.get_current_value_id()
        self.blocks.emit(LoadLIR(self.get_value_id(), target, target_type))

        loaded_id = self.get_current_value_id()
        self.blocks.emit(AddLIR(self.get_value_id(), target_type, loaded_id, step_id))
        self.blocks.emit(StoreLIR(target, target_type, self.get_current_value_id()))
        self.blocks.jump(condition_block)

        self.blocks.switch_to(merge_block)

    def _lower_branch_body(self, body, merge_block):
        if isinstance(body, BlockIR):
            body = body.body

        for stmt in body:
            self.process(stmt)

        if not self.blocks.is_terminated():
            self.blocks.jump(merge_block)

    def _lower_else_chain(self, elifs, else_body, current_false_block, merge_block):
        if elifs:
            for idx, elif_ir in enumerate(elifs):
                is_last = idx == len(elifs) - 1
                next_false = (
                    self.blocks.create_block()
                    if (not is_last or else_body is not None)
                    else merge_block
                )

                self.blocks.switch_to(current_false_block)
                self.process(elif_ir.cond)
                cond_id = self.get_current_value_id()

                elif_then = self.blocks.create_block()
                self.blocks.branch(cond_id, elif_then, next_false)

                self.blocks.switch_to(elif_then)
                self._lower_branch_body(elif_ir.body, merge_block)

                current_false_block = next_false

        if else_body is not None:
            self.blocks.switch_to(current_false_block)
            self._lower_branch_body(else_body, merge_block)

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
        if self.blocks.current is None:
            self.blocks.new_block()

        for hir in self.hir:
            res = self.process(hir)
            if isinstance(res, FunctionLIR):
                self.lir.append(res)

        for box in self.blocks.blocks:
            if box.parent is None or box.parent.block in self.lir:
                if box.block not in self.lir and box.block.body:
                    self.lir.append(box.block)

        # raise Exception(self.lir)

        return self.lir
