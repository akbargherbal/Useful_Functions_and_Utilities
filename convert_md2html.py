#!/usr/bin/env python3
"""
md2html.py — Markdown → polished HTML converter
-------------------------------------------------
Converts a single Markdown file or an entire directory of Markdown files
into beautifully styled, self-contained HTML pages ready for desktop viewing.

Usage:
  python md2html.py <source> [options]

Examples:
  python md2html.py README.md
  python md2html.py ./docs -o ./site --prefix docs_
  python md2html.py notes.md --lang ar
  python md2html.py algorithms.md --code-heavy
  python md2html.py ./src --prefix v2_ -o ./out --lang ar --code-heavy
"""

import argparse
import re
import sys
import textwrap
from pathlib import Path

# ─── Optional dependency check ────────────────────────────────────────────────

def _check_deps() -> None:
    missing = []
    for pkg, pip_name in [("markdown", "markdown"), ("pygments", "pygments")]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pip_name)
    if missing:
        print(
            "❌  Missing dependencies. Install them with:\n"
            f"    pip install {' '.join(missing)}\n"
            "\n    Recommended full install:\n"
            "    pip install markdown pygments",
            file=sys.stderr,
        )
        sys.exit(1)

_check_deps()

import markdown  # noqa: E402 — imported after dep-check
from pygments.formatters import HtmlFormatter  # noqa: E402

# ─── Styling ──────────────────────────────────────────────────────────────────

def _pygments_css() -> str:
    """Return the Pygments CSS for the 'one-dark' style (fallback: monokai)."""
    try:
        fmt = HtmlFormatter(style="one-dark", cssclass="codehilite")
    except Exception:
        fmt = HtmlFormatter(style="monokai", cssclass="codehilite")
    return fmt.get_style_defs(".codehilite")


