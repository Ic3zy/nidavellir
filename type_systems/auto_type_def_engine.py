from .integer_systems import int_type
from .symbol_types import *
from .tree_builder import SymbolTreeBuilder
from .type_lowering import TypeLowering


class TypeDefHelper:
    @staticmethod
    def _to_int(val) -> int:
        return int(val, 0) if isinstance(val, str) else int(val)

    @classmethod
    def _resolve_sym_range(cls, sym):
        if isinstance(sym, NumberSymbol):
            val = cls._to_int(sym.value)
            return (val, val)

        if isinstance(sym, BinaryOpSymbol):
            if sym.min_val is not None and sym.max_val is not None:
                return (sym.min_val, sym.max_val)

            bounds = cls.infer_int_range_from_binaryop(sym)
            if bounds is None:
                return None
            return (min(bounds), max(bounds))

        if isinstance(sym, VariableSymbol):
            if hasattr(sym, "lookup") and sym.lookup is not None:
                return cls.infer_int_range(sym.lookup)
            return None

        return None

    @classmethod
    def infer_int_range(cls, sym):
        uses = getattr(sym, "uses", None)
        if not uses:
            sym_val_range = cls._resolve_sym_range(sym.value)
            if sym_val_range is not None:
                return sym_val_range
            return None

        range_list = []
        if isinstance(sym.value, NumberSymbol):
            range_list.append(cls._to_int(sym.value.value))

        for use in uses:
            if isinstance(use, NumberSymbol):
                range_list.append(cls._to_int(use.value))
            else:
                val_node = use.value if hasattr(use, "value") else use
                if isinstance(val_node, NumberSymbol):
                    range_list.append(cls._to_int(val_node.value))
                else:
                    raise SyntaxError(
                        f"Cannot infer integer range of '{getattr(use, 'name', 'unknown')}' ({type(use).__name__})"
                    )

        if not range_list:
            return None

        return (min(range_list), max(range_list))

    @classmethod
    def infer_int_range_from_binaryop(cls, binaryop):
        left_range = cls._resolve_sym_range(binaryop.left_sym)
        right_range = cls._resolve_sym_range(binaryop.right_sym)

        if (
            left_range is None
            or right_range is None
            or left_range[0] is None
            or right_range[0] is None
        ):
            return None

        l_min, l_max = left_range
        r_min, r_max = right_range

        return ((l_min, l_max), (r_min, r_max))

    @classmethod
    def get_int_value(cls, arg):
        if isinstance(arg, NumberSymbol):
            return cls._to_int(arg.value)
        elif (
            isinstance(arg, VariableSymbol)
            and hasattr(arg, "lookup")
            and arg.lookup is not None
        ):
            return cls.get_int_value(arg.lookup)
        return None

    @classmethod
    def infer_int_range_from_calls(cls, calls):
        range_list = {}
        for call in calls:
            if not isinstance(call, CallSymbol):
                continue

            for arg_c, arg in enumerate(call.args):
                int_val = cls.get_int_value(arg)
                if int_val is not None:
                    if arg_c not in range_list:
                        range_list[arg_c] = []
                    range_list[arg_c].append(int_val)

        for arg_c in range_list:
            range_list[arg_c] = (min(range_list[arg_c]), max(range_list[arg_c]))

        return range_list

    @classmethod
    def infer_returns(cls, arg):
        if not isinstance(arg, FunctionSymbol):
            raise Exception(f"Cannot infer returns of {type(arg).__name__}")

        return [body.value for body in arg.body if isinstance(body, ReturnSymbol)]


