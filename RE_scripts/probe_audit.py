#!/usr/bin/env python3
# REGISTRY: caps: probe-audit, instrument-gate, deploy-refuse
"""probe_audit.py - THE INSTRUMENT-SOURCE GATE (2026-09-06, the
POSTMORTEM_2026-09-06_THE-BLIND-GUARD conversion: instrument changes need
the same gates as shipped code - five boots were spent on an instrument
whose own guard refused its subject, found by disassembly, not by a boot).

Scans the client hook sources for the 09-06 defect classes, mechanically:

  A. ALIGNMENT GUARDS vs the SUBJECT'S DECODED ALIGNMENT (R1). A probe
     emitter that guards dereferences with an alignment test (`& 7`,
     `& 0x7`, `% 8`) is REFUSED unless the raw source within 5 lines
     carries a citation of the field's decoded alignment
     (`ALIGN-CITED`, or a `&7=N`-style cite, or the decode's offset).
     The 09-06 defect: emit_sesscmp's `(ptr & 7) == 0` guard refused the
     gate's OWN blob pointers for five boots - the blobs sit at +0x57C
     (&7=4) and +0x94E (&7=6), unaligned BY DESIGN, and the alignment fact
     was already in the project's decode. Comments are STRIPPED before the
     code check (the compiler's view) but READ for the citation (the
     citation is a claim, like the boot brief's).

  B. NOVELTY SIGNATURES THAT COLLIDE ON THE EVENT OF INTEREST (R4). A
     signature computed as a plain XOR of two field reads collides to zero
     exactly when the fields are EQUAL - i.e. exactly on MATCHES, the
     event a compare-probe exists to observe (the shipped defect hid every
     match). REFUSED unless BOTH:
       - the two operands are individually transformed (mix/rotate), AND
       - the signature has a zero-guard (`if (sig == 0) sig = 1;`) AND the
         operands individually transformed (mix/rotl/shift). NOTE: a
         `collision` COMMENT alone can NEVER satisfy arm B - B reads
         comment-STRIPPED source (what the compiler sees); only the real
         guard or the transform is checkable. The shipped fix
         (8252f1dad6e8a0c1) satisfies both conditions in code.

  C. LOOKUP ROWS WITHOUT THEIR LEAVE (R6). A lookup's OUTCOME is on its
     return. For every install-table row whose name is lookup-class,
     audit requires ONE of: a leave-probe row on the same RVA, an emit
     function pairing the stem with leave, or a machine-readable
     `no-leave: <reason>` citation in the raw source near the row. The
     09-06 walker had enter-only coverage; its return value (the gate's
     own lookup decision) was never logged across the arc.

Output: findings with file:line; exit 1 on any; writes
RE_output/map/probe_audit.json (the freshness token the deploy gate
consumes - deploy_client_dll.sh refuses a client whose hook sources are
not covered by a PASS record). `--quiet` for the deploy path.

Selftest: synthetic hook trees for every arm (A-bad/A-good, B-bad/B-good,
C-bad/C-good) - the negative arms use the SHAPES OF THE SHIPPED DEFECTS.
Prints PROBE_AUDIT SELFTEST: n/n PASS last (liveness).
Interpreter: /usr/bin/python3.
"""
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from hook_targets import (strip_comments, parse_tables,       # noqa: E402
                          duplicate_rva_problems, raw_lines_around)

DEFAULT_HOOKS = (Path(ROOT) / "RE_build/Sunrise-fork-inventory/Sunrise/"
                 "src/client/hooks")
DEFAULT_OUT = Path(ROOT) / "RE_output/map/probe_audit.json"

EMIT_RE = re.compile(r"\bvoid\s+(emit_\w+)\s*\(")
ALIGN_GUARD_RE = re.compile(r"[&%]\s*(?:0x7|7)\b")
CITE_RE = re.compile(r"ALIGN-CITED|alignment|misalign|&7\s*=|\+0x[0-9A-Fa-f]+",
                     re.I)
