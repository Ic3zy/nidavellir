import unittest
from nida_ast.base import AssignAST, NumberAST, FunctionAST, CallAST
from semantic import SimpleAnalyzer
from type_systems import AutoTypeDefEngine
from type_systems.types import IntType, StringType, BoolType, Type


class TestTypeInferenceFlow(unittest.TestCase):
    def test_explicit_type_resolution_in_semantic(self):
        # x: u8 = 10
        assign_ast = AssignAST(
            "x",
            [],
            "u8",
            NumberAST("10"),
        )
        ast_tree = [assign_ast]

        analyzer = SimpleAnalyzer(ast_tree)
        analyzer.analyze_all()

        # Check that semantic analyzer normalized explicit "u8" string into IntType object
        self.assertIsInstance(assign_ast.type, IntType)
        self.assertEqual(assign_ast.type.byte_size, 1)
        self.assertFalse(assign_ast.type.signed)

    def test_auto_type_def_engine_flow(self):
        # x = 10 (untyped, inferred as u8)
        assign_ast = AssignAST(
            "x",
            [],
            None,
            NumberAST("10"),
        )
        ast_tree = [assign_ast]

        analyzer = SimpleAnalyzer(ast_tree)
        analyzer.analyze_all()

        engine = AutoTypeDefEngine(ast_tree)

        # Check that AutoTypeDefEngine assigned an IntType instance
        self.assertIsInstance(assign_ast.type, IntType)
        self.assertEqual(str(assign_ast.type), "u8")


if __name__ == "__main__":
    unittest.main()