def _build_html(
    body_html: str,
    title: str,
    lang: str,
    rtl: bool,
    code_heavy: bool,
    pygments_css: str,
) -> str:
    direction = "rtl" if rtl else "ltr"
    text_align = "right" if rtl else "left"
    # Slightly wider max-width for code-heavy docs so lines don't wrap too early
    content_max = "1100px" if code_heavy else "860px"

    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{direction}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>

  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,600;1,9..144,300&family=JetBrains+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet" />

  <style>
    /* ── Reset & base ──────────────────────────────────────── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      /* Palette — dark editorial */
      --bg:          #0f1117;
      --surface:     #161b27;
      --surface2:    #1e2535;
      --border:      #2a3348;
      --accent:      #e8c87d;        /* warm gold */
      --accent2:     #6eb5ff;        /* sky blue for links / inline code */
      --text:        #d4dce8;
      --text-muted:  #7a8aa0;
      --text-strong: #eef2f8;

      /* Typography */
      --font-body:   'DM Sans', sans-serif;
      --font-head:   'Fraunces', Georgia, serif;
      --font-mono:   'JetBrains Mono', 'Fira Code', monospace;

      /* Layout */
      --content-max: {content_max};
      --sidebar-w:   260px;
      --gap:         2rem;
    }}

    html {{ scroll-behavior: smooth; }}

    body {{
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-body);
      font-size: clamp(16px, 1.1vw, 18px);
      line-height: 1.8;
      text-align: {text_align};
      -webkit-font-smoothing: antialiased;
      display: flex;
      min-height: 100vh;
    }}

    /* ── Progress bar ──────────────────────────────────────── */
    #progress {{
      position: fixed;
      top: 0; left: 0;
      height: 3px;
      width: 0%;
      background: linear-gradient(90deg, var(--accent), var(--accent2));
      z-index: 1000;
      transition: width 0.1s linear;
    }}

    /* ── Sidebar TOC ───────────────────────────────────────── */
    #sidebar {{
      position: fixed;
      top: 0;
      {'right' if rtl else 'left'}: 0;
      width: var(--sidebar-w);
      height: 100vh;
      overflow-y: auto;
      background: var(--surface);
      border-{'left' if rtl else 'right'}: 1px solid var(--border);
      padding: 2rem 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      z-index: 100;
      scrollbar-width: thin;
      scrollbar-color: var(--border) transparent;
    }}

    #sidebar-title {{
      font-family: var(--font-head);
      font-size: 0.75rem;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: var(--accent);
      margin-bottom: 1rem;
    }}

    #toc {{ list-style: none; }}
    #toc li {{ line-height: 1.4; }}
    #toc a {{
      display: block;
      padding: 0.25rem 0.5rem;
      font-size: 0.82rem;
      color: var(--text-muted);
      text-decoration: none;
      border-radius: 4px;
      transition: background 0.15s, color 0.15s;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    #toc a:hover, #toc a.active {{
      background: var(--surface2);
      color: var(--text-strong);
    }}
    #toc .toc-h2 {{ padding-{'right' if rtl else 'left'}: 0.5rem; }}
    #toc .toc-h3 {{ padding-{'right' if rtl else 'left'}: 1.25rem; font-size: 0.77rem; }}
    #toc .toc-h4 {{ padding-{'right' if rtl else 'left'}: 2rem;   font-size: 0.73rem; color: var(--border); }}

    /* ── Main content ──────────────────────────────────────── */
    #main {{
      margin-{'right' if rtl else 'left'}: var(--sidebar-w);
      flex: 1;
      display: flex;
      justify-content: center;
      padding: 4rem var(--gap) 6rem;
    }}

    article {{
      width: 100%;
      max-width: var(--content-max);
    }}

    /* ── Header strip ──────────────────────────────────────── */
    #doc-header {{
      margin-bottom: 3.5rem;
      padding-bottom: 2rem;
      border-bottom: 1px solid var(--border);
      position: relative;
    }}
    #doc-header::before {{
      content: '';
      position: absolute;
      bottom: -1px;
      {'right' if rtl else 'left'}: 0;
      width: 80px;
      height: 1px;
      background: var(--accent);
    }}
    #doc-title {{
      font-family: var(--font-head);
      font-size: clamp(2rem, 3.5vw, 3.2rem);
      font-weight: 600;
      color: var(--text-strong);
      line-height: 1.15;
      letter-spacing: -0.01em;
    }}
    #doc-meta {{
      margin-top: 0.6rem;
      font-size: 0.82rem;
      color: var(--text-muted);
      font-family: var(--font-mono);
    }}

    /* ── Headings ──────────────────────────────────────────── */
    h1, h2, h3, h4, h5, h6 {{
      font-family: var(--font-head);
      color: var(--text-strong);
      line-height: 1.2;
      font-weight: 600;
      scroll-margin-top: 2rem;
    }}
    h1 {{ font-size: clamp(1.7rem, 2.5vw, 2.4rem); margin: 3rem 0 1.2rem; }}
    h2 {{
      font-size: clamp(1.35rem, 2vw, 1.85rem);
      margin: 2.8rem 0 1rem;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid var(--border);
    }}
    h3 {{ font-size: clamp(1.1rem, 1.5vw, 1.4rem); margin: 2.2rem 0 0.8rem; }}
    h4 {{ font-size: 1.05rem; margin: 1.8rem 0 0.6rem; color: var(--accent); }}
    h5, h6 {{ font-size: 0.95rem; margin: 1.5rem 0 0.5rem; font-weight: 500; }}

    /* ── Paragraphs & text ─────────────────────────────────── */
    p {{ margin-bottom: 1.25rem; }}
    strong {{ color: var(--text-strong); font-weight: 600; }}
    em {{ font-style: italic; color: var(--accent); }}
    del {{ color: var(--text-muted); }}
    mark {{
      background: rgba(232, 200, 125, 0.2);
      color: var(--accent);
      border-radius: 2px;
      padding: 0 3px;
    }}

    /* ── Links ─────────────────────────────────────────────── */
    a {{
      color: var(--accent2);
      text-decoration: none;
      border-bottom: 1px solid transparent;
      transition: border-color 0.15s;
    }}
    a:hover {{ border-bottom-color: var(--accent2); }}

    /* ── Lists ─────────────────────────────────────────────── */
    ul, ol {{
      margin: 0.75rem 0 1.25rem;
      padding-{'right' if rtl else 'left'}: 1.8rem;
    }}
    li {{ margin-bottom: 0.4rem; }}
    li > ul, li > ol {{ margin-bottom: 0; }}
    ul li::marker {{ color: var(--accent); }}
    ol li::marker {{ color: var(--accent); font-family: var(--font-mono); font-size: 0.85em; }}

    /* ── Inline code ───────────────────────────────────────── */
    code:not([class]) {{
      font-family: var(--font-mono);
      font-size: 0.85em;
      background: var(--surface2);
      color: var(--accent2);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 0.15em 0.45em;
    }}

    /* ── Code blocks (Pygments) ────────────────────────────── */
    .codehilite {{
      background: #111827 !important;
      border: 1px solid var(--border);
      border-radius: 10px;
      overflow: hidden;
      margin: 1.75rem 0;
      position: relative;
      box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    }}

    .code-wrap {{
      position: relative;
    }}

    .code-lang {{
      position: absolute;
      top: 0;
      {'left' if not rtl else 'right'}: 0;
      font-family: var(--font-mono);
      font-size: 0.7rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--text-muted);
      padding: 0.5rem 1rem;
      background: rgba(255,255,255,0.03);
      border-bottom: 1px solid var(--border);
      border-{'right' if not rtl else 'left'}: 1px solid var(--border);
      border-{'bottom-right' if not rtl else 'bottom-left'}-radius: 6px;
      user-select: none;
    }}

    .copy-btn {{
      position: absolute;
      top: 0.5rem;
      {'right' if not rtl else 'left'}: 0.75rem;
      background: var(--surface2);
      border: 1px solid var(--border);
      color: var(--text-muted);
      font-family: var(--font-mono);
      font-size: 0.72rem;
      padding: 0.25rem 0.65rem;
      border-radius: 4px;
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
      z-index: 2;
    }}
    .copy-btn:hover {{ background: var(--border); color: var(--text-strong); }}
    .copy-btn.copied {{ color: #7dffaa; border-color: #7dffaa44; }}

    .codehilite pre {{
      margin: 0 !important;
      padding: 2.8rem 1.5rem 1.5rem !important;
      font-family: var(--font-mono) !important;
      font-size: clamp(0.78rem, 0.9vw, 0.88rem) !important;
      line-height: 1.7 !important;
      overflow-x: auto;
      tab-size: 4;
    }}

    /* ── Plain fenced blocks (no lang) ────────────────────── */
    pre:not(.codehilite pre) {{
      background: #111827;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.5rem;
      overflow-x: auto;
      font-family: var(--font-mono);
      font-size: 0.86rem;
      line-height: 1.7;
      margin: 1.75rem 0;
    }}

    /* ── Blockquotes ───────────────────────────────────────── */
    blockquote {{
      border-{'right' if rtl else 'left'}: 3px solid var(--accent);
      margin: 1.5rem 0;
      padding: 1rem 1.5rem;
      background: var(--surface2);
      border-radius: 0 8px 8px 0;
      color: var(--text-muted);
      font-style: italic;
    }}
    blockquote p {{ margin-bottom: 0; }}

    /* ── Tables ────────────────────────────────────────────── */
    .table-wrap {{ overflow-x: auto; margin: 1.75rem 0; border-radius: 10px; border: 1px solid var(--border); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
    }}
    thead {{
      background: var(--surface2);
    }}
    th {{
      font-family: var(--font-mono);
      font-size: 0.78rem;
      letter-spacing: 0.07em;
      text-transform: uppercase;
      color: var(--accent);
      padding: 0.8rem 1.1rem;
      text-align: {text_align};
      border-bottom: 1px solid var(--border);
      font-weight: 500;
    }}
    td {{
      padding: 0.7rem 1.1rem;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: rgba(255,255,255,0.02); }}

    /* ── Horizontal rule ───────────────────────────────────── */
    hr {{
      border: none;
      height: 1px;
      background: linear-gradient(90deg, var(--accent), transparent);
      margin: 2.5rem 0;
    }}

    /* ── Task lists ────────────────────────────────────────── */
    .task-list-item input[type="checkbox"] {{
      accent-color: var(--accent);
      margin-{'left' if rtl else 'right'}: 0.5rem;
    }}

    /* ── Images ────────────────────────────────────────────── */
    img {{
      max-width: 100%;
      border-radius: 8px;
      border: 1px solid var(--border);
      display: block;
      margin: 1.5rem auto;
    }}

    /* ── Footnotes ─────────────────────────────────────────── */
    .footnote {{
      border-top: 1px solid var(--border);
      margin-top: 3rem;
      padding-top: 1rem;
      font-size: 0.82rem;
      color: var(--text-muted);
    }}

    /* ── Back to top ───────────────────────────────────────── */
    #back-top {{
      position: fixed;
      bottom: 2rem;
      {'left' if rtl else 'right'}: 2rem;
      width: 40px;
      height: 40px;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--text-muted);
      text-decoration: none;
      font-size: 1.1rem;
      opacity: 0;
      transform: translateY(8px);
      transition: opacity 0.2s, transform 0.2s, color 0.15s;
      z-index: 200;
    }}
    #back-top.visible {{ opacity: 1; transform: translateY(0); }}
    #back-top:hover {{ color: var(--accent); border-color: var(--accent); }}

    /* ── Sidebar toggle (hidden on wide screens) ───────────── */
    #sidebar-toggle {{
      display: none;
      position: fixed;
      bottom: 2rem;
      {'right' if rtl else 'left'}: 1rem;
      z-index: 300;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.4rem 0.75rem;
      color: var(--text-muted);
      font-size: 0.8rem;
      font-family: var(--font-mono);
      cursor: pointer;
    }}

    /* ── Scrollbar ─────────────────────────────────────────── */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}

    /* ── Animations ────────────────────────────────────────── */
    @keyframes fadeUp {{
      from {{ opacity: 0; transform: translateY(14px); }}
      to   {{ opacity: 1; transform: translateY(0);    }}
    }}
    article {{ animation: fadeUp 0.45s ease both; }}

    /* ── Responsive ────────────────────────────────────────── */
    @media (max-width: 1100px) {{
      :root {{ --sidebar-w: 220px; }}
    }}
    @media (max-width: 820px) {{
      #sidebar {{ transform: translateX({'100%' if rtl else '-100%'}); transition: transform 0.25s; }}
      #sidebar.open {{ transform: translateX(0); }}
      #main {{ margin-{'right' if rtl else 'left'}: 0 !important; }}
      #sidebar-toggle {{ display: block; }}
    }}

    /* ── Pygments injected ─────────────────────────────────── */
    {pygments_css}
  </style>
