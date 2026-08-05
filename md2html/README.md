# md2html

Markdown → styled HTML converter.

## Setup
```
pip install -r requirements.txt
```

## Usage
```
python convert_md2html.py README.md
python convert_md2html.py ./docs -o ./site --prefix docs_
python convert_md2html.py notes.md --lang ar
```

## What's new
The sidebar table-of-contents is now collapsible on desktop: a small
"◂" button sits next to the "CONTENTS" label. Clicking it shrinks the
sidebar to a narrow 56px strip (hiding the title/links) and rotates the
button; clicking again restores it. This is independent of the existing
mobile hamburger toggle (`☰ TOC`), which still opens/closes the sidebar
as an overlay on small screens.

## Tests
```
pip install -r requirements.txt
pytest
```
45 tests cover: CLI argument parsing, RTL/LTR language detection,
Markdown extension selection (code-heavy / prose modes), the
`convert_file` conversion logic (title extraction, prefixing, RTL
attributes, home button, syntax highlighting), the new collapsible
sidebar markup/CSS/JS, and end-to-end CLI runs (single file, directory,
recursive, quiet mode, error cases).
