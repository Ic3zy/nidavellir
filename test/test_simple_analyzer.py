import time
from nidac_importer import Nidac
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def read_nida_test_file(file_path) -> list["str"]:
    file_path = BASE_DIR / file_path
    file = None
    with open(file_path, "r") as f:
        file = f.read()

    return file.split("#nida_test")


PASS_TESTS = read_nida_test_file("./codes/pass_tests.nida")

FAIL_TESTS = read_nida_test_file("./codes/error_tests.nida")


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
