class Symbol:
    pass


class GlobalScope(Symbol):
    pass


class VariableSymbol(Symbol):
    def __init__(self, name: str, type_annotation: str):
        self.name = name
        self.type = type_annotation

        self.used_stack = []


class FunctionSymbol(Symbol):
    def __init__(self, name: str, return_type: str, params: list):
        self.name = name
        self.return_type = return_type
        self.params = params

        self.call_stack = []
