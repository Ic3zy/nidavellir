from .sys_args_parser import SysArgs as s_a
from .stopwatch import ExecutionTimer

SysArgs = s_a()
__all__ = ["SysArgs", "ExecutionTimer"]
