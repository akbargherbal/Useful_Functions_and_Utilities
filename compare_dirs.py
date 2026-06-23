#!/usr/bin/env python3

import argparse
import ast
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Tuple


def normalize_python_file(path: Path) -> str:
    """
    Normalize Python source code so formatting differences
    (blank lines, indentation, quote style, etc.) don't matter.

    We parse the AST and dump it back into a canonical form.
    """
    try:
        source = path.read_text(encoding="utf-8")

        # Parse into AST
        tree = ast.parse(source)

        # Canonical representation
        normalized = ast.dump(tree, annotate_fields=True, include_attributes=False)

        return normalized

    except SyntaxError as e:
        raise RuntimeError(f"Syntax error in {path}: {e}")

    except Exception as e:
        raise RuntimeError(f"Failed to process {path}: {e}")


def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def collect_files(directory: Path, extension: str) -> Dict[str, Path]:
    """
    Collect files recursively and map them by relative path.
    """
    files = {}

    for file_path in directory.rglob(f"*{extension}"):
        relative = str(file_path.relative_to(directory))
        files[relative] = file_path

    return files


def compare_directories(dir1: Path, dir2: Path, extension: str) -> Tuple[List[str], List[str], List[str]]:
    files1 = collect_files(dir1, extension)
    files2 = collect_files(dir2, extension)

    only_in_dir1 = sorted(set(files1) - set(files2))
    only_in_dir2 = sorted(set(files2) - set(files1))

    different_files = []

    common_files = sorted(set(files1) & set(files2))

    for rel_path in common_files:
        file1 = files1[rel_path]
        file2 = files2[rel_path]

        norm1 = normalize_python_file(file1)
        norm2 = normalize_python_file(file2)

        if hash_content(norm1) != hash_content(norm2):
            different_files.append(rel_path)

    return only_in_dir1, only_in_dir2, different_files


def main():
    parser = argparse.ArgumentParser(
        description="Compare two directories while ignoring Python formatting differences."
    )

    parser.add_argument("dir1", help="First directory")
    parser.add_argument("dir2", help="Second directory")
    parser.add_argument(
        "--ext",
        default=".py",
        help="File extension to compare (default: .py)"
    )

    args = parser.parse_args()

    dir1 = Path(args.dir1).resolve()
    dir2 = Path(args.dir2).resolve()

    if not dir1.is_dir():
        print(f"ERROR: {dir1} is not a directory")
        return

    if not dir2.is_dir():
        print(f"ERROR: {dir2} is not a directory")
        return

    only1, only2, different = compare_directories(dir1, dir2, args.ext)

    print("\n=== Comparison Result ===\n")

    if only1:
        print("Files only in first directory:")
        for f in only1:
            print(f"  {f}")
        print()

    if only2:
        print("Files only in second directory:")
        for f in only2:
            print(f"  {f}")
        print()

    if different:
        print("Files with REAL code differences:")
        for f in different:
            print(f"  {f}")
        print()
    else:
        print("No differing files found.\n")

    if not only1 and not only2 and not different:
        print("Directories are equivalent for the selected file type.")


if __name__ == "__main__":
    main()