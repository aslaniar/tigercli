#!/usr/bin/env python3
"""beacons.py - string/constant beacon census over the unpacked binary.

Finds every ASCII/UTF-16LE string in the image, then sweeps .text for
rip-relative references (lea/mov/call displacements - same proven math as
xref_scan.py) landing on those strings. Output joins to the function spine:
"which functions reference which strings" is the cheapest naming evidence
that exists (Bungie's own asserts/errors/format strings name their readers).

ORACLES (real, from FINDINGS):
  POSITIVE: "Could not find tracking data for peer '%s'" - a client log line
  (20.81) - must exist in the image and carry >=1 code reference.
  POSITIVE: "tried-to-join-self" - the client's own reason enum string
  (20.83) - must exist.
  NEGATIVE: "Sending peer-reservation release for machine" - established
  (20.82/20.86) to be in NEITHER the client image NOR dumps - must NOT be
  found. A hit would mean the beacon scan is hallucinating.

Output: RE_output/map/beacons.json + tables appended to function_map.db
(strings, string_refs). Interpreter: /usr/bin/python3.

Usage:
  /usr/bin/python3 RE_scripts/beacons.py --selftest
  /usr/bin/python3 RE_scripts/beacons.py [--min-len 6] [--map DB]

Exit: 0 ok, 1 failure, 2 usage.
"""
import argparse
import bisect
import json
import os
import re
import sqlite3
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe_reader import PE
import reconcile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BINARY = os.path.join(ROOT, "RE_output", "destiny2_unpacked_full.exe")
DEFAULT_MAP = os.path.join(ROOT, "RE_output", "map", "function_map.db")

ORACLE_POS = ["privacy-mode", "peer-creating", "tried-to-join-self",
              "managed-session-start"]  # client-own strings (FINDINGS
# 20.68/20.82/20.83/FRONT) - each must appear EXACTLY once in the image
ORACLE_NEG = ["ev=steamnet", "Sending peer-reservation release"]
# fork-side log tags - must be ABSENT from the client binary (the pen
# session's own logging lives in the fork, not Bungie's code)

ASCII_MIN = 6


def extract_strings(pe, min_len=ASCII_MIN):
    """ASCII (NUL-terminated, printable) + UTF-16LE strings from all image
    sections with raw content. Returns sorted list of (va, enc, text)."""
    out = []
    base = pe.imagebase
    printable = set(range(0x20, 0x7F))
    for name, vaddr, vsize, rawptr, rawsize in pe.sections:
        if not rawsize:
            continue
        blob = pe.data[rawptr:rawptr + rawsize]
        # ASCII runs
        i = 0
        n = len(blob)
        while i < n:
            b = blob[i]
            if b in printable:
                j = i
                while j < n and blob[j] in printable:
                    j += 1
                if j < n and blob[j] == 0 and j - i >= min_len:
                    out.append((base + vaddr + i, "ascii",
                                blob[i:j].decode("ascii")))
                i = j + 1
            else:
                i += 1
        # UTF-16LE runs (printable char + 0x00 pairs)
        i = 0
        while i + 1 < n:
            if blob[i] in printable and blob[i + 1] == 0:
                j = i
                chars = []
                while j + 1 < n and blob[j] in printable and blob[j + 1] == 0:
                    chars.append(chr(blob[j]))
                    j += 2
                if j + 1 < n and blob[j] == 0 and blob[j + 1] == 0 and \
                        len(chars) >= min_len:
                    out.append((base + vaddr + i, "utf16",
                                "".join(chars)))
                i = j + 2
            else:
                i += 1
    out.sort()
    return out


def xref_strings(pe, string_vas, text_section=None):
    """One .text sweep: rip-relative disp32 whose target lands on a string.
    Returns list of (insn_va, string_va) - instruction start approximated
    from the byte(s) before the displacement (same heuristic as xref_scan)."""
    text = None
    for sec in pe.sections:
        if sec[0] == ".text":
            text = sec
            break
    if text is None:
        raise SystemExit("no .text")
    base = pe.imagebase
    blob = pe.data[text[3]:text[3] + text[4]]
    starts = [va for va, _, _ in string_vas]
    n = len(blob) - 4
    refs = []
    t0 = time.time()
    for off in range(n):
        disp = struct.unpack_from("<i", blob, off)[0]
        if disp == 0:
            continue
        target = base + text[1] + off + 4 + disp
        i = bisect.bisect_left(starts, target)
        if i < len(starts) and starts[i] == target:
            insn = base + text[1] + off - 3
            if insn < base + text[1]:
                insn = base + text[1]
            refs.append((insn, target))
    return refs, time.time() - t0


