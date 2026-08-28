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
        begin, end, _unwind = table[index]
        inside = begin <= rva < end
        print(f"0x{rva:X}  fn 0x{BASE + begin:X}..0x{BASE + end:X} "
              f"size={end - begin} offset_in_fn=0x{rva - begin:X} "
              f"{'' if inside else '** OUTSIDE - address is in a gap **'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
