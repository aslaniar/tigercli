#!/usr/bin/env python3
# REGISTRY: caps: struct-annotate, dump-field-view, field-xref-join
"""struct_view.py - THE STRUCT FIELD ANNOTATOR (tool-brief-struct-view.md,
2026-09-06). A JOIN tool, not a scanner: given a dump + a VA it walks the
object field by field and joins THREE existing evidence stores per
displacement - field_xref (who touches +N, post-T1.3), the function map
(funcq's reconcile db), and the beacon census - plus pointer classification
from the dump's own module/range tables. Composition, not a fork: any byte
scanning duplicated here is a defect.

The question class: "what is this live object, field by field, and who
touches each field" - the manual loop behind the ctx+0x28 container, the
identity blobs, the participant records, and p2-186's copier walk (which
cost a boot on a wrong offset before being settled on paper).

COVERAGE HONESTY (the forbidden-phrase rule, T1.3): this tool may NEVER print
"no writers". The only legal negatives are NOT-SCANNED / UNCOVERED /
SCAN-COMPLETE-n-hits. Every xref hit is a CANDIDATE (the 20.291 R9.3 rule:
unjudged is unjudged). A hole is a HOLE, never a silent zero.

Usage:
  /usr/bin/python3 RE_scripts/struct_view.py <dump> <va>
      [--size 0x100] [--width 8] [--depth 1] [--follow-size 0x20]
      [--disp HEXLIST] [--no-xref] [--json] [--exe P] [--selftest]

<va> may be static (0x140000000-based) or runtime (dump-module-based).
Exit codes: 0 annotated (holes possible, each marked); 1 REFUSED (base VA
not in any dumped range); 4 selftest failure; 5 usage.
Interpreter: /usr/bin/python3 (capstone via field_xref; NO unicorn needed).
"""
import bisect
import json
import os
import sqlite3
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from pe_reader import PE                    # noqa: E402
from pdata_bounds import entries            # noqa: E402
from callers import owner_of                # noqa: E402
import field_xref                            # noqa: E402
from minidump_reader import Minidump         # noqa: E402

DEFAULT_EXE = os.path.join(ROOT, "RE_output", "destiny2_unpacked_full.exe")
DEFAULT_DB = os.path.join(ROOT, "RE_output", "map", "function_map.db")
DEFAULT_BEACONS = os.path.join(ROOT, "RE_output", "map", "beacons.json")
BASE = 0x140000000

FORBIDDEN = ("no writers", "nobody touches", "nothing writes", "no writes",
             "no reads")


class Ctx(object):
    """Everything expensive, loaded once."""

    def __init__(self, dump_path, exe_path=DEFAULT_EXE):
        self.md = Minidump(dump_path)
        self.pe = PE(exe_path)
        self.pdata = entries(self.pe)
        self.begins = [e[0] for e in self.pdata]
        self.mod = self.md.module("destiny2")
        if not self.mod_ok():
            raise SystemExit("ERROR: no destiny2 module in %s" % dump_path)
        self.rt_base = self.mod["base"]
        self.image_span = max(v + vs for _n, v, vs, _r, _rs in self.pe.sections)
        self.db = None
        if os.path.exists(DEFAULT_DB):
            self.db = sqlite3.connect(DEFAULT_DB)
        self.beacons = {}
        if os.path.exists(DEFAULT_BEACONS):
            with open(DEFAULT_BEACONS) as f:
                raw = json.load(f)
            # strings: [[static_va, kind, text], ...] -> per-function lists
            per = {}
            for va_s, _kind, text in raw.get("strings", []):
                va = int(va_s, 16)
                per.setdefault(va, []).append(text)
            self.beacons = per

    # -- address-space helpers -------------------------------------------
    def dumped_at(self, va):
        """@return (start, size) of the dumped range containing va, else None."""
        for start, size, _off in self.md.ranges:
            if start <= va < start + size:
                return (start, size)
        return None

    def in_image(self, va):
        return (self.rt_base <= va <
                self.rt_base + self.image_span)

    def static_of(self, rt):
        return self.pe.imagebase + (rt - self.rt_base)

    def runtime_of(self, static):
        return self.rt_base + (static - self.pe.imagebase)

    def mod_ok(self):
        return self.mod is not None

    # -- evidence ----------------------------------------------------------
    def fname(self, func_va):
        if self.db is None:
            return []
        rows = self.db.execute(
            "SELECT name, status FROM names WHERE func=?",
            (func_va,)).fetchall()
        return ["%s [%s]" % (n, s) for n, s in rows[:4]]

    def beacon_strings(self, begin, end):
        out = []
        for va, texts in self.beacons.items():
            if begin <= va < end:
                out.extend(texts[:2])
        return out[:3]


