"""Find every occurrence of a u32 value in the unpacked client image.

Usage: find_u32.py <hex-value> [more-hex...]
Reports section + VA (imagebase 0x140000000) for each hit, with surrounding
context bytes, so a {hash, key} pair-table would be visible on the spot.
Only RAW stored bytes are scanned (.data is 7% stored - see FINDINGS 20.52).
"""
import sys
import os
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe_reader import PE

IMAGE = ("/Users/rubenaslanian/Documents/opencode/sunrise-fork/"
         "RE_output/destiny2_unpacked_full.exe")


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    values = [int(a, 16) & 0xFFFFFFFF for a in argv]
    pe = PE(IMAGE)
    blobs = []
    for name, vaddr, _vsize, rawptr, rawsize in pe.sections:
        if rawsize:
            blobs.append((name, pe.imagebase + vaddr,
                          pe.data[rawptr:rawptr + rawsize]))
    for value in values:
        total = 0
        for label, needle in (("LE", struct.pack("<I", value)),
                              ("BE", struct.pack(">I", value))):
            for name, va, raw in blobs:
                start = 0
                while True:
                    off = raw.find(needle, start)
                    if off < 0:
                        break
                    start = off + 1
                    total += 1
                    ctx = raw[max(0, off - 16):off + 20]
                    print("%s %-8s va=%#x  ctx: %s"
                          % (label, name, va + off, ctx.hex()))
        print("value %#010x: %d hit(s)" % (value, total))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
