from type_systems.types import *


class IntrinsicType:
    def check(self, type):
        raise NotImplementedError


class AnyType(IntrinsicType):
    def check(self, type):
        return True


class OneOf(IntrinsicType):
    def __init__(self, *types):
        self.types = types

    def check(self, type):
        return any(isinstance(type, t) for t in self.types)


class ParamsType:
    def __init__(
        self,
        type,
        min_t=None,
        max_t=None,
        args_count=None,
        is_variadic=False,
    ):
        if min_t is None and max_t is None and args_count is None and not is_variadic:
            raise ValueError("Invalid params type")

        if args_count is not None and (
            min_t is not None or max_t is not None or is_variadic
        ):
            raise ValueError("Invalid params type")

        if min_t is not None and min_t < 0:
            raise ValueError("min_t cannot be negative")

        if max_t is not None and max_t < 0:
            raise ValueError("max_t cannot be negative")

        if min_t is not None and max_t is not None and min_t > max_t:
            raise ValueError("min_t cannot exceed max_t")

        self.type = type
        self.min_t = min_t
        self.max_t = max_t
        self.args_count = args_count
        self.is_variadic = is_variadic

    def check_arg_count(self, count):
        if self.args_count is not None and count != self.args_count:
            return False

        if self.min_t is not None and count < self.min_t:
            return False

        if self.max_t is not None and count > self.max_t:
            return False

        return True

    def check(self, args):
        count = len(args)

        if not self.check_arg_count(count):
            return False

        return all(self.type.check(arg.type) for arg in args)
