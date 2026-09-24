import argparse
import sys
import tempfile
from pathlib import Path


class SysArgs:
    def __init__(self, args=None):
        if args is None:
            args = sys.argv[1:]

        parser = argparse.ArgumentParser(
            prog="nidavellir",
            description="Nidavellir Compiler Toolchain",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        # Positional Input File
        parser.add_argument(
            "file",
            type=Path,
            help="Path to the source .nida file",
        )

        # Optional Paths
        parser.add_argument(
            "-o",
            "--output",
            type=Path,
            default=None,
            help="Path for compiled binary executable (Defaults to temp directory)",
        )
        parser.add_argument(
            "--emit-c",
            type=Path,
            default=None,
            help="Path for generated C source file (Defaults to temp directory)",
        )

        # Feature flags
        parser.add_argument(
            "-np",
            "--no-print",
            action="store_true",
            help="Disables printing at compile time",
        )
        parser.add_argument(
            "-nr",
            "--no-auto-run",
            action="store_true",
            help="Disables automatic execution of the compiled binary",
        )
        parser.add_argument(
            "-nc",
            "--no-cache",
            action="store_true",
            help="Bypasses build cache and forces full re-compilation",
        )

        parsed = parser.parse_args(args)

        temp_dir = Path(tempfile.gettempdir())
        file_stem = parsed.file.stem

        if parsed.emit_c is None:
            parsed.emit_c = temp_dir / f"{file_stem}.c"

        if parsed.output is None:
            parsed.output = temp_dir / file_stem

        self.__dict__.update(vars(parsed))
