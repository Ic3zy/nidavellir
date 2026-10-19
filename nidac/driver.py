from pathlib import Path
from lexer import Lexer
from nida_ast import Parser
from semantic import SimpleAnalyzer, FunctionAllocator
from import_systems import ImportSystem

from type_systems.main import TypeSystem
from IR_gen import IRGen
from LIR_gen import IRLowerer
from C_gen import C_Gen
from C_gen import HeaderGenerator
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
    ):
        self.ctx = {
            "f_alloc": FunctionAllocator(),
        }

        self.source = source
        self.file_path = file_path
        self.debug = debug

        self.current_path = Path.cwd()

        self.lexer = None
        self.asts = []
        self.imported_modules = []
        self.symbol_table = None

        self.hir = None
        self.lir = None
        self.final_c_code = None
        self.c_gen = None

    def compile(self):
        self.lex()
        self.parse()
        if SysArgs.stop_after == "ast":
            return

        self.import_systems()

        self.analyze()
        if SysArgs.stop_after == "semantic":
            return

        # self.type_def()
        if SysArgs.stop_after == "type-engine" or SysArgs.stop_after == "type-tree":
            return

        # self.check_types()  # TODO: HardAnalyzer

        self.HIRGen()
        if SysArgs.stop_after == "hir":
            return

        self.LIRGen()
        if SysArgs.stop_after == "lir":
            return

        self.emit_c11()
        if SysArgs.stop_after == "c":
            return

        if not SysArgs.no_binary_compile:
            self.compile_binary()

    def import_systems(self):
        root_path = Path.cwd()
        module_scanner = ImportSystem(root_path, self.asts)
        self.imported_modules = module_scanner.ordered_modules

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

        compile_c_file(c_path, SysArgs.output)
        self.run_binary(SysArgs.output)

    def generate_dependencies_c_code(self):
        for module in self.imported_modules:
            if not module.lirs:
                continue

            extra_include = []
            if module.dependencies:
                for dep in module.dependencies:
                    if not dep.include_path:
                        raise Exception(f"No include path for module '{dep.name}'")
                    extra_include.append(dep.include_path.name)

            c_gen = C_Gen(module.lirs, extra_include=extra_include)
            module.c_code = c_gen.gen_from_list(module.lirs)
            c_nodes = c_gen.c_nodes

            h_gen = HeaderGenerator(module.name, c_nodes)
            module.header_code = h_gen.gen_Header()

            c_path = module.path.parent / "__nidacache__" / f"{module.name}.c"
            c_header_path = module.path.parent / "__nidacache__" / f"{module.name}.h"

            module.include_path = c_header_path

            if not module.include_path.exists():
                module.include_path.parent.mkdir(parents=True, exist_ok=True)

            with open(c_path, "w") as f:
                f.write(module.c_code)

            with open(c_header_path, "w") as f:
                f.write(module.header_code)

            SysArgs.add_include_path(c_header_path.parent)
            SysArgs.add_extra_c_include(c_header_path.name)
            SysArgs.add_c_file(c_path)

    def emit_c11(self):
        if self.lir is None:
            self.LIRGen()

        self.generate_dependencies_c_code()

        self.c_gen = C_Gen(self.lir)
        self.final_c_code = self.c_gen.gen_from_list(self.lir)

        if SysArgs.dump_c:
            print("===== C Code =====")
            print(self.final_c_code)
            print("===== C Nodes =====")
            print(self.c_gen.c_nodes)

    def HIRGen(self):
        hir = IRGen(self.asts, self.ctx)
        self.hir = hir.run()

        if SysArgs.dump_hir:
            print("===== HIR =====")
            print(self.hir)

    def LIRGen(self):
        lir = IRLowerer(self.hir)
        self.lir = lir.run()

        if SysArgs.dump_lir:
            print("===== LIR =====")
            print(self.lir)

    def read_file(self):
        with open(self.file_path, "r") as f:
            self.source = f.read()

    def lex(self):
        if self.source is None:
            self.read_file()

        self.lexer = Lexer(self.source)
        return self.lexer

    def parse(self):
        if not self.lexer:
            self.lex()

        parser = Parser(self.lexer)

        self.asts = parser.run()
        if SysArgs.dump_ast:
            print("===== AST =====")
            print(self.asts)

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

        analyzer = SimpleAnalyzer(self.asts, self.ctx)
        analyzer.analyze_all()

        self.symbol_table = analyzer.stm
        if SysArgs.dump_ast_after_semantic:
            print("===== AST (after semantic analysis) =====")
            print(self.asts)

        return self.symbol_table

    def type_def(self):
        if not self.symbol_table:
            self.analyze()

        TypeSystem(self.asts)


SysArgs.nidac_ptr = Nidac