class AutoTypeDefEngine:
    def __init__(self, ast_tree):
        self.stb = SymbolTreeBuilder(ast_tree)
        self.sym_tree = self.stb.st
        self.run()

    def error(self, sym, message):
        line = getattr(sym, "line", None)
        col = getattr(sym, "column", None)
        loc = f" [Line {line}:{col}]" if line is not None else ""
        raise SyntaxError(f"Nidavellir Error{loc}: {message}")

    def eval_NumberSymbol(self, sym):
        val = int(sym.value, 0) if isinstance(sym.value, str) else int(sym.value)
        sym.type = int_type(val, val)
        return sym

    def eval_BinaryOpSymbol(self, sym):
        left = sym.left_sym
        if isinstance(left, BinaryOpSymbol):
            self.process_eval(left)

        right = sym.right_sym
        if isinstance(right, BinaryOpSymbol):
            self.process_eval(right)

        ranges = TypeDefHelper.infer_int_range_from_binaryop(sym)

        if ranges is None:
            self.error(sym, f"Cannot infer type of binary operation '{sym.op}'")
            return None

        (left_min, left_max), (right_min, right_max) = ranges
        if isinstance(left, BinaryOpSymbol):
            left_min = left.min_val
            left_max = left.max_val

        if isinstance(right, BinaryOpSymbol):
            right_min = right.min_val
            right_max = right.max_val

        if (
            left_min is None
            or right_min is None
            or left_max is None
            or right_max is None
        ):
            self.error(sym, f"Cannot infer type of binary operation '{sym.op}'")
            return None

        op = sym.op

        if op == "+":
            res_min = left_min + right_min
            res_max = left_max + right_max

        elif op == "-":
            res_min = left_min - right_max
            res_max = left_max - right_min

        elif op == "*":
            p1 = left_min * right_min
            p2 = left_min * right_max
            p3 = left_max * right_min
            p4 = left_max * right_max
            res_min = min(p1, p2, p3, p4)
            res_max = max(p1, p2, p3, p4)

        elif op in ("/", "//"):
            if right_min <= 0 <= right_max:
                self.error(sym, "Possible division by zero during type inference")
                return None

            d1 = left_min // right_min
            d2 = left_min // right_max
            d3 = left_max // right_min
            d4 = left_max // right_max
            res_min = min(d1, d2, d3, d4)
            res_max = max(d1, d2, d3, d4)

        elif op == "%":
            res_min = 0
            res_max = max(abs(right_min), abs(right_max)) - 1

        elif op in ("==", "!=", "<", "<=", ">", ">="):
            res_min = 0
            res_max = 1

        else:
            self.error(
                sym, f"Unsupported binary operator '{op}' for interval arithmetic"
            )
            return None

        inferred_type = int_type(res_min, res_max)

        sym.type = inferred_type
        sym.max_val = res_max
        sym.min_val = res_min

        return sym

    def eval_VariableSymbol(self, sym):
        if sym.type is None:
            self.process_eval(sym.lookup)
            sym.type = sym.lookup.type

        if sym.type is None:
            self.error(sym, f"Cannot infer type of variable '{sym.name}'")

        return sym

    def eval_StringSymbol(self, sym):
        return sym

    def eval_AssignSymbol(self, sym):
        return self.stmt_AssignSymbol(sym)

    def eval_CallSymbol(self, sym):
        return self.stmt_CallSymbol(sym)

    def stmt_FunctionSymbol(self, sym):
        inferred_args_types = []
        uses = sym.uses
        int_ranges = TypeDefHelper.infer_int_range_from_calls(uses) if uses else {}

        if uses:
            for use in uses:
                if not use.args:
                    continue

                for idx, arg in enumerate(use.args):
                    self.process_eval(arg)
                    arg_type = arg.type

                    if arg_type is None:
                        self.error(arg, f"Cannot infer type of argument '{arg.name}'")

                    if idx >= len(inferred_args_types):
                        inferred_args_types.append(arg_type)
                    elif inferred_args_types[idx] != arg_type:
                        self.error(
                            arg,
                            f"Type mismatch in '{use.name}' at arg #{idx}: "
                            f"Expected {inferred_args_types[idx]}, got {arg_type}.",
                        )

        for idx, arg_type in enumerate(inferred_args_types):
            if isinstance(arg_type, int_type) and idx in int_ranges:
                arg_type = int_type(int_ranges[idx][0], int_ranges[idx][1])

            sym.args[idx].type = arg_type
            sym.args[idx].set_type_to_AST()

        returns = TypeDefHelper.infer_returns(sym)
        inferred_return_type = None

        if returns:
            for ret in returns:
                res = self.process_eval(ret)
                if res.type is None:
                    self.error(
                        ret, f"Cannot infer type of return statement in '{sym.name}'"
                    )

                if inferred_return_type is None:
                    inferred_return_type = res.type
                elif inferred_return_type != res.type:
                    raise Exception(
                        f"Cannot infer return type of '{sym.name}': Conflicting return types ({inferred_return_type} vs {res.type})"
                    )

        if inferred_return_type is not None:
            sym.return_type = inferred_return_type
        elif sym.return_type is None:
            sym.return_type = "None"

        sym.set_type_to_AST()
        return sym

    def stmt_CallSymbol(self, sym):
        func_return_type = sym.lookup.return_type
        if func_return_type is None:
            self.process_eval(sym.lookup)
            func_return_type = sym.lookup.return_type

        if func_return_type is None:
            self.error(sym, f"Cannot infer return type of call '{sym.name}'")

        sym.type = func_return_type
        return sym

    def stmt_AssignSymbol(self, sym):
        val = sym.value

        if val is not None and val.type is None:
            self.process_eval(val)

        val_type = None

        if sym.uses:
            is_int = False
            for use in sym.uses:
                self.process_stmt(use)
                use_type = use.type

                if isinstance(use_type, int_type):
                    is_int = True
                elif is_int and not isinstance(use_type, int_type):
                    self.error(use, f"Cannot infer type of '{use.name}'")

            if is_int:
                min_val, max_val = TypeDefHelper.infer_int_range(sym)
                val_type = int_type(min_val, max_val)

        if val_type is None and val is not None:
            val_type = val.type

        if val_type is None and val.type is not None:
            val_type = val.type

        if val_type is None:
            self.error(sym, f"Cannot infer type of assignment '{sym.name}'")

        sym.type = val_type
        sym.set_type_to_AST()

        if sym.name == "a1":
            raise Exception(self.stb.print_scopes(st=[sym]))

        return sym

    def process_stmt(self, sym):
        method_name = f"stmt_{type(sym).__name__}"
        visitor = getattr(self, method_name, None)
        if visitor is None:
            self.error(sym, f"No visitor method '{method_name}' for symbol")

        return visitor(sym)

    def process_eval(self, sym):
        method_name = f"eval_{type(sym).__name__}"
        visitor = getattr(self, method_name, None)
        if visitor is None:
            self.error(sym, f"No evaluator method '{method_name}' for symbol")

        return visitor(sym)

    def lower_types(self):
        self.tl = TypeLowering(self.stb.ast_tree)
        self.tl.run()

    def run(self):
        for sym in self.sym_tree:
            self.process_stmt(sym)

        # raise Exception(self.stb.print_scopes(st=self.sym_tree))

        self.lower_types()
