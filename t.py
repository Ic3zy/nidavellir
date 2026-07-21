from lexer import Lexer
from nida_ast import Parser

a = None
with open("./a.nida", "r") as f:
    a = f.read()

l = Lexer(a)
parser = Parser(l.tokenize())
ast = parser.parse_all()
print(l.tokenize())