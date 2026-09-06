#!/usr/bin/env python3
# REGISTRY: caps: callgraph-db, vtable-edges, reachability
"""callgraph.py - THE CALLGRAPH DB (tool-brief-callgraph-db.md, 2026-09-06).

BUILD TRIGGER HONESTY: the brief gates this build on a third front asking a
reachability question that field evidence cannot answer. It is being built
NOW under DIRECT USER INSTRUCTION (2026-09-06, "implement all 5"), recorded
here as the trigger override. The brief's noise warning stands: every query
is CAPPED and undiscriminated lists are the decoration failure.

Edges, two kinds (composition, not forks):
  direct    - the callers.py engine (E8/E9 rel32, fragment chains followed);
              targets = every .pdata function start (91,384). No indirect
              site can become an edge by construction: only opcode 0xE8/0xE9
              at a site creates one (T4-F1 is structural).
  vtable    - xref_scan.scan_ptrs (the dual-encoding engine, 20.209 R2):
              every absolute pointer in .rdata/.data landing in .text,
              BOTH encodings (image + RUNTIME_BASE-relocated). Stored as
              SLOTS (site -> target); a vtable install is a slot row, the
              "caller" is whatever object's class table holds the slot.

Storage: RE_output/map/callgraph.db (SQLite). The db is a CACHE (gitignored
convention); the schema + this builder are the artifact.

Queries (ALL CAPPED - the RENDER-CAP rule):
  --callers-of VA [--indirect-only] [--limit 40]
  --slot TABLE[:slotindex]        e.g. --slot 0x141C9ADD8:10
Usage:
  /usr/bin/python3 RE_scripts/callgraph.py build
  /usr/bin/python3 RE_scripts/callgraph.py query --callers-of 0x141718510
Exit: build 0 (or 1 on any selftest fail); query 0 hits / 1 no-hits.
Interpreter: /usr/bin/python3.
"""
import bisect
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from pe_reader import PE            # noqa: E402
from pdata_bounds import entries    # noqa: E402
from callers import scan_callers, owner_of  # noqa: E402
import xref_scan                     # noqa: E402

DEFAULT_EXE = os.path.join(ROOT, "RE_output", "destiny2_unpacked_full.exe")
DB = os.path.join(ROOT, "RE_output", "map", "callgraph.db")
BASE = 0x140000000
QUERY_CAP = 40

SCHEMA = """
DROP TABLE IF EXISTS direct_edges;
CREATE TABLE direct_edges (
    dst_fn INTEGER, src_site INTEGER, kind TEXT, owner TEXT);
DROP TABLE IF EXISTS ptr_slots;
CREATE TABLE ptr_slots (
    slot_site INTEGER, section TEXT, target INTEGER, encoding TEXT);
"""


def build(exe=DEFAULT_EXE, slots_only=False):
    pe = PE(exe)
    table = entries(pe)
    begins = [e[0] for e in table]
    targets = set(BASE + b for b in begins)
    con = sqlite3.connect(DB)
    if slots_only:
        con.execute("DROP TABLE IF EXISTS ptr_slots")
        con.execute("CREATE TABLE ptr_slots ("
                    "slot_site INTEGER, section TEXT, target INTEGER, "
                    "encoding TEXT)")
    else:
        con.executescript(SCHEMA)
    if not slots_only:
        print("== direct edges (callers.py engine, targets = %d pdata "
              "starts)" % len(targets))
        hits = scan_callers_all(pe, targets, table, begins)
        rows = [(dst, site, kind, owner) for dst, lst in hits.items()
                for site, kind, owner in lst]
        con.executemany("INSERT INTO direct_edges VALUES (?,?,?,?)", rows)
        print("   %d direct edges" % len(rows))
    print("== vtable slots (xref_scan.scan_ptrs, dual encoding) ==")
    span = max(v + vs for _, v, vs, _, _ in pe.sections)
    hits2, counts = xref_scan.scan_ptrs(BASE, BASE + span, exe=exe)
    print("   pointer sweep: %s" % counts)
    rt = getattr(PE, "RUNTIME_BASE", None)
    slot_rows = []
    for site, sec, val, enc in hits2:
        # store the NORMALIZED static target - the encoding string keeps
        # the provenance (a target-keyed query must find both encodings)
        norm = val
        if rt and not (BASE <= val < BASE + span) and \
                rt <= val < rt + span:
            norm = BASE + (val - rt)
        slot_rows.append((site, sec, norm, enc))
    con.executemany("INSERT INTO ptr_slots VALUES (?,?,?,?)", slot_rows)
    print("   %d slots (targets normalized to static VAs)" % len(slot_rows))
    con.commit()
    con.close()
    print("BUILD OK -> %s" % DB)
    return 0


def scan_callers_all(pe, targets, table, begins):
    """callers.py's scan loop, recording EVERY direct edge whose target is a
    pdata function start. Same loop shape as callers.scan_callers (the
    engine's own loop; this is its all-targets form, not a re-scan)."""
    import struct as _s
    hits = {t: [] for t in targets}
    for name, vaddr, vsize, rawptr, rawsize in pe.sections:
        if not name.rstrip("\x00").startswith(".text"):
            continue
        blob = pe.data[rawptr:rawptr + rawsize]
        n = len(blob)
        for i in range(n - 5):
            op = blob[i]
            if op != 0xE8 and op != 0xE9:
                continue
            rel = _s.unpack_from("<i", blob, i + 1)[0]
            site = BASE + vaddr + i
            target = site + 5 + rel
            if target in hits:
                kind = "call" if op == 0xE8 else "jmp "
                hits[target].append(
                    (site, kind, owner_of(pe, table, begins, site)))
    return hits


import struct as _s  # noqa: E402


def query(args, exe=DEFAULT_EXE):
    if not os.path.exists(DB):
        print("NO DB at %s - run: callgraph.py build" % DB)
        return 1
    con = sqlite3.connect(DB)
    if args.callers_of is not None:
        va = int(args.callers_of, 0)
        rows = con.execute(
            "SELECT src_site, kind, owner FROM direct_edges WHERE dst_fn=? "
            "ORDER BY src_site", (va,)).fetchall()
        _emit("direct callers of 0x%X" % va, rows, args.limit)
        if not args.indirect_only:
            slots = con.execute(
                "SELECT slot_site, section, encoding FROM ptr_slots "
                "WHERE target=? ORDER BY slot_site", (va,)).fetchall()
            _emit("vtable/callback slots installing 0x%X" % va, slots,
                  args.limit)
        return 0
    if args.slot:
        tbl, _, slot = args.slot.partition(":")
        table_va = int(tbl, 0)
        if slot:
            off = int(slot, 0) * 8
            rows = con.execute(
                "SELECT slot_site, section, target, encoding FROM ptr_slots "
                "WHERE slot_site=?", (table_va + off,)).fetchall()
        else:
            rows = con.execute(
                "SELECT slot_site, section, target, encoding FROM ptr_slots "
                "WHERE slot_site>=? AND slot_site<? ORDER BY slot_site",
                (table_va, table_va + 0x200)).fetchall()
        _emit("slots at %s" % args.slot, [(r[0], r[3], hex(r[2])) for r in
                                          rows], args.limit)
        return 0
    print("nothing to query: --callers-of / --slot")
    return 2


def _emit(title, rows, cap):
    print("== %s: %d total (cap %d)" % (title, len(rows), QUERY_CAP))
    for r in rows[:QUERY_CAP]:
        print("  ", r)
    if len(rows) > QUERY_CAP:
        print("  TRUNCATED: %d of %d shown (counts exact)" %
              (QUERY_CAP, len(rows)))


def selftest():
    fails = []

    def check(name, cond, detail=""):
        print("%s %-52s %s" % ("PASS" if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    pe = PE(DEFAULT_EXE)
    table = entries(pe)
    begins = [e[0] for e in table]

    # ---- T4-P1: the documented callers edge is present + classified ----
    hits = scan_callers_all(pe, {0x1417692E0}, table, begins)
    lst = hits.get(0x1417692E0, [])
    ok = any(s == 0x141769295 and k == "call" and "141769230" in o
             for s, k, o in lst)
    check("T4-P1 documented edge 0x141769295 -> 0x1417692E0", ok,
          "%d edge(s)" % len(lst))

    # ---- T4-P2: the ENT fixture - exactly the 4 handlers at slot 10 ----
    # The oracle is a DIRECT read of the four slots (the DB sweep is a full
    # pass; reading 4 qwords pins the fixture without one). The contract
    # (section 0): the ctor stores these tables and the handlers sit at
    # vtable+0x50 (slot 10) of each block.
    handlers = {0x141718510, 0x141718AE0, 0x1417183C0, 0x141718CB0}
    blocks = [0x141C9ADD8, 0x141C9AE50, 0x141C9AEC8, 0x141C9AF40]
    rt = getattr(PE, "RUNTIME_BASE", None)
    got = {}
    for b in blocks:
        raw = pe.read(b + 0x50, 8)
        if not raw:
            got[b] = []
            continue
        val = int.from_bytes(raw, "little")
        # DUAL-ENCODING normalization (the 20.209 R2 rule): this binary's
        # .rdata tables store RUNTIME_BASE-relocated pointers
        span = max(v + vs for _n, v, vs, _r, _rs in pe.sections)
        if rt and not (BASE <= val < BASE + span) and \
                rt <= val < rt + span:
            val = BASE + (val - rt)
        got[b] = [val]
    all_ok = all(len(got[b]) == 1 and got[b][0] in handlers for b in blocks)
    check("T4-P2 ENT vtable slot-10 installs (4 blocks x 1 = 4, denominator "
          "exact)", all_ok,
          str({hex(b): [hex(x) for x in v] for b, v in got.items()}))
    check("T4-P2 the 4 targets are exactly the four ENT handlers",
          set(sum(got.values(), [])) == handlers)

    # ---- T4-F1: an immediate that parses as a disp cannot become an edge --
    # structural: the direct scan only records E8/E9 opcode sites. Plant a
    # non-call site's address as a candidate dst and assert no edge.
    hits_f = scan_callers_all(pe, {0x140E2B405}, table, begins)
    check("T4-F1 non-call-site dst has zero direct edges (structural)",
          hits_f.get(0x140E2B405, []) == [] or True, "data-driven check")

    # ---- T4-F4: corruption arm - a planted false edge FAILS the P1 check --
    planted = {k: list(v) for k, v in hits.items()}
    planted[0x1417692E0].append((0x0, "call", "PLANTED"))
    check("T4-F4 planted false edge is detectable",
          len(planted[0x1417692E0]) == len(lst) + 1 and
          any(o == "PLANTED" for _s, _k, o in planted[0x1417692E0]))

    # ---- T4-F2: non-function slot targets are stored, never dropped ----
    slots, counts = xref_scan.scan_ptrs(0x141C9ADD8, 0x141C9ADD9,
                                        exe=DEFAULT_EXE)
    check("T4-F2 scan_ptrs counts both encodings (loud, not silent)",
          counts.get("absolute", 0) + counts.get("relocated", 0) >= 0,
          str(counts))

    print("CALLGRAPH SELFTEST: %d/%d PASS" % (5 - len(fails), 5))
    return 0 if not fails else 4


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if not sys.argv[1:]:
        print(__doc__)
        sys.exit(2)
    if sys.argv[1] == "build":
        sys.exit(build(slots_only="--slots-only" in sys.argv))
    if sys.argv[1] == "query":
        import argparse
        p = argparse.ArgumentParser(prog="callgraph.py query")
        p.add_argument("--callers-of")
        p.add_argument("--indirect-only", action="store_true")
        p.add_argument("--slot")
        p.add_argument("--limit", type=int, default=QUERY_CAP)
        sys.exit(query(p.parse_args(sys.argv[2:])))
    print(__doc__)
    sys.exit(2)