SIG_RE = re.compile(r"(\w*[sS]ig\w*)\s*=\s*([^;\n]+);")
ZERO_GUARD_RE = re.compile(r"(sig|Sig|SIG)\s*==\s*0")
TRANSFORM_RE = re.compile(r"\bmix\w*\(|rotl\w*\(|\(\s*\w+\s*<<\s*1\b|\brol\d*\(")
LEAVE_RE = re.compile(r"leave|return|_ret\b|retwatch", re.I)
LOOKUP_STEM_RE = re.compile(r"walk|lookup|find|map|cmp|compare|gate|sess|"
                            "search|resolve")


def _emit_functions(stripped):
    """{name: start_line} of the emit_* function definitions."""
    out = {}
    lines = stripped.split("\n")
    for i, line in enumerate(lines, 1):
        m = EMIT_RE.search(line)
        if m:
            out[m.group(1)] = i
    return out


def audit_alignment_guards(rel, raw, stripped, findings):
    """A: any live alignment-test guard in an emit function must carry an
    alignment citation within 5 lines above (raw text)."""
    lines = stripped.split("\n")
    raw_lines = raw.split("\n")
    for i, line in enumerate(lines):
        if "return" not in line:
            continue
        if not ALIGN_GUARD_RE.search(line):
            continue
        # is this inside an emit function? find the nearest emit above
        lo = max(0, i - 8)
        if not any(EMIT_RE.search(l) for l in lines[max(0, i - 40):i + 1]):
            continue
        cited = any(CITE_RE.search(raw_lines[j])
                    for j in range(max(0, i - 5), i + 1)
                    if j < len(raw_lines))
        if not cited:
            findings.append(
                f"{rel}:{i + 1}: alignment guard without a decoded-alignment "
                "citation - the 09-06 BLIND-GUARD class: a qword-alignment "
                "guard refused the gate's own deliberately-unaligned fields "
                "for five boots. Cite the field's decoded alignment "
                "(ALIGN-CITED / &7=N / the +offset) or drop the guard to the "
                "wild-pointer floor")


def _payload_xor_findings(rel, stripped, findings):
    """B: plain XOR-of-two-field signatures, without per-operand transforms
    or a zero-guard, hide MATCHES (the 09-06 addendum defect)."""
    lines = stripped.split("\n")
    for i, line in enumerate(lines):
        m = SIG_RE.search(line)
        if not m:
            continue
        lhs, rhs = m.group(1), m.group(2).strip()
        # the RHS's last token before ^ and first after: plain idents?
        parts = [p.strip() for p in rhs.split("^")]
        if len(parts) < 2:
            continue
        plain = all(re.fullmatch(r"\w+", p.strip()) for p in parts)
        transformed = all(("mix" in p or "rot" in p or "<<" in p)
                          for p in parts)
        window = "\n".join(lines[max(0, i - 2):i + 3])
        guard = bool(ZERO_GUARD_RE.search(window))
        if plain and not guard:
            findings.append(
                f"{rel}:{i + 1}: novelty signature is a PLAIN XOR of two "
                f"fields ({lhs}) - it collides to zero exactly when the "
                "fields are EQUAL, i.e. on MATCHES, the event a compare "
                "probe exists to observe (09-06 BLIND-GUARD ADDENDUM). "
                "Hash the fields JOINTLY (mix one, rotate the other) and "
                "add the zero-guard; the collision arm ((k,k) must not "
                "alias (0,0)) is the probe's own required test")
        elif not transformed and not guard:
            findings.append(
                f"{rel}:{i + 1}: signature {lhs} mixes transformed and raw "
                "operands without a zero-guard - prove the collision "
                "property ((k,k) != (0,0)) or transform each operand "
                "(rotl one into the other, the 8252f1dad6e8a0c1 form)")


def leave_capable_kinds(raw_by_file):
    """Read the Probe enum's OWN doc comments: a kind whose doc says
    'On leave' / 'returns' observes the OUTCOME (the leave side) by
    construction - the project's declared taxonomy, not a guess."""
    caps = set()
    for raw in raw_by_file.values():
        lines = raw.split("\n")
        for i, line in enumerate(lines):
            km = re.match(r"\s*([A-Za-z_]\w*),?\s*$", line)
            if not km:
                continue
            kind = km.group(1)
            doc = "\n".join(lines[max(0, i - 10):i])
            if re.search(r"[Oo]n [Ll][Ee][Aa][Vv][Ee]|\breturn|RETURNS|\brax\b"
                         r"|the outcome", doc):
                caps.add(kind)
    return caps


