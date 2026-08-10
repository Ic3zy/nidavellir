from nida_ast.base import IntrinsicAST


def not_implemented(*a, **k):
    raise NotImplementedError("Intrinsic not implemented", a, k)


INTRINSIC_HANDLERS = {
    "list": {
        "name": "list",
        "return_type": "List",
        "params": [("size", "int"), ("type", "type")],
        "handler": not_implemented,
        "is_variadic": False,
    },
    "print": {
        "name": "print",
        "return_type": "void",
        "params": [],
        "handler": not_implemented,
        "is_variadic": True,
    },
}
