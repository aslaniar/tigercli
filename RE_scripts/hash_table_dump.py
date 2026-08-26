"""Dump the hash->pointer table found at .data ~0x14206f0f0 (2026-08-25 session).

Records look like {u32 hash, u32 pad, u64 runtime-ptr}, 16 B stride, hashes
consecutive around 0x80806AC0. Walk out from an anchor VA until the pattern
breaks, print every record, and try to resolve each pointer to static .data
(stored range only - FINDINGS 20.52).
"""
import sys
import os
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe_reader import PE

IMAGE = ("/Users/rubenaslanian/Documents/opencode/sunrise-fork/"
         "RE_output/destiny2_unpacked_full.exe")
ANCHOR = 0x14206F0F0


def main():
    pe = PE(IMAGE)
    # Read a generous window around the anchor.
    start = ANCHOR - 0x400
    window = pe.read(start, 0x1000)
    if window is None:
        print("window unmapped")
        return 1
    base_off = None
    for i in range(0, len(window) - 16, 8):
        va = start + i
        if va == ANCHOR:
            base_off = i
            break
    if base_off is None:
        print("anchor not 8-aligned in window?")
        return 1
    # Walk back to the table's first record: a record is {u32 h, u32 pad==0,
    # u64 ptr}; walk while records hold a nonzero high-ish hash word.
    first = base_off
    while first >= 16:
        h, pad = struct.unpack_from("<II", window, first - 16)
        if h & 0x80000000 and pad == 0:
            first -= 16
        else:
            break
    last = base_off
    while last + 16 <= len(window):
        h, pad = struct.unpack_from("<II", window, last)
        ptr, = struct.unpack_from("<Q", window, last + 8)
        if h & 0x80000000 and pad == 0 and ptr != 0:
            last += 16
        else:
            break
    n = (last - first) // 16
    print("records: %d   first va=%#x   end va=%#x"
          % (n, start + first, start + last))
    statics = 0
    for r in range(n):
        o = first + r * 16
        h, _pad = struct.unpack_from("<II", window, o)
        ptr, = struct.unpack_from("<Q", window, o + 8)
        st = pe.to_static(ptr)
        stored = pe.off(st) is not None if st else False
        statics += bool(stored)
        if r < 8 or r >= n - 4:
            print("  [%3d] hash=%#010x ptr=%#x static=%s %s"
                  % (r, h, ptr,
                     ("%.12X" % st) if st and st != ptr else "-",
                     "STORED" if stored else ""))
    print("pointers resolving into STORED image bytes: %d/%d" % (statics, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
