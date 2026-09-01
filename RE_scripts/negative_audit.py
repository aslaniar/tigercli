#!/usr/bin/env python3
# REGISTRY: caps: scan-negative-audit, invalidation-scan
"""negative_audit.py - scan-negative hygiene (2026-08-31).

A scan-negative ("zero references", "no writers", "statically unreachable")
is only as good as the ENCODINGS the scan searched. Three documented incidents
where a tool's coverage limit was promoted to a structural claim:
  - xref_scan "0 refs" (form filter dropped cmp/REX variants) - 08-31
  - field_xref "no writers" (disp32 forms only; mod=00 SIB invisible) - 08-31
  - 20.209 R2 "statically unreachable" (scanned image-encoded pointers only;
    .data pointers are RUNTIME_BASE-relocated) - cost the entity-table dead
    end until the dump hunt found the relocated pointer at 0x141C9AE28

This audit greps the corpus for scan-negative claim phrases and flags:
  1. claims missing an `ENCODEDS:` declaration (what forms were searched)
  2. claims that predate a known encoding fact that could invalidate them
     (e.g. RUNTIME_BASE relocation landed 08-30; image-encoding-only pointer
     scans predating it are premise-stale)

Usage: /usr/bin/python3 RE_scripts/negative_audit.py [--full]
Exit: 0 no stale flags, 1 flags found, 2 usage.
Wired into bootstrap_check (liveness: prints even when clean).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# phrases that indicate a scan-negative claim (lowercase substring match)
NEGATIVE_PHRASES = [
    "zero static references",
    "no static references",
    "statically unreachable",
    "no references anywhere",
    "zero refs",
    "0 refs",
    "no writers",
    "nobody writes",
    "never called statically",
    "not referenced anywhere",
    "zero references",
]
# encoding facts that invalidate older scan-negatives of the pointer class
FACTS = [
    ("2026-08-30", "RUNTIME_BASE pointer relocation: .data/.rdata pointers "
     "are stored runtime-relocated (pe_reader.to_static, 19,990/20,000 "
     "empirical) - invalidates image-encoding-only pointer scans"),
]
CORPOR_GLOBS = ["FINDINGS_2026-*.md", "findings/FINDINGS_2026-*.md",
                "STATE.md", "docs/handoffs/HANDOFF*.md", "FRONT*.md"]
DATE_RE = re.compile(r"20\d{2}-\d{2}-\d{2}")
HEAD_RE = re.compile(r"^#{1,2} ")


def iter_corpus():
    import glob
    for g in CORPOR_GLOBS:
        for path in glob.glob(os.path.join(ROOT, g)):
            yield path


def audit():
    flags = []
    checked = 0
    for path in iter_corpus():
        try:
            with open(path, encoding="utf8", errors="replace") as fh:
                lines = fh.read().splitlines()
        except OSError:
            continue
        entry = "(top)"
        entry_date = None
        for lineno, line in enumerate(lines, 1):
            if HEAD_RE.match(line):
                entry = line.lstrip("# ").strip()[:70]
                dm = DATE_RE.search(line)
                entry_date = dm.group(0) if dm else entry_date
            low = line.lower()
            for phrase in NEGATIVE_PHRASES:
                if phrase not in low:
                    continue
                checked += 1
                # ENCODEDS declaration within +-8 lines?
                window = "\n".join(lines[max(0, lineno - 9):lineno + 8])
                has_encodeds = "encodeds" in window.lower()
                # pointer-class negatives + predates-the-fact check
                pointer_class = any(w in low for w in
                                    ("reference", "ref", "pointer", "table"))
                stale = False
                if pointer_class and entry_date and entry_date < FACTS[0][0]:
                    stale = True
                if not has_encodeds or stale:
                    flags.append({
                        "file": os.path.basename(path), "line": lineno,
                        "entry": entry, "phrase": phrase,
                        "has_encodeds": has_encodeds, "stale": stale,
                        "quote": line.strip()[:110]})
                break  # one flag per line
    return flags, checked


def main(argv):
    flags, checked = audit()
    print("LIVENESS: scan-negative claims checked=%d flagged=%d" %
          (checked, len(flags)))
    if not flags:
        print("NEGATIVE AUDIT PASS - all scan-negative claims carry "
              "ENCODEDS declarations and predate no invalidating fact")
        return 0
    print("NEGATIVE AUDIT FLAGS (%d) - premise possibly stale or "
          "undeclared:" % len(flags))
    for f in flags[:15]:
        miss = []
        if not f["has_encodeds"]:
            miss.append("no ENCODEDS")
        if f["stale"]:
            miss.append("predates RUNTIME_BASE fact")
        print("  %s:%d [%s] (%s)\n    %s" %
              (f["file"], f["line"], f["entry"][:44], ", ".join(miss),
               f["quote"]))
    if len(flags) > 15:
        print("  ... +%d more" % (len(flags) - 15))
    print("REMEDIATION: re-run the scan with dual encodings "
          "(xref_scan --ptrs tests image + RUNTIME_BASE-relocated), then "
          "add an ENCODEDS: line to the claim.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
