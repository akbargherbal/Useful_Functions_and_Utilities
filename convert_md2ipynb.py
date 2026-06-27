#!/usr/bin/env python3
"""
convert_md2ipynb.py
====================
Converts Markdown file(s) or directory of Markdown files to valid Jupyter Notebooks (.ipynb).

Usage:
    python convert_md2ipynb.py input.md
    python convert_md2ipynb.py input.md -o output.ipynb
    python convert_md2ipynb.py /path/to/dir
    python convert_md2ipynb.py /path/to/dir -o /output/dir
    python convert_md2ipynb.py input.md --kernel python3 --verbose

Handles:
    - Fenced code blocks  ``` python / ```py / ``` (bare)
    - IPython magic lines  %matplotlib inline, %%timeit, etc.
    - Shell escape lines   !pip install …, !ls, etc.
    - Multi-language kernels (python, bash, r, julia, …)
    - Markdown prose → Markdown cells
    - Consecutive blank lines collapsed in Markdown cells
    - Raw HTML blocks preserved in Markdown cells
    - Notebook-level metadata (kernelspec, language_info)
    - Deterministic cell IDs (short SHA-1 slices, Jupyter ≥ 4.5 compliant)
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Iterator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NBFORMAT = 4
NBFORMAT_MINOR = 5  # required for cell IDs (Jupyter ≥ 4.5)

# All aliases that map to a Python kernel
PYTHON_ALIASES = {
    "python",
    "python2",
    "python3",
    "py",
    "py2",
    "py3",
    "ipython",
    "ipython3",
}

# Fenced-code opening pattern
# Captures indent (rare but valid), fence chars, optional lang, optional extra attrs
_FENCE_OPEN = re.compile(
    r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})\s*(?P<lang>[^\s`~]*).*$"
)

# Lines that are always code even inside a "no-lang" block
_MAGIC_RE = re.compile(r"^\s*(%%|%)[a-zA-Z]")
_SHELL_RE = re.compile(r"^\s*!")

# ---------------------------------------------------------------------------
# Cell ID generation
# ---------------------------------------------------------------------------

_id_counter: dict[str, int] = {}


def _make_cell_id(source: str, index: int) -> str:
    """Return a stable 8-char hex cell ID (unique within the notebook)."""
    digest = hashlib.sha1(f"{index}:{source}".encode()).hexdigest()[:8]
    # Guarantee uniqueness if collision (extremely unlikely but correct)
    _id_counter[digest] = _id_counter.get(digest, 0) + 1
    if _id_counter[digest] > 1:
        digest = hashlib.sha1(
            f"{index}:{source}:{_id_counter[digest]}".encode()
        ).hexdigest()[:8]
    return digest


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _make_lines_iter(text: str) -> Iterator[str]:
    """Yield raw lines preserving line endings (needed for source fidelity)."""
    for line in text.splitlines(keepends=True):
        yield line


def _normalise_source(lines: list[str]) -> list[str]:
    """
    Jupyter convention: every line except the last ends with \n.
    Strip a trailing bare newline on the very last line only if it results
    in an empty string — keeps intentional trailing blank lines.
    """
    if not lines:
        return lines
    # Ensure each interior line ends with \n
    normalised = []
    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            normalised.append(line if line.endswith("\n") else line + "\n")
        else:
            # Last line: strip a lone trailing newline to match nbformat style
            normalised.append(line.rstrip("\n") if line == "\n" else line.rstrip("\n"))
    return normalised


# ---------------------------------------------------------------------------
# Core parser
# ---------------------------------------------------------------------------


class _Block:
    """Intermediate representation before turning into a Jupyter cell."""

    __slots__ = ("kind", "lang", "lines")

    def __init__(self, kind: str, lang: str = "") -> None:
        self.kind = kind  # "code" | "markdown"
        self.lang = lang  # detected language (empty = unknown/prose)
        self.lines: list[str] = []

    def is_empty(self) -> bool:
        return all(ln.strip() == "" for ln in self.lines)


def parse_markdown(text: str, default_lang: str = "python") -> list[_Block]:
    """
    State-machine parser.  Produces a flat list of _Block objects.

    Rules
    -----
    1. A fenced block with a known code language → code block with that lang.
    2. A fenced block with no language → inspect lines:
       - If any line looks like a magic/shell command → code block.
       - Otherwise → markdown block (raw fenced content preserved).
    3. Everything else → markdown block.
    4. Consecutive markdown blocks are merged.
    """
    blocks: list[_Block] = []
    current: _Block | None = None

    inside_fence = False
    fence_char = ""
    fence_indent = ""
    fence_lang = ""
    fence_raw_lines: list[str] = []  # raw content between fences

    def _flush_markdown(block: _Block) -> None:
        """Merge into previous markdown block or append."""
        if blocks and blocks[-1].kind == "markdown":
            # Separate with a blank line if not already blank
            if blocks[-1].lines and blocks[-1].lines[-1].strip():
                blocks[-1].lines.append("\n")
            blocks[-1].lines.extend(block.lines)
        else:
            blocks.append(block)

    def _flush_code_fence(lang: str, raw_lines: list[str]) -> None:
        """Decide whether fenced block is code or markdown."""
        has_magic_or_shell = any(
            _MAGIC_RE.match(ln) or _SHELL_RE.match(ln) for ln in raw_lines
        )
        # Treat text, txt, none, plain, etc. as non-code languages so they stay in markdown cells
        is_code_lang = lang and lang.lower() not in {
            "text",
            "txt",
            "none",
            "plain",
            "csv",
            "tsv",
            "markdown",
            "md",
            "html",
        }
        effective_lang = (
            lang if is_code_lang else (default_lang if has_magic_or_shell else "")
        )

        if effective_lang:
            b = _Block("code", effective_lang)
            b.lines = raw_lines[:]
            blocks.append(b)
        else:
            # Re-wrap as markdown fenced block
            b = _Block("markdown")
            fence = "```" if not lang else f"```{lang}"
            b.lines = [fence + "\n"] + raw_lines + ["```\n"]
            _flush_markdown(b)

    lines = list(_make_lines_iter(text))
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.rstrip("\n")

        # ── Inside a fenced block ──────────────────────────────────────────
        if inside_fence:
            close_match = re.match(
                rf"^{re.escape(fence_indent)}(?P<fence>{re.escape(fence_char)}+)\s*$",
                stripped,
            )
            if close_match:
                # Closing fence found
                _flush_code_fence(fence_lang, fence_raw_lines)
                inside_fence = False
                fence_char = ""
                fence_indent = ""
                fence_lang = ""
                fence_raw_lines = []
            else:
                fence_raw_lines.append(raw)
            i += 1
            continue

        # ── Opening fence? ─────────────────────────────────────────────────
        m = _FENCE_OPEN.match(stripped)
        if m:
            fence_char = m.group("fence")[0] * len(m.group("fence"))
            fence_indent = m.group("indent")
            fence_lang = (m.group("lang") or "").lower().strip()
            # Normalise language alias
            if fence_lang in PYTHON_ALIASES:
                fence_lang = "python"
            inside_fence = True
            fence_raw_lines = []
            i += 1
            continue

        # ── Prose / markdown line ──────────────────────────────────────────
        # Append directly onto the current markdown block instead of routing
        # through _flush_markdown(): that helper inserts a spacer blank line
        # whenever it merges onto a non-blank last line, which is correct for
        # joining whole re-wrapped fence blocks but wrong here — calling it
        # once per raw line injected a blank line between every two
        # consecutive non-blank lines (breaking tables, lists, etc.). Any
        # blank lines in the source are already preserved because blank
        # lines pass through this same branch as their own `raw` value.
        if blocks and blocks[-1].kind == "markdown":
            blocks[-1].lines.append(raw)
        else:
            b = _Block("markdown")
            b.lines.append(raw)
            blocks.append(b)
        i += 1

    # Handle unclosed fence (treat as code, best-effort)
    if inside_fence and fence_raw_lines:
        _flush_code_fence(fence_lang, fence_raw_lines)

    return [b for b in blocks if not b.is_empty()]


# ---------------------------------------------------------------------------
# Cell builders
# ---------------------------------------------------------------------------


def _build_code_cell(block: _Block, index: int) -> dict:
    src = _normalise_source(block.lines)
    return {
        "cell_type": "code",
        "id": _make_cell_id("".join(src), index),
        "metadata": {},
        "source": src,
        "outputs": [],
        "execution_count": None,
    }


def _build_markdown_cell(block: _Block, index: int) -> dict:
    src = _normalise_source(block.lines)
    return {
        "cell_type": "markdown",
        "id": _make_cell_id("".join(src), index),
        "metadata": {},
        "source": src,
    }


# ---------------------------------------------------------------------------
# Kernelspec helpers
# ---------------------------------------------------------------------------

_KERNELSPECS = {
    "python": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "r": {
        "display_name": "R",
        "language": "R",
        "name": "ir",
    },
    "julia": {
        "display_name": "Julia",
        "language": "julia",
        "name": "julia-1.9",
    },
    "bash": {
        "display_name": "Bash",
        "language": "bash",
        "name": "bash",
    },
    "javascript": {
        "display_name": "JavaScript (Node.js)",
        "language": "javascript",
        "name": "javascript",
    },
}

_LANGUAGE_INFO = {
    "python": {
        "name": "python",
        "version": "3.x",
        "mimetype": "text/x-python",
        "file_extension": ".py",
        "pygments_lexer": "ipython3",
        "codemirror_mode": {"name": "ipython", "version": 3},
    },
    "r": {
        "name": "R",
        "mimetype": "text/x-r-source",
        "file_extension": ".r",
        "pygments_lexer": "r",
    },
    "julia": {
        "name": "julia",
        "mimetype": "application/julia",
        "file_extension": ".jl",
    },
    "bash": {
        "name": "bash",
        "mimetype": "text/x-sh",
        "file_extension": ".sh",
    },
    "javascript": {
        "name": "javascript",
        "mimetype": "application/javascript",
        "file_extension": ".js",
    },
}


def _detect_kernel(blocks: list[_Block], override: str | None) -> str:
    """Return the dominant code language (or the CLI override)."""
    if override:
        return override.lower()
    counts: dict[str, int] = {}
    for b in blocks:
        if b.kind == "code" and b.lang:
            counts[b.lang] = counts.get(b.lang, 0) + 1
    if not counts:
        return "python"
    return max(counts, key=lambda k: counts[k])


def _build_metadata(kernel_lang: str) -> dict:
    ks = _KERNELSPECS.get(
        kernel_lang,
        {
            "display_name": kernel_lang.capitalize(),
            "language": kernel_lang,
            "name": kernel_lang,
        },
    )
    li = _LANGUAGE_INFO.get(
        kernel_lang,
        {
            "name": kernel_lang,
            "file_extension": f".{kernel_lang}",
        },
    )
    return {"kernelspec": ks, "language_info": li}


# ---------------------------------------------------------------------------
# Notebook assembler
# ---------------------------------------------------------------------------


def build_notebook(blocks: list[_Block], kernel_lang: str) -> dict:
    cells = []
    for idx, block in enumerate(blocks):
        if block.kind == "code":
            cells.append(_build_code_cell(block, idx))
        else:
            cells.append(_build_markdown_cell(block, idx))

    return {
        "nbformat": NBFORMAT,
        "nbformat_minor": NBFORMAT_MINOR,
        "metadata": _build_metadata(kernel_lang),
        "cells": cells,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Convert Markdown file(s) or directory of Markdown files to valid Jupyter Notebooks (.ipynb).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "input",
        type=Path,
        help="Path to the input .md file or directory containing markdown files",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output .ipynb path or target directory (default: beside each input file)",
    )
    p.add_argument(
        "--kernel",
        default=None,
        help="Force kernel language (python, r, julia, bash, …). "
        "Auto-detected from code blocks if omitted.",
    )
    p.add_argument(
        "--default-lang",
        default="python",
        help="Language assumed for bare ``` blocks that look like code (default: python)",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print a summary of detected cells for each converted file",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    input_path: Path = args.input.expanduser().resolve()
    if not input_path.exists():
        print(f"ERROR: Path not found: {input_path}", file=sys.stderr)
        return 1

    jobs: list[tuple[Path, Path]] = []

    if input_path.is_file():
        if args.output:
            output_path = args.output.expanduser().resolve()
            if output_path.is_dir():
                jobs.append(
                    (input_path, output_path / input_path.with_suffix(".ipynb").name)
                )
            else:
                jobs.append((input_path, output_path))
        else:
            jobs.append((input_path, input_path.with_suffix(".ipynb")))

    elif input_path.is_dir():
        if args.output:
            output_path = args.output.expanduser().resolve()
            if output_path.exists() and output_path.is_file():
                print(
                    f"ERROR: Input is a directory but output path is an existing file: {output_path}",
                    file=sys.stderr,
                )
                return 1
        else:
            output_path = None

        # Find all markdown files (globbing multiple extensions safely)
        md_files = []
        seen = set()
        for ext in ("*.md", "*.markdown", "*.MD", "*.MARKDOWN", "*.Markdown"):
            for p in input_path.rglob(ext):
                resolved = p.resolve()
                if resolved not in seen and resolved.is_file():
                    seen.add(resolved)
                    md_files.append(p)

        # Sort for deterministic processing order
        md_files.sort()

        if not md_files:
            print(
                f"WARNING: No markdown files found in directory: {input_path}",
                file=sys.stderr,
            )
            return 0

        for md_file in md_files:
            if output_path:
                # Maintain subdirectory structure under the output directory
                rel_path = md_file.relative_to(input_path)
                target_ipynb = (output_path / rel_path).with_suffix(".ipynb")
            else:
                target_ipynb = md_file.with_suffix(".ipynb")
            jobs.append((md_file, target_ipynb))

    else:
        print(
            f"ERROR: Path is neither a file nor a directory: {input_path}",
            file=sys.stderr,
        )
        return 1

    # Process all conversion jobs
    success_count = 0
    for md_path, ipynb_path in jobs:
        try:
            # ── Read ───────────────────────────────────────────────────────
            try:
                text = md_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = md_path.read_text(encoding="utf-8-sig", errors="replace")

            # ── Parse ──────────────────────────────────────────────────────
            blocks = parse_markdown(text, default_lang=args.default_lang)

            # ── Kernel detection ───────────────────────────────────────────
            kernel_lang = _detect_kernel(blocks, args.kernel)

            # ── Build notebook ─────────────────────────────────────────────
            notebook = build_notebook(blocks, kernel_lang)

            # ── Output path preparation & write ────────────────────────────
            ipynb_path.parent.mkdir(parents=True, exist_ok=True)
            ipynb_path.write_text(
                json.dumps(notebook, indent=1, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            # ── Output summary ─────────────────────────────────────────────
            n_code = sum(1 for b in blocks if b.kind == "code")
            n_md = sum(1 for b in blocks if b.kind == "markdown")

            try:
                display_md = md_path.relative_to(Path.cwd())
            except ValueError:
                display_md = md_path
            try:
                display_ipynb = ipynb_path.relative_to(Path.cwd())
            except ValueError:
                display_ipynb = ipynb_path

            print(f"✓  {display_md} -> {display_ipynb}")
            print(f"   kernel : {kernel_lang}")
            print(
                f"   cells  : {n_code} code  +  {n_md} markdown  =  {len(blocks)} total"
            )

            if args.verbose:
                print()
                for i, b in enumerate(blocks):
                    lang_tag = f"[{b.lang}]" if b.lang else ""
                    preview = "".join(b.lines[:2]).replace("\n", " ↵ ").strip()[:60]
                    print(f"  [{i:>3}] {b.kind:<8} {lang_tag:<10}  {preview}")
                print()

            success_count += 1

        except Exception as e:
            print(f"ERROR processing {md_path}: {e}", file=sys.stderr)

    if len(jobs) > 1:
        print(f"\nCompleted: {success_count}/{len(jobs)} files converted successfully.")

    return 0 if success_count == len(jobs) else 1


if __name__ == "__main__":
    sys.exit(main())
