"""Shared helpers for the sunrise-vault generators (RE_scripts/vault_gen/common.py).

Vault root + frontmatter writer. Every generated note carries the Bases contract:
kind/status/subsystem/evidence so the Bases views filter correctly.
"""
from __future__ import annotations

import os
from pathlib import Path

VAULT = Path(r"C:\Users\rasla\Documents\sunrise-vault")
PROJECT = Path(r"C:\Users\rasla\Downloads\destiny-preservation")

KINDS = {
    "opcode", "bap-type", "queuez-family", "activity-msg", "authority-slot",
    "flag", "record", "rva", "hook", "path", "subsystem", "wire",
}


def slugify(text: str) -> str:
    out = []
    for ch in str(text).strip():
        if ch.isalnum() or ch in "-_ .":
            out.append(ch)
        else:
            out.append("-")
    s = "".join(out)
    return "-".join(part for part in s.replace(" ", "-").split("-") if part)


def safe_filename(text: str, maxlen: int = 64) -> str:
    """Windows-safe filename stem (no parens, colons, slashes, quotes, etc.)."""
    out = []
    for ch in str(text).strip():
        if ch.isalnum() or ch in "-_.":
            out.append(ch)
        else:
            out.append("-")
    s = "-".join(p for p in "".join(out).split("-") if p)
    return s[:maxlen].rstrip(".") or "untitled"


def write_note(rel_dir: str, filename: str, front: dict, body: str = "") -> Path:
    """Write one note into VAULT/rel_dir, with YAML frontmatter from `front`."""
    assert set(front) >= {"kind", "status", "subsystem"}, f"missing required frontmatter: {front.get('id')}"
    lines = ["---"]
    for key, val in front.items():
        if val is None or val == "":
            continue
        if isinstance(val, bool):
            lines.append(f"{key}: {'true' if val else 'false'}")
        elif isinstance(val, (int, float)):
            lines.append(f"{key}: {val}")
        else:
            # string / list-of-strings
            if isinstance(val, list):
                if not val:
                    continue
                lines.append(f"{key}:")
                for item in val:
                    lines.append(f'  - "{item}"')
            else:
                val = str(val)
                if any(ch in val for ch in ':"#[]{}') or val.startswith(("-", "0x")):
                    lines.append(f'{key}: "{val}"')
                else:
                    lines.append(f"{key}: {val}")
    lines.append("---")
    lines.append("")
    if body:
        lines.append(body)
    out_dir = VAULT / rel_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{filename}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