def audit_lookup_pairing(tables, files_raw):
    """C (R6): a lookup-class install row needs its LEAVE side (a same-RVA
    leave row, an emit pairing the stem with leave, or a `no-leave:`
    citation) - the 09-06 walker had enter-only coverage and the gate's own
    lookup decision was never logged."""
    findings = []
    emit_names = set()
    for rel, raw in files_raw.items():
        stripped = strip_comments(raw)
        for name in _emit_functions(stripped):
            emit_names.add(name.lower())
    for t in tables:
        for e in t.entries:
            if e.name is None or e.rva in (None, 0):
                continue
            if not LOOKUP_STEM_RE.search(e.name):
                continue
            if LEAVE_RE.search(e.name):
                continue    # this row IS a leave-side probe
            if e.kind and e.kind in leave_capable_kinds(files_raw):
                continue    # its kind's own doc declares it outcome-observing
            stem = e.name.split("_")[0]
            paired = False
            for other in t.entries:
                # pairing must be ON THE SAME FUNCTION (same RVA): a
                # leave-named row on an unrelated function does not give
                # this lookup its outcome (the 09-06 walker shape)
                if other is e or other.name is None or other.rva != e.rva:
                    continue
                if LEAVE_RE.search(other.name):
                    paired = True
            if not paired:
                for en in emit_names:
                    if "leave" in en and stem in en:
                        paired = True
                        break
            if not paired:
                raw = files_raw.get(t.file.name) or \
                    files_raw.get(str(t.file), "")
                window = raw_lines_around(t.file, e.lineno, span=2)
                if "no-leave:" in window:
                    paired = True
            if not paired:
                findings.append(
                    f"{t.file.name}:{e.lineno}: lookup-class row "
                    f"{e.name!r} has no LEAVE-side coverage - a lookup's "
                    "OUTCOME is on leave (the 09-06 walker logged enter "
                    "only; its return value was the gate's own decision, "
                    "never logged). Pair a leave probe on the same row's "
                    "dispatch or cite `no-leave: <reason>`")
    return findings


def _emit_function_bodies(stripped):
    """{name: (start_line, text)} for every emit_* function - the body is
    BRACE-MATCHED from the emit_ line, not 'to the next emit_': emit
    functions are interleaved with tables and dispatch code, and a sloppy
    slice made six unrelated probes look budgeted (found by the real-tree
    run of check D, 2026-09-06)."""
    lines = stripped.split("\n")
    out = {}
    i = 0
    while i < len(lines):
        m = EMIT_RE.search(lines[i])
        if not m:
            i += 1
            continue
        name = m.group(1)
        depth, opened, j = 0, False, i
        while j < len(lines):
            for ch in lines[j]:
                if ch == "{":
                    depth += 1
                    opened = True
                elif ch == "}":
                    depth -= 1
                    if opened and depth == 0:
                        break
            if opened and depth == 0:
                break
            j += 1
        out[name] = (i, "\n".join(lines[i:j + 1]))
        i = j + 1
    return out


BUDGET_RE = re.compile(r"\bbudget\b|>=\s*k\w*[Bb]udget|\w*[Bb]udget\w*\)")
EXHAUSTED_RE = re.compile(r"budget_exhausted|exhaustedLogged|budget exhaust")
READ_RE = re.compile(r"safe_read\(|ReadProcessMemory|mem_read\(")


def check_budget_marker(rel, stripped, findings):
    """D (T3.1, 09-01/09-03): a budgeted probe must SAY its detail stream
    ended - the log itself carries the budget_exhausted marker; a reader
    must never derive 'no X happened' from budget silence."""
    for name, (start, body) in _emit_function_bodies(stripped).items():
        if BUDGET_RE.search(body) and not EXHAUSTED_RE.search(body):
            findings.append(
                f"{rel}: probe {name} gates on a BUDGET but never names its "
                "exhaustion - a capped probe's silence reads as 'no X "
                "happened' (T3.1: the budget measures the beginning of a "
                "boot, the census continues). Emit a budget_exhausted "
                "marker when the budget first runs out")