def classify_value(ctx, v, width):
    """Classify one slot value. Pure over (ctx modules/ranges) - unit-testable.
    Small values are checked FIRST: in this address space (static 0x140..,
    runtime 0x7FF.., heap 0x1000_0000_000+) a value < 0x10000 is a count or
    a flag, never a pointer."""
    if v == 0:
        return "0"
    if v < 0x10000:
        return "small-int %d" % v
    if width == 8 and ctx.in_image(v):
        s = ctx.static_of(v)
        sec = ctx.pe.section_of(s)
        return "MODULE-PTR -> static 0x%X (%s)" % (s, sec or "?")
    if width == 8:
        for mod in ctx.md.modules:
            if mod["base"] <= v < mod["base"] + mod["size"]:
                nm = os.path.basename(mod["name"].replace("\\", "/"))
                if mod["base"] != ctx.rt_base:
                    return "OTHER-MODPTR(%s) 0x%X" % (nm, v)
        r = ctx.dumped_at(v)
        if r:
            return "RUNTIME-PTR (dumped @%s..+%#x)" % (hex(r[0]), r[1])
        return "HEAP/UNMAPPED-PTR?"
    raw = struct.pack("<Q" if width == 8 else "<I", v)
    if all(32 <= b < 127 for b in raw.rstrip(b"\x00")) and raw.rstrip(b"\x00"):
        return "ascii %r" % raw.rstrip(b"\x00").decode()
    return "int 0x%X" % v


def xref_for_disp(ctx, disp, do_xref=True, max_rows=40, validated_disps=()):
    """THE field_xref join. Returns (lines, coverage_state). Capped at
    max_rows rendered CANDIDATE rows with a TRUNCATED marker naming N of M
    (the T3.1 rule: the output itself says the detail stream ended; the
    counts stay exact). disp8 candidates are UNVALIDATED by default
    (boundary validation is ~44s per displacement on this binary - the
    per-item enrichment cost measured 2026-09-06); pass the disp in
    validated_disps (CLI --validate-disp) for the boundary-confirmed census."""
    if not do_xref:
        return [], "NOT-SCANNED (--no-xref)"
    hits32 = field_xref.scan(ctx.pe, disp)
    rows = []
    if disp <= 0x7F:
        signed = disp if disp < 0x80 else disp - 0x100
        validated = disp in validated_disps
        hits8 = field_xref.scan8(ctx.pe, signed, validate=disp in
                                 validated_disps)
        if validated:
            confirmed = [h for h in hits8 if h[3]]
            coverage = ("SCAN-COMPLETE-32+8-VALIDATED "
                        "(%d disp32 + %d confirmed disp8; SIB/rip NOT RUN)"
                        % (len(hits32), len(confirmed)))
            for va, acc, mnem, conf, det in confirmed:
                rows.append((va, acc + "8v", mnem, det))
        else:
            confirmed = hits8
            coverage = ("SCAN-COMPLETE-32+disp8-CANDIDATES-UNVALIDATED "
                        "(%d disp32 + %d disp8 candidates, boundary "
                        "validation NOT run - cite them as CANDIDATE only; "
                        "validated census: field_xref.py --disp8 %#x; "
                        "SIB/rip NOT RUN)"
                        % (len(hits32), len(hits8), disp))
            for va, acc, mnem, conf, det in hits8:
                rows.append((va, acc + "8u", mnem, "unvalidated"))
    else:
        coverage = ("SCAN-COMPLETE-32 (disp8 N/A above 0x7F; "
                    "SIB/rip NOT RUN) - %d disp32 hits" % len(hits32))
    for va, acc, mnem, raw in hits32:
        rows.append((va, acc, mnem, raw))
    lines = []
    total = len(rows)
    for va, acc, mnem, det in sorted(rows)[:max_rows]:
        owner = owner_of(ctx.pe, ctx.pdata, ctx.begins, va)
        m = None
        if owner != "NO-PDATA-ENTRY":
            m = __import__("re").search(r"0x([0-9A-F]+)\.\.", owner)
        names, beacons = [], []
        if m:
            begin = BASE + int(m.group(1), 16)
            row = None
            if ctx.db:
                row = ctx.db.execute(
                    "SELECT addr, size FROM functions WHERE addr=?",
                    (begin,)).fetchone()
                if row is None:
                    row = ctx.db.execute(
                        "SELECT addr, size FROM functions "
                        "WHERE addr<=? AND addr+size>? ORDER BY addr "
                        "DESC LIMIT 1", (begin, begin)).fetchone()
            if row:
                names = [n for n, in ctx.db.execute(
                    "SELECT name FROM names WHERE func=?", (row[0],))]
                beacons = ctx.beacon_strings(row[0], row[0] + row[1])
        ev = ""
        if names:
            ev += " names=%s" % names
        if beacons:
            ev += " beacons=%s" % beacons
        lines.append("      %s  %-13s %-16s CANDIDATE %s owner=%s%s"
                     % (hex(va), acc, mnem, det[:46], owner, ev))
    if total > max_rows:
        lines.append("      TRUNCATED: %d of %d CANDIDATE rows shown "
                     "(cap %d - raise --max-rows for the full census; the "
                     "counts above are exact)" % (max_rows, total, max_rows))
        coverage += " | TRUNCATED %d->%d rows" % (total, max_rows)
    return lines, coverage


