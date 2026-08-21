# iv_struct_dump.py -- dump the FULL struct region (0x141F44C00, 0x3C0 bytes =
# the heap-copy stride) from BOTH dumps + the healthy heap copies, and check
# the failing dump at the heap addresses.
import struct, sys
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from diff_minidumps import read_minidump_regions, extract

BASE = 0x7FF641BF0000
A = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_healthy_inproc.dmp'
B = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_failing_external.dmp'
ra = read_minidump_regions(A); rb = read_minidump_regions(B)

def dump(path, regions, va, size, label):
    d = extract(path, regions, va, size)
    if d is None:
        print('%s: MISSING' % label)
        return None
    print('%s @0x%X (0x%X bytes):' % (label, va, size))
    for i in range(0, size, 16):
        chunk = d[i:i+16]
        print('  +0x%03X: %s' % (i, ' '.join('%02X' % x for x in chunk)))
    return d

# 1. struct region, 0x3C0 bytes, both dumps
hs = dump(A, ra, BASE + 0x1F44C00, 0x3C0, 'HEALTHY struct 0x3C0')
fs = dump(B, rb, BASE + 0x1F44C00, 0x3C0, 'FAILING struct 0x3C0')
if hs and fs:
    diffs = [i for i in range(0x3C0) if hs[i] != fs[i]]
    print('struct diffs: %d bytes' % len(diffs))
    runs = []
    for i in diffs:
        if runs and i == runs[-1][1] + 1:
            runs[-1] = (runs[-1][0], i)
        else:
            runs.append((i, i))
    for a, b in runs:
        print('  [0x%03X..0x%03X] len=%d H=%s F=%s' % (a, b, b-a+1,
              ' '.join('%02X' % hs[i] for i in range(a, b+1)),
              ' '.join('%02X' % fs[i] for i in range(a, b+1))))

# 2. healthy heap copies (first hit at 0x18CDBA4B258), dump 0x3C0
print()
dump(A, ra, 0x18CDBA4B258, 0x3C0, 'HEALTHY heap copy #1 @0x18CDBA4B258')
print()
dump(B, rb, 0x18CDBA4B258, 0x3C0, 'FAILING @ same heap address')

# 3. also the IV +- 0x40 in both dumps (the immediate neighborhood)
print()
dump(A, ra, BASE + 0x1F44CA0, 0x100, 'HEALTHY IV neighborhood 0xCA0..0xDA0')
print()
dump(B, rb, BASE + 0x1F44CA0, 0x100, 'FAILING IV neighborhood 0xCA0..0xDA0')
