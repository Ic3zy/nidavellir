from .tree_builder import SymbolTreeBuilder


class TypeDefEngine:
    def __init__(self, ast_tree):
        self.ast_tree = ast_tree
        self.stb = SymbolTreeBuilder(ast_tree)
        self.stb.run()

    def process_symbol(self, symbol):
        print(symbol)

    def process_symbols(self, node):
        for symbol in node.symbols.values():
            self.process_symbol(symbol)

    def process_node(self, node):
        if isinstance(node, list):
            self.process_children(node)
            return

        method_name = f"process_{type(node).__name__}"
        print(method_name)

        symbols = node.symbols
        if symbols is not None:
            self.process_symbols(node)

        if node.children:
            self.process_children(node)

    def process_children(self, node):
        for child in node.children:
            self.process_node(child)

    def run(self):
        current_scope = self.stb.sm.current_scope
        self.process_node(current_scope)
