from lexer import Lexer
from nida_ast import Parser
from semantic import SimpleAnalyzer
from type_systems import TypeDefEngine
from IR_gen import IRGen
from C_gen import C_Gen
from .gcc import compile_c_file, run_compiled_file


class Nidac:
    def __init__(self, source: str = None, file_path: str = None, debug: bool = False):
        self.source = source
        self.file_path = file_path
        self.debug = debug

        self.tokens = []
        self.asts = []
        self.symbol_table = None

        self.ir = None
        self.final_c_code = None

        # compile_c_file("output.c", "output_bin")

    def compile(self):
        self.lex()
        self.parse()
        self.analyze()
        # self.type_def() # TODO: impl
        # self.check_types()  # TODO: HardAnalyzer
        # return self.emit_c11() # TODO: CodeGen
        self.IRGen()
        self.emit_c11()
        self.compile_binary()

        return self

    def run_binary(self, binary_path: str, args: list[str] = None):
        if self.final_c_code is None:
            self.emit_c11()

        run_compiled_file(binary_path, args)

    def compile_binary(self):
        if self.final_c_code is None:
            self.emit_c11()

        with open("output.c", "w") as f:
            f.write(self.final_c_code)

        compile_c_file("output.c", "output_bin")
        self.run_binary("output_bin")

    def emit_c11(self):
        if self.ir is None:
            self.IRGen()

        c_gen = C_Gen(self.ir)
        self.final_c_code = c_gen.gen_from_list(self.ir)

    def IRGen(self):
        ir = IRGen(self.asts)
        self.ir = ir.gen_from_list(self.asts)

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
        print(self.asts)
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
