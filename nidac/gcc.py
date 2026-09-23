import subprocess
from pathlib import Path


def compile_c_file(c_path: str | Path, output_path: str | Path) -> bool:
    cmd = [
        "gcc",
        str(c_path),
        "-o",
        str(output_path),
        "-O2",
        "-Wall",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("GCC error: ", result.stderr)
        return False

    print(f"Compilation successful: {c_path} -> {output_path}")
    return True


def run_compiled_file(
    bin_path: str | Path,
    args: list[str] = None,
    user_input: str = None,
    timeout: float = 5.0,
) -> int:
    print("\n\n\n")
    exec_path = Path(bin_path).resolve()

    if not exec_path.exists():
        print(f"Runner error: File not found -> {exec_path}")
        return -1

    cmd = [str(exec_path)]
    if args:
        cmd.extend(args)

    actual_timeout = timeout if timeout and timeout > 0 else None

    try:
        result = subprocess.run(
            cmd,
            input=user_input,
            text=True if user_input else None,
            timeout=actual_timeout,
        )
        return result.returncode

    except subprocess.TimeoutExpired:
        print(f"\nRunner error: Execution timed out after {timeout} seconds.")
        return -1
    except Exception as e:
        print(f"\nRunner error: {e}")
        return -1
