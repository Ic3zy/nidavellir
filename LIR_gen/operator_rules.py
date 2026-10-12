from dataclasses import dataclass
from .lirs import *


@dataclass(frozen=True)
class LIRRule:
    instruction: type | None = None
    runtime: str | None = None
    result_type: str | None = None


INT_OPS = {
    "+": LIRRule(instruction=AddLIR),
    "-": LIRRule(instruction=SubLIR),
    "*": LIRRule(instruction=MulLIR),
    "/": LIRRule(instruction=DivLIR),
    "%": LIRRule(instruction=ModLIR),
    "==": LIRRule(instruction=EqLIR, result_type="bool"),
    "!=": LIRRule(instruction=NeLIR, result_type="bool"),
    ">": LIRRule(instruction=GtLIR, result_type="bool"),
    "<": LIRRule(instruction=LtLIR, result_type="bool"),
    ">=": LIRRule(instruction=GeLIR, result_type="bool"),
    "<=": LIRRule(instruction=LeLIR, result_type="bool"),
}

STR_OPS = {
    "+": LIRRule(runtime="Nida_str_concat"),
    "==": LIRRule(runtime="Nida_str_eq", result_type="bool"),
    "!=": LIRRule(runtime="Nida_str_ne", result_type="bool"),
}

IDYN_OPS = {
    "+": LIRRule(runtime="Nida_idyn_add"),
    "-": LIRRule(runtime="Nida_idyn_sub"),
    "*": LIRRule(runtime="Nida_idyn_mul"),
    "/": LIRRule(runtime="Nida_idyn_div"),
    "%": LIRRule(runtime="Nida_idyn_mod"),
    "==": LIRRule(runtime="Nida_idyn_eq", result_type="bool"),
    "!=": LIRRule(runtime="Nida_idyn_ne", result_type="bool"),
}

FDYN_OPS = {
    "+": LIRRule(runtime="Nida_fdyn_add"),
    "-": LIRRule(runtime="Nida_fdyn_sub"),
    "*": LIRRule(runtime="Nida_fdyn_mul"),
    "/": LIRRule(runtime="Nida_fdyn_div"),
    "==": LIRRule(runtime="Nida_fdyn_eq", result_type="bool"),
    "!=": LIRRule(runtime="Nida_fdyn_ne", result_type="bool"),
}
