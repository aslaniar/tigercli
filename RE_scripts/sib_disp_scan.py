#!/usr/bin/env python3
"""SIB+disp32 field scanner - the coverage gap field_xref misses.

field_xref.py classifies [reg+disp32] (mod=10, rm!=100) and --sib-scan covers
mod=00 SIB (no disp). The mod=10+SIB+disp32 form ([base+index*scale+disp32])
is scanned by NEITHER - and FINDINGS 20.287's birth-word OR
(`or word [rdx+rsi+0x3112]`) is exactly that form, found only by reading.

This scans both .text sections for disp32 occurrences preceded by a plausible
SIB+modrm pair and classifies by the preceding opcode byte(s). Crude but
sound: it enumerates CANDIDATES, each needing an eyeball - the output is a
work list, not a verdict.

Usage: sib_disp_scan.py [disp ...]   (defaults: the masks + mask words)
"""
import struct
import sys

sys.path.insert(0, "RE_scripts")
from pe_reader import PE

BINARY = "RE_output/destiny2_unpacked_full.exe"

# opcode bytes that plausibly read/write r/m32/r/m16 with a modrm (1-byte
# opcodes only; 0F xx two-byte forms need the byte at i-4 checked separately)
R_M_OPS = {
    0x88: "mov r/m8,r8", 0x89: "mov r/m,r", 0x8A: "mov r,r/m",
    0x8B: "mov r,r/m", 0x83: "grp1 r/m,imm8", 0x81: "grp1 r/m,imm32",
    0x80: "grp1 r/m8,imm8", 0x8D: "lea",
    0xC7: "mov r/m,imm32", 0xC6: "mov r/m8,imm8",
    0x03: "add r,r/m", 0x2B: "sub r,r/m", 0x0B: "or r,r/m",
    0x33: "xor r,r/m", 0x39: "cmp r/m,r", 0x3B: "cmp r,r/m",
    0x85: "test r/m,r", 0xF7: "grp3 r/m", 0xFF: "grp5 r/m",
    0x63: "movsxd", 0x0F: "0F-escape (two-byte op)",
}


def main():
    targets = [int(x, 0) for x in sys.argv[1:]] or [
        0x59248, 0x5924C, 0x59250, 0x3112, 0x3114, 0x850, 0x31BA]
    pe = PE(BINARY)
    data = pe.data
    for disp in targets:
        needle = struct.pack("<I", disp)
        print("=== disp 0x%X ===" % disp)
        total = 0
        for name, vaddr, vsize, rawptr, rawsize in pe.sections:
            if not name.startswith(".text"):
                continue
            lo, hi = rawptr, rawptr + rawsize
            pos = lo
            while True:
                i = data.find(needle, pos, hi)
                if i < 0:
                    break
                pos = i + 1
                va = pe.imagebase + vaddr + (i - rawptr)
                # candidate A: modrm(mod=10)+sib+disp32  -> modrm@i-2, sib@i-1
                if i >= 3:
                    modrm = data[i - 2]
                    sib = data[i - 1]
                    if (modrm & 0xC0) == 0x80 and (sib & 0x07) == 0x04:
                        op = data[i - 3]
                        total += 1
                        print("  %s va=%s op=%s(%02x) modrm=%02x sib=%02x "
                              "b=%d ix=%d sc=%d"
                              % (name, hex(va),
                                 R_M_OPS.get(op, "?"), op, modrm, sib,
                                 sib & 7, (sib >> 3) & 7, sib >> 6))
                        continue
                    # candidate B: modrm(mod=10, rm!=SIB)+disp32 - field_xref
                    # territory; skip unless it looks like our form
                    if (modrm & 0xC0) == 0x80 and (modrm & 0x07) != 0x04:
                        # check for 0F two-byte escape at i-3
                        if data[i - 3] == 0x0F:
                            op2 = data[i - 2 - 1]
                            total += 1
                            print("  %s va=%s 0F%02x modrm=%02x (sib?no) "
                                  "CANDIDATE" % (name, hex(va), data[i - 2],
                                                 modrm))
            if total == 0:
                print("  (0 candidates)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
