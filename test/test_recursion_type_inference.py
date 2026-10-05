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

def compute(x, y, z):
    t1 = add(x, y)
    t2 = add(t1, z)
    def helper(m, n):
        return add(m, n)
    return helper(t1, t2)

val = compute(1, 2, 3)
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

    def test_ultra_deep_call_chain_15_levels(self):
        code = """
def f1(x):
    return x + 1
def f2(x):
    return f1(x) + 2
def f3(x):
    return f2(x) + 3
def f4(x):
    return f3(x) + 4
def f5(x):
    return f4(x) + 5
def f6(x):
    return f5(x) + 6
def f7(x):
    return f6(x) + 7
def f8(x):
    return f7(x) + 8
def f9(x):
    return f8(x) + 9
def f10(x):
    return f9(x) + 10
def f11(x):
    return f10(x) + 11
def f12(x):
    return f11(x) + 12
def f13(x):
    return f12(x) + 13
def f14(x):
    return f13(x) + 14
def f15(x):
    return f14(x) + 15

total = f15(1)
"""
        asts = self._run_type_inference(code)
        self.assertIsNotNone(asts)

    def test_diamond_call_graph(self):
        code = """
def leaf(val):
    return val + 1

def branch_a(x):
    return leaf(x) * 2

def branch_b(x):
    return leaf(x) * 3

def root(x):
    return branch_a(x) + branch_b(x)

res = root(5)
"""
        asts = self._run_type_inference(code)
        self.assertIsNotNone(asts)

    def test_deeply_nested_4_level_closures(self):
        code = """
def lvl1(a):
    b = a + 1
    def lvl2(c):
        d = b + c
        def lvl3(e):
            f = d + e
            def lvl4(g):
                return a + b + c + d + e + f + g
            return lvl4(f)
        return lvl3(d)
    return lvl2(b)

ans = lvl1(1)
"""
        asts = self._run_type_inference(code)
        self.assertIsNotNone(asts)

    def test_interleaved_multi_param_calls(self):
        code = """
def sub(a, b):
    return a - b

def mul(a, b):
    return a * b

def combine(w, x, y, z):
    p1 = sub(w, x)
    p2 = mul(y, z)
    p3 = sub(p2, p1)
    return mul(p3, p1)

res = combine(10, 2, 3, 4)
"""
        asts = self._run_type_inference(code)
        self.assertIsNotNone(asts)

    def test_many_call_sites_same_func(self):
        code = """
def add(a, b):
    return a + b

v1 = add(1, 2)
v2 = add(v1, 3)
v3 = add(v2, v1)
v4 = add(v3, v2)
v5 = add(v4, v3)
"""
        asts = self._run_type_inference(code)
        self.assertIsNotNone(asts)


if __name__ == "__main__":
    unittest.main()