def check_hot_path(rel, raw, stripped, baseline_stripped, findings):
    """E (R8, 09-06 p2-194b): the number of memory reads inside the emit_
    functions is checked against the git baseline; an INCREASE on the hot
    path is refused unless the raw source cites `HOT-PATH-OK: <reason>` -
    the six extra guarded reads stalled the mac's landing transition."""
    cur_counts = {}
    for name, (_s, body) in _emit_function_bodies(stripped).items():
        cur_counts[name] = len(READ_RE.findall(body))
    base_counts = {}
    if baseline_stripped:
        for name, (_s, body) in _emit_function_bodies(baseline_stripped).items():
            base_counts[name] = len(READ_RE.findall(body))
    for name, n in cur_counts.items():
        b = base_counts.get(name)
        if b is None or n <= b:
            continue
        cited = "HOT-PATH-OK:" in raw
        if not cited:
            findings.append(
                f"{rel}: probe {name}'s read count grew {b} -> {n} on the "
                "hot path - new reads go BEHIND the change gate (read only "
                "when a line emits), never into the loop (09-06 p2-194b: "
                "the six extra reads stalled the mac's landing transition). "
                "Cite `HOT-PATH-OK: <reason>` if the cost is re-derived")


def git_baselines(files):
    """HEAD:<path> text for each git-TRACKED hook file (the R8 cost arm's
    baseline). Untracked/new files have no baseline - check E skips them,
    honestly (a new file's read count has no prior to compare)."""
    out = {}
    import subprocess
    for path in files:
        try:
            r = subprocess.run(["git", "show", "HEAD:%s" % path],
                               capture_output=True, text=True,
                               timeout=60, cwd=str(ROOT))
            if r.returncode == 0:
                out[str(path)] = r.stdout
        except (OSError, subprocess.TimeoutExpired):
            continue
    return out


def audit(hooks_dir, quiet=False, baselines=None):
    findings = []
    hooks = Path(hooks_dir)
    files = sorted(hooks.rglob("*.cpp"))
    stripped_texts, raw_texts = {}, {}
    for path in files:
        raw = path.read_text(errors="replace")
        raw_texts[path.name] = raw
        stripped_texts[path.name] = strip_comments(raw)
    if baselines is None:
        # R8's cost arm MUST be reachable from the CLI - it was built with a
        # baselines parameter the CLI never passed, so the hot-path defect
        # sailed through the gate built for it (STATE tooling debt (c))
        baselines = git_baselines(files)
    for path in files:
        rel = path.relative_to(hooks).as_posix()
        stripped = stripped_texts[path.name]
        raw = raw_texts[path.name]
        baseline = (baselines or {}).get(str(path))
        baseline_stripped = strip_comments(baseline) if baseline else None
        audit_alignment_guards(rel, raw, stripped, findings)
        _payload_xor_findings(rel, stripped, findings)
        check_budget_marker(rel, stripped, findings)
        check_hot_path(rel, raw, stripped, baseline_stripped, findings)
    tables = parse_tables(hooks)
    findings.extend(audit_lookup_pairing(tables, raw_texts))
    for p in duplicate_rva_problems(
            tables, raw_reader=lambda path, ln: raw_lines_around(path, ln)):
        findings.append(p)

    tree_hash = hashlib.sha256(
        b"".join(str(p).encode() + p.read_bytes() for p in files)).hexdigest()[
        :16]
    verdict = "PASS" if not findings else "FAIL"
    if not quiet or findings:
        print(f"PROBE AUDIT: {verdict} "
              f"({len(files)} hook files, {len(findings)} finding(s))")
        for f in findings:
            print(f"  ** {f}")
    record = {
        "hooks_tree_hash": tree_hash,
        "verdict": verdict,
        "findings": findings,
        "files": [p.relative_to(hooks).as_posix() for p in files],
        "when": datetime.now().isoformat(timespec="seconds"),
    }
    out = Path(ROOT) / "RE_output" / "map" / "probe_audit.json"
    try:
        out.write_text(json.dumps(record, indent=2))
        if not quiet:
            print(f"record -> {out}")
    except OSError as e:
        print(f"WARN: could not write {out}: {e}")
    return 0 if not findings else 1


# ----------------------------------------------------------------- selftest ---
GOOD_GUARD = """
void emit_okprobe(const char* fn, std::uint64_t call, std::uint64_t ptr) noexcept {
    if (ptr < 0x10000U) { return; }  // wild-pointer floor
    std::uint64_t q = safe_read(ptr);
}
"""

