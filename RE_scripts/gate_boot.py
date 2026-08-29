#!/usr/bin/env python3
"""gate_boot.py - pre-boot gate (2026-08-26, DOC GOVERNANCE / Universal Lesson
mechanism). Enforces the PRE-BOOT CHECKLIST mechanically: the items are checked
against a boot brief document; exit 1 = do not boot until fixed.

Usage:
  python3 RE_scripts/gate_boot.py <boot-brief.md> [--literals <deployed-file>...]

The brief must be written BEFORE this check and must follow
RE_output/claims/boot-brief-template.md. Rationale for each requirement is in
LESSONS.md; the gate stops the slip when vigilance fails.

Required section headers in the brief (case-insensitive substring):
  1. PURPOSE            - what THIS boot learns, win or lose
  2. GRAPHICS DELTA     - L12: how many NEW rendered models; minimized?
  3. FALSIFIABLE CLAIM  - plus pre-named CONTENT negative (L6)
  4. ABSENCE NEGATIVE   - what zero instrument lines means (L13)
  5. CHAIN MARKS        - every link marked verified/assumed/unknown (L16)
  6. ADVERSARIAL PASS   - session-id or "waived: <reason>" (B-checkpoint)

--literals: each named file is bytes-grepped for every literal listed under an
INSTRUMENTS: line/block in the brief - the L14 provenance check that instruments
actually shipped. If the brief declares no INSTRUMENTS and no --literals are
given, that is a WARNING only (not every boot deploys a new instrument).

LITERAL TARGETS: (optional brief section, closes the 20.157 gap - the global
check demands every literal in EVERY named binary, which cannot gate a boot
shipping instruments in two binaries). Lines of the form
    <file-path>: <literal>, <literal>
are checked against that ONE file only. Global INSTRUMENTS still apply to all
--literals targets as before.

Exit codes: 0 = GO, 1 = NO-GO with reasons, 2 = usage/environment error.
"""
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    ("PURPOSE", "what this boot learns win or lose"),
    ("GRAPHICS DELTA", "L12 new-rendered-model count + minimization note"),
    ("FALSIFIABLE CLAIM", "the one delivery contract under test + content negative"),
    ("ABSENCE NEGATIVE", "L13: meaning of zero instrument lines"),
    ("CHAIN MARKS", "L16 evidence mark per link"),
    ("ADVERSARIAL PASS", "session id or waived:<reason>"),
]

MARK_TOKENS = ["verified-by-execution", "verified-by-reading", "assumed", "unknown"]


def fail(reasons):
    print("NO-GO - do not boot until all of these hold:")
    for r in reasons:
        print(f"  - {r}")
    print("Template: RE_output/claims/boot-brief-template.md")
    return 1


def main(argv):
    args = [a for a in argv if a != "--literals"]
    literals_targets = []
    if "--literals" in argv:
        idx = argv.index("--literals")
        literals_targets = argv[idx + 1:]
    if not args:
        print(__doc__)
        return 2
    brief_path = Path(args[0])
    if not brief_path.exists():
        return fail([f"boot brief MISSING: {brief_path}"])
    text = brief_path.read_text(encoding="utf8", errors="replace")
    lower = text.lower()
    problems = []
    warnings = []
    for token, why in REQUIRED_SECTIONS:
        if token.lower() not in lower:
            problems.append(f"missing required section '{token}' ({why})")
    if not any(tok in lower for tok in MARK_TOKENS):
        problems.append("CHAIN MARKS present but no evidence tokens found "
                        f"(any of {MARK_TOKENS})")
    ap_match = re.search(r"adversarial pass\s*[:\-]\s*(.+)", text, re.I)
    if REQUIRED_SECTIONS[5][0].lower() in lower and not ap_match:
        problems.append("ADVERSARIAL PASS header present but no 'ADVERSARIAL PASS: "
                        "<session-id | waived: reason>' line")
    # literals
    instr = []
    im = re.search(r"instruments?\s*:\s*(.*)", text, re.I | re.M)
    def unquote(s):
        return s.strip().strip('"\'')
    if im:
        instr += [unquote(s) for s in im.group(1).split(",") if s.strip()]
        iblock = re.search(r"instruments?\s*:\s*\n((?:[ \t]+.*\n?)+)", text, re.I)
        if iblock:
            instr += [unquote(l) for l in iblock.group(1).splitlines() if l.strip()]
    if not instr and not literals_targets:
        warnings.append("no INSTRUMENTS declared and no --literals given "
                        "(ok if this boot ships no new instrument)")
    for target in literals_targets:
        tp = Path(target)
        if not tp.exists():
            problems.append(f"--literals target missing: {target}")
            continue
        data = tp.read_bytes()
        for lit in set(instr):
            if lit.encode() not in data:
                problems.append(f"L14 provenance FAIL: literal {lit!r} NOT found "
                                f"in deployed {tp.name}")
    # Per-target mapping (20.157: gate_boot --literals could not gate a
    # two-binary boot because it required every literal in every binary).
    per_target = []
    lt = re.search(r"literal targets?\s*:\s*\n((?:[ \t]+.*\n?)+)", text, re.I)
    if lt:
        for line in lt.group(1).splitlines():
            s = line.strip()
            if not s or ":" not in s:
                continue
            tpath, lits = s.split(":", 1)
            entries = [unquote(x) for x in lits.split(",") if x.strip()]
            if entries:
                per_target.append((tpath.strip(), entries))
    for tpath, lits in per_target:
        tp = Path(tpath)
        if not tp.exists():
            problems.append(f"literal-target file missing: {tpath}")
            continue
        data = tp.read_bytes()
        for lit in set(lits):
            if lit.encode() not in data:
                problems.append(f"L14 provenance FAIL: literal {lit!r} NOT found "
                                f"in {tp.name} (per-target mapping)")
    if problems:
        return fail(problems)
    print("GATE PASS")
    for w in warnings:
        print(f"  warn: {w}")
    print(f"  brief: {brief_path} ({len(instr) or 'no'} instrument literals checked"
          f"{', ' + str(sum(len(l) for _, l in per_target)) + ' per-target' if per_target else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