</head>
<body>

<div id="progress"></div>

<!-- Sidebar -->
<nav id="sidebar" aria-label="Table of contents">
  <div id="sidebar-title">Contents</div>
  <ul id="toc"></ul>
</nav>

<button id="sidebar-toggle" aria-label="Toggle sidebar">☰ TOC</button>

<!-- Main -->
<div id="main">
  <article>
    <header id="doc-header">
      <h1 id="doc-title">{title}</h1>
      <div id="doc-meta"></div>
    </header>

    {body_html}
  </article>
</div>

<a id="back-top" href="#" title="Back to top" aria-label="Back to top">↑</a>

<script>
(function () {{
  // ── Reading progress ──────────────────────────────────────
  const bar = document.getElementById('progress');
  window.addEventListener('scroll', () => {{
    const h = document.documentElement;
    const pct = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100;
    bar.style.width = pct + '%';
  }}, {{ passive: true }});

  // ── Build TOC from headings ───────────────────────────────
  const article = document.querySelector('article');
  const toc     = document.getElementById('toc');
  const headings = article.querySelectorAll('h1,h2,h3,h4');
  let idx = 0;

  headings.forEach(h => {{
    if (h.id === 'doc-title') return;
    if (!h.id) {{ h.id = 'heading-' + (idx++); }}
    const li  = document.createElement('li');
    const a   = document.createElement('a');
    a.href    = '#' + h.id;
    a.textContent = h.textContent;
    a.className   = 'toc-' + h.tagName.toLowerCase();
    li.appendChild(a);
    toc.appendChild(li);
  }});

  // ── Active TOC highlight on scroll ───────────────────────
  const tocLinks = toc.querySelectorAll('a');
  const observer = new IntersectionObserver(entries => {{
    entries.forEach(e => {{
      const link = toc.querySelector('a[href="#' + e.target.id + '"]');
      if (link) link.classList.toggle('active', e.isIntersecting);
    }});
  }}, {{ rootMargin: '-10% 0px -80% 0px' }});
  headings.forEach(h => {{ if (h.id !== 'doc-title') observer.observe(h); }});

  // ── Back-to-top visibility ────────────────────────────────
  const btt = document.getElementById('back-top');
  window.addEventListener('scroll', () => {{
    btt.classList.toggle('visible', window.scrollY > 300);
  }}, {{ passive: true }});
  btt.addEventListener('click', e => {{
    e.preventDefault();
    window.scrollTo({{ top: 0, behavior: 'smooth' }});
  }});

  // ── Sidebar toggle (mobile) ───────────────────────────────
  document.getElementById('sidebar-toggle').addEventListener('click', () => {{
    document.getElementById('sidebar').classList.toggle('open');
  }});

  // ── Copy buttons on code blocks ───────────────────────────
  document.querySelectorAll('.codehilite').forEach(block => {{
    const btn  = document.createElement('button');
    btn.className   = 'copy-btn';
    btn.textContent = 'Copy';
    btn.setAttribute('aria-label', 'Copy code');
    block.style.position = 'relative';
    block.prepend(btn);
    btn.addEventListener('click', () => {{
      const code = block.querySelector('pre')?.innerText ?? '';
      navigator.clipboard.writeText(code).then(() => {{
        btn.textContent = '✓ Copied';
        btn.classList.add('copied');
        setTimeout(() => {{ btn.textContent = 'Copy'; btn.classList.remove('copied'); }}, 2000);
      }});
    }});
  }});

  // ── Wrap tables for horizontal scroll ────────────────────
  document.querySelectorAll('article table').forEach(t => {{
    const w = document.createElement('div');
    w.className = 'table-wrap';
    t.parentNode.insertBefore(w, t);
    w.appendChild(t);
  }});

  // ── Doc meta (word count + read time) ────────────────────
  const words = article.innerText.trim().split(/\\s+/).length;
  const mins  = Math.max(1, Math.round(words / 200));
  const meta  = document.getElementById('doc-meta');
  if (meta) meta.textContent = words.toLocaleString() + ' words · ' + mins + ' min read';
}})();
</script>

