#!/usr/bin/env python3
# REGISTRY: caps: function-disasm, gap-refuse
"""Disassemble one function from the dumped image, following to a heuristic end.

Usage: disasm_fn.py <static_va> [max_insns]
Protobuf note: the client dispatches on TAG bytes, not field numbers.
tag = (field << 3) | wiretype, so field 3 length-delimited = 0x1A, field 5 = 0x2A,
field 7 = 0x3A, field 4 = 0x22, field 1 varint = 0x08.
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from pe_reader import PE
import capstone

TAGS = {0x08: "f1 varint", 0x10: "f2 varint", 0x18: "f3 varint", 0x1A: "f3 LEN",
        0x22: "f4 LEN", 0x28: "f5 varint", 0x2A: "f5 LEN", 0x32: "f6 LEN",
        0x38: "f7 varint", 0x3A: "f7 LEN", 0x40: "f8 varint", 0x42: "f8 LEN",
        0x12: "f2 LEN", 0x0A: "f1 LEN"}


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    va = int(argv[0], 16)
    limit = int(argv[1]) if len(argv) > 1 else 400
    pe = PE("/Users/rubenaslanian/Documents/opencode/sunrise-fork/"
            "RE_output/destiny2_unpacked_full.exe")
    bounds = pe.pdata_bounds(va)
    if bounds:
        end_va = bounds[1]
        print(f"; pdata bounds: {bounds[0]:#x} .. {end_va:#x} (exact)")
    else:
        # T3.4 (TOOLING_AUDIT): a .pdata GAP means there is no authoritative
        # function extent, and the heuristic fall-back used to print a
        # PLAUSIBLE FALSE STREAM from mid-instruction desync (the 20.291
        # trap - the two 0x1404DD470-class leaf getters). Refuse; hand off
        # to the linear disassembler, which decodes forward without a
        # function extent and says so.
        print(f"REFUSED: {va:#x} is in a .pdata GAP (no enclosing "
              "RUNTIME_FUNCTION) - heuristic disassembly here would invent a "
              "plausible false stream (the 20.291 trap).")
        print("  Use the LINEAR disassembler instead, and start from a "
              "known-good boundary:")
        print(f"    /usr/bin/python3 RE_scripts/lane_svc43_disasm_range.py "
              f"{va:#x} $(( {va:#x} + N ))   # N = bytes you can justify")
        print("  If you need this function's REAL extent, find its start by "
              "xref/callers and re-check pdata_bounds at THAT address.")
        return 1
    code = pe.read(va, limit * 16)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    n = 0
    for ins in md.disasm(code, va):
        note = ""
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_IMM and op.imm in TAGS:
                note = f"   <-- protobuf tag {op.imm:#04x} = {TAGS[op.imm]}"
        print(f"{ins.address:#012x}  {ins.mnemonic:<7} {ins.op_str}{note}")
        n += 1
        if end_va is not None and ins.address + ins.size >= end_va:
            print(f"; -- pdata end of function reached ({end_va:#x}) --")
            break
        if ins.mnemonic in ("ret", "jmp") and n > 8 and end_va is None:
            break
        if n >= limit:
            break


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
