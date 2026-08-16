from lexer import Lexer
from nida_ast import Parser
from semantic import SimpleAnalyzer
from type_systems import TypeDefEngine


class Nidac:
    def __init__(self, source: str = None, file_path: str = None, debug: bool = False):
        self.source = source
        self.file_path = file_path
        self.debug = debug

        self.tokens = []
        self.asts = []
        self.symbol_table = None

    def compile(self):
        self.lex()
        self.parse()
        self.analyze()
        self.type_def()
        # self.check_types()  # TODO: HardAnalyzer
        # return self.emit_c11() # TODO: CodeGen
        return self

    def read_file(self):
        with open(self.file_path, "r") as f:
            self.source = f.read()

    def lex(self):
        if self.source is None:
            self.read_file()

        lexer = Lexer(self.source)
        self.tokens = getattr(lexer, "tokens", [])
        # print(lexer.tokenize())
        return self.tokens

    def parse(self):
        if not self.tokens:
            self.lex()

        lexer_obj = Lexer(self.source)
        parser = Parser(lexer_obj)
        parser.parse_all()
        self.asts = parser.asts
        # print(self.asts)
        return self.asts

    def analyze(self):
        if not self.asts:
            self.parse()

        analyzer = SimpleAnalyzer(self.asts)
        analyzer.analyze_all()
        self.symbol_table = analyzer.stm
        return self.symbol_table

    def type_def(self):
        if not self.symbol_table:
            self.analyze()

        type_def_engine = TypeDefEngine(self.asts)
        type_def_engine.run()
