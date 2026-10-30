import time
from pathlib import Path

from nidac_importer import Nidac
from utils.errors import *

BASE_DIR = Path(__file__).resolve().parent


def read_nida_test_file(file_path) -> list[str]:
    file_path = BASE_DIR / file_path

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return [test.strip() for test in content.split("#nida_test") if test.strip()]


PASS_TESTS = read_nida_test_file("./codes/if_tests_pass.nida")
FAIL_TESTS = read_nida_test_file("./codes/if_tests_error.nida")


t1 = time.perf_counter()
error = False

# Tests that should compile successfully.
for c, test in enumerate(PASS_TESTS):
    try:
        nida = Nidac(source=test)
        nida.compile()

    except Exception as e:
        error = True
        print(f"[FAIL] Pass-test #{c} failed unexpectedly:")
        print(f"{type(e).__name__}: {e}")
        print("\nTest source:")
        print(test)
        break

# Tests that should raise a Nidavellir error.
if not error:
    for c, test in enumerate(FAIL_TESTS):
        try:
            nida = Nidac(source=test)
            nida.compile()

        except NidavellirError as e:
            print(f"[PASS] Fail-test #{c}: {type(e).__name__}")
            continue

        except Exception as e:
            error = True
            print(f"[FAIL] Unexpected exception in fail-test #{c}:")
            print(f"{type(e).__name__}: {e}")
            print("\nTest source:")
            print(test)
            break

        else:
            error = True
            print(f"[FAIL] Expected error was NOT caught in fail-test #{c}")
            print("\nTest source:")
            print(test)
            break


if not error:
    print(f"ALL TESTS PASSED " f"({len(PASS_TESTS)} pass, {len(FAIL_TESTS)} fail)")
else:
    print("TEST SUITE FAILED")


t2 = time.perf_counter()
print(f"Time taken: {t2 - t1:.6f} seconds")
