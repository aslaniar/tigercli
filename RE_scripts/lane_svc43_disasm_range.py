#!/usr/bin/env python3
"""Linear disassembly of a VA range (no early stop). Usage: <va_start> <va_end>."""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from pe_reader import PE
import capstone

TAGS = {0x08: "f1 varint", 0x10: "f2 varint", 0x18: "f3 varint", 0x1A: "f3 LEN",
        0x22: "f4 LEN", 0x28: "f5 varint", 0x2A: "f5 LEN", 0x32: "f6 LEN",
        0x38: "f7 varint", 0x3A: "f7 LEN", 0x40: "f8 varint", 0x42: "f8 LEN",
        0x12: "f2 LEN", 0x0A: "f1 LEN"}

pe = PE("/Users/rubenaslanian/Documents/opencode/sunrise-fork/"
        "RE_output/destiny2_unpacked_full.exe")
start = int(sys.argv[1], 16)
end = int(sys.argv[2], 16)
code = pe.read(start, end - start)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
md.detail = True
for ins in md.disasm(code, start):
    note = ""
    for op in ins.operands:
        if op.type == capstone.x86.X86_OP_IMM and op.imm in TAGS:
            note = f"   <-- protobuf tag {op.imm:#04x} = {TAGS[op.imm]}"
    print(f"{ins.address:#012x}  {ins.mnemonic:<7} {ins.op_str}{note}")
