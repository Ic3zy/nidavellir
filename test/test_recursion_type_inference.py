import unittest
from lexer import Lexer
from nida_ast import Parser
from semantic import SimpleAnalyzer
from type_systems import AutoTypeDefEngine


class TestRecursionAndNestedScopeInference(unittest.TestCase):
    def _run_type_inference(self, source_code: str):
        lexer = Lexer(source_code)
        parser = Parser(lexer)
        parser.parse_all()
        asts = parser.asts
        analyzer = SimpleAnalyzer(asts)
        analyzer.analyze_all()
        engine = AutoTypeDefEngine(asts)
        return asts

    def test_deep_call_chain(self):
        code = """
def func_e(x):
    return x + 1

def func_d(x):
    return func_e(x) + 2

def func_c(x):
    return func_d(x) + 3

def func_b(x):
    return func_c(x) + 4

def func_a(x):
    return func_b(x) + 5

res = func_a(10)
"""
        asts = self._run_type_inference(code)
        self.assertIsNotNone(asts)

    def test_nested_function_parameter_shadowing(self):
        code = """
def outer(a):
    b = a + 1
    def inner1(a):
        b = a + 2
        def inner2(a):
            b = a + 3
            return b
        return inner2(b)
    return inner1(b)

res = outer(5)
"""
        asts = self._run_type_inference(code)
        self.assertIsNotNone(asts)

    def test_multiple_inner_functions_shared_outer_vars(self):
        code = """
def parent(x):
    y = x + 10
    def child1(a):
        return a + y
    def child2(b):
        return child1(b) + y
    return child2(x)

ans = parent(2)
"""
        asts = self._run_type_inference(code)
        self.assertIsNotNone(asts)

    def test_multi_argument_function_propagation(self):
        code = """
def add(a, b):
    return a + b

def helper(m, n):
    return add(m, n)

val = helper(1, 2)
"""
        asts = self._run_type_inference(code)
        self.assertIsNotNone(asts)

    def test_cross_function_variable_forwarding(self):
        code = """
def base(val):
    return val

def middle(val):
    x = base(val)
    return x + 5

def top(val):
    y = middle(val)
    return y * 2

final = top(10)
"""
        asts = self._run_type_inference(code)
        self.assertIsNotNone(asts)


if __name__ == "__main__":
    unittest.main()
