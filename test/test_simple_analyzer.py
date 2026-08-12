import time
from nidac_importer import Nidac

PASS_TESTS = [
    """
class Point:
    def void __init__(self, float x, float y):
        self.x = x
        self.y = y

    def float get_x(self):
        return self.x
""",
    """
def void main():
    val = calculate(10)

def int calculate(int num):
    return num * 2
""",
    """
class Engine:
    def void __init__(self, int hp):
        self.hp = hp

class Car:
    def void __init__(self, Engine engine):
        self.engine = engine

    def void check(self):
        print(self.engine.hp)
""",
    """
class Counter:
    def void __init__(self):
        self.count = 0

    def void increment(self):
        step = 1
        self.count = self.count + step
""",
    """
class Calculator:
    def int double_val(self, int x):
        return x * 2

    def int compute(self, int a):
        temp = self.double_val(a)
        return temp
""",
    """
class ChainAccess1:
    def __init__(self):
        self.a = 10

class ChainAccess2:
    c = ChainAccess1()
    def __init__(self):
        self.c.a = 20
""",
]


FAIL_TESTS = [
    """
class Test:
    def int get_val():
        return 100
""",
    """
class Vehicle:
    def void __init__(self):
        self.fuel = 100

    def void drive(self):
        print(self.speed)
""",
    """
def void print(String text):
    pass
""",
    """
class ScopeError:
    return 42
""",
    """
def void run():
    a = undefined_var + 5
""",
    """
class Test:
    a = 5
    def __init__(self):
        self.a.b = 10
""",
    """
class ChainAccess1:
    def __init__(self):
        self.a = 10 

class ChainAccess2:
    c = ChainAccess1()
    def __init__(self):
        self.c.b = 20
""",
    """
class ChainAccess1:
    def __init__(self):
        self.a = 10

class ChainAccess2:
    c = undefined_func()
    def __init__(self):
        self.c.a = 20
""",
]
t1 = time.perf_counter()
error = False
c = 0
for test in PASS_TESTS:
    try:
        nida = Nidac(source=test)
        nida.compile()
    except Exception as e:
        error = True
        print(f"[FAIL] Pass-test #{c} failed unexpectedly: {e}")
        break
    finally:
        c += 1

c = 0
for test in FAIL_TESTS:
    try:
        nida = Nidac(source=test)
        nida.compile()
        print(f"[FAIL] Expected error was NOT caught in fail-test #{c}")
        error = True
        break

    except Exception as e:
        continue

    finally:
        c += 1


print("ALL TESTS PASSED" if not error else "TEST SUITE FAILED")

t2 = time.perf_counter()
print(f"Time taken: {t2 - t1} seconds")
