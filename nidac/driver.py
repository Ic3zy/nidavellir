from pathlib import Path
from lexer import Lexer
from nida_ast import Parser
from semantic import SimpleAnalyzer
from import_systems import ImportSystem
from type_systems import TypeDefEngine
from IR_gen import IRGen
from C_gen import C_Gen
from utils import SysArgs
from .gcc import compile_c_file, run_compiled_file


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

        self.ir = None
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
        # self.type_def() # TODO: impl
        # self.check_types()  # TODO: HardAnalyzer
        # return self.emit_c11() # TODO: CodeGen
        self.IRGen()
        self.emit_c11()
        self.compile_binary()

        return self

    def import_systems(self):
        root_path = Path.cwd()
        self.module_scanner = ImportSystem(root_path, self.asts)
        modules = self.module_scanner.modules
        self.imported_modules = modules

    def run_binary(self, binary_path: str, args: list[str] = None):
        if self.final_c_code is None:
            self.emit_c11()

        run_compiled_file(binary_path, args)

    def create_header(self, path):
        if self.c_gen is None:
            self.emit_c11()

        header_str = self.c_gen.create_header()
        with open(path, "w") as f:
            f.write(header_str)

    def compile_binary(self):
        if self.final_c_code is None:
            self.emit_c11()

        c_path = SysArgs.emit_c
        if self.is_module:
            cache_dir = self.current_path / "__nidacache__"
            cache_dir.mkdir(parents=True, exist_ok=True)
            c_path = cache_dir / f"{self.module_name}.c"
            header_path = cache_dir / f"{self.module_name}.h"
            self.create_header(header_path)
            SysArgs.add_include_path(header_path.parent)

        with open(c_path, "w") as f:
            f.write(self.final_c_code)

        if not self.is_module:
            compile_c_file(c_path, SysArgs.output)
            self.run_binary(SysArgs.output)

    def emit_c11(self):
        if self.ir is None:
            self.IRGen()

        self.c_gen = C_Gen(self.ir, module_name=self.module_name)
        self.final_c_code = self.c_gen.gen_from_list(self.ir)

    def IRGen(self):
        ir = IRGen(self.asts, module_name=self.module_name)
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

        analyzer = SimpleAnalyzer(self.asts, self.imported_modules)
        analyzer.analyze_all()
        self.symbol_table = analyzer.stm
        return self.symbol_table

    def type_def(self):
        if not self.symbol_table:
            self.analyze()

        type_def_engine = TypeDefEngine(self.asts)
        type_def_engine.run()


SysArgs.nidac_ptr = Nidac
