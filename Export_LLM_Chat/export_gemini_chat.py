#!/usr/bin/env python3

import json
import re
import click
from pathlib import Path
from typing import Any, List, Dict


def slugify(text: str) -> str:
    """Convert arbitrary text into a lowercase hyphenated slug."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)       # drop punctuation (keep hyphens)
    text = re.sub(r"[\s_]+", "-", text)         # spaces/underscores → hyphens
    text = re.sub(r"-{2,}", "-", text)          # collapse repeated hyphens
    return text.strip("-") or "chat"            # never return an empty slug


def derive_slug(data: Dict, fallback_stem: str) -> str:
    """Return a slug from the JSON title field, falling back to the filename stem."""
    title = data.get("title") or data.get("name") or ""
    return slugify(title) if title.strip() else slugify(fallback_stem)

# ----------------------------
# Core cleaning logic
# ----------------------------


def remove_thought_signature(obj: Any) -> Any:
    """Recursively remove 'thoughtSignature' keys."""
    if isinstance(obj, list):
        return [remove_thought_signature(x) for x in obj]
    elif isinstance(obj, dict):
        return {
            k: remove_thought_signature(v)
            for k, v in obj.items()
            if k != "thoughtSignature"
        }
    return obj


def extract_text(parts: Any) -> str:
    """Normalize parts/text into a single string."""
    if parts is None:
        return ""

    if isinstance(parts, str):
        return parts

    if isinstance(parts, list):
        texts = []
        for item in parts:
            if isinstance(item, dict) and "text" in item:
                texts.append(item["text"])
            elif isinstance(item, str):
                texts.append(item)
        return "".join(texts)

    return str(parts)


def process_chunks(chunks: List[Dict]) -> List[Dict]:
    """Convert raw chunks into clean chat messages."""
    messages = []

    for chunk in chunks:
        # ❌ Skip thoughts
        if chunk.get("isThought"):
            continue

        role = chunk.get("role", "unknown")

        # Normalize content
        parts = chunk.get("parts")
        text = chunk.get("text")

        content = parts if parts not in (None, "", []) else text
        content = content if content is not None else ""

        content = extract_text(content)
        content = content.strip()

        if not content:
            continue

        # Normalize role
        if role == "model":
            role = "assistant"

        messages.append({"role": role, "content": content})

    return messages


def extract_system_prompt(data: Dict) -> str:
    """Extract and normalize the systemInstruction field into plain text."""
    instruction = data.get("systemInstruction")
    if instruction is None:
        return ""

    # Plain string
    if isinstance(instruction, str):
        return instruction.strip()

    # {role: ..., parts: [...]} style object (standard Gemini format)
    if isinstance(instruction, dict):
        parts = instruction.get("parts", instruction.get("text"))
        if parts is not None:
            return extract_text(parts).strip()

    # Fallback: best-effort serialization
    return str(instruction).strip()


def write_system_prompt_md(prompt_text: str, path: Path) -> None:
    """Write the system prompt to a Markdown file."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("# System Prompt\n\n")
        f.write(prompt_text)
        f.write("\n")


def process_file(input_path: Path) -> tuple[List[Dict], str, str]:
    """Load and process a single JSON file.

    Returns:
        (messages, system_prompt_text, slug)
    """
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    chunks = data.get("chunkedPrompt", {}).get("chunks", [])
    chunks = remove_thought_signature(chunks)

    system_prompt = extract_system_prompt(data)
    slug = derive_slug(data, input_path.stem)

    return process_chunks(chunks), system_prompt, slug


# ----------------------------
# CLI
# ----------------------------


@click.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), help="Output file or directory")
@click.option("--pretty", is_flag=True, help="Pretty print JSON")
@click.option(
    "--system-prompt",
    is_flag=True,
    default=False,
    help="Also export the system prompt as a <name>.system_prompt.md file",
)
def main(input_path, output, pretty, system_prompt):
    """
    Convert LLM chat logs into clean JSON format.

    INPUT_PATH can be:
    - a JSON file
    - a directory containing JSON files
    """

    input_path = Path(input_path)

    if input_path.is_file():
        messages, sp_text, slug = process_file(input_path)

        if output:
            out_path = Path(output)
        else:
            out_path = input_path.parent / f"{slug}.json"

        write_output(messages, out_path, pretty)
        click.echo(f"✔ Processed: {input_path} → {out_path}")

        if system_prompt:
            _export_system_prompt(sp_text, out_path.with_name(f"{slug}.system-prompt.md"))

    else:
        # Directory mode
        out_dir = Path(output) if output else input_path / "cleaned"
        out_dir.mkdir(parents=True, exist_ok=True)

        for file in input_path.glob("*.json"):
            try:
                messages, sp_text, slug = process_file(file)
                out_path = out_dir / f"{slug}.json"

                write_output(messages, out_path, pretty)
                click.echo(f"✔ {file.name} → {slug}.json")

                if system_prompt:
                    _export_system_prompt(sp_text, out_dir / f"{slug}.system-prompt.md")

            except Exception as e:
                click.echo(f"✖ Failed: {file.name} ({e})")


def _export_system_prompt(sp_text: str, md_path: Path) -> None:
    """Write system prompt to .md and report to the user."""
    if sp_text:
        write_system_prompt_md(sp_text, md_path)
        click.echo(f"  ↳ System prompt → {md_path}")
    else:
        click.echo("  ↳ No systemInstruction found — skipping .md export")


def write_output(data: List[Dict], path: Path, pretty: bool):
    """Write JSON output."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2 if pretty else None)


if __name__ == "__main__":
    main()
