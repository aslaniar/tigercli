#!/usr/bin/env python3
# REGISTRY: caps: boot-gate, brief-tie, outcome-ledger
"""gate_boot.py - pre-boot gate (2026-08-26; v3 brief-tie fields 2026-09-05,
per docs/plans/boot-gate-v3.md + TOOLING_AUDIT_2026-09-05). Enforces the
PRE-BOOT CHECKLIST mechanically against a boot brief document;
exit 1 = do not boot until fixed.

Usage:
  python3 RE_scripts/gate_boot.py <boot-brief.md> [--literals <deployed-file>...]

The brief must be written BEFORE this check and must follow
RE_output/claims/boot-brief-template.md. Rationale per requirement: LESSONS.md
PRE-BOOT CHECKLIST + the six postmortems. The gate stops the slip when
vigilance fails; content QUALITY stays with the reviewer (forced judgment).

Required sections (case-insensitive):
  1. PURPOSE            - what THIS boot learns, win or lose
  2. GRAPHICS DELTA     - L12: how many NEW rendered models; minimized?
  3. FALSIFIABLE CLAIM  - plus pre-named CONTENT negative (L6)
  4. ABSENCE NEGATIVE   - what zero instrument lines means (L13)
  5. CHAIN MARKS        - every link marked verified/assumed/unknown (L16)
  6. ADVERSARIAL PASS   - session-id or "waived: <reason>" (B-checkpoint)
  7. PRIOR ART          - the q.sh queries run on the front's central address
                          and central noun, with verdicts; or "none: <why>"
                          (09-05 FAILURE 5: 3 findings + 2 paired boots
                          re-measured a front 20.260 had closed 3 days
                          earlier). Lines citing a closed/dead/retracted/
                          superseded finding require a DEAD-END AUDIT section.
  8. STATE READERS      - the DIRECT instrument that reads each asserted state
                          (empty-mask #1, the root cause: a return code was
                          read as a state). Any reader line saying "inferred
                          from" is rejected outright.
  9. EFFECT CLAIM       - the effect this boot pre-names, distinct from
                          delivery (empty-mask #5: "arrived and decoded" is
                          delivery; a boot whose only outcome is arrival is
                          not a boot)
 10. ABANDON OUTCOME    - a pre-named outcome that ABANDONS the front
                          (empty-mask #7: continuation was structurally
                          guaranteed because no outcome killed the lane)
 11. FIX SURFACE        - "server" or "client" (U18: THE CLIENT IS NEVER
                          MODIFIED). A client surface requires a
                          SERVER-SIDE GAP section naming the specific
                          missing wire item.

If the brief declares INSTRUMENTS, these are also required (the brief ties to
the build - enforcement-layer plan; 08-30 B2/B3/B4/C3, 09-01 DEFECTS 2/3,
09-05 T2.1):
  - READOUT TRIGGER     - per instrument: THE EVENT THAT MAKES IT EMIT, cited
                          from a prior log/archive, or the explicit words
                          "NEVER-OBSERVED (first-fire risk)". (T2.1: p2-177's
                          decisive read was impossible by construction - the
                          probe fired on participant-table events, never on
                          creation - and the gate could not tell.)
  - OBSERVER BUDGET     - per instrument: the event class the budget covers
                          (B2; 09-01 DEFECT 2: budgets spent before the event
                          of interest - "the first 2 PLAYER-BEARING
                          snapshots", not "the first 2")
  - CALL FREQUENCY      - per hook: per-load/per-tick/rare (C3: hot-path hooks
                          are pure risk without a frequency argument)
  - HOOK COUNT          - N; when the client hook tree exists, verified ==
                          the checked count printed by verify_hook_rvas.py
                          (B4). A value-initialised table entry (rva==0) is
                          silently skipped by the verifier, so a shrunk table
                          shows up as a count MISMATCH (09-05 FAILURE 2).
  - INSTRUMENT LIVENESS - literals that must appear in the INSTRUMENT SOURCES
                          files named in the brief (B3: the brief pre-named
                          the ambiguity the instrument could not resolve and
                          nothing tied them)

Third-branch counter (empty-mask #6): a "FRONT: <name>" line opts the brief
into the outcome ledger (RE_output/map/boot_outcomes.jsonl; recorded by
boot_outcome.py at boot close). >=2 consecutive third-branch outcomes
("behaviour changed, outcome didn't") on that front REFUSE the boot unless the
brief contains a MODEL REVIEW: section - which must name the causal assumption
that dies. Ledger path override: env BOOT_OUTCOMES_LEDGER.

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
Self-test (run before every gate change; negative arms first per 09-05):
  negative: the pre-v3 briefs (BOOT_BRIEF_p2-176/177) must FAIL with the new
            field names listed;
  negative: BOOT_OUTCOMES_LEDGER=<tmp> with two third-branch records + a brief
            with that FRONT and no MODEL REVIEW must REFUSE;
  positive: RE_output/map/boot_brief_v3_selftest.md must PASS.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_SECTIONS = [
    ("PURPOSE", "what this boot learns win or lose"),
    ("GRAPHICS DELTA", "L12 new-rendered-model count + minimization note"),
    ("FALSIFIABLE CLAIM", "the one delivery contract under test + content negative"),
    ("ABSENCE NEGATIVE", "L13: meaning of zero instrument lines"),
    ("CHAIN MARKS", "L16 evidence mark per link"),
    ("ADVERSARIAL PASS", "session id or waived:<reason>"),
    ("PRIOR ART", "q.sh queries on the front's central address+noun + verdicts (09-05 FAILURE 5)"),
    ("STATE READERS", "direct reader per asserted state; 'inferred from' is NOT a reader (empty-mask #1)"),
    ("EFFECT CLAIM", "the pre-named effect, distinct from delivery (empty-mask #5)"),
    ("ABANDON OUTCOME", "a pre-named outcome that abandons the front (empty-mask #7)"),
    ("WIDE NET", "probes at every decision point on the suspect chain (empty-mask #7, user directive)"),
    ("FIX SURFACE", "server | client; client requires a SERVER-SIDE GAP section (U18)"),
]

# Required ONLY when the brief declares INSTRUMENTS (the brief ties to the build).
INSTRUMENT_SECTIONS = [
    ("READOUT TRIGGER", "per instrument: the event that makes it emit, cited from a prior log, or NEVER-OBSERVED (T2.1)"),
    ("OBSERVER BUDGET", "per instrument: the event class its budget covers (B2)"),
    ("CALL FREQUENCY", "per hook: per-load/per-tick/rare (C3); 'n/a (server-side only)' when true"),
    ("HOOK COUNT", "N == verify_hook_rvas checked count (B4); 'n/a (no hook changes)' when true"),
    ("INSTRUMENT LIVENESS", "literals must appear in the brief-named INSTRUMENT SOURCES (B3)"),
]

MARK_TOKENS = ["verified-by-execution", "verified-by-reading", "assumed", "unknown"]
DEAD_END_RE = re.compile(r"\b(closed|dead[- ]end|retracted?|superseded)\b", re.I)
LEDGER_DEFAULT = ROOT / "RE_output/map/boot_outcomes.jsonl"
THIRD_BRANCH_LIMIT = 2


def fail(reasons):
    print("NO-GO - do not boot until all of these hold:")
    for r in reasons:
        print(f"  - {r}")
    print("Template: RE_output/claims/boot-brief-template.md")
    return 1


def section_text(text, header):
    """Text under a 'HEADER' / '## HEADER' / 'HEADER:' line, up to the next
    heading of any level or EOF. '' when the header is absent."""
    m = re.search(
        r"^[ \t]*#{0,4}[ \t]*" + re.escape(header) + r"[ \t]*:?[^\n]*\n(.*?)"
        r"(?=^[ \t]*#{1,4}[ \t]*\S|\Z)",
        text, re.I | re.M | re.S)
    return m.group(1) if m else ""


def block_items(text, header):
    """Comma-list on the header line and/or an indented block under it.
    Both bare and '## '-headed forms match."""
    items = []

    def unquote(s):
        return s.strip().strip("\"'")

    m = re.search(r"^[ \t]*#{0,4}[ \t]*" + re.escape(header) +
                  r"[ \t]*:[ \t]*([^\n]*)", text, re.I | re.M)
    if m:
        items += [unquote(s) for s in m.group(1).split(",") if s.strip()]
    b = re.search(r"^[ \t]*#{0,4}[ \t]*" + re.escape(header) +
                  r"[ \t]*:?[ \t]*\n((?:[ \t]+[^\n]*\n?)+)", text, re.I | re.M)
    if b:
        items += [unquote(l) for l in b.group(1).splitlines() if l.strip()]
    return items


def third_branch_streak(front, ledger_path):
    """@return (trailing third-branch streak, records-for-front, ledger-exists)."""
    if not ledger_path.exists():
        return 0, 0, False
    recs = []
    for line in ledger_path.read_text(encoding="utf8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(r, dict):
            recs.append(r)
    fl = [r for r in recs if isinstance(r.get("front"), str) and
          (front.lower() in r["front"].lower() or r["front"].lower() in front.lower())]
    streak = 0
    for r in reversed(fl):
        if r.get("outcome_class") == "third-branch":
            streak += 1
        else:
            break
    return streak, len(fl), True


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

    # --- PRIOR ART content (09-05 FAILURE 5) + conditional DEAD-END AUDIT ---
    pa = section_text(text, "PRIOR ART")
    if "prior art" in lower:
        has_q = "q.sh" in pa or "q.sh" in lower
        has_none = bool(re.search(r"^\s*none\s*[:\-]", pa, re.I | re.M))
        if not has_q and not has_none:
            problems.append("PRIOR ART must list the q.sh queries run (central "
                            "address, central noun) with verdicts, or a "
                            "'none: <why>' line")
        if DEAD_END_RE.search(pa) and "dead-end audit" not in lower:
            problems.append("PRIOR ART cites a closed/dead/retracted/superseded "
                            "finding - a DEAD-END AUDIT section is required "
                            "(the cheap check before building to escape a "
                            "recorded dead end)")

    # --- STATE READERS: a return code is not a reader (empty-mask #1) ---
    sr = section_text(text, "STATE READERS")
    for line in sr.splitlines():
        if re.search(r"inferred from", line, re.I):
            problems.append(f"STATE READERS: '{line.strip()}' - 'inferred from' "
                            "is NOT a direct reader (empty-mask #1); name the "
                            "instrument that reads the state itself, or "
                            "'BUILD: <name>' if building it IS the boot")

    # --- FIX SURFACE / U18 ---
    if "fix surface" in lower:
        fm = re.search(r"fix surface\s*[:\-][ \t]*(server|client)\b", text, re.I)
        if not fm:
            problems.append("FIX SURFACE must declare 'server' or 'client' "
                            "(U18: the client is never modified)")
        elif fm.group(1).lower() == "client" and "server-side gap" not in lower:
            problems.append("FIX SURFACE: client - a SERVER-SIDE GAP section "
                            "is required naming the specific wire item the "
                            "server is missing (U18 retail-client rule)")

    # --- instruments: declared? ---
    instr = []
    im = re.search(r"instruments?\s*:\s*(.*)", text, re.I | re.M)

    def unquote(s):
        return s.strip().strip("\"'")

    if im:
        instr += [unquote(s) for s in im.group(1).split(",") if s.strip()]
        iblock = re.search(r"instruments?\s*:\s*\n((?:[ \t]+.*\n?)+)", text, re.I)
        if iblock:
            instr += [unquote(l) for l in iblock.group(1).splitlines() if l.strip()]
    if not instr and not literals_targets:
        warnings.append("no INSTRUMENTS declared and no --literals given "
                        "(ok if this boot ships no new instrument)")

    # --- brief-tie sections, required when instruments are declared ---
    for token, why in INSTRUMENT_SECTIONS:
        if instr and token.lower() not in lower:
            problems.append(f"missing required section '{token}' ({why})")

    if instr and "readout trigger" in lower:
        rt = section_text(text, "READOUT TRIGGER")
        rt_l = rt.lower()
        cited = ("never-observed" in rt_l or "prior log" in rt_l or
                 re.search(r"\d{8}_\d{6}", rt) or re.search(r"\.log\b", rt) or
                 "logindex" in rt_l or "archive" in rt_l)
        if not cited:
            problems.append("READOUT TRIGGER must cite a PRIOR LOG in which "
                            "each instrument emitted under its trigger, or "
                            "declare 'NEVER-OBSERVED (first-fire risk)' "
                            "(T2.1: p2-177's decisive read was impossible by "
                            "construction)")

    # --- INSTRUMENT LIVENESS in SOURCE (B3) ---
    if instr and "instrument liveness" in lower:
        sources = block_items(text, "INSTRUMENT SOURCES")
        lits = block_items(text, "INSTRUMENT LIVENESS")
        if not sources:
            problems.append("INSTRUMENT LIVENESS declared but no INSTRUMENT "
                            "SOURCES block (the files the literals must "
                            "appear in)")
        else:
            found_any = {lit: False for lit in lits}
            for src in sources:
                sp = Path(src.strip())
                if not sp.is_absolute():
                    sp = ROOT / sp
                if not sp.exists():
                    problems.append(f"INSTRUMENT SOURCES file missing: {src.strip()}")
                    continue
                data = sp.read_bytes()
                for lit in found_any:
                    if lit.encode() in data:
                        found_any[lit] = True
            for lit, ok in found_any.items():
                if not ok:
                    problems.append(f"INSTRUMENT LIVENESS FAIL: literal {lit!r} "
                                    "appears in NO named instrument SOURCE "
                                    "(B3: the brief must be tied to what the "
                                    "instrument can actually log)")

    # --- HOOK COUNT == verify_hook_rvas checked count (B4) ---
    if instr and re.search(r"hook count", text, re.I):
        hm = re.search(r"hook count\s*[:\-][ \t]*(\d+)", text, re.I)
        if hm:
            n_declared = int(hm.group(1))
            hooks_dir = ROOT / "RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks"
            vr = ROOT / "RE_scripts/verify_hook_rvas.py"
            if not hooks_dir.is_dir() or not vr.exists():
                warnings.append(f"HOOK COUNT {n_declared} declared but the hook "
                                "tree/verify_hook_rvas unavailable on this "
                                "machine - run verify_hook_rvas where the "
                                "tree lives before deploy")
            else:
                try:
                    out = subprocess.run(
                        [sys.executable, str(vr)],
                        capture_output=True, text=True, timeout=300)
                    m2 = re.search(r"(\d+) hook RVAs checked, (\d+) bad", out.stdout)
                    if not m2:
                        warnings.append("could not parse verify_hook_rvas "
                                        "output - run it directly and compare "
                                        f"to HOOK COUNT {n_declared}")
                    else:
                        checked, bad = int(m2.group(1)), int(m2.group(2))
                        if checked != n_declared:
                            problems.append(
                                f"HOOK COUNT MISMATCH: brief declares "
                                f"{n_declared}, verify_hook_rvas checked "
                                f"{checked} - the verifier silently skips "
                                "rva==0 entries, so a value-initialised "
                                "table entry shrinks the count (09-05 "
                                "FAILURE 2: the RVA-0 login crash)")
                        if bad or out.returncode != 0:
                            problems.append(
                                f"verify_hook_rvas FAIL ({bad} bad, "
                                f"rc={out.returncode}) - run it directly for "
                                "the offending RVAs")
                except subprocess.TimeoutExpired:
                    warnings.append("verify_hook_rvas timed out (300s) - run "
                                    "it directly and compare to HOOK COUNT "
                                    f"{n_declared} before deploy")

    # --- third-branch counter (empty-mask #6) ---
    front = None
    fm2 = re.search(r"^front\s*[:\-][ \t]*(.+)$", text, re.I | re.M)
    if fm2:
        front = fm2.group(1).strip()
    streak_line = "front: not declared (third-branch counter not applied)"
    if front:
        ledger = Path(os.environ.get("BOOT_OUTCOMES_LEDGER", str(LEDGER_DEFAULT)))
        streak, n_front, exists = third_branch_streak(front, ledger)
        if not exists:
            streak_line = (f"front: {front} | outcome ledger absent "
                           f"({ledger}) - no third-branch history yet; "
                           "record outcomes with boot_outcome.py")
        else:
            streak_line = (f"front: {front} | ledger records for front: {n_front}"
                           f" | trailing third-branch streak: {streak}")
            model_review = section_text(text, "MODEL REVIEW").strip()
            if streak >= THIRD_BRANCH_LIMIT and not model_review:
                problems.append(
                    f"third-branch streak {streak} on front '{front}' - a "
                    "MODEL REVIEW: SECTION (with content, not a mention) is "
                    "required before another boot (empty-mask #6: repeated "
                    "third-branch outcomes are a model indictment, not 'on "
                    "to the next lead')")

    # --- literals (L14 provenance) ---
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
    print(f"  {streak_line}")
    print(f"  brief: {brief_path} ({len(instr) or 'no'} instrument literals checked"
          f"{', ' + str(sum(len(l) for _, l in per_target)) + ' per-target' if per_target else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
