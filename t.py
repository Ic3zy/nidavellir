from lexer import Lexer
from nida_ast import Parser
from semantic import SimpleAnalyzer

a = None
with open("./a.nida", "r") as f:
    a = f.read()


l = Lexer(a)
parser = Parser(l)
ast = parser.parse_all()
SimpleAnalyzer(parser.asts).analyze_all()
# print(l.tokens)
