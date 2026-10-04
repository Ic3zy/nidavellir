class AST:
    def _format(self, indent=0):
        lines = []
        prefix = "  " * indent
        class_name = self.__class__.__name__

        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

        if not attrs:
            return f"{prefix}{class_name}()"

        lines.append(f"{prefix}{class_name}:")
        for key, value in attrs.items():
            field_prefix = f"{prefix}  {key}:"

            if isinstance(value, AST):
                lines.append(field_prefix)
                lines.append(value._format(indent + 2))
            elif isinstance(value, list):
                if not value:
                    lines.append(f"{field_prefix} []")
                else:
                    lines.append(field_prefix)
                    for item in value:
                        if isinstance(item, AST):
                            lines.append(f"{prefix}    -")
                            lines.append(item._format(indent + 3))
                        elif isinstance(item, list):
                            for sub_item in item:
                                if isinstance(sub_item, AST):
                                    lines.append(f"{prefix}    -")
                                    lines.append(sub_item._format(indent + 3))
                                else:
                                    lines.append(f"{prefix}    - {repr(sub_item)}")
                        else:
                            lines.append(f"{prefix}    - {repr(item)}")
            elif value is None:
                lines.append(f"{field_prefix} None")
            else:
                lines.append(f"{field_prefix} {repr(value)}")

        return "\n".join(lines)

    def __repr__(self):
        return self._format()


class FunctionAST(AST):
    def __init__(self, decorators, name, args, body, type):
        self.decorators = decorators
        self.name = name
        self.args = args
        self.body = body
        self.type = type


class BlockAST(AST):
    def __init__(self, body):
        self.body = body


class ElifAST(AST):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body


class IfAST(AST):
    def __init__(self, cond, body, elifs, else_body):
        self.cond = cond
        self.body = body
        self.elifs = elifs
        self.else_body = else_body


class NumberAST(AST):
    def __init__(self, value, type=None):
        self.value = value
        self.type = type


class StringAST(AST):
    def __init__(self, value):
        self.value = value


class VariableAST(AST):
    def __init__(self, name):
        self.name = name
        self.type = None


class IndexAccessAST(AST):
    def __init__(self, target, index):
        self.target = target
        self.index = index


class CallAST(AST):
    def __init__(self, target, chain, args):
        self.target = target
        self.chain = chain
        self.args = args

        self.imported_func_call = False
        self.type = None


class ReturnAST(AST):
    def __init__(self, value):
        self.value = value


class AssignAST(AST):
    def __init__(self, target, chain, type, value):
        self.target = target
        self.chain = chain
        self.type = type
        self.value = value

        self.is_re_assign = None


class WhileAST(AST):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body


class ForAST(AST):
    def __init__(self, target, source, body):
        self.target = target
        self.source = source
        self.body = body


class ListAST(AST):
    def __init__(self, body):
        self.body = body


class OperatorAST(AST):
    def __init__(self, op):
        self.op = op


class PassAST(AST):
    def __init__(self):
        pass


class BinaryOpAST(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class BooleanAST(AST):
    def __init__(self, value):
        self.value = value


class ClassAST(AST):
    def __init__(self, decorators, name, body):
        self.decorators = decorators
        self.name = name
        self.body = body


class SelfAST(AST):
    def __init__(self):
        self.target = "self"
        self.type


class UnaryOpAST(AST):
    def __init__(self, op, right):
        self.op = op
        self.right = right


class DecoratorAST(AST):
    def __init__(self, name, args):
        self.name = name
        self.args = args


class FieldAccessAST(AST):
    def __init__(self, target, chain):
        self.target = target
        self.chain = chain


class ListLiteralAST(AST):
    def __init__(self, elements):
        self.elements = elements


class IntrinsicAST(AST):
    def __init__(self, name, type, params, handler, is_variadic=False):
        self.name = name
        self.type = type
        self.args = params
        self.handler = handler
        self.is_variadic = is_variadic


class ImportAST(AST):
    def __init__(
        self, module: str, symbols: list = None, alias: str = None, line: int = 1
    ):
        self.module = module
        self.symbols = symbols or []
        self.alias = alias
        self.line = line


class GroupAST:
    def __init__(self, expr):
        self.expr = expr


class NoneAST:
    pass