</body>
</html>"""


# ─── Markdown → HTML conversion ───────────────────────────────────────────────

def _md_extensions(code_heavy: bool) -> list:
    exts = [
        "fenced_code",
        "codehilite",
        "tables",
        "toc",
        "footnotes",
        "attr_list",
        "def_list",
        "abbr",
        "admonition",
        "meta",
        "nl2br",
        "sane_lists",
        "smarty",
        "wikilinks",
    ]
    if code_heavy:
        exts.append("extra")
    return exts


def _md_extension_configs(code_heavy: bool) -> dict:
    return {
        "codehilite": {
            "guess_lang": code_heavy,
            "linenums": code_heavy,
            "css_class": "codehilite",
        },
        "toc": {
            "permalink": True,
            "permalink_class": "headerlink",
        },
    }


def convert_file(
    src: Path,
    out_dir: Path,
    prefix: str,
    lang: str,
    rtl: bool,
    code_heavy: bool,
    pygments_css: str,
    verbose: bool,
) -> Path:
    text = src.read_text(encoding="utf-8")

    md = markdown.Markdown(
        extensions=_md_extensions(code_heavy),
        extension_configs=_md_extension_configs(code_heavy),
        output_format="html",
    )
    body_html = md.convert(text)

    # Derive title from first H1 in source, fall back to filename
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else src.stem.replace("_", " ").replace("-", " ").title()
    # Strip any markdown from title
    title = re.sub(r"[*_`~]", "", title)

    html = _build_html(
        body_html=body_html,
        title=title,
        lang=lang,
        rtl=rtl,
        code_heavy=code_heavy,
        pygments_css=pygments_css,
    )

    out_name = f"{prefix}{src.stem}.html"
    out_path = out_dir / out_name
    out_path.write_text(html, encoding="utf-8")

    if verbose:
        print(f"  ✓  {src}  →  {out_path}")
    return out_path


# ─── CLI ──────────────────────────────────────────────────────────────────────

RTL_LANGUAGES = {
    "ar", "he", "fa", "ur", "yi", "ps", "sd", "ug", "ckb",
    "arabic", "hebrew", "persian", "farsi", "urdu",
}

HELP_EPILOG = textwrap.dedent("""\
examples:
  # Convert a single file (output next to source)
  python md2html.py README.md

  # Convert a directory, save to ./site, prefix each file
  python md2html.py ./docs -o ./site --prefix docs_

  # Arabic RTL document
  python md2html.py notes.md --lang ar

  # Code-heavy file (line numbers, language guessing)
  python md2html.py algorithms.md --code-heavy

  # Full combo
  python md2html.py ./src --prefix v2_ -o ./out --lang ar --code-heavy

  # Quiet mode (no per-file output)
  python md2html.py ./docs -o ./site -q
