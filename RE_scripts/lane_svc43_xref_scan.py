#!/usr/bin/env python3
"""Scan .text for rip-relative LEA references into given VA ranges.

Lane svc43-field3 phase 4: find code that consumes the field-schema tables
(0x141C38000-0x141C3B400), the decoder registry (0x141FBF000-0x141FC0000),
and the descriptor objects (0x141C2E700-0x141C2E800).

Forms scanned: REX.W-ish (0x48-0x4F) 8D /r with mod=00 rm=101 -> lea r64,[rip+d32];
plain 8D /r same modrm -> lea r32,[rip+d32].
"""
import re
import struct
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from pe_reader import PE

EXE = ("/Users/rubenaslanian/Documents/opencode/sunrise-fork/"
       "RE_output/destiny2_unpacked_full.exe")

RANGES = [
    ("schema", 0x141C38000, 0x141C3B400),
    ("registry", 0x141FBF000, 0x141FC0000),
    ("descriptor", 0x141C2E700, 0x141C2E800),
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
    # REX-prefixed lea r64, [rip+disp32]: 3-byte opcode+modrm, then d32
    rex = re.compile(rb"[\x48-\x4f]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]",
                     re.S)
    for m in rex.finditer(text):
        p = m.start()
        insn_start_va = text_base + p
        next_va = insn_start_va + 7
        disp = struct.unpack_from("<i", text, p + 3)[0]
        tgt = next_va + disp
        for label, lo, hi in RANGES:
            if lo <= tgt < hi:
                hits.append((insn_start_va, "lea64", tgt, label))
                break
    # plain lea r32, [rip+disp32]
    plain = re.compile(rb"\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]", re.S)
    for m in plain.finditer(text):
        p = m.start()
        if p > 0 and 0x40 <= text[p - 1] <= 0x4f:
            continue  # already covered by REX pass
        insn_start_va = text_base + p
        next_va = insn_start_va + 6
        disp = struct.unpack_from("<i", text, p + 2)[0]
        tgt = next_va + disp
        for label, lo, hi in RANGES:
            if lo <= tgt < hi:
                hits.append((insn_start_va, "lea32", tgt, label))
                break

    hits.sort()
    print(f"{len(hits)} hits")
    for va, kind, tgt, label in hits:
        print(f"  {va:#x} {kind} -> {tgt:#x} ({label})")


if __name__ == "__main__":
    main()