BAD_GUARD = """
void emit_badprobe(const char* fn, std::uint64_t call, std::uint64_t ptr) noexcept {
    if ((ptr & 7) != 0) { return; }   // qword pointers only
    std::uint64_t q = safe_read(ptr);
}

void emit_citedprobe(const char* fn, std::uint64_t call, std::uint64_t ptr) noexcept {
    // ALIGN-CITED: the gate blob sits at +0x57C (&7=4); x86-64 reads any alignment
    if ((ptr & 7) != 0) { return; }
    std::uint64_t q = safe_read(ptr);
}
"""

BAD_SIG = """
void emit_badsig(std::uint64_t keyQ, std::uint64_t blobQ) noexcept {
    std::uint64_t pairSig = keyQ ^ blobQ;
    if (seen(pairSig)) return;
}
"""

GOOD_SIG = """
// collision arm: mix(k)^rotl(blob,1) does not alias (0,0) for (k,k) pairs
void emit_goodsig(std::uint64_t keyQ, std::uint64_t blobQ) noexcept {
    std::uint64_t pairSig = mix_u64(keyQ) ^ ((blobQ << 1) | (blobQ >> 63));
    if (pairSig == 0) { pairSig = 1; }
}
"""

TABLE_ENTER_ONLY = """
constexpr std::size_t kTargetsSize = 2;
constexpr std::array<Target, kTargetsSize> kTargets{{
    {"walk_map",   0x17A0B0, 16},
    {"leave_probe", 0x4F34C0, 8},
}};
"""

TABLE_PAIRED = """
constexpr std::size_t kTargetsSize = 2;
constexpr std::array<Target, kTargetsSize> kTargets{{
    {"walk_map",   0x1417A0B0, 16},
    {"walk_leave", 0x1417A0B0, 16},   // DUAL-OK: one detour, enter+leave dispatch
}};
"""


