#!/usr/bin/env python3
"""
export_claude_chat.py
Export Claude chat sessions from a Claude data export zip file.
"""

import json
import re
import zipfile
from pathlib import Path

import click
import pandas as pd

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def slugify(text: str) -> str:
    """Convert a conversation name to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text or "conversation"


_UNICODE_ESC = re.compile(r"\\u([0-9a-fA-F]{4})")


def _decode_unicode_escapes(text: str) -> str:
    """
    Decode \\uXXXX escape sequences, handling surrogate pairs correctly.

    Claude exports sometimes store surrogate pairs as two adjacent escape
    sequences (e.g. \\uD83D\\uDE00 for 😀).  Naively replacing each escape
    independently leaves lone surrogates in the string, which utf-8 refuses
    to encode later.  We detect adjacent high+low surrogate pairs and combine
    them into the correct Unicode code point before falling back to
    single-char replacement.
    """
    tokens = _UNICODE_ESC.split(text)
    # split gives: [literal, hex1, literal, hex2, ...]
    result = []
    i = 0
    while i < len(tokens):
        if i % 2 == 0:
            # Even indices are literal text segments
            result.append(tokens[i])
        else:
            code = int(tokens[i], 16)
            if 0xD800 <= code <= 0xDBFF:
                # High surrogate — peek ahead for a matching low surrogate.
                # The next literal segment (i+1) must be empty and (i+2) the low hex.
                if (
                    i + 2 < len(tokens)
                    and tokens[i + 1] == ""  # no literal between the two escapes
                ):
                    low_code = int(tokens[i + 2], 16)
                    if 0xDC00 <= low_code <= 0xDFFF:
                        # Valid surrogate pair → combine
                        code_point = (
                            0x10000 + (code - 0xD800) * 0x400 + (low_code - 0xDC00)
                        )
                        result.append(chr(code_point))
                        i += 3  # consume high surrogate, empty literal, low surrogate
                        continue
                # Lone high surrogate — replace with replacement character
                result.append("\ufffd")
            elif 0xDC00 <= code <= 0xDFFF:
                # Lone low surrogate
                result.append("\ufffd")
            else:
                result.append(chr(code))
        i += 1
    return "".join(result)


def unescape_unicode(obj):
    """Recursively decode pre-escaped \\uXXXX sequences in string values."""
    if isinstance(obj, str):
        return _decode_unicode_escapes(obj)
    if isinstance(obj, list):
        return [unescape_unicode(item) for item in obj]
    if isinstance(obj, dict):
        return {k: unescape_unicode(v) for k, v in obj.items()}
    return obj


def _sanitize_surrogates(text: str) -> str:
    """
    Last-resort safety net: encode→decode round-trip that replaces any
    remaining lone surrogates with the Unicode replacement character U+FFFD.
    """
    return text.encode("utf-8", errors="surrogatepass").decode(
        "utf-8", errors="replace"
    )


def load_conversations(zip_path: Path | None, json_path: Path | None) -> pd.DataFrame:
    """Load conversations.json from either a zip archive or a direct file path."""
    if zip_path:
        with zipfile.ZipFile(zip_path, "r") as zf:
            candidates = [n for n in zf.namelist() if n.endswith("conversations.json")]
            if not candidates:
                raise click.ClickException(
                    "Could not find conversations.json inside the zip archive."
                )
            with zf.open(candidates[0]) as f:
                data = json.load(f)
    else:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    data = unescape_unicode(data)
    return pd.DataFrame(data)


def pick_conversation(df: pd.DataFrame, uuid: str | None) -> dict:
    """Return a single conversation row as a dict."""
    if uuid:
        mask = df["uuid"] == uuid
        if not mask.any():
            raise click.ClickException(f"No conversation found with UUID: {uuid}")
        row = df[mask].iloc[0]
    else:
        df_sorted = df.sort_values("created_at", ascending=False)
        row = df_sorted.iloc[0]

    return row.to_dict()


def slim_messages(conversation: dict) -> list[dict]:
    """
    Reduce a conversation's chat_messages down to just the fields needed
    for a lightweight transcript: text, sender, created_at, updated_at.

    Mirrors the manual steps from the notebook:
      df = pd.DataFrame(data['chat_messages'])
      df = df[['text', 'sender', 'created_at', 'updated_at']]
      df = df.sort_values(['created_at', 'updated_at'])
    """
    messages = conversation.get("chat_messages") or []
    slim = [
        {
            "text": m.get("text"),
            "sender": m.get("sender"),
            "created_at": m.get("created_at"),
            "updated_at": m.get("updated_at"),
        }
        for m in messages
    ]
    slim.sort(key=lambda m: (m.get("created_at") or "", m.get("updated_at") or ""))
    return slim


def write_slim_output(conversation: dict, output_dir: Path) -> Path:
    """Serialise a conversation's slimmed-down messages to a JSON file."""
    name = conversation.get("name") or "conversation"
    slug = slugify(name)
    out_path = output_dir / f"{slug}-slim.json"

    output_dir.mkdir(parents=True, exist_ok=True)

    slim = slim_messages(conversation)

    json_str = json.dumps(slim, ensure_ascii=False, indent=2, default=str)
    safe_str = _sanitize_surrogates(json_str)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(safe_str)

    return out_path


