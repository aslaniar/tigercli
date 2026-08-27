#!/usr/bin/env python3
"""Find rip-relative references from .text into an arbitrary VA range.

Generalises the proven byte-pattern pass in lane_svc43_xref_scan.py /
hashtable_xref_scan.py so a new lane does not have to fork it again.

    xref_scan.py <lo_va> <hi_va> [--context N]

ORACLE (per AGENTS.md "give every reader an oracle it can fail against"):
run with --self-test. The activity-message type-name table at .data 0x141f91ad0
is known to be consumed by the getter at 0x1404dc070 (census_types.py header,
Lane M 1a). The scan must find that pair or it is broken.

x86-64 rip-relative operands are encoded as a 4-byte signed displacement whose
base is the address of the NEXT instruction. This scans every offset in .text
for a displacement landing inside the range, then reports the instruction start
inferred from the common LEA/MOV encodings so the hit is usable as a function
address rather than merely a byte offset.
"""
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe_reader import PE

EXE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "RE_output", "destiny2_unpacked_full.exe")

# (name, bytes before the displacement) for the encodings that carry a
# rip-relative operand in this image. The displacement always sits last.
FORMS = [
    ("lea r64",     3),   # 48/4C 8D /r  mod=00 rm=101
    ("mov r64,[m]", 3),   # 48/4C 8B /r
    ("mov [m],r64", 3),   # 48/4C 89 /r
    ("mov r32,[m]", 2),   # 8B /r
    ("call [m]",    2),   # FF /15
]


def scan(lo, hi, exe=EXE):
    """@return list of (instruction_va, target_va, form_name)."""
    pe = PE(exe)
    text_base = None
    for name, vaddr, vsize, rawptr, rawsize in pe.sections:
        if name == ".text":
            text_base = pe.imagebase + vaddr
            blob = pe.data[rawptr:rawptr + rawsize]
            break
    if text_base is None:
        raise SystemExit(".text not found")

    hits = []
    end = len(blob) - 4
    for off in range(end):
        disp = struct.unpack_from("<i", blob, off)[0]
        if disp == 0:
            continue
        next_va = text_base + off + 4
        target = next_va + disp
        if not (lo <= target < hi):
            continue
        # Infer the instruction start from the byte before the displacement.
        form = "unknown"
        start = off
        prev = blob[max(0, off - 3):off]
        if len(prev) == 3 and prev[0] in (0x48, 0x4C):
            if prev[1] in (0x8D, 0x8B, 0x89):
                form = {0x8D: "lea r64", 0x8B: "mov r64,[m]", 0x89: "mov [m],r64"}[prev[1]]
                start = off - 3
        elif len(prev) >= 2 and prev[-2] == 0x8B:
            form = "mov r32,[m]"
            start = off - 2
        elif len(prev) >= 2 and prev[-2] == 0xFF and prev[-1] == 0x15:
            form = "call [m]"
            start = off - 2
        if form == "unknown":
            continue
        hits.append((text_base + start, target, form))
    return hits


def main():
    argv = sys.argv[1:]
    if argv and argv[0] == "--self-test":
        # The oracle: 0x141f91ad0 is read by the getter at 0x1404dc070.
        hits = scan(0x141F91AD0, 0x141F91AD8)
        near = [h for h in hits if 0x1404DC000 <= h[0] <= 0x1404DC200]
        print(f"oracle: refs to 0x141F91AD0 = {len(hits)}")
        for va, tgt, form in hits[:10]:
            print(f"   0x{va:X}  -> 0x{tgt:X}  [{form}]")
        print("ORACLE " + ("PASS" if near else "FAIL - expected a hit near 0x1404DC070"))
        return 0 if near else 1

    if len(argv) < 2:
        print(__doc__)
        return 2
    lo = int(argv[0], 0)
    hi = int(argv[1], 0)
    hits = scan(lo, hi)
    print(f"refs into 0x{lo:X}..0x{hi:X}: {len(hits)}")
    for va, tgt, form in hits:
        print(f"   0x{va:X}  -> 0x{tgt:X}  [{form}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
