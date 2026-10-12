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
    def __init__(self, ast_node, path, source_code=None, is_c_import=False):
        self.ast_node = ast_node

        self.name = ast_node.module
        self.path = path
        self.alias = ast_node.alias
        self.source_code = source_code
        # TODO: impl c imp
        self.is_c_import = is_c_import

    def __repr__(self):
        kind = "C Header" if self.is_c_import else "Nidavellir"
        path_str = self.path.name if self.path else "NoPath"
        alias_str = f" as {self.alias}" if self.alias else ""
        return f"<Module '{self.name}'{alias_str} [{kind}] path='{path_str}'>"


class ImportSystem:
    def __init__(self, root_path, root_asts):
        self.root_path = root_path
        self.root_asts = root_asts
        self.modules = []

        self.run()

    def run(self):
        self.scan_for_ast(self.root_asts)
        self.scan_for_imported_modules()

    def add_module(self, ast_node, path, source_code=None, is_c_import=False):
        imp_obj = ModuleOBJ(ast_node, path, source_code, is_c_import)
        self.modules.append(imp_obj)

    def get_source_code(self, path):
        if path.is_file():
            with open(path, "r") as f:
                return f.read()

        return None

    def scan_for_ast(self, ast):
        for node in ast:
            if isinstance(node, FunctionAST):
                node.is_imported = True

            if not isinstance(node, ImportAST):
                continue

            name = node.module
            if check_header_exists(name):
                continue

            name = self.name_mapper(name)
            path = self.get_path_from_name(name)

            source_code = self.get_source_code(path)
            if source_code is None:
                raise Exception(f"No source code for module '{name}'")

            self.add_module(node, path, source_code)

    def execute_module(self, module):
        if module.source_code is None:
            raise Exception(f"No source code for module '{module.name}'")

        asts = get_nidac().parse_from_source_code(module.source_code)

        ast_node = module.ast_node

        ast_node.imported_asts = asts

    def scan_for_imported_modules(self):
        for module in self.modules:
            self.execute_module(module)

        # raise Exception(self.modules[0].ast_node)

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

    def name_mapper(self, name):
        return f"{name}.nida"

    def name_mapper_reverse(self, name):
        return name.replace(".nida", "")

    def get_path_from_name(self, name):
        return self.root_path / name