""")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="md2html",
        description="Convert Markdown file(s) to beautifully styled HTML.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=HELP_EPILOG,
    )
    p.add_argument(
        "source",
        metavar="SOURCE",
        help="Path to a .md file or a directory containing .md files.",
    )
    p.add_argument(
        "-o", "--output",
        metavar="DIR",
        default=None,
        help=(
            "Directory where HTML files are saved. "
            "Created automatically if it does not exist. "
            "Defaults to the same directory as the source file(s)."
        ),
    )
    p.add_argument(
        "--prefix",
        metavar="PREFIX",
        default="",
        help="String prepended to every output HTML filename. Example: --prefix docs_",
    )
    p.add_argument(
        "--lang",
        metavar="LANG",
        default="en",
        help=(
            "BCP-47 language tag for the HTML <html lang> attribute "
            "(e.g. en, ar, fr, he). RTL is applied automatically for "
            "Arabic, Hebrew, Persian, Urdu, and related languages. "
            "Default: en"
        ),
    )
    p.add_argument(
        "--code-heavy",
        action="store_true",
        dest="code_heavy",
        help=(
            "Optimise for code-heavy documents: enables line numbers, "
            "language auto-detection, wider content column, and "
            "additional Markdown extensions."
        ),
    )
    p.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress per-file progress output.",
    )
    p.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Search sub-directories recursively when SOURCE is a directory.",
    )
    return p


def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()

    src_path = Path(args.source).expanduser().resolve()

    if not src_path.exists():
        print(f"❌  Source not found: {src_path}", file=sys.stderr)
        sys.exit(1)

    # Collect input files
    if src_path.is_file():
        if src_path.suffix.lower() not in {".md", ".markdown"}:
            print(f"❌  Expected a .md or .markdown file, got: {src_path}", file=sys.stderr)
            sys.exit(1)
        files   = [src_path]
        out_dir = Path(args.output).expanduser().resolve() if args.output else src_path.parent
    elif src_path.is_dir():
        glob = "**/*.md" if args.recursive else "*.md"
        files = sorted(src_path.glob(glob))
        files += sorted(src_path.glob(glob.replace(".md", ".markdown")))
        if not files:
            print(f"⚠️   No Markdown files found in: {src_path}", file=sys.stderr)
            sys.exit(0)
        out_dir = Path(args.output).expanduser().resolve() if args.output else src_path
    else:
        print(f"❌  SOURCE must be a file or directory: {src_path}", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    out_dir.mkdir(parents=True, exist_ok=True)

    # Determine RTL
    lang_lower = args.lang.lower().split("-")[0]
    rtl = lang_lower in RTL_LANGUAGES

    # Pre-compute shared CSS
    pygments_css = _pygments_css()

    verbose = not args.quiet
    if verbose:
        mode = "RTL" if rtl else "LTR"
        heavy = " [code-heavy]" if args.code_heavy else ""
        print(
            f"\n🖊  md2html  ·  lang={args.lang} ({mode}){heavy}\n"
            f"   source  : {src_path}\n"
            f"   output  : {out_dir}\n"
            f"   prefix  : '{args.prefix}'\n"
            f"   files   : {len(files)}\n"
        )

    converted = 0
    errors    = 0
    for f in files:
        try:
            convert_file(
                src=f,
                out_dir=out_dir,
                prefix=args.prefix,
                lang=args.lang,
                rtl=rtl,
                code_heavy=args.code_heavy,
                pygments_css=pygments_css,
                verbose=verbose,
            )
            converted += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗  {f}  →  ERROR: {exc}", file=sys.stderr)
            errors += 1

    if verbose:
        status = "✅" if errors == 0 else "⚠️ "
        print(f"\n{status}  Done — {converted} converted, {errors} errors.\n")


if __name__ == "__main__":
    main()