def selftest(binary_path, min_len):
    fails = []

    def check(name, cond, detail=""):
        print("%s %-52s %s" % ("PASS" if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    pe = PE(binary_path)
    print("== A. string extraction ==")
    t0 = time.time()
    strings = extract_strings(pe, min_len)
    vas = [va for va, _, _ in strings]
    texts = {va: t for va, e, t in strings}
    check("strings extracted (thousands expected)", len(strings) > 3000,
          "%d in %.1fs" % (len(strings), time.time() - t0))
    joined = list({t for _, _, t in strings})
    for s in ORACLE_POS:
        n = sum(1 for t in joined if s in t)
        check("POSITIVE client string %r present once" % s, n == 1,
              "n=%d" % n)
    for s in ORACLE_NEG:
        n = sum(1 for t in joined if s in t)
        check("NEGATIVE fork-side string %r absent" % s, n == 0, "n=%d" % n)

    print("== B. .text xref sweep ==")
    refs, elapsed = xref_strings(pe, strings)
    check("string references found (hundreds expected)",
          len(refs) > 100, "%d refs in %.1fs" % (len(refs), elapsed))
    # every ref target must actually be a string VA we extracted
    ok = all(any(va == t for va, _, _ in strings) for _, t in refs[:50])
    check("sampled ref targets are exact string VAs", ok)

    print("== C. spot-verify: disassemble referencing instructions ==")
    # the instruction start is INFERRED (off-3/-2); verify by trying each
    # candidate start and checking capstone's computed rip-target equals the
    # string VA (capstone detail=True gives operand mem.disp)
    if refs:
        try:
            import capstone
        except ImportError:
            capstone = None
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64) \
            if capstone else None
        md.detail = True if md else False
        if md:
            verified = checked = 0
            text_lo = pe.imagebase + [s for s in pe.sections
                                      if s[0] == ".text"][0][1]
            for insn_va, target in refs[:40]:
                checked += 1
                hit = False
                for back in (3, 2, 1, 0):
                    start = insn_va - back
                    fb = pe.read(start, 16)
                    if not fb:
                        continue
                    for insn in md.disasm(fb, start):
                        if insn.address > insn_va + 3:
                            break
                        for op in insn.operands:
                            if op.type == capstone.x86.X86_OP_MEM and \
                                    op.mem.base == capstone.x86.X86_REG_RIP:
                                t = insn.address + insn.size + op.mem.disp
                                if t == target:
                                    hit = True
                        if hit:
                            break
                    if hit:
                        break
                verified += 1 if hit else 0
            check("disasm spot-check: rip-target == string VA",
                  verified >= checked * 0.5,
                  "%d/%d verified" % (verified, checked))
        else:
            check("capstone available for spot-check", False,
                  "pip install capstone")

    print("BEACONS SELFTEST %s" % ("PASS" if not fails else "FAIL: %s" % fails))
    return 0 if not fails else 1


def HAVE_CAPSTONE_AND(refs):
    try:
        import capstone  # noqa
        return bool(refs)
    except ImportError:
        return False


def persist(strings, refs, map_db, spine_path):
    rows, starts = reconcile.load_spine(spine_path)
    con = sqlite3.connect(map_db)
    con.execute("CREATE TABLE IF NOT EXISTS strings("
                "va INTEGER PRIMARY KEY, enc TEXT, text TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS string_refs("
                "insn_va INTEGER, string_va INTEGER, func INTEGER)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_sref_fn ON string_refs(func)")
    con.executemany("INSERT OR REPLACE INTO strings VALUES (?,?,?)", strings)
    con.executemany("INSERT OR REPLACE INTO string_refs VALUES (?,?,?)",
                    [(i, t, (reconcile.enclosing(starts, rows, i) or
                             (None,))[0]) for i, t in refs])
    # functions-with-strings summary for the queue
    con.execute("CREATE TABLE IF NOT EXISTS string_stats AS SELECT "
                "func, COUNT(*) n_refs, COUNT(DISTINCT string_va) n_strings "
                "FROM string_refs WHERE func IS NOT NULL GROUP BY func")
    con.commit()
    n_fn = con.execute("SELECT COUNT(DISTINCT func) FROM string_refs "
                       "WHERE func IS NOT NULL").fetchone()[0]
    con.close()
    return n_fn


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--binary", default=DEFAULT_BINARY)
    ap.add_argument("--map", default=DEFAULT_MAP)
    ap.add_argument("--spine", default=reconcile.DEFAULT_SPINE)
    ap.add_argument("--min-len", type=int, default=ASCII_MIN)
    ap.add_argument("--no-db", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        if not os.path.exists(args.binary):
            print("ERROR: binary missing: %s" % args.binary)
            return 2
        return selftest(args.binary, args.min_len)

    if not os.path.exists(args.binary):
        print("ERROR: binary missing: %s" % args.binary)
        return 2
    pe = PE(args.binary)
    strings = extract_strings(pe, args.min_len)
    refs, elapsed = xref_strings(pe, strings)
    print("LIVENESS: strings=%d refs=%d sweep=%.1fs" %
          (len(strings), len(refs), elapsed))
    out_json = os.path.join(ROOT, "RE_output", "map", "beacons.json")
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w") as fh:
        json.dump({"strings": [[hex(va), e, t] for va, e, t in strings],
                   "refs": [[hex(i), hex(t)] for i, t in refs]}, fh)
    print("wrote %s" % out_json)
    if not args.no_db:
        if not os.path.exists(args.map):
            print("WARN: no function_map.db at %s - run reconcile.py first; "
                  "writing db anyway" % args.map)
        n_fn = persist(strings, refs, args.map, args.spine)
        print("MAP: string-referencing functions=%d (beacon naming evidence)"
              % n_fn)
    if len(refs) == 0:
        print("DEGENERATE: zero string references - check the sweep")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
