#!/usr/bin/env python3
# REGISTRY: caps: e8-callers, callgraph-enum
"""callers.py - enumerate the DIRECT callers of one or more target functions.

The gap this fills: every caller-climb lane (20.271 R2, 20.273 R1) re-rolled an
ad-hoc E8 scan. Registered so the next lane stops forking it.

Method: x86-64 CALL rel32 (E8) and JMP rel32 (E9) encode the target as a
signed 4-byte displacement from the END of the instruction. Scan both .text
sections for every E8/E9 whose computed target lands on a requested VA, and
resolve each site to its OWNING function via .pdata (fragment chains followed
per pdata_bounds.py). Report site VA, kind (call/jmp), and owner.

ANSWERS "who calls X directly". KNOWN BLIND SPOTS (same class as
field_xref's --sib-scan note - check before concluding "no callers"):
  - indirect calls: call [reg] / call [rip+..] / vtable / function-pointer
    dispatch (runtime-registered tables are invisible to ANY static scan)
  - obfuscated/VMP regions (the keyed family)
  - sites reachable only by falling through a fragment boundary
A "no direct callers" result is a STATEMENT ABOUT ENCODINGS, not about the
world - pair it with an indirect check (xref_scan --ptrs over .data/.rdata
for the target's address as a pointer) before promoting it to a finding.

Usage:
  callers.py <va> [more...]            e.g. callers.py 0x1417692E0
  callers.py --selftest

Exit 1 = no hits for at least one target (a result, not silence).
"""
import bisect
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pe_reader import PE
from pdata_bounds import entries

EXE = Path(__file__).resolve().parent.parent / "RE_output" / "destiny2_unpacked_full.exe"
BASE = 0x140000000


def owner_of(pe, table, begins, site):
    """@return human-readable owner description for a site VA (follows fragment
    chains exactly as pdata_bounds.py's main does)."""
    rva = site - BASE
    index = bisect.bisect_right(begins, rva) - 1
    if index < 0:
        return "NO-PDATA-ENTRY"
    begin, end, unwind = table[index]
    hops, cur = 0, (begin, end, unwind)
    while hops < 8:
        info = pe.read(BASE + cur[2], 4)
        flags = (info[0] >> 3) & 0x1F
        if not flags & 0x4:
            break
        count = info[2]
        codes = count + (count & 1)
        parent = pe.read(BASE + cur[2] + 4 + codes * 2, 12)
        pb = int.from_bytes(parent[0:4], "little")
        pe_ = int.from_bytes(parent[4:8], "little")
        pu = int.from_bytes(parent[8:12], "little")
        if pb == 0 or pb == cur[0]:
            break
        cur = (pb, pe_, pu)
        hops += 1
    desc = f"0x{BASE + cur[0]:X}..0x{BASE + cur[1]:X} (size={cur[1] - cur[0]}"
    if hops:
        desc += f", fragment after {hops} hop(s)"
    return desc + ")"


def scan_callers(pe, targets):
    """@return {target_va: [(site_va, kind, owner_desc), ...]} sorted by site."""
    table = entries(pe)
    begins = [e[0] for e in table]
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
            rel = struct.unpack_from("<i", blob, i + 1)[0]
            site = BASE + vaddr + i
            target = site + 5 + rel
            if target in hits:
                kind = "call" if op == 0xE8 else "jmp "
                hits[target].append((site, kind, owner_of(pe, table, begins, site)))
    return hits


def selftest(pe):
    """Oracle: 0x141769230..2D4 is documented (FINDINGS 20.271 R2) to call the
    reserve core 0x1417692E0. The scan must find that edge, classify it as a
    call, and attribute it to the right owner. Also: a control target with no
    expected callers must report zero (exit-path liveness)."""
    ok = True
    target = 0x1417692E0
    hits = scan_callers(pe, [target])[target]
    sites = [h for h in hits if 0x141769230 <= h[0] < 0x1417692D4]
    if not sites:
        print("selftest FAIL: no E8 hit into 0x1417692E0 from 0x141769230..2D4")
        return False
    for site, kind, owner in sites:
        print(f"selftest edge: site {site:#x} {kind} owner {owner}")
        if kind != "call":
            print("selftest FAIL: expected kind 'call'")
            ok = False
        if "0x141769230" not in owner:
            print(f"selftest FAIL: owner should start at 0x141769230, got {owner}")
            ok = False
    print("selftest PASS" if ok else "selftest FAIL")
    return ok


def main(argv):
    if "--selftest" in argv:
        return 0 if selftest(PE(EXE)) else 1
    targets = [int(a, 16) for a in argv]
    if not targets:
        print(__doc__)
        return 2
    pe = PE(EXE)
    hits = scan_callers(pe, targets)
    rc = 0
    for t in targets:
        rows = sorted(hits[t])
        print(f"=== target {t:#x}: {len(rows)} direct E8/E9 site(s) ===")
        if not rows:
            rc = 1
        for site, kind, owner in rows:
            print(f"  {site:#x}  {kind}  owner {owner}")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
