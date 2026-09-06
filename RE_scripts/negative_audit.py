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

ROOT = os.environ.get("RE_AUDIT_ROOT") or \
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
# WAIVED (2026-09-01 housekeeping pass, all 11 flags adjudicated individually):
# each entry (filename, line substring, reason). Waivers are VISIBLE in output -
# a waiver is a reviewed decision, never a silent pass. FINDINGS is append-only,
# so dead/retracted claims keep their original text and are waived here instead.
#  - three are phrase false positives ("zero references" = refcount RETIRE, or
#    the flag hits the tool-debt note / the changelog citing the trap rule);
#  - four are retracted or corrected claims (the flag hits the retraction text
#    itself: 20.222 correcting 20.209 R2, staging population dead 20.191/2);
#  - three are live claims whose encodings are documented inline in the entry
#    without the literal ENCODEDS keyword (all-sections E8/E9/rip-rel; the
#    enumerated covered-encoding set of 20.234; the four dual-encoding attempts
#    of 20.246 R1-R4) - all three are now behind the dynamic front (20.246 R7).
WAIVERS = [
    ("FINDINGS_2026-08-25.md",
     "0x1416E73A0 has ZERO references of any kind in the unpacked binary",
     "RETRACTED by 20.291 R1 - the pointer IS in the static file at offset "
     "0x1C9E308; the scan searched the STATIC VA instead of the RUNTIME-RELOCATED "
     "form (stale base 0x7FF6AF7F0000). Dead claim kept for history"),
    ("FINDINGS_2026-08-25.md",
     '20.288 R3: "0x1416E73A0 has ZERO references of any kind',
     "the flag hits the RETRACTION text itself (20.291 R1 quoting 20.288 R3) - "
     "same shape as the 12357 waiver"),
    ("FINDINGS_2026-08-25.md",
     "source mismatch with zero references",
     "not a scan-negative: 'zero references' = refcount-zero RETIRE in "
     "group_host_sessions logic"),
    ("FINDINGS_2026-08-25.md",
     "The selector at stage 2 reads a slot nobody writes",
     "RETRACTED claim (staging population, 20.191/20.192) - dead entry kept "
     "for history"),
    ("FINDINGS_2026-08-25.md",
     "THE ENTITY RECEIVE CHAIN HAS ZERO STATIC REFERENCES OF ANY KIND",
     "corrected by 20.222 (handler table was in .rdata all along) - "
     "retraction on record in the corpus"),
    ("FINDINGS_2026-08-25.md",
     "ZERO static references to 0x1404F2970 anywhere",
     "encodings documented inline (all-sections E8/E9/rip-rel scan) - "
     "declaration satisfied in substance"),
    ("FINDINGS_2026-08-25.md",
     'disp32 scans cannot see - the "no writers exist" trap',
     "not a claim: tool-honesty changelog citing the trap rule"),
    ("FINDINGS_2026-08-25.md",
     "STATICALLY UNREACHABLE. THE HANDLER TABLE IS IN .rdata AND ALWAYS WAS",
     "the flag hits the retraction text itself (20.222 correcting 20.209 R2)"),
    ("FINDINGS_2026-08-25.md",
     'xref_scan.py returned "0 refs" for 0x1427E45D0',
     "not a claim: tool-debt incident record"),
    ("FINDINGS_2026-08-25.md",
     "nobody writes +0x38 by any covered encoding in any participant",
     "encodings enumerated in 20.234 R1-R2 ('covered encoding' is that "
     "enumerated set); scope-limited claim, superseded by the dynamic "
     "front 20.246 R7"),
    ("FINDINGS_2026-08-25.md",
     "statically unreachable after four attempts",
     "four dual-encoding attempts documented in the entry (20.246 R1-R4); "
     "superseded by the dynamic front 20.246 R7"),
    ("FINDINGS_2026-08-15.md",
     "later proven inert (see 9.36, the zero references)",
     "historical entry, resolved in-file at 9.36"),
    ("FINDINGS_2026-08-15.md",
     "ZERO references from the chain's executed flow",
     "historical entry, resolved in-file at 9.36"),
]


def waived(fname, line):
    low = line.lower()
    return [(sub, why) for (f, sub, why) in WAIVERS
            if f == fname and sub.lower() in low]


CORPOR_GLOBS = ["FINDINGS_2026-*.md", "findings/FINDINGS_2026-*.md",
                "STATE.md", "docs/handoffs/HANDOFF*.md", "FRONT*.md",
                "HANDOFF*.md"]  # root handoffs too (backlog 3.5)
