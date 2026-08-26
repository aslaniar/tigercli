#!/usr/bin/env python3
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
    va = int(argv[0], 16)
    limit = int(argv[1]) if len(argv) > 1 else 400
    pe = PE("/Users/rubenaslanian/Documents/opencode/sunrise-fork/"
            "RE_output/destiny2_unpacked_full.exe")
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
        if ins.mnemonic in ("ret", "jmp") and n > 8:
            break
        if n >= limit:
            break


if __name__ == "__main__":
    main(sys.argv[1:])
