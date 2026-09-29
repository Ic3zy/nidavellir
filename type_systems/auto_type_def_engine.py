from .tree_builder import SymbolTreeBuilder


class AutoTypeDefEngine:
    def __init__(self, ast_tree):
        self.sym_tree = SymbolTreeBuilder(ast_tree)