DATE_RE = re.compile(r"20\d{2}-\d{2}-\d{2}")
HEAD_RE = re.compile(r"^#{1,2} ")
# a retraction/correction QUOTES the claim it kills; the flag then hits the
# retraction text itself (the 12357/16997 waiver shape). Auto-waive - visibly.
QUOTING_RE = re.compile(r"retract|corrected|correction|withdrawn|supersed", re.I)
# pointer-class by WORD: bare "ref" matched "p(ref)er" (the 'prefer' false
# match, backlog 3.5)
POINTER_CLASS_RE = re.compile(r"\b(ref|refs|reference|references|pointer|"
                              r"pointers|table|tables)\b", re.I)


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
                pointer_class = bool(POINTER_CLASS_RE.search(line))
                quoting = bool(QUOTING_RE.search(low) or
                               QUOTING_RE.search(entry))
                stale = False
                if pointer_class and entry_date and entry_date < FACTS[0][0]:
                    stale = True
                if quoting or not has_encodeds or stale:
                    flags.append({
                        "file": os.path.basename(path), "line": lineno,
                        "entry": entry, "phrase": phrase,
                        "has_encodeds": has_encodeds, "stale": stale,
                        "quoting": quoting,
                        "line_text": line,
                        "quote": line.strip()[:110]})
                break  # one flag per line
    return flags, checked


def main(argv):
    flags, checked = audit()
    active_t1, backlog_t2, quoting, waived_flags = [], [], [], []
    for f in flags:
        w = waived(f["file"], f["line_text"])
        if w:
            waived_flags.append((f, w[0][1]))
        elif f.get("quoting"):
            quoting.append(f)
        elif f["stale"]:
            active_t1.append(f)      # stale premise = actionable
        else:
            backlog_t2.append(f)     # undeclared encodings = migration backlog
    print("LIVENESS: scan-negative claims checked=%d flagged=%d "
          "waived=%d quoting=%d stale(tier1)=%d undeclared(tier2)=%d" %
          (checked, len(flags), len(waived_flags), len(quoting),
           len(active_t1), len(backlog_t2)))
    if waived_flags:
        print("WAIVED (%d) - reviewed waivers, see WAIVERS in negative_audit.py:"
              % len(waived_flags))
        for f, why in waived_flags:
            print("  %s:%d - %s" % (f["file"], f["line"], why))
    if quoting:
        print("CORRECTION-QUOTING (%d) - the flag hits retraction/correction "
              "text quoting the claim it kills; auto-waived, visible here:"
              % len(quoting))
        for f in quoting[:10]:
            print("  %s:%d - %s" % (f["file"], f["line"], f["quote"][:100]))
    if not active_t1:
        print("NEGATIVE AUDIT PASS - no actionable (stale-premise) flags."
              + (" %d undeclared-ENCODEDS item(s) remain on the MIGRATION "
                 "BACKLOG (tier 2 - add declarations when touching those "
                 "entries):" % len(backlog_t2) if backlog_t2 else ""))
        for f in backlog_t2[:10]:
            print("  tier2 %s:%d [%s] %s" %
                  (f["file"], f["line"], f["entry"][:44], f["quote"][:80]))
        if len(backlog_t2) > 10:
            print("  ... +%d more" % (len(backlog_t2) - 10))
        return 0
    print("NEGATIVE AUDIT FLAGS - TIER 1 STALE-PREMISE (%d) - actionable:"
          % len(active_t1))
    for f in active_t1[:15]:
        print("  %s:%d [%s] (predates RUNTIME_BASE fact)\n    %s" %
              (f["file"], f["line"], f["entry"][:44], f["quote"]))
    if len(active_t1) > 15:
        print("  ... +%d more" % (len(active_t1) - 15))
    if backlog_t2:
        print("TIER 2 MIGRATION BACKLOG (%d undeclared-ENCODEDS items):" %
              len(backlog_t2))
        for f in backlog_t2[:10]:
            print("  tier2 %s:%d [%s] %s" %
                  (f["file"], f["line"], f["entry"][:44], f["quote"][:80]))
    print("REMEDIATION: re-run the scan with dual encodings "
          "(xref_scan --ptrs tests image + RUNTIME_BASE-relocated), then "
          "add an ENCODEDS: line to the claim.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
