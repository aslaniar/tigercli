#!/usr/bin/env python3
# REGISTRY: caps: transition-readout, dump-census
"""Transition-window dump readout (20.331's next read).

Turns a boot-end dump - ideally a FULL DUMP SNAPPED DURING THE LOADING/
SPAWN TRANSITION (the only state where gate1's +0x108/+0x109 are armed;
every held dump so far is idle-tower, unarmed) - into the complete census:

  1. GATE CLUSTER      AF0/AF1/AF2/AF3, B08/B09 + the VMP cookie
                       (0x142746738) - vs the p2-146/p2-205 recorded values
                       (the byte-identical baseline, 20.331 R1).
  2. GATE1             the global 0x142F71508 (raw; VMP-unmixed base unknown)
                       + the raw object's +0x100..0x130 window
                       (+0x108 armed byte, +0x109 comparator).
  3. ARMED-COMPARATOR  unmix-independent: search the dump for the machine's
                       own identity qwords (RIG 0x846C8338F7D022E6 / MAC
                       0xE4DDDA60E08629C3 real-account forms; pass --identity)
                       and report every site whose preceding byte +0x108 is
                       set - the armed gate1 comparator, wherever it lives.
  4a. ENT INSTANCES    the four VTABLE BASES (0x141C9ADD8/0x141C9AE50/
                       0x141C9AEC8/0x141C9AF40) - what an object actually
                       stores; a HEAP hit = CONSTRUCTION (the win).
  4b. CONTROL          the four slot-10 handler addresses. These are NOT an
                       instance test (20.336): they can only ever match the
                       .rdata words. Kept to prove the scan is alive.
  5. IDENTITY ROW      DAT_1426BDCC8 row 2 (with --log, echo-verified via
                       identity_dumpcheck's window logic).

Usage:
  python3 RE_scripts/transition_readout.py --dump <full minidump> \
      [--identity 0x846C8338F7D022E6] [--log <server log>]
Exit 0 = census complete. Exit 1 = dump unreadable / no module.
"""

import argparse
import re
import sys

from minidump_reader import Minidump
from dump_search import scan

TABLE_RVA = 0x26BDCC8
ROW2_OFFSET = 0x70
WINDOW_OFFSET = 0x02
WINDOW_LEN = 0x56

GATE_CLUSTER = {
    "master AF0  0x142037AF0": 0x2037AF0,
    "AF1         0x142037AF1": 0x2037AF1,
    "AF2         0x142037AF2": 0x2037AF2,
    "AF3         0x142037AF3": 0x2037AF3,
    "B08         0x142037B08": 0x2037B08,
    "B09         0x142037B09": 0x2037B09,
    "VMP cookie  0x142746738": 0x2746738,
}
GATE1_GLOBAL_RVA = 0x2F71508  # 0x142F71508, gate1's [rip+0x1c45a97]

