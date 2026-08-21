import struct, sys
from diff_minidumps import read_minidump_regions, extract

A = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_healthy_inproc.dmp'
B = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_failing_external.dmp'
BASE = 0x7FF641BF0000
ra = read_minidump_regions(A)
rb = read_minidump_regions(B)

def va(off):
    return BASE + off

def g32(regions, path, off):
    d = extract(path, regions, va(off), 4)
    return struct.unpack('<I', d)[0] if d else None

def g64(regions, path, off):
    d = extract(path, regions, va(off), 8)
    return struct.unpack('<Q', d)[0] if d else None

def g8(regions, path, off):
    d = extract(path, regions, va(off), 1)
    return d[0] if d else None

checks = [
    (0x1F916FC, 'registration state', 4),
    (0x1F916D5, 'GUID gate', 1),
    (0x1F916D8, 'table ptr', 8),
    (0x1F916E0, 'compacted ptr', 8),
    (0x1F916E8, 'compacted count', 8),
    (0x1F91698, 'R1', 4),
    (0x1F916D0, 'DAT_141f916d0', 8),
    (0x267AA50, '-87 counter', 4),
    (0x1F916F0, 'aux ptr', 8),
    (0x1F916F8, 'aux count', 8),
]
print(f'{"global":<22} {"healthy":<22} {"failing":<22}')
for off, name, sz in checks:
    if sz == 8:
        a, b = g64(ra, A, off), g64(rb, B, off)
        print(f'{name:<22} {hex(a) if a else "NULL/0":<22} {hex(b) if b else "NULL/0":<22}')
    elif sz == 4:
        a, b = g32(ra, A, off), g32(rb, B, off)
        print(f'{name:<22} {a if a is not None else "?":<22} {b if b is not None else "?":<22}')
    else:
        a, b = g8(ra, A, off), g8(rb, B, off)
        print(f'{name:<22} {a:<22} {b:<22}')
