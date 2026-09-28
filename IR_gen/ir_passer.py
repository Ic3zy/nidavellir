from .irs import *
from type_systems.types import IntType
from semantic.intrinsics import INTRINSIC_HANDLERS


class IRPasser:
    def __init__(self, irs, module_name=None):
        self.irs = irs
        self.module_name = module_name

    @property
    def is_module(self):
        return self.module_name is not None

    def run(self):
        final_irs = []
        top_level_stmts = []

        for ir in self.irs:
            if isinstance(ir, (FunctionIR, IRImport)):
                final_irs.append(self.run_stmt(ir))
            else:
                top_level_stmts.append(self.run_stmt(ir))

        if top_level_stmts:
            top_level_stmts.append(ReturnIR(NumberIR("0"), val_type="int"))
            name = f"Nida_Func_By_{self.module_name}_main" if self.is_module else "main"
            main_fn = FunctionIR(
                decs=[],
                name=name,
                args=[],
                body=[],
                return_type=IntType(byte_size=4, signed=True),
                is_main_func=True,
            )
            main_fn.body_irs = top_level_stmts
            final_irs.append(main_fn)

        return final_irs

    def run_stmt(self, ir):
        name = ir.__class__.__name__
        func = getattr(self, f"stmt_{name}", self.default_pass)
        return func(ir)

    def run_expr(self, ir):
        name = ir.__class__.__name__
        func = getattr(self, f"expr_{name}", self.default_pass)
        return func(ir)

    def default_pass(self, ir):
        return ir

    def stmt_CallIR(self, ir):
        return self.run_expr(ir)

    def stmt_AssignIR(self, ir):
        ir.value = self.run_expr(ir.value)
        return ir

    def stmt_ReturnIR(self, ir):
        if ir.value:
            ir.value = self.run_expr(ir.value)
        return ir

    def stmt_FunctionIR(self, ir):
        new_body = []
        for body_ir in ir.body_irs:
            new_body.append(self.run_stmt(body_ir))
        ir.body_irs = new_body

        if self.is_module:
            ir.name = f"Nida_Func_By_{self.module_name}_{ir.name}"
        elif not ir.is_main_func and not self.is_module:
            ir.name = f"Nida_Func_{ir.name}"

        for arg in ir.args:
            self.run_stmt(arg)

        return ir

    def expr_BinaryOpIR(self, ir):
        ir.left = self.run_expr(ir.left)
        ir.right = self.run_expr(ir.right)
        return ir

    def expr_NumberIR(self, ir):
        return ir

    def expr_VariableIR(self, ir):
        return ir

    def expr_CallIR(self, ir):
        target = ir.target
        if target not in INTRINSIC_HANDLERS and not ir.imported_func_call:
            if self.is_module:
                target = f"Nida_Func_By_{self.module_name}_{target}"
            elif not self.is_module:
                target = f"Nida_Func_{target}"

        ir.target = target

        ir.args = [self.run_expr(arg) for arg in ir.args]

        return ir