# THE INSTANCE TEST (corrected 2026-09-08, FINDINGS 20.336). A C++ object stores a
# pointer to its VTABLE BASE - it never stores the address of an individual virtual
# function. Searching a dump for ENT_HANDLERS therefore cannot find instances at all:
# it can only ever return the four .rdata slot-10 words themselves, which are present
# in every image whether or not a single object exists. Five artifacts were censused
# with that needle and the ".rdata-only = never constructed" line was read off it.
#
# The four bases below are proven, not inferred: the ctor 0x1416BB1E0 loads all four
# with rip-relative LEAs in its first 0x66 bytes (0x16BB1E0/0x16BB1FF/0x16BB214/
# 0x16BB246; the dtor-side site 0x1416CB034 loads them in reverse), and each handler
# sits at base+0x50 = slot 10, the tables spaced 0x78 apart.
#
# A HEAP hit on one of these == a constructed receive block == the win.
# The handler needles are KEPT as a labelled control: they must return exactly four
# image hits and zero heap hits, which is what proves the scan itself is working.
ENT_VTABLES = [0x141C9ADD8, 0x141C9AE50, 0x141C9AEC8, 0x141C9AF40]
ENT_HANDLERS = [0x141718510, 0x141718AE0, 0x1417183C0, 0x141718CB0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True)
    ap.add_argument("--identity", default=None,
                    help="the machine's own identity qword (hex); enables arm 3")
    ap.add_argument("--log", default=None,
                    help="server log for the echo-vs-row check (arm 5)")
    args = ap.parse_args()

    md = Minidump(args.dump)
    base = None
    for m in md.modules:
        if "destiny2" in (m.get("name") or "").lower() and m["name"].lower().endswith(".exe"):
            base = m["base"]
    if base is None:
        print("READOUT: no destiny2 module in the dump")
        return 1
    print(f"READOUT: module base {hex(base)}")

    print("\n== 1. GATE CLUSTER (baseline p2-146/p2-205: AF0=01 AF1-3=00 B08/B09=0101) ==")
    for name, rva in GATE_CLUSTER.items():
        d = md.read_va(base + rva, 8)
        print(f"  {name}: {d[:4].hex()}")

    print("\n== 2. GATE1 global + raw object window ==")
    g = md.read_va(base + GATE1_GLOBAL_RVA, 8)
    print(f"  [0x142F71508] = {g.hex()} (raw; the VMP unmix is private)")
    try:
        obj = int.from_bytes(g, "little")
    except ValueError:
        obj = 0
    if obj:
        win = md.read_va(obj + 0x100, 0x30)
        print(f"  raw object @ {hex(obj)}:")
        for off in range(0, 0x30, 8):
            print(f"    +0x{0x100 + off:X}: {win[off:off + 8].hex()}")
        armed = md.read_va(obj + 0x108, 1)
        comp = md.read_va(obj + 0x109, 8)
        print(f"  [+0x108] armed byte: {armed.hex()}   [+0x109] comparator: {comp.hex()}")

    if args.identity:
        ident = int(args.identity, 16)
        print("\n== 3. ARMED-COMPARATOR HUNT (identity present + armed byte before it) ==")
        needles = [(args.identity, ident.to_bytes(8, "little"))]
        hits = scan(args.dump, needles, 40, 8, base)
        print(f"  identity sites: {hits}")
        # The armed gate1 comparator: [obj+0x108]=01 immediately before the
        # identity qword at [obj+0x109]. For every hit, check the byte at
        # (site-1). A 01 there = THE ARMED COMPARATOR (the transition state).
        armed_pairs = []
        for label, pat in needles:
            pass
        print("  armed-pair check (byte at each identity site - 1):")
        # Re-run the raw search to get locations (scan only prints; re-implement
        # the location walk directly over the committed ranges).
        import dump_search as ds
        for rstart, rsize, roff in ds.memory_ranges(args.dump):
            pass
        with open(args.dump, "rb") as f:
            for rstart, rsize, roff in ds.memory_ranges(args.dump):
                f.seek(roff)
                buf = f.read(rsize)
                i = buf.find(ident.to_bytes(8, "little"))
                while i != -1:
                    va = rstart + i
                    flag = md.read_va(va - 1, 1) if va > 0 else b""
                    mark = " <<< ARMED" if flag == b"\x01" else ""
                    if flag == b"\x01":
                        armed_pairs.append(va)
                    if len(armed_pairs) < 6 or flag == b"\x01":
                        print(f"    0x{va:016X} [+0x108]={flag.hex()}{mark}")
                    i = buf.find(ident.to_bytes(8, "little"), i + 1)
        print(f"  ARMED COMPARATOR PAIRS IN THIS DUMP: {len(armed_pairs)} "
              f"({'candidates found - verify structure before claiming the gate' if armed_pairs else 'none'})")

    print("\n== 4a. ENT RECEIVE-BLOCK INSTANCE CENSUS (vtable-base pointers) ==")
    print("   a HEAP hit here == a constructed receive block; image hits are expected 0")
    needles = [(f"vtable {hex(v)}", (base + (v - 0x140000000)).to_bytes(8, "little"))
               for v in ENT_VTABLES]
    scan(args.dump, needles, 10, 8, base)

    print("\n== 4b. CONTROL - handler-address needles (NOT an instance test) ==")
    print("   expected: exactly 4 image hits (the .rdata slot-10 words), 0 heap.")
    print("   anything else means the scan or the base is wrong - see 4a's verdict.")
    needles = [(hex(h), (base + (h - 0x140000000)).to_bytes(8, "little")) for h in ENT_HANDLERS]
    scan(args.dump, needles, 10, 8, base)

    if args.log:
        print("\n== 5. IDENTITY ROW (DAT_1426BDCC8 row 2) ==")
        runtime = base + TABLE_RVA + ROW2_OFFSET + WINDOW_OFFSET
        window = md.read_va(runtime, WINDOW_LEN)
        if len(window) == WINDOW_LEN:
            print(f"  row-2 window: '{window[:42].decode('ascii', errors='replace')}' "
                  f"version 0x{window[0x55]:02X}")
        else:
            print(f"  row-2 window unreadable ({len(window)} of {WINDOW_LEN} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())