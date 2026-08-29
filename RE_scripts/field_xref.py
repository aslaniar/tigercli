#!/usr/bin/env python3
"""field_xref.py - find every .text access to a STRUCT FIELD displacement.

The gap this fills: xref_scan.py finds rip-relative references to a DATA RANGE,
and needle_scan.py searches a minidump for u32 values. Neither answers "who
touches [reg + 0xNNN]", which is the question every layout lane ends up asking
(member +181/+183 in 20.152, peer +0xD0 in ms-start-gate3, the transition
manager's +0x2c1 in 20.154). Three hand-rolled greps over ad-hoc disassembly
dumps motivated registering this instead of a fourth.

Method: x86-64 `[reg + disp32]` encodes the displacement as 4 little-endian
bytes inside the instruction, so every access to field +N contains those bytes.
Scan .text for them, then walk back over any SIB byte to the ModRM and the
opcode, and classify the access. Reports VA, classification and raw bytes.

False positives are expected and wanted: an immediate or an unrelated constant
can carry the same 4 bytes. The classification column is the filter - a hit with
opcode '??' is almost always noise. Never treat a bare hit count as an answer.

Usage:
  field_xref.py <hex-disp> [more...]        e.g. field_xref.py 0x2c1 0x350
  field_xref.py --selftest

Exit 1 = no hits for at least one displacement (a result, not silence).
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pe_reader import PE

EXE = Path(__file__).resolve().parent.parent / "RE_output" / "destiny2_unpacked_full.exe"

# opcode -> (mnemonic, access). Only the forms that actually reach a field.
OPCODES = {
    0x88: ("mov  r/m8, r8", "WRITE"),
    0x89: ("mov  r/m, r", "WRITE"),
    0xC6: ("mov  r/m8, imm8", "WRITE"),
    0xC7: ("mov  r/m, imm32", "WRITE"),
    0x8A: ("mov  r8, r/m8", "read"),
    0x8B: ("mov  r, r/m", "read"),
    0x38: ("cmp  r/m8, r8", "read"),
    0x3A: ("cmp  r8, r/m8", "read"),
    0x39: ("cmp  r/m, r", "read"),
    0x3B: ("cmp  r, r/m", "read"),
    0x80: ("grp1 r/m8, imm8", "read"),
    0x81: ("grp1 r/m, imm32", "read"),
    0x83: ("grp1 r/m, imm8", "read"),
    0x84: ("test r/m8, r8", "read"),
    0x85: ("test r/m, r", "read"),
    0xFE: ("inc/dec r/m8", "RMW"),
    0xFF: ("inc/dec/call r/m", "RMW"),
}


def classify(data, pos):
    """@param pos Offset of the disp32's first byte. @return (mnemonic, access, start)."""
    # ModRM sits 1 byte back, or 2 with a SIB (r/m == 100).
    for sib in (0, 1):
        modrm_at = pos - 1 - sib
        if modrm_at < 2:
            continue
        modrm = data[modrm_at]
        if modrm >> 6 != 0b10:            # mod=10 is the [reg+disp32] form
            continue
        if (modrm & 7 == 0b100) != bool(sib):
            continue
        op_at = modrm_at - 1
        op = data[op_at]
        if op == 0xB6 or op == 0xB7:      # movzx is 0F B6/B7
            if op_at >= 1 and data[op_at - 1] == 0x0F:
                return ("movzx r, r/m8", "read", op_at - 1)
            continue
        if op in OPCODES:
            m, a = OPCODES[op]
            return (m, a, op_at)
    return None


def scan(pe, disp):
    needle = struct.pack("<i", disp)
    hits = []
    for name, vaddr, vsize, rawptr, rawsize in pe.sections:
        if name != ".text":
            continue
        data = pe.data[rawptr:rawptr + rawsize]
        pos = 0
        while True:
            p = data.find(needle, pos)
            if p < 0:
                break
            pos = p + 1
            c = classify(data, p)
            if c is None:
                continue
            m, a, start = c
            va = pe.imagebase + vaddr + start
            hits.append((va, a, m, data[start:p + 8].hex()))
    return hits


def selftest():
    """Oracle: three accesses read directly out of the 20.152/20.154 disassembly.
    Each must be found AND classified correctly, or the walk-back is wrong."""
    pe = PE(str(EXE))
    cases = [
        (0x2c1, 0x140E23002, "read"),   # cmp byte [rdi+0x2c1], 2   (20.154 public gate)
        (0x350, 0x140E2B405, "WRITE"),  # mov byte [rsi+0x350], al  (20.154 token store)
        (0x53c, 0x140E289EF, "WRITE"),  # mov dword [rsi+0x53c], edi
    ]
    ok = True
    for disp, want_va, want_access in cases:
        hits = {va: acc for va, acc, _m, _b in scan(pe, disp)}
        got = hits.get(want_va)
        good = got == want_access
        ok = ok and good
        print(f"  {'PASS' if good else 'FAIL'} disp={disp:#x} va={want_va:#x} "
              f"expect={want_access} got={got}")
    # Negative: a displacement no field uses must not classify a store at those VAs.
    bogus = scan(pe, 0x7FFFFF)
    stores = [h for h in bogus if h[1] == "WRITE"]
    print(f"  {'PASS' if not stores else 'FAIL'} negative disp=0x7fffff -> "
          f"{len(stores)} classified writes (want 0)")
    ok = ok and not stores
    print("SELFTEST", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "--selftest":
        return selftest()
    pe = PE(str(EXE))
    empty = False
    for arg in argv:
        disp = int(arg, 16)
        hits = scan(pe, disp)
        writes = [h for h in hits if h[1] in ("WRITE", "RMW")]
        print(f"\n=== field +{disp:#x}: {len(hits)} classified access(es), "
              f"{len(writes)} write/RMW ===")
        for va, access, mnem, raw in sorted(hits):
            print(f"  {va:#012x}  {access:<5}  {mnem:<18} {raw}")
        if not hits:
            empty = True
    return 1 if empty else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