def write_output(conversation: dict, output_dir: Path) -> Path:
    """Serialise a conversation to a JSON file and return the path."""
    name = conversation.get("name") or "conversation"
    slug = slugify(name)
    out_path = output_dir / f"{slug}.json"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Serialize to string first so we can sanitize surrogates before disk I/O.
    json_str = json.dumps(conversation, ensure_ascii=False, indent=2, default=str)
    safe_str = _sanitize_surrogates(json_str)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(safe_str)

    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.command()
@click.argument(
    "source",
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "--uuid",
    "-u",
    default=None,
    metavar="UUID",
    help="Export a specific conversation by its UUID. Defaults to the most recent session.",
)
@click.option(
    "--output-dir",
    "-o",
    default=".",
    show_default=True,
    type=click.Path(path_type=Path),
    help="Directory where the exported JSON file will be written.",
)
@click.option(
    "--slim",
    is_flag=True,
    default=False,
    help=(
        "Export a lightweight version containing only text, sender, "
        "created_at, and updated_at for each message, sorted by "
        "created_at/updated_at (equivalent to the manual notebook workflow)."
    ),
)
def main(source: Path, uuid: str | None, output_dir: Path, slim: bool) -> None:
    """Export a Claude chat session from a Claude data export.

    \b
    SOURCE can be:
      • Path to the .zip export file  (e.g. cl.zip)
      • Path directly to conversations.json
    """
    suffix = source.suffix.lower()

    if suffix == ".zip":
        df = load_conversations(zip_path=source, json_path=None)
    elif suffix == ".json":
        df = load_conversations(zip_path=None, json_path=source)
    else:
        raise click.ClickException(
            f"Unsupported file type '{suffix}'. Pass a .zip archive or a conversations.json file."
        )

    if df.empty:
        raise click.ClickException("conversations.json is empty — nothing to export.")

    click.echo(f"Loaded {len(df)} conversation(s).")

    conversation = pick_conversation(df, uuid)

    if slim:
        out_path = write_slim_output(conversation, output_dir)
    else:
        out_path = write_output(conversation, output_dir)

    click.secho(f"✓ Exported → {out_path}", fg="green")
    click.echo(f"  Name     : {conversation.get('name', '(unnamed)')}")
    click.echo(f"  UUID     : {conversation.get('uuid')}")
    click.echo(f"  Date     : {conversation.get('created_at')}")
    msgs = conversation.get("chat_messages") or []
    click.echo(f"  Messages : {len(msgs)}")
    if slim:
        click.echo("  Mode     : slim (text, sender, created_at, updated_at only)")


if __name__ == "__main__":
    main()
