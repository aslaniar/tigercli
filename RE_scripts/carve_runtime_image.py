#!/usr/bin/env python3
# REGISTRY: caps: carve-runtime-image, dump-read
"""carve_runtime_image.py - build a file-layout PE from a full minidump's
DECRYPTED runtime image.

Why: the on-disk destiny2.exe is encrypted at every code site (verified
2026-09-07: root/ctor/job-runner/registration all garbage on disk, clean in
memory) - so every Ghidra/xref scan against the stored file is void for .text.
The dump's memory image is the decrypted truth (100% coverage of the module
checked). This tool re-lays the dump's memory sections back into the section
table's FILE layout, producing a loadable PE whose bytes match runtime.

Method: headers copied verbatim from the on-disk exe (the section table is
legitimate); each section's bytes read from the dump at module_base + RVA and
written at the header's raw offset (min(rawsize, vsize)).

Oracle (must pass before the file is usable): the bytes at ctor 0x1416BB1E0
in the output must equal the dump's bytes and decode as a prologue - the
on-disk file FAILS this oracle (that is the whole point).

Usage: carve_runtime_image.py <dump.dmp> <out.exe> [--check]
Requires: minidump_reader (same dir).
"""
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from minidump_reader import Minidump

ORACLE_VA = 0x1416BB1E0          # ctor - known-readable in dump, garbage on disk
ORACLE_EXPECT_PREFIX = b"\x48\x8d\x05"   # lea rax, [rip+...]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    dump_path, out_path = sys.argv[1], sys.argv[2]
    disk_exe = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "Game", "destiny2.exe")

    md = Minidump(dump_path)
    mod = md.module("destiny2")
    base = mod["base"]
    img_size = mod["size"]

    hdr = open(disk_exe, "rb").read(0x1000)
    e = struct.unpack_from("<I", hdr, 0x3C)[0]
    coff = e + 4
    nsec = struct.unpack_from("<H", hdr, coff + 2)[0]
    opt = coff + 20
    opt_size = struct.unpack_from("<H", hdr, coff + 16)[0]
    sec_off = opt + opt_size
    secs = []
    for i in range(nsec):
        s = hdr[sec_off + i * 40: sec_off + (i + 1) * 40]
        name = s[:8].rstrip(b"\0").decode(errors="replace")
        vsz, vaddr, rsz, raddr, chars = struct.unpack_from("<IIIII", s, 8)
        secs.append((name, vaddr, vsz, raddr, rsz))
    headers_size = sec_off + nsec * 40

    out = bytearray(img_size)
    out[0:headers_size] = hdr[0:headers_size]

    total = 0
    for name, vaddr, vsz, raddr, rsz in secs:
        n = min(rsz, vsz)
        if n == 0:
            continue
        data = md.read_va(base + vaddr, n)
        if data is None or len(data) < n:
            print(f"FAIL: section {name}: dump read short "
                  f"({0 if data is None else len(data)}/{n})")
            return 1
        out[raddr:raddr + n] = data
        total += n
        print(f"  {name:10} rva 0x{vaddr:X} -> raw 0x{raddr:X} ({n} bytes)")

    # oracle 1: output bytes at the ctor equal the dump's bytes
    want = md.read_va(ORACLE_VA + (base - 0x140000000), 8)
    rva = ORACLE_VA - 0x140000000
    # map rva -> file offset via section table
    foff = None
    for name, vaddr, vsz, raddr, rsz in secs:
        if vaddr <= rva < vaddr + vsz:
            foff = raddr + (rva - vaddr)
    got = bytes(out[foff:foff + 8]) if foff is not None else b""
    ok1 = got == want
    # oracle 2: it decodes as the known prologue
    ok2 = got.startswith(ORACLE_EXPECT_PREFIX)
    print(f"oracle1 (output==dump at 0x{ORACLE_VA:X}): {ok1} ({got.hex()} vs {want.hex()})")
    print(f"oracle2 (prologue decode):                 {ok2}")
    if "--check" in sys.argv:
        return 0 if (ok1 and ok2) else 1
    if not (ok1 and ok2):
        print("ORACLE FAILED - output not written")
        return 1

    with open(out_path, "wb") as f:
        f.write(out)
    print(f"WROTE {out_path} ({len(out)} bytes, {total} section bytes from dump)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