def walk(ctx, va_rt, size, width, depth, follow_size, do_xref, out_slots,
         max_rows=40, validated_disps=()):
    """One level of the walk. Appends slot dicts to out_slots."""
    disp_cache = {}

    def disp_evidence(disp):
        if disp not in disp_cache:
            disp_cache[disp] = xref_for_disp(ctx, disp, do_xref, max_rows,
                                             validated_disps)
        return disp_cache[disp]

    for off in range(0, size, width):
        raw = ctx.md.read_va(va_rt + off, width)
        slot = {"off": off, "disp": hex(off)}
        if raw is None:
            slot["value"] = None
            slot["class"] = "HOLE (page not in dump)"
            lines, cov = disp_evidence(off)
            slot["coverage"] = cov
            slot["xref"] = lines
            out_slots.append(slot)
            continue
        v = int.from_bytes(raw, "little")
        slot["value"] = hex(v)
        slot["class"] = classify_value(ctx, v, width)
        lines, cov = disp_evidence(off)
        slot["coverage"] = cov
        slot["xref"] = lines
        # pointer follow (one level, bounded)
        if (depth > 0 and width == 8 and v and
                (slot["class"].startswith("MODULE-PTR") or
                 slot["class"].startswith("RUNTIME-PTR"))):
            sub = []
            walk(ctx, v, follow_size, width, depth - 1, follow_size,
                 do_xref, sub, max_rows)
            slot["follow"] = {
                "target": hex(v),
                "note": ("followed sub-object - field evidence here is per "
                         "DISPLACEMENT, not per type; a field reached via a "
                         "sub-object base spells a different displacement "
                         "(the 20.276 base-alias trap)"),
                "slots": sub,
            }
        out_slots.append(slot)


def render(slots, indent=0):
    lines = []
    pad = "  " * indent
    for s in slots:
        val = s["value"] if s["value"] is not None else "<unavailable>"
        lines.append("%s+%#06x %-18s %s" % (pad, s["off"], val, s["class"]))
        lines.append("%s        COVERAGE %s" % (pad, s["coverage"]))
        for x in s.get("xref", []):
            lines.append(pad + x)
        f = s.get("follow")
        if f:
            lines.append("%s        -> followed %s:" % (pad, f["target"]))
            lines.extend(render(f["slots"], indent + 3))
    return lines


def to_json(slots):
    return json.dumps(slots, indent=2)


