from pathlib import Path
from lexer import Lexer
from nida_ast import Parser
from semantic import SimpleAnalyzer
from import_systems import ImportSystem

# from type_systems import AutoTypeDefEngine
from type_systems import TypeSystem
from IR_gen import IRGen
from LIR_gen import IRLowerer
from C_gen import C_Gen
from utils import SysArgs
from .gcc import compile_c_file, run_compiled_file

import sys

sys.set_int_max_str_digits(0)


class Nidac:
    def __init__(
        self,
        source: str = None,
        file_path: str = None,
        debug: bool = False,
        module_name: str = None,
    ):
        self.source = source
        self.file_path = file_path
        self.debug = debug
        self.module_name = module_name

        self.current_path = Path.cwd()

        self.tokens = []
        self.asts = []
        self.symbol_table = None

        self.hir = None
        self.lir = None
        self.final_c_code = None
        self.c_gen = None
        # compile_c_file("output.c", "output_bin")

    @property
    def is_module(self):
        return self.module_name is not None

    def compile(self):
        self.lex()
        self.parse()

        self.import_systems()

        self.analyze()
        self.type_def()
        # self.check_types()  # TODO: HardAnalyzer
        self.IRGen()

        self.emit_c11()

        if not SysArgs.no_binary_compile:
            self.compile_binary()

    def import_systems(self):
        root_path = Path.cwd()
        self.module_scanner = ImportSystem(root_path, self.asts)

    def run_binary(self, binary_path: str, args: list[str] = None):
        if self.final_c_code is None:
            self.emit_c11()

        run_compiled_file(binary_path, args)

    def compile_binary(self):
        if self.final_c_code is None:
            self.emit_c11()

        c_path = SysArgs.emit_c

        with open(c_path, "w") as f:
            f.write(self.final_c_code)

        if not self.is_module:
            compile_c_file(c_path, SysArgs.output)
            self.run_binary(SysArgs.output)

    def emit_c11(self):
        if self.lir is None:
            self.IRGen()

        self.c_gen = C_Gen(self.lir, module_name=self.module_name)
        self.final_c_code = self.c_gen.gen_from_list(self.lir)

    def IRGen(self):
        ir = IRGen(self.asts, module_name=self.module_name)
        self.hir = ir.gen_from_list(self.asts)
        lir = IRLowerer(self.hir)
        self.lir = lir.run()

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

    @staticmethod
    def parse_from_source_code(source_code):
        lexer_obj = Lexer(source_code)
        parser = Parser(lexer_obj)
        parser.parse_all()
        return parser.asts

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

        TypeSystem(self.asts)


SysArgs.nidac_ptr = Nidac
