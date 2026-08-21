import struct, sys
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from diff_minidumps import read_minidump_regions, extract

BASE = 0x7FF641BF0000
A = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_healthy_inproc.dmp'
B = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_failing_external.dmp'
ra = read_minidump_regions(A)
rb = read_minidump_regions(B)

IV_KIND0 = BASE + 0x1F44CE0
IV_KINDN = BASE + 0x1B7CAC8

for name, va in [('kind0 IV (0x1F44CE0)', IV_KIND0), ('kindN IV (0x1B7CAC8)', IV_KINDN)]:
    h = extract(A, ra, va, 16)
    f = extract(B, rb, va, 16)
    print(f'{name}:')
    if h is None or f is None:
        print('  MISSING in a dump')
        continue
    hd = struct.unpack('<4I', h)
    fd = struct.unpack('<4I', f)
    for i in range(4):
        mark = '  <== DIFFERS' if hd[i] != fd[i] else ''
        print(f'  dword[{i}]: healthy=0x{hd[i]:08X} failing=0x{fd[i]:08X}{mark}')
    print(f'  healthy bytes: {h.hex()}')
    print(f'  failing bytes: {f.hex()}')
    print()

print('--- the candidate compare (the computed vs the known) ---')
print('computed kind0 healthy: 0x281141FD')
print('computed kind0 failing: 0x3DB8F835')
print('computed kindN (both):  0xFB438DF4')
print('PHR h2 0x01CE:          0x59676967')
print('tail slot-0:            0xEA313FE7137CE59F (low32 0x137CE59F)')
print('tail slot-2:            0x4B99BC940E044093 (low32 0x0E044093)')
print('tail slot-3:            0xEC153CBF6D3F59EE (low32 0x6D3F59EE)')
print('config field-1 (offerKey): 0xD0000448')
