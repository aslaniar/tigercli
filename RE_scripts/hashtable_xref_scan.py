#!/usr/bin/env python3
"""Scan .text for rip-relative LEA/MOV references into the hash->ptr table
found at .data 0x14206ED00..0x14206FCF0 (2026-08-25 session).

Adapted from lane_svc43_xref_scan.py's proven byte-pattern pass; MOV forms
added because a consumer may load rather than compute an address.
"""
import re
import struct
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from pe_reader import PE

EXE = ("/Users/rubenaslanian/Documents/opencode/sunrise-fork/"
       "RE_output/destiny2_unpacked_full.exe")

RANGES = [
    ("hashtable", 0x14206EC80, 0x14206FD40),
]


def main():
    pe = PE(EXE)
    text = None
    for name, vaddr, vsize, rawptr, rawsize in pe.sections:
        if name == ".text":
            text_base = pe.imagebase + vaddr
            text = pe.data[rawptr:rawptr + rawsize]
            break
    assert text is not None, "no .text"
    print(f".text @ {text_base:#x}, {len(text):#x} bytes")

    hits = []
    # lea r64,[rip+d32]
    for m in re.finditer(rb"[\x48-\x4f]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]",
                         text, re.S):
        p = m.start()
        disp = struct.unpack_from("<i", text, p + 3)[0]
        tgt = text_base + p + 7 + disp
        for label, lo, hi in RANGES:
            if lo <= tgt < hi:
                hits.append((text_base + p, "lea64", tgt))
                break
    # mov r64,[rip+d32] / mov r32,[rip+d32]
    for m in re.finditer(rb"[\x48-\x4f]\x8b[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]",
                         text, re.S):
        p = m.start()
        disp = struct.unpack_from("<i", text, p + 3)[0]
        tgt = text_base + p + 7 + disp
        for label, lo, hi in RANGES:
            if lo <= tgt < hi:
                hits.append((text_base + p, "mov64", tgt))
                break

    hits.sort()
    print(f"{len(hits)} hits")
    for va, kind, tgt in hits[:60]:
        print(f"  {va:#x} {kind} -> {tgt:#x}")


if __name__ == "__main__":
    main()
