"""Search every mapped byte of the full dump for u32 needle values.

Usage: needle_scan.py <hex u32> [more...]
Reports every hit VA + 24 B context, deduplicating consecutive hits.
"""
import struct
import sys

sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\scripts')
from minidump_reader import Minidump

DUMP = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_healthy_inproc.dmp'


def main():
    needles = [struct.pack('<I', int(x, 16)) for x in sys.argv[1:]]
    md = Minidump(DUMP)
    for start, size, offset in md.ranges:
        data = md._read(offset, size)
        for ni, needle in enumerate(needles):
            pos = 0
            while True:
                p = data.find(needle, pos)
                if p < 0:
                    break
                pos = p + 1
                ctx = data[max(0, p - 12):p + 16]
                print('needle %#010x @ %#x  ctx %s'
                      % (int.from_bytes(needle, 'little'), start + p,
                         ctx.hex()))
    print('done')


if __name__ == '__main__':
    main()
