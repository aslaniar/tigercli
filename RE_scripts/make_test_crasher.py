#!/usr/bin/env python3
# REGISTRY: caps: test-crasher, aedebug-oracle
"""Generate a minimal 64-bit PE that faults deterministically (div by zero).

Purpose: the AeDebug crash-forensics oracle. Wine's unhandled-exception path
(raise -> unhandled -> AeDebug\Debugger) is only provable with a process that
ACTUALLY faults; this PE is that process. No imports, no sections but .code,
entry = xor ecx,ecx / div ecx / ret. Nothing to do with the game.

Usage: python3 make_test_crasher.py <out.exe>
"""
import struct
import sys


def build():
    e_lfanew = 0x80
    file_align = 0x200
    sect_align = 0x1000
    base = 0x140000000

    dos = bytearray(b"\x00" * e_lfanew)
    dos[0:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, e_lfanew)

    coff = struct.pack(
        "<HHIIIHH",
        0x8664,      # machine x64
        1,           # sections
        0,           # timestamp
        0,           # symbol table
        0,           # nsyms
        240,         # size of optional header (PE32+)
        0x0022,      # characteristics: EXECUTABLE_IMAGE | LARGE_ADDRESS_AWARE
    )

    entry_rva = 0x1000
    opt = struct.pack("<HBB", 0x20B, 2, 0)                       # magic, linker ver
    opt += struct.pack("<III", 0x20, 0, 0)                       # sizes of code/init/uninit
    opt += struct.pack("<II", entry_rva, entry_rva)              # entry point, base of code
    opt += struct.pack("<Q", base)                               # image base
    opt += struct.pack("<II", sect_align, file_align)            # section/file alignment
    opt += struct.pack("<HHHHHH", 6, 0, 0, 0, 6, 0)              # os/image/subsys versions
    opt += struct.pack("<IIII", 0, 0x2000, file_align, 0)        # win32ver, sizeofimage, headers, checksum
    opt += struct.pack("<HH", 3, 0)                              # subsystem console, dllchars
    opt += struct.pack("<QQQQ", 0x1000, 0x1000, 0x1000, 0x1000)  # stack/heap reserve/commit
    opt += struct.pack("<II", 0, 16)                             # loader flags, rva count
    opt += b"\x00" * (240 - len(opt))

    sect = struct.pack(
        "<8sIIIIIIHHI",
        b".code\x00\x00",
        0x1000,      # virtual size
        entry_rva,   # virtual address
        0x20,        # raw data size
        file_align,  # raw data ptr
        0, 0,        # reloc / line-number pointers
        0, 0,        # reloc / line-number counts
        0x60000020,  # code, execute, read
    )

    code = bytes([0x31, 0xC9,   # xor ecx, ecx
                  0xF7, 0xF1,   # div ecx  -> INT 0 / STATUS_DIVIDE_BY_ZERO
                  0xC3])        # ret (unreachable)
    raw = code + b"\x90" * (0x20 - len(code))

    img = dos + b"PE\x00\x00" + coff + opt + sect
    img += b"\x00" * (file_align - len(img))
    img += raw
    return img


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    open(sys.argv[1], "wb").write(build())
    print(f"wrote {sys.argv[1]} ({0x220} bytes)")
