#!/usr/bin/env python3
"""Resolve the containing function bounds of one or more addresses from .pdata.

Usage: pdata_bounds.py <addr> [<addr>...]
  addr = an RVA (0x17E245C) or a static VA (0x1417E245C); both are accepted and
  normalised against the image base.

.pdata holds RUNTIME_FUNCTION{begin RVA, end RVA, unwind RVA}, 12 bytes each, in
ascending order of begin. That makes it the ONLY exact source of function bounds
in a stripped image - a caller-capture RVA (LESSONS 18c) means nothing until it
is resolved to the function that owns it.
"""
import bisect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pe_reader import PE

IMAGE = ("/Users/rubenaslanian/Documents/opencode/sunrise-fork/"
         "RE_output/destiny2_unpacked_full.exe")
BASE = 0x140000000


def entries(pe):
    """@return Ascending [(begin_rva, end_rva, unwind_rva)] from the .pdata section."""
    for name, vaddr, vsize, _rawptr, _rawsize in pe.sections:
        if name.rstrip("\x00") != ".pdata":
            continue
        blob = pe.read(BASE + vaddr, vsize)
        out = []
        for off in range(0, len(blob) - 11, 12):
            begin = int.from_bytes(blob[off:off + 4], "little")
            end = int.from_bytes(blob[off + 4:off + 8], "little")
            unwind = int.from_bytes(blob[off + 8:off + 12], "little")
            if begin == 0 and end == 0:
                continue
            out.append((begin, end, unwind))
        out.sort()
        return out
    raise SystemExit("no .pdata section")


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    pe = PE(IMAGE)
    table = entries(pe)
    begins = [e[0] for e in table]
    print(f"{len(table)} .pdata entries")
    for arg in argv:
        value = int(arg, 16)
        rva = value - BASE if value >= BASE else value
        index = bisect.bisect_right(begins, rva) - 1
        if index < 0:
            print(f"0x{rva:X}  NO ENTRY (below the first)")
            continue
        begin, end, unwind = table[index]
        inside = begin <= rva < end
        chain = ""
        # UNW_FLAG_CHAININFO: this entry is a FRAGMENT, and its parent RUNTIME_FUNCTION
        # is appended after the unwind codes. Without following it, a fragment's begin
        # address is mistaken for a function start - which is how a caller-capture RVA
        # gets attributed to the wrong function.
        hops = 0
        cur = (begin, end, unwind)
        while hops < 8:
            info = pe.read(BASE + cur[2], 4)
            flags = (info[0] >> 3) & 0x1F
            if not flags & 0x4:
                break
            count = info[2]
            codes = count + (count & 1)  # padded to an even count of 2-byte slots
            parent = pe.read(BASE + cur[2] + 4 + codes * 2, 12)
            pb = int.from_bytes(parent[0:4], "little")
            pe_ = int.from_bytes(parent[4:8], "little")
            pu = int.from_bytes(parent[8:12], "little")
            if pb == 0 or pb == cur[0]:
                break
            cur = (pb, pe_, pu)
            hops += 1
        if hops:
            chain = (f"  [FRAGMENT: primary fn 0x{BASE + cur[0]:X}..0x{BASE + cur[1]:X} "
                     f"size={cur[1] - cur[0]} after {hops} chain hop(s)]")
        print(f"0x{rva:X}  entry 0x{BASE + begin:X}..0x{BASE + end:X} "
              f"size={end - begin} offset=0x{rva - begin:X} "
              f"{'' if inside else '** OUTSIDE - address is in a gap **'}{chain}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
