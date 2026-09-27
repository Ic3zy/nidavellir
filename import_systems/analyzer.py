import subprocess


def check_header_exists(header_name: str, gcc_bin: str = "gcc") -> bool:
    cmd = [gcc_bin, "-x", "c", "-E", "-"]

    code_snippet = f"#include <{header_name}>\n"

    try:
        res = subprocess.run(
            cmd,
            input=code_snippet,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return res.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
