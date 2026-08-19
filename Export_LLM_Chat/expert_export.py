import json
import re
import shutil
from pathlib import Path
import pandas as pd
from xml.sax.saxutils import escape

# ============================================================
# CONFIG
# ============================================================

# Your repo absolute windows path (from notebook)
REPO_ROOT = Path(r"C:\Users\DELL\Jupyter_Notebooks\TRACK_QA")

# experts.json path
EXPERTS_JSON = REPO_ROOT / "experts.json"

# output folder
OUTPUT_ROOT = REPO_ROOT / "EXPERTS_OUTPUT"


# ============================================================
# HELPERS
# ============================================================


def safe_name(text: str) -> str:
    """
    Convert title into folder-safe name.

    Prefers the abbreviation inside parentheses if present:
        "Audio Signal Processing (DSP)" -> "DSP"

    Falls back to uppercased, non-alphanumeric chars replaced with underscores:
        "Mastering & Perceptual Audio Engineering" -> "MASTERING__PERCEPTUAL_AUDIO_ENGINEERING"
    """
    m = re.search(r"\((.*?)\)", text)
    if m:
        return m.group(1).upper().replace(" ", "_")

    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", text)
    return cleaned.upper()


def read_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_experts_dataframe() -> pd.DataFrame:
    """
    Parses experts.json into a DataFrame.

    Expected JSON shape (mirrors notebook exploration):
        {
            "response": "<JSON-encoded string of list[{fields: {...}}]>"
        }

    Each record's `fields` dict must contain:
        id, title, documents_to_review, skills_required, questions_to_answer
    """
    raw = read_json(EXPERTS_JSON)
    data = raw["response"]                    # outer key, matches notebook: data = data['response']
    df = pd.DataFrame(json.loads(data))       # double-decode: matches notebook: df = pd.DataFrame(json.loads(data))
    df = df.rename(columns={"fields": "DATA"})

    df["EXPERT_ID"]        = df["DATA"].apply(lambda x: x["id"])
    df["EXPERT_TITLE"]     = df["DATA"].apply(lambda x: x["title"])
    df["EXPERT_CONTEXT"]   = df["DATA"].apply(lambda x: x["documents_to_review"])
    df["EXPERT_SKILLS"]    = df["DATA"].apply(lambda x: x["skills_required"])
    df["EXPERT_QUESTIONS"] = df["DATA"].apply(lambda x: x["questions_to_answer"])

    return df


def resolve_repo_file(filename: str) -> Path:
    """
    Search recursively under REPO_ROOT for `filename`.
    Raises FileNotFoundError if no match is found.
    Returns the first match (repo filenames are assumed unique).
    """
    matches = list(REPO_ROOT.rglob(filename))
    if not matches:
        raise FileNotFoundError(f"Cannot find file in repo: {filename}")
    return matches[0]


def copy_context_files(context_items: list, context_folder: Path) -> dict[str, Path]:
    """
    Copy every context file into `context_folder`.

    Duplicate-filename handling
    --------------------------
    Although no duplicates exist in the current dataset, the function is
    defensive: if two source files share the same filename but come from
    different parent directories, the copy for the second (and beyond) file
    is renamed as:

        <parent_folder>__<filename>

    e.g.  src/data/config.py  vs  src/config.py
          would produce:  config.py  and  data__config.py

    Returns
    -------
    dict mapping original `filename` string -> Path of the copy inside
    `context_folder` (used by build_context_xml to write accurate paths).
    """
    context_folder.mkdir(parents=True, exist_ok=True)
    seen: dict[str, Path] = {}          # basename -> dest path already written
    filename_to_dest: dict[str, Path] = {}

    for item in context_items:
        filename = item["filename"]
        src: Path = resolve_repo_file(filename)
        basename = src.name

        if basename not in seen:
            dest = context_folder / basename
        else:
            # Disambiguate with the immediate parent folder name
            parent_tag = src.parent.name.upper().replace(" ", "_")
            dest = context_folder / f"{parent_tag}__{basename}"

        shutil.copy2(src, dest)
        seen[basename] = dest
        filename_to_dest[filename] = dest

    return filename_to_dest


