from .irs import *


class IRPasser:
    def __init__(self, irs):
        self.irs = irs

    def run(self):
        final_irs = []
        top_level_stmts = []

        for ir in self.irs:
            if isinstance(ir, FunctionIR):
                final_irs.append(self.run_stmt(ir))
            else:
                top_level_stmts.append(self.run_stmt(ir))

        if top_level_stmts:
            top_level_stmts.append(ReturnIR(NumberIR("0"), val_type="int"))
            # TODO: this is not safe
            main_fn = FunctionIR(
                decs=[],
                name="main",
                args=[],
                body=[],
                return_type="int",
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
        ir.args = [self.run_expr(arg) for arg in ir.args]
        return ir
