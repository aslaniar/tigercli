import struct, sys
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from diff_minidumps import read_minidump_regions, extract

BASE = 0x7FF641BF0000
A = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_healthy_inproc.dmp'
B = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_failing_external.dmp'
ra = read_minidump_regions(A)
rb = read_minidump_regions(B)

for name, img in [('FUN_14689840b', 0x14689840b), ('FUN_1453de4c4', 0x1453de4c4)]:
    runtime = BASE + (img - 0x140000000)
    h = extract(A, ra, runtime - 0x800, 0x1000)
    f = extract(B, rb, runtime - 0x800, 0x1000)
    diffs = [(i, h[i], f[i]) for i in range(0x1000) if h[i] != f[i]]
    print(f'{name}: {len(diffs)} differing bytes')
    for i, x, y in diffs[:16]:
        va = runtime - 0x800 + i
        print(f'  @0x{i:X} (VA 0x{va:X}): healthy=0x{x:02X} failing=0x{y:02X}')
    if diffs:
        lo, hi = diffs[0][0], diffs[-1][0]
        print(f'  diff span: 0x{lo:X}..0x{hi:X}')
    print()