def build_context_xml(context_items: list, filename_to_dest: dict[str, Path]) -> str:
    """
    Build EXPERT_CONTEXT.xml.

    <absolute_path> now points to the file's location inside the CONTEXT/
    subfolder rather than its original repo location, so the XML is
    self-consistent with the exported directory tree.
    """
    xml = ["<expert_context>"]

    for item in context_items:
        filename    = item["filename"]
        description = item.get("description", "")
        dest_path   = filename_to_dest[filename]
        content     = dest_path.read_text(encoding="utf-8", errors="ignore")

        xml.append("  <context_file>")
        xml.append(f"    <filename>{escape(filename)}</filename>")
        xml.append(f"    <absolute_path>{escape(str(dest_path))}</absolute_path>")
        xml.append(f"    <description>{escape(description)}</description>")
        xml.append("    <file_content>")
        xml.append(escape(content))
        xml.append("    </file_content>")
        xml.append("  </context_file>")

    xml.append("</expert_context>")
    return "\n".join(xml)


def build_skills_xml(skills: list) -> str:
    xml = ["<expert_skills>"]
    for skill in skills:
        xml.append(f"  <skill>{escape(str(skill))}</skill>")
    xml.append("</expert_skills>")
    return "\n".join(xml)


def build_questions_xml(questions: list) -> str:
    xml = ["<expert_questions>"]
    for q in questions:
        xml.append(f"  <question>{escape(str(q))}</question>")
    xml.append("</expert_questions>")
    return "\n".join(xml)


# ============================================================
# MAIN
# ============================================================


def export_experts() -> None:
    """
    For each expert row in experts.json, produce:

        EXPERTS_OUTPUT/
        └── EXPERT_{ID}_{SUFFIX}/
            ├── CONTEXT/                  ← physical copies of all context files
            │   ├── extractor.py
            │   └── ...
            ├── EXPERT_CONTEXT.xml        ← XML with embedded file content
            ├── EXPERT_SKILLS.xml
            └── EXPERT_QUESTIONS.xml
    """
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    df = load_experts_dataframe()

    for _, row in df.iterrows():
        expert_id = row["EXPERT_ID"]
        title     = row["EXPERT_TITLE"]
        suffix    = safe_name(title)

        expert_folder  = OUTPUT_ROOT / f"EXPERT_{expert_id}_{suffix}"
        context_folder = expert_folder / "CONTEXT"

        expert_folder.mkdir(parents=True, exist_ok=True)

        # ── 1. Copy physical files into CONTEXT/ ──────────────────────────
        filename_to_dest = copy_context_files(row["EXPERT_CONTEXT"], context_folder)

        # ── 2. EXPERT_CONTEXT.xml (paths now point into CONTEXT/) ─────────
        context_xml = build_context_xml(row["EXPERT_CONTEXT"], filename_to_dest)
        (expert_folder / "EXPERT_CONTEXT.xml").write_text(context_xml, encoding="utf-8")

        # ── 3. EXPERT_SKILLS.xml ──────────────────────────────────────────
        skills_xml = build_skills_xml(row["EXPERT_SKILLS"])
        (expert_folder / "EXPERT_SKILLS.xml").write_text(skills_xml, encoding="utf-8")

        # ── 4. EXPERT_QUESTIONS.xml ───────────────────────────────────────
        questions_xml = build_questions_xml(row["EXPERT_QUESTIONS"])
        (expert_folder / "EXPERT_QUESTIONS.xml").write_text(questions_xml, encoding="utf-8")

        print(f"✓ {expert_folder.name}  ({len(filename_to_dest)} context file(s) copied)")


if __name__ == "__main__":
    export_experts()
