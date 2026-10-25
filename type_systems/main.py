from .type_def import AutoTypeDefEngine
from utils import SysArgs


class TypeSystem:
    def __init__(self, symbol_tree, optimization=False):
        self.symbol_tree = symbol_tree

        self.type_def()

        if optimization:
            self.optimize()

    def type_def(self):
        self.tde = AutoTypeDefEngine(self.symbol_tree)
        self.tde.run()

        if SysArgs.dump_type_engine:
            print(self.symbol_tree)

        # raise Exception(self.ast_tree)

    def optimize(self):
        raise NotImplementedError