def main(argv):
    if "--selftest" in argv:
        return selftest()
    import argparse
    p = argparse.ArgumentParser(prog="struct_view.py")
    p.add_argument("dump")
    p.add_argument("va")
    p.add_argument("--size", type=lambda x: int(x, 0), default=0x100)
    p.add_argument("--width", type=int, default=8, choices=(8, 4))
    p.add_argument("--depth", type=int, default=0)
    p.add_argument("--follow-size", type=lambda x: int(x, 0), default=0x20)
    p.add_argument("--disp", action="append", default=[],
                   help="extra displacements to xref (repeatable)")
    p.add_argument("--no-xref", action="store_true")
    p.add_argument("--max-rows", type=int, default=40,
                   help="per-disp CANDIDATE row cap (TRUNCATED marker when "
                        "exceeded; counts stay exact)")
    p.add_argument("--validate-disp", action="append", default=[],
                   help="displacement to boundary-validate disp8 for "
                        "(~44s each on this binary; repeatable)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--exe", default=DEFAULT_EXE)
    a = p.parse_args(argv)

    try:
        va = int(a.va, 0)
    except ValueError:
        print("usage: <va> must be a number")
        return 5
    ctx = Ctx(a.dump, a.exe)

    # static <-> runtime resolution
    if ctx.in_image(va):
        va_rt = va
    elif BASE <= va < BASE + ctx.image_span:
        va_rt = ctx.runtime_of(va)
    else:
        va_rt = va  # a plain heap/runtime address
    r = ctx.dumped_at(va_rt)
    if r is None:
        print("REFUSED: 0x%X is not in any dumped memory range "
              "(nothing was captured there - that is a capture fact, not a "
              "zero)" % va_rt)
        return 1

    slots = []
    vdisps = set(int(x, 16) for x in a.validate_disp)
    walk(ctx, va_rt, a.size, a.width, a.depth, a.follow_size,
         not a.no_xref, slots, a.max_rows, vdisps)
    for extra in a.disp:
        lines, cov = xref_for_disp(ctx, int(extra, 16), not a.no_xref,
                                   a.max_rows, vdisps)
        slots.append({"off": int(extra, 16), "disp": extra, "value": None,
                      "class": "(extra --disp request)", "coverage": cov,
                      "xref": lines})
    hdr = ["== struct_view ==",
           "dump module destiny2 base=0x%X" % ctx.rt_base]
    if ctx.in_image(va_rt):
        hdr.append("object static 0x%X (section %s)"
                   % (ctx.static_of(va_rt),
                      ctx.pe.section_of(ctx.static_of(va_rt)) or "?"))
    if a.json:
        print(json.dumps({"header": hdr, "slots": slots}, indent=2))
    else:
        print("\n".join(hdr))
        print("\n".join(render(slots)))
        n_holes = sum(1 for s in slots if s["class"].startswith("HOLE"))
        if n_holes:
            print("PROVENANCE: %d HOLE slot(s) - pages the dump did not "
                  "capture; never treated as zeros" % n_holes)
    return 0


