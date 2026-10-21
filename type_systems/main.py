from .tree_gen import SymbolTreeBuilder
from .type_def import AutoTypeDefEngine
from utils import SysArgs


class TypeSystem:
    def __init__(self, ast_tree, optimization=False):
        self.ast_tree = ast_tree
        self.stb = None

        self.tree_gen()
        self.type_def()

        if optimization:
            self.optimize()

    def tree_gen(self):
        if not self.ast_tree:
            raise Exception("No AST tree provided")

        self.stb = SymbolTreeBuilder(self.ast_tree)

        if SysArgs.dump_type_tree:
            print(self.stb.print_scopes())

    def type_def(self):
        if self.stb is None:
            self.tree_gen()

        self.tde = AutoTypeDefEngine(self.stb.st)
        self.tde.run()

        if SysArgs.dump_type_engine:
            print(self.stb.print_scopes())

        # raise Exception(self.ast_tree)

    def optimize(self):
        raise NotImplementedError
