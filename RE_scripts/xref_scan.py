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
# 2026-08-31: this table is best-effort ANNOTATION only - it is no longer a
# filter. The old `if form == "unknown": continue` dropped every rip-relative
# ref whose encoding was not one of 7 recognized shapes (REX 0x48/0x4C only,
# 5 opcodes), which produced false "0 refs" verdicts - the most dangerous
# output a xref tool can give. Unknown-form hits are now KEPT and marked.
FORMS = [
    ("lea r64",     3),   # 48/4C 8D /r  mod=00 rm=101
    ("mov r64,[m]", 3),   # 48/4C 8B /r
    ("mov [m],r64", 3),   # 48/4C 89 /r
    ("mov r32,[m]", 2),   # 8B /r
    ("call [m]",    2),   # FF /15
]

REX_OPS = {0x8D: "lea r64", 0x8B: "mov r64,[m]", 0x89: "mov [m],r64",
           0x88: "mov [m],r8", 0x8A: "mov r8,[m]",
           0x39: "cmp [m],r", 0x3B: "cmp r,[m]", 0x3A: "cmp r8,[m8]",
           0x85: "test [m],r", 0x83: "grp1 [m],imm8", 0x81: "grp1 [m],imm32",
           0xC7: "mov [m],imm32"}


def classify_form(blob, off):
    """Best-effort instruction-start + form inference at a disp32 hit."""
    prev = blob[max(0, off - 3):off]
    if len(prev) == 3 and 0x40 <= prev[0] <= 0x4F:
        if prev[1] in REX_OPS:
            return (REX_OPS[prev[1]], off - 3)
    elif len(prev) >= 2 and 0x40 <= prev[-2] <= 0x4F:
        if prev[-1] in REX_OPS:
            return (REX_OPS[prev[-1]], off - 2)
    if len(prev) >= 2:
        if prev[-2] == 0xFF and prev[-1] == 0x15:
            return ("call [m]", off - 2)
        if prev[-2] == 0xFF and prev[-1] == 0x25:
            return ("jmp [m]", off - 2)
        if prev[-2] == 0x0F and prev[-1] in (0xB6, 0xB7, 0xBE, 0xBF):
            return ("movzx/movsx", off - 2)
        if prev[-1] == 0x8B:
            return ("mov r32,[m]", off - 2)
    if len(prev) >= 1:
        if prev[-1] == 0xE8:
            return ("call rel32", off - 1)
        if prev[-1] == 0xE9:
            return ("jmp rel32", off - 1)
    return ("unknown", off)


def text_sections(pe):
    """ALL .text sections - this unpacked binary has TWO (the unpacker
    appended an 81MB second .text; v1 scanned only the first)."""
    return [(pe.imagebase + vaddr, pe.data[rawptr:rawptr + rawsize])
            for name, vaddr, vsize, rawptr, rawsize in pe.sections
            if name == ".text"]


def scan(lo, hi, exe=EXE):
    """@return list of (instruction_va, target_va, form_name).
    Every rip-relative disp32 landing in [lo,hi) is a hit; the form is
    annotation. Data-pointer references (vtables/callback tables) need
    --ptrs (separate mode) - a rip-relative sweep cannot see them."""
    pe = PE(exe)
    hits = []
    for text_base, blob in text_sections(pe):
        end = len(blob) - 4
        for off in range(end):
            disp = struct.unpack_from("<i", blob, off)[0]
            if disp == 0:
                continue
            target = text_base + off + 4 + disp
            if not (lo <= target < hi):
                continue
            form, start = classify_form(blob, off)
            hits.append((text_base + start, target, form))
    return hits


def scan_ptrs(lo, hi, exe=EXE):
    """Data-pointer mode: absolute 8-byte references to [lo,hi) in the
    writable/readonly data sections (vtables, callback tables, dispatch
    entries). Returns (slot_va, section, value)."""
    pe = PE(exe)
    hits = []
    for name, vaddr, vsize, rawptr, rawsize in pe.sections:
        if not name.startswith((".data", ".rdata")):
            continue
        blob = pe.data[rawptr:rawptr + rawsize]
        for off in range(0, len(blob) - 7):
            val = struct.unpack_from("<Q", blob, off)[0]
            if lo <= val < hi:
                hits.append((pe.imagebase + vaddr + off, name, val))
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

    ptrs = "--ptrs" in argv
    if ptrs:
        argv.remove("--ptrs")
    if len(argv) < 2:
        print(__doc__)
        return 2
    lo = int(argv[0], 0)
    hi = int(argv[1], 0)
    if ptrs:
        hits = scan_ptrs(lo, hi)
        print(f"data-pointer refs with value in 0x{lo:X}..0x{hi:X}: {len(hits)}")
        for va, sec, val in hits[:40]:
            print(f"   0x{va:X}  [{sec}]  = 0x{val:X}")
        if not hits:
            print("NOTE: 0 data-pointer hits. Remaining known blind spots: "
                  "absolute moffs64 embedded in .text code.")
        return 0
    hits = scan(lo, hi)
    unknown = sum(1 for _, _, f in hits if f == "unknown")
    print(f"refs into 0x{lo:X}..0x{hi:X}: {len(hits)} "
          f"({unknown} unknown-form - kept, judge by context)")
    for va, tgt, form in hits:
        print(f"   0x{va:X}  -> 0x{tgt:X}  [{form}]")
    if not hits:
        print("NOTE: 0 rip-relative hits. Before concluding 'nothing "
              "references this': run --ptrs for data-pointer/vtable refs; "
              "absolute moffs64 in .text remains a known blind spot.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
