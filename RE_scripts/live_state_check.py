import ctypes, struct, sys
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from dump_sunrise_memory import find_pid, open_process, read_memory

pid = find_pid('destiny2.exe')
if not pid:
    print('no game')
    sys.exit(1)
base = 0x7FF641BF0000
handle = open_process(pid)
print('pid', pid)

def r64(a):
    try:
        d = read_memory(handle, a, 8)
    except Exception:
        return None
    return struct.unpack('<Q', d)[0] if d and len(d) == 8 else None

def r32(a):
    try:
        d = read_memory(handle, a, 4)
    except Exception:
        return None
    return struct.unpack('<I', d)[0] if d and len(d) == 4 else None

def r8(a):
    try:
        d = read_memory(handle, a, 1)
    except Exception:
        return None
    return d[0] if d else None

def va(a):
    return base + (a - 0x140000000)

checks = [
    (0x14267AA50, 'DAT_14267aa50 (-87 counter)', 4),
    (0x141F916FC, 'DAT_141f916fc (registration state)', 4),
    (0x141F916D5, 'DAT_141f916d5 (GUID gate)', 1),
    (0x141F916D8, 'DAT_141f916d8 (table ptr)', 8),
    (0x141F916E0, 'DAT_141f916e0 (compacted)', 8),
    (0x141F916E8, 'DAT_141f916e8 (compacted count)', 8),
    (0x141F91698, 'DAT_141f91698 (R1)', 4),
    (0x141F916D0, 'DAT_141f916d0', 8),
    (0x141F916D1, 'DAT_141f916d1', 1),
    (0x141F916D2, 'DAT_141f916d2', 1),
    (0x141F916D3, 'DAT_141f916d3', 1),
    (0x141F916D4, 'DAT_141f916d4', 1),
]
for g, name, sz in checks:
    if sz == 8:
        v = r64(va(g))
        print(f'{name}: {hex(v) if v else "NULL/0"}')
    elif sz == 4:
        v = r32(va(g))
        print(f'{name}: {v} (0x{v:X})' if v is not None else f'{name}: unreadable')
    else:
        v = r8(va(g))
        print(f'{name}: {v}')
