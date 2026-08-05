"""
Tests for convert_md2html.py

Run with:
    pytest
    (from inside the md2html/ folder, or `pytest md2html/`)

Requires: pytest, markdown, pygments
    pip install pytest markdown pygments
"""
import subprocess
import sys
from pathlib import Path

import pytest

# Make the script importable as a module (it lives one directory up from tests/)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import convert_md2html as m  # noqa: E402  (import after sys.path tweak)

SCRIPT = ROOT / "convert_md2html.py"


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────

def run_cli(*args):
    """Run the script as a subprocess and return the CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


SAMPLE_MD = """\
# My Sample Title

Some **bold** intro text.

## Section One

Body content.

```python
print("hi")
```
"""

NO_H1_MD = """\
Just a paragraph, no heading at all.
"""


# ─────────────────────────────────────────────────────────────────────────
# Unit tests: argument parser
# ─────────────────────────────────────────────────────────────────────────

class TestArgParser:
    def test_defaults(self):
        args = m.build_parser().parse_args(["file.md"])
        assert args.source == "file.md"
        assert args.output is None
        assert args.prefix == ""
        assert args.lang == "en"
        assert args.code_heavy is False
        assert args.prose is False
        assert args.quiet is False
        assert args.recursive is False
        assert args.home_url == ""

    def test_prose_and_no_code_are_aliases(self):
        args1 = m.build_parser().parse_args(["file.md", "--prose"])
        args2 = m.build_parser().parse_args(["file.md", "--no-code"])
        assert args1.prose is True
        assert args2.prose is True

    def test_code_heavy_flag(self):
        args = m.build_parser().parse_args(["file.md", "--code-heavy"])
        assert args.code_heavy is True

    def test_output_and_prefix(self):
        args = m.build_parser().parse_args(
            ["src", "-o", "out_dir", "--prefix", "docs_"]
        )
        assert args.output == "out_dir"
        assert args.prefix == "docs_"

    def test_home_url(self):
        args = m.build_parser().parse_args(["file.md", "--home-url", "../index.html"])
        assert args.home_url == "../index.html"


# ─────────────────────────────────────────────────────────────────────────
# Unit tests: RTL language detection
# ─────────────────────────────────────────────────────────────────────────

class TestRtlDetection:
    @pytest.mark.parametrize("lang", ["ar", "he", "fa", "ur", "yi", "ps"])
    def test_known_rtl_languages(self, lang):
        assert lang in m.RTL_LANGUAGES

    @pytest.mark.parametrize("lang", ["en", "fr", "de", "es", "zh"])
    def test_known_ltr_languages(self, lang):
        assert lang not in m.RTL_LANGUAGES


# ─────────────────────────────────────────────────────────────────────────
# Unit tests: markdown extension selection
# ─────────────────────────────────────────────────────────────────────────

class TestMdExtensions:
    def test_default_extensions_include_codehilite(self):
        exts = m._md_extensions(code_heavy=False, prose=False)
        assert "codehilite" in exts
        assert "extra" not in exts

    def test_prose_mode_disables_codehilite(self):
        exts = m._md_extensions(code_heavy=False, prose=True)
        assert "codehilite" not in exts

    def test_code_heavy_adds_extra(self):
        exts = m._md_extensions(code_heavy=True, prose=False)
        assert "extra" in exts
        assert "codehilite" in exts

    def test_base_extensions_always_present(self):
        exts = m._md_extensions(code_heavy=False, prose=False)
        for required in ("fenced_code", "tables", "toc", "footnotes"):
            assert required in exts


# ─────────────────────────────────────────────────────────────────────────
# Unit tests: convert_file()
# ─────────────────────────────────────────────────────────────────────────

class TestConvertFile:
    @pytest.fixture
    def pygments_css(self):
        return m._pygments_css()

    def test_creates_output_file(self, tmp_path, pygments_css):
        src = tmp_path / "doc.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        out_path = m.convert_file(
            src=src, out_dir=out_dir, prefix="", lang="en", rtl=False,
            code_heavy=False, prose=False, pygments_css=pygments_css, verbose=False,
        )
        assert out_path.exists()
        assert out_path.suffix == ".html"

    def test_title_extracted_from_h1(self, tmp_path, pygments_css):
        src = tmp_path / "doc.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out_path = m.convert_file(
            src=src, out_dir=tmp_path, prefix="", lang="en", rtl=False,
            code_heavy=False, prose=False, pygments_css=pygments_css, verbose=False,
        )
        html = out_path.read_text(encoding="utf-8")
        assert "<title>My Sample Title</title>" in html
        assert 'id="doc-title">My Sample Title<' in html

    def test_title_falls_back_to_filename(self, tmp_path, pygments_css):
        src = tmp_path / "my_cool-doc.md"
        src.write_text(NO_H1_MD, encoding="utf-8")
        out_path = m.convert_file(
            src=src, out_dir=tmp_path, prefix="", lang="en", rtl=False,
            code_heavy=False, prose=False, pygments_css=pygments_css, verbose=False,
        )
        html = out_path.read_text(encoding="utf-8")
        assert "My Cool Doc" in html

    def test_prefix_applied_to_output_filename(self, tmp_path, pygments_css):
        src = tmp_path / "doc.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out_path = m.convert_file(
            src=src, out_dir=tmp_path, prefix="site_", lang="en", rtl=False,
            code_heavy=False, prose=False, pygments_css=pygments_css, verbose=False,
        )
        assert out_path.name == "site_doc.html"

    def test_rtl_sets_html_dir_attribute(self, tmp_path, pygments_css):
        src = tmp_path / "doc.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out_path = m.convert_file(
            src=src, out_dir=tmp_path, prefix="", lang="ar", rtl=True,
            code_heavy=False, prose=False, pygments_css=pygments_css, verbose=False,
        )
        html = out_path.read_text(encoding="utf-8")
        assert 'dir="rtl"' in html
        assert 'lang="ar"' in html

    def test_ltr_sets_html_dir_attribute(self, tmp_path, pygments_css):
        src = tmp_path / "doc.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out_path = m.convert_file(
            src=src, out_dir=tmp_path, prefix="", lang="en", rtl=False,
            code_heavy=False, prose=False, pygments_css=pygments_css, verbose=False,
        )
        html = out_path.read_text(encoding="utf-8")
        assert 'dir="ltr"' in html

    def test_home_url_renders_home_button(self, tmp_path, pygments_css):
        src = tmp_path / "doc.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out_path = m.convert_file(
            src=src, out_dir=tmp_path, prefix="", lang="en", rtl=False,
            code_heavy=False, prose=False, pygments_css=pygments_css, verbose=False,
            home_url="../index.html",
        )
        html = out_path.read_text(encoding="utf-8")
        assert 'id="home-btn"' in html
        assert 'href="../index.html"' in html

    def test_no_home_url_omits_home_button(self, tmp_path, pygments_css):
        src = tmp_path / "doc.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out_path = m.convert_file(
            src=src, out_dir=tmp_path, prefix="", lang="en", rtl=False,
            code_heavy=False, prose=False, pygments_css=pygments_css, verbose=False,
        )
        html = out_path.read_text(encoding="utf-8")
        assert 'id="home-btn"' not in html

    def test_code_block_is_highlighted(self, tmp_path, pygments_css):
        src = tmp_path / "doc.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out_path = m.convert_file(
            src=src, out_dir=tmp_path, prefix="", lang="en", rtl=False,
            code_heavy=False, prose=False, pygments_css=pygments_css, verbose=False,
        )
        html = out_path.read_text(encoding="utf-8")
        assert "codehilite" in html


# ─────────────────────────────────────────────────────────────────────────
# Unit tests: collapsible sidebar markup (new feature)
# ─────────────────────────────────────────────────────────────────────────

class TestCollapsibleSidebar:
    @pytest.fixture
    def html(self, tmp_path):
        pygments_css = m._pygments_css()
        src = tmp_path / "doc.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out_path = m.convert_file(
            src=src, out_dir=tmp_path, prefix="", lang="en", rtl=False,
            code_heavy=False, prose=False, pygments_css=pygments_css, verbose=False,
        )
        return out_path.read_text(encoding="utf-8")

    def test_collapse_button_present(self, html):
        assert 'id="sidebar-collapse-btn"' in html

    def test_sidebar_header_wraps_title_and_button(self, html):
        assert 'id="sidebar-header"' in html
        header_start = html.index('id="sidebar-header"')
        header_chunk = html[header_start:header_start + 400]
        assert 'id="sidebar-title"' in header_chunk
        assert 'id="sidebar-collapse-btn"' in header_chunk

    def test_collapsed_css_rule_shrinks_width(self, html):
        assert "#sidebar.collapsed" in html
        assert "width: 56px" in html

    def test_collapsed_css_hides_toc_and_title(self, html):
        assert "#sidebar.collapsed #sidebar-title,\n    #sidebar.collapsed #toc" in html \
            or "#sidebar.collapsed #toc" in html

    def test_js_toggle_listener_present(self, html):
        assert "sidebar-collapse-btn" in html
        assert "classList.toggle('collapsed')" in html

    def test_collapse_independent_of_mobile_toggle(self, html):
        # The pre-existing mobile hamburger toggle must still be present
        # and distinct from the new collapse button.
        assert 'id="sidebar-toggle"' in html
        assert "classList.toggle('open')" in html


# ─────────────────────────────────────────────────────────────────────────
# CLI / integration tests (subprocess, closest to real usage)
# ─────────────────────────────────────────────────────────────────────────

class TestCli:
    def test_single_file_conversion(self, tmp_path):
        src = tmp_path / "readme.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out_dir = tmp_path / "out"

        result = run_cli(str(src), "-o", str(out_dir))

        assert result.returncode == 0
        assert (out_dir / "readme.html").exists()
        assert "converted" in result.stdout.lower()

    def test_quiet_mode_suppresses_output(self, tmp_path):
        src = tmp_path / "readme.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out_dir = tmp_path / "out"

        result = run_cli(str(src), "-o", str(out_dir), "-q")

        assert result.returncode == 0
        assert result.stdout.strip() == ""
        assert (out_dir / "readme.html").exists()

    def test_directory_conversion(self, tmp_path):
        src_dir = tmp_path / "docs"
        src_dir.mkdir()
        (src_dir / "one.md").write_text(SAMPLE_MD, encoding="utf-8")
        (src_dir / "two.md").write_text(NO_H1_MD, encoding="utf-8")
        out_dir = tmp_path / "site"

        result = run_cli(str(src_dir), "-o", str(out_dir), "--prefix", "doc_")

        assert result.returncode == 0
        assert (out_dir / "doc_one.html").exists()
        assert (out_dir / "doc_two.html").exists()

    def test_recursive_directory_conversion(self, tmp_path):
        src_dir = tmp_path / "docs"
        nested = src_dir / "nested"
        nested.mkdir(parents=True)
        (src_dir / "top.md").write_text(SAMPLE_MD, encoding="utf-8")
        (nested / "deep.md").write_text(SAMPLE_MD, encoding="utf-8")
        out_dir = tmp_path / "site"

        result = run_cli(str(src_dir), "-o", str(out_dir), "-r")

        assert result.returncode == 0
        assert (out_dir / "top.html").exists()
        assert (out_dir / "deep.html").exists()

    def test_nonexistent_source_errors(self, tmp_path):
        missing = tmp_path / "nope.md"
        result = run_cli(str(missing))
        assert result.returncode == 1
        assert "not found" in result.stderr.lower()

    def test_wrong_extension_errors(self, tmp_path):
        src = tmp_path / "notes.txt"
        src.write_text("hello", encoding="utf-8")
        result = run_cli(str(src))
        assert result.returncode == 1
        assert ".md" in result.stderr or "markdown" in result.stderr.lower()

    def test_empty_directory_exits_cleanly(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        result = run_cli(str(empty_dir))
        assert result.returncode == 0
        assert "no markdown files" in result.stderr.lower()

    def test_arabic_lang_produces_rtl_output(self, tmp_path):
        src = tmp_path / "doc.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out_dir = tmp_path / "out"

        result = run_cli(str(src), "-o", str(out_dir), "--lang", "ar")

        assert result.returncode == 0
        html = (out_dir / "doc.html").read_text(encoding="utf-8")
        assert 'dir="rtl"' in html

    def test_prose_mode_end_to_end(self, tmp_path):
        src = tmp_path / "poem.md"
        src.write_text("# A Poem\n\n```\nRoses are red\nViolets are blue\n```\n", encoding="utf-8")
        out_dir = tmp_path / "out"

        result = run_cli(str(src), "-o", str(out_dir), "--lang", "ar", "--prose")

        assert result.returncode == 0
        html = (out_dir / "poem.html").read_text(encoding="utf-8")
        assert "Amiri" in html

    def test_code_heavy_end_to_end(self, tmp_path):
        src = tmp_path / "algo.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out_dir = tmp_path / "out"

        result = run_cli(str(src), "-o", str(out_dir), "--code-heavy")

        assert result.returncode == 0
        html = (out_dir / "algo.html").read_text(encoding="utf-8")
        assert "linenos" in html or "codehilite" in html


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