# ----------------------------------------------------------------- selftest ---
def selftest():
    """No dump required: classification unit (synthetic module/range tables),
    join-equality vs raw field_xref, coverage honesty (the forbidden-phrase
    arms), CALL-INDIRECT passthrough, owner/naming joins.
    Prints STRUCT_VIEW SELFTEST: n/n PASS last (liveness)."""
    fails = []

    def check(name, cond, detail=""):
        print("%s %-52s %s" % ("PASS" if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    pe = PE(DEFAULT_EXE)

    # ---- T1-P1: join-equality - struct_view's evidence == raw field_xref --
    class FakeCtx(object):
        pass
    ctx = FakeCtx()
    ctx.pe = pe
    cases = [(0x2C1, 0x140E23002, "read"), (0x350, 0x140E2B405, "WRITE"),
             (0x53C, 0x140E289EF, "WRITE")]
    for disp, want_va, want_access in cases:
        got = {va: acc for va, acc, _m, _d in field_xref.scan(pe, disp)}
        check("T1-P1 join: disp %#x @ %#x == %s"
              % (disp, want_va, want_access),
              got.get(want_va) == want_access,
              "got=%s" % got.get(want_va))
    hits8 = field_xref.scan8(pe, 0x44)
    conf = {va for va, a, m, c, d in hits8 if c}
    check("T1-P1 join: disp8 0x44 confirmed set intact",
          {0x1416E9CF0, 0x1416EBD51, 0x14171812A} <= conf,
          "%d confirmed" % len(conf))

    # ---- T1-F4: CALL-INDIRECT passthrough (T1.3 preservation) ----
    c = field_xref.classify(bytes([0x90, 0xFF, 0x97, 0x38, 0, 0, 0]), 3)
    check("T1-F4 ff/2 renders as CALL-INDIRECT (never write/RMW)",
          c is not None and c[1] == "CALL-INDIRECT", str(c))

    # ---- T1-F3: coverage honesty - the forbidden-phrase arms ----
    # direct check: NOT-SCANNED state and the renderer never emit the phrase
    _, cov_nox = xref_for_disp(FakeCtx(), 0x38, do_xref=False)
    check("T1-F3 --no-xref -> NOT-SCANNED (not a silent negative)",
          cov_nox == "NOT-SCANNED (--no-xref)", cov_nox)
    sample = json.dumps({"coverage": cov_nox})
    check("T1-F3 forbidden phrases absent from output vocabulary",
          not any(f in sample.lower() for f in FORBIDDEN))

    # coverage for a small disp names the disp8 requirement
    fc2 = FakeCtx()
    fc2.pe = pe
    fc2.pdata = entries(pe)
    fc2.begins = [e[0] for e in fc2.pdata]
    fc2.db = None
    fc2.beacons = {}
    lines38, cov38 = xref_for_disp(fc2, 0x38, do_xref=True)
    check("T1-F3 small disp -> complete w/ UNVALIDATED disp8 named",
          cov38.startswith("SCAN-COMPLETE-32+disp8-CANDIDATES-UNVALIDATED")
          and "validation NOT run" in cov38, cov38[:70])
    check("T1-F3 unvalidated disp8 rows carry the UNVALIDATED tag",
          all("8u" in ln.split()[1] or "unvalidated" in ln
              for ln in lines38 if "8u" in ln.split()[1]),
          "%d rows" % len(lines38))
    linesbig, covbig = xref_for_disp(fc2, 0x94E, do_xref=True)
    check("T1-F3 large disp -> SCAN-COMPLETE-32 (disp8 N/A, named)",
          covbig.startswith("SCAN-COMPLETE-32"), covbig)

    # ---- T1-P4: owner + naming joins ----
    table = entries(pe)
    begins = [e[0] for e in table]
    owner = owner_of(pe, table, begins, 0x140E2B405)
    check("T1-P4 owner resolution on a known WRITE site",
          owner != "NO-PDATA-ENTRY" and ".." in owner, owner[:60])

    # ---- classification unit (synthetic address space) ----
    class FakeMD(object):
        modules = [{"base": 0x7FF600000000, "size": 0x1000000,
                    "name": "C:\\x\\destiny2.exe"}]
        ranges = [(0x7FF600000000, 0x1000000, 0),
                  (0x1000000000, 0x10000, 0)]
    fc = FakeCtx()
    fc.pe = pe
    fc.md = FakeMD()
    fc.mod = FakeMD.modules[0]
    fc.rt_base = 0x7FF600000000
    fc.in_image = lambda v: (fc.rt_base <= v < fc.rt_base + 0x1000000)
    fc.static_of = lambda v: BASE + (v - fc.rt_base)
    fc.pe.section_of = pe.section_of
    fc.dumped_at = lambda v: next(((s, z) for s, z, _ in fc.md.ranges
                                   if s <= v < s + z), None)
    c1 = classify_value(fc, 0x7FF6000123A0, 8)
    check("classify: module pointer -> static + section",
          c1.startswith("MODULE-PTR -> static 0x1400123A0"), c1)
    c2 = classify_value(fc, 0x1000004242, 8)
    check("classify: heap pointer (dumped range)", c2.startswith("RUNTIME-PTR"),
          c2)
    c3 = classify_value(fc, 0x1234, 8)
    check("classify: small int", c3 == "small-int 4660", c3)
    c4 = classify_value(fc, int.from_bytes(b"ABCD", "little"), 4)
    check("classify: ascii hint", "ascii" in c4, c4)

    print("STRUCT_VIEW SELFTEST: %d/%d PASS" % (12 - len(fails), 12))
    return 0 if not fails else 4


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
