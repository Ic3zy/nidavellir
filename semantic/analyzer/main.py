from .analyzer import SymbolTreeBuilder
from nida_ast.base import *


def semantic_analyze(ast_tree):
    stb = SymbolTreeBuilder(ast_tree)
    stb.run()
    return stb
