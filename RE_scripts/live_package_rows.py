import ctypes, struct, sys, time
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from dump_sunrise_memory import find_pid, open_process, read_memory

pid = find_pid('destiny2.exe')
if not pid:
    print('no game')
    sys.exit(1)
base = None
for _ in range(120):
    try:
        from dump_sunrise_memory import find_module_base
        base = find_module_base(pid, 'destiny2.exe')
        break
    except Exception:
        base = 0x7FF641BF0000
        break
handle = open_process(pid)
print('pid', pid, 'base', hex(base))

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

def va(a):
    return base + (a - 0x140000000)

tbl = r64(va(0x141F916D8))
comp = r64(va(0x141F916E0))
aux = r64(va(0x141F916F0))
print('orig:', hex(tbl) if tbl else 'NULL', '| compacted:', hex(comp) if comp else 'NULL', '| aux:', hex(aux) if aux else 'NULL')
target = comp or tbl
if target:
    print('+0x4408 count:', r64(target + 0x4408), '| +0xa810 count:', r32(target + 0xa810))
    n = r32(target + 0xa810)
    if n and 0 < n < 5000:
        print('--- package rows (+0xa818, 0x118 stride), first 12 ---')
        for i in range(min(n, 12)):
            off = target + 0xa818 + i * 0x118
            row = read_memory(handle, off, 0x118)
            if not row or len(row) < 0x118:
                break
            print(f'row {i}: {row[:48].hex()}')
