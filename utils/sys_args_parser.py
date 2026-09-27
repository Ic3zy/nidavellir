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

        # Include Search Paths (-I / --include-path)
        parser.add_argument(
            "-I",
            "--include-path",
            type=Path,
            action="append",
            dest="include_paths",
            default=[],
            help="Additional search paths for headers and modules (can be specified multiple times)",
        )

        # Extra C Source Files to link (-cfile / --c-file)
        parser.add_argument(
            "-cfile",
            "--c-file",
            type=Path,
            action="append",
            dest="extra_c_files",
            default=[],
            help="Additional .c source files to compile and link into the final binary",
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

    def add_include_path(self, path: Path | str) -> None:
        path_obj = Path(path).resolve()
        if path_obj not in self.include_paths:
            self.include_paths.append(path_obj)

    def add_c_file(self, path: Path | str) -> None:
        path_obj = Path(path).resolve()
        if path_obj not in self.extra_c_files:
            self.extra_c_files.append(path_obj)
