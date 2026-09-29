class AssignSymbol:
    def __init__(self, name, type, value, ast_node):
        self.name = name
        self.type = type
        self.value = value

        self.ast_node = ast_node

        self.uses = []