def selftest():
    fails = []

    def check(name, cond, detail=""):
        print("%s %-52s %s" % ("PASS" if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        # A: alignment guard arms
        d1 = root / "g1"
        d1.mkdir()
        (d1 / "a.cpp").write_text(
            BAD_GUARD + GOOD_GUARD, encoding="utf-8")
        f1 = []
        audit_alignment_guards("a.cpp", BAD_GUARD + GOOD_GUARD,
                               strip_comments(BAD_GUARD + GOOD_GUARD), f1)
        check("A-bad: uncited alignment guard flagged",
              len(f1) == 1 and "a.cpp" in f1[0], f1[0][:70] if f1 else "")
        # with the citation present -> the cited probe is NOT flagged
        d2 = root / "g2"
        d2.mkdir()
        (d2 / "a.cpp").write_text(BAD_GUARD, encoding="utf-8")
        f2 = []
        audit_alignment_guards("a.cpp", BAD_GUARD, strip_comments(BAD_GUARD),
                               f2)
        check("A-good: the ALIGN-CITED sibling is exempt",
              len(f2) == 1 and "citedprobe" not in f2[0],
              "%d finding(s)" % len(f2))

        # B: XOR-signature arms
        _x, b_bad = [], []
        _payload_xor_findings("sig.cpp", strip_comments(BAD_SIG), b_bad)
        check("B-bad: plain XOR-of-fields signature flagged",
              len(b_bad) == 1 and "MATCHES" in b_bad[0],
              b_bad[0][:70] if b_bad else "")
        b_good = []
        _payload_xor_findings("sig.cpp", strip_comments(GOOD_SIG), b_good)
        check("B-good: joint hash + zero-guard passes",
              b_good == [], str(b_good))

        # C: enter/leave pairing arms
        d3 = root / "g3"
        d3.mkdir()
        (d3 / "t_enter_only.cpp").write_text(TABLE_ENTER_ONLY,
                                             encoding="utf-8")
        t_bad = parse_tables(d3)
        c_bad = audit_lookup_pairing(t_bad, {"t_enter_only.cpp":
                                             TABLE_ENTER_ONLY})
        check("C-bad: lookup row without leave coverage flagged",
              len(c_bad) == 1 and "walk_map" in c_bad[0],
              c_bad[0][:70] if c_bad else "")
        d4 = root / "g4"
        d4.mkdir()
        (d4 / "t_paired.cpp").write_text(TABLE_PAIRED, encoding="utf-8")
        t_good = parse_tables(d4)
        c_good = audit_lookup_pairing(t_good, {"t_paired.cpp": TABLE_PAIRED})
        check("C-good: paired rows / DUAL-OK waiver passes", c_good == [],
              str(c_good))

        # D: budget marker arms (T3.1)
        BAD_BUDGET = """
void emit_budgetprobe(const char* fn, std::uint64_t call, std::uint64_t a) noexcept {
    SessSlot* s = find_slot(a);
    if (s->emits.load() >= kBudget) return;
    log("x=%u", a);
}
"""
        GOOD_BUDGET = """
void emit_budgetprobe(const char* fn, std::uint64_t call, std::uint64_t a) noexcept {
    SessSlot* s = find_slot(a);
    if (s->emits.load() >= kBudget) {
        if (!exhaustedLogged.exchange(true)) log("budget_exhausted");
        return;
    }
    log("x=%u", a);
}
"""
        d_bad = []
        check_budget_marker("d.cpp", strip_comments(BAD_BUDGET), d_bad)
        check("D-bad: budgeted probe without an exhausted marker flagged",
              len(d_bad) == 1 and "budget_exhausted" in d_bad[0],
              d_bad[0][:70] if d_bad else "")
        d_good = []
        check_budget_marker("d.cpp", strip_comments(GOOD_BUDGET), d_good)
        check("D-good: the budget_exhausted marker satisfies", d_good == [],
              str(d_good))

        # E: hot-path read accounting arms (R8)
        BASE_TEXT = """
void emit_hotsig(const char* fn, std::uint64_t call, std::uint64_t p) noexcept {
    std::uint64_t q = safe_read(p);
    log("q=%u", q);
}
"""
        CUR_MORE = BASE_TEXT.replace('log("q=%u", q);',
                                     'std::uint64_t r = safe_read(p + 8);\n'
                                     '    log("q=%u r=%u", q, r);')
        e_bad = []
        check_hot_path("e.cpp", CUR_MORE, strip_comments(CUR_MORE),
                       strip_comments(BASE_TEXT), e_bad)
        check("E-bad: added reads on the hot path flagged",
              len(e_bad) == 1 and "1 -> 2" in e_bad[0],
              e_bad[0][:70] if e_bad else "")
        e_ok = []
        check_hot_path("e.cpp", CUR_MORE.replace("std::uint64_t r = safe_read",
                                                 "// HOT-PATH-OK: cost re-derived\n    std::uint64_t r = safe_read"),
                       strip_comments(CUR_MORE), strip_comments(BASE_TEXT),
                       e_ok)
        check("E-good: HOT-PATH-OK: citation satisfies", e_ok == [],
              str(e_ok))

        # duplicate-RVA: unwaivered fails, DUAL-OK waives
        d5 = root / "g5"
        d5.mkdir()
        (d5 / "t_dup.cpp").write_text(
            TABLE_PAIRED.replace("DUAL-OK: one detour", ""), encoding="utf-8")
        t_dup = parse_tables(d5)
        dup_bad = duplicate_rva_problems(
            t_dup, raw_reader=lambda p, ln: raw_lines_around(p, ln))
        check("C-bad2: duplicate RVA without DUAL-OK waiver fails",
              len(dup_bad) == 1, dup_bad[0][:70] if dup_bad else "")
        t_ok = parse_tables(d3.parent / "g4")
        dup_ok = duplicate_rva_problems(
            t_ok, raw_reader=lambda p, ln: raw_lines_around(p, ln))
        check("C-good2: DUAL-OK: waiver accepted", dup_ok == [], str(dup_ok))

    print("PROBE_AUDIT SELFTEST: %d/%d PASS" % (10 - len(fails), 10))
    return 0 if not fails else 4


def main(argv):
    if "--selftest" in argv:
        return selftest()
    quiet = "--quiet" in argv
    hooks = DEFAULT_HOOKS
    if "--hooks-dir" in argv:
        i = argv.index("--hooks-dir")
        hooks = Path(argv[i + 1])
    if not hooks.is_dir():
        print(f"PROBE AUDIT FAIL: hook tree missing: {hooks}")
        return 1
    rc = audit(hooks, quiet=quiet)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
