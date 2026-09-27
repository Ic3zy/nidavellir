from pathlib import Path
from nida_ast.base import *
from semantic.c_header_analyze import GCCHeaderScraper
from .analyzer import check_header_exists
from utils import SysArgs


def get_nidac():
    if (Nidac := SysArgs.nidac_ptr) is not None:
        return Nidac
    else:
        raise Exception("No Nidac instance")


class ModuleOBJ:
    def __init__(
        self, name, path, alias, source_code=None, is_c_import=False, Nidac=None
    ):
        self.name = name
        self.path = path
        self.alias = alias
        self.source_code = source_code
        self.is_c_import = is_c_import
        self.is_core = False

        self.importable_names = []

        self.nidac = None
        self.is_compiled = False

    def __repr__(self):
        kind = "C Header" if self.is_c_import else "Nidavellir"

        path_str = self.path.name if self.path else "NoPath"

        alias_str = f" as {self.alias}" if self.alias else ""

        exports_count = len(self.importable_names)

        return f"<Module '{self.name}'{alias_str} [{kind}] path='{path_str}' exports={exports_count} importable_names={self.importable_names}>"


class ImportSystem:
    def __init__(self, root_path, root_asts):
        self.root_path = root_path
        self.root_asts = root_asts
        self.modules = {}

        self.scan_for_ast(root_asts)
        self.scan_for_imported_modules()
        self.compile_all()

        self.init_core_imports()

    def init_core_imports(self):
        runtime_path = Path(__file__).parent.parent / "runtime"
        SysArgs.add_include_path(runtime_path)

        sc = GCCHeaderScraper()
        signatures = sc.extract_signatures("Nida_core.h")

        core_symbols = list(signatures.keys())

        core_module = ModuleOBJ(
            name="Nida_core",
            path=runtime_path / "Nida_core.h",
            alias=None,
            is_c_import=True,
        )
        core_module.importable_names = core_symbols
        core_module.is_compiled = True
        core_module.is_core = True

        self.modules["Nida_core"] = core_module

    def add_module(
        self, name, path, alias, symbols, source_code=None, is_c_import=False
    ):
        self.modules[name] = ModuleOBJ(name, path, alias, source_code, is_c_import)

    def get_module(self, name):
        return self.modules.get(name)

    def name_mapper(self, name):
        return f"{name}.nida"

    def name_mapper_reverse(self, name):
        return name.replace(".nida", "")

    def get_source_code(self, name):
        module_path = self.root_path / name
        if module_path.is_file():
            with open(module_path, "r") as f:
                return f.read()

        return None

    def scan_for_ast(self, ast):
        for node in ast:
            if isinstance(node, ImportAST):
                name = node.module
                if check_header_exists(name):
                    continue

                name = self.name_mapper(name)
                alias = node.alias
                symbols = node.symbols

                source_code = self.get_source_code(name)
                if source_code is None:
                    raise Exception(f"No source code for module '{name}'")

                self.add_module(name, Path(name), alias, symbols, source_code)

    def scan_importable_names(self, ast):
        importable_names = []
        for node in ast:
            if isinstance(node, ClassAST):
                name = node.name
                importable_names.append(name)
            elif isinstance(node, FunctionAST):
                name = node.name
                importable_names.append(name)

        return importable_names

    def scan_for_imported_modules(self):
        for name, module in self.modules.items():
            if module.source_code is None:
                raise Exception(f"No source code for module '{module.name}'")

            Nidac = get_nidac()(
                source=module.source_code, module_name=self.name_mapper_reverse(name)
            )
            ast = Nidac.parse()
            importable_names = self.scan_importable_names(ast)

            module.importable_names = importable_names
            module.nidac = Nidac

        print(self.modules)

    def compile_module(self, module):
        if module.is_c_import:
            return

        Nidac = module.nidac
        Nidac.compile()
        module.is_compiled = True
        print("COMPILED: ", module.name)

    def compile_all(self):
        for module in self.modules.values():
            self.compile_module(module)

        print(self.modules)
