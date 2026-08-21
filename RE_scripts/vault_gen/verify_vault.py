"""Verification v2: resolve [[links]] the way Obsidian does (support \\| alias,
# sections, folder links with trailing /, .canvas targets), report only GENUINE
dangles."""
from __future__ import annotations
import re, sys
from pathlib import Path

VAULT = Path(r"C:\Users\rasla\Documents\sunrise-vault")
all_stems = {p.stem for p in VAULT.rglob("*") if p.is_file()}
all_stems_l = {s.lower() for s in all_stems}

link_re = re.compile(r"!?\[\[([^\]|]+?)(?:\\?\||[#|])([^\]]*?)\]\]")
# simpler: split on | (escaped or not) then on keyword #
simple_re = re.compile(r"!?\[\[([^\]]+)\]\]")

orphans = []
total = 0
for md in VAULT.rglob("*.md"):
    text = md.read_text(encoding="utf-8")
    for m in simple_re.finditer(text):
        inner = m.group(1)
        total += 1
        # alias: split on | (allow \| )
        tgt = re.split(r"\\?\||#", inner, maxsplit=1)[0].strip()
        if not tgt:
            continue
        if tgt == "create a link":  # the stock Obsidian placeholder—ignored
            continue
        target_l = tgt.lower()
        if target_l in all_stems_l:
            continue
        # folder link with trailing slash
        if tgt.endswith("/") and (VAULT / tgt).is_dir():
            continue
        # Obsidian canvas links to 'A Conversation.canvas' by stem
        if target_l in {s.lower() for s in all_stems_l}:
            continue
        orphans.append((md.relative_to(VAULT).as_posix(), tgt))

print(f"links parsed: {total}")
if orphans:
    print(f"\nGENUINE DANGLES ({len(orphans)}):")
    seen = set()
    for src, tgt in orphans:
        if (src, tgt) not in seen:
            print(f"  {src} -> [[{tgt}]]")
            seen.add((src, tgt))
else:
    print("NO DANGLING LINKS — vault links resolve cleanly.")

print("\n--- inventory ---")
for folder in sorted({p.parent.name for p in VAULT.rglob('*') if p.is_file() and p.parent != VAULT}):
    n = len([p for p in (VAULT / folder).rglob('*') if p.is_file()]) if (VAULT / folder).exists() else 0
    print(f"  {folder}: {n}")
