import ctypes, struct, sys, time
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from dump_sunrise_memory import find_pid, find_module_base, open_process, read_memory

def plausible(p):
    return p is not None and 0x10000000000 < p < 0x7FFFFFFFFFFF

KNOWN_BASE = 0x7FF641BF0000

print('watcher armed (package rows at +0xa818)', flush=True)
old = find_pid('destiny2.exe')
print('current pid (if any):', old, flush=True)
pid = None
deadline = time.time() + 900
while time.time() < deadline:
    try:
        cur = find_pid('destiny2.exe')
    except Exception:
        cur = None
    if cur and cur != old and not pid:
        pid = cur
        print('NEW GAME PID', pid, flush=True)
        base = KNOWN_BASE
        handle = open_process(pid)

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

        seen = False
        t_deadline = time.time() + 300
        while time.time() < t_deadline:
            tbl = r64(va(0x141F916D8))
            if plausible(tbl):
                npk = r32(tbl + 0xa810)
                if npk and npk > 20 and not seen:
                    seen = True
                    print('PACKAGE TABLE at', hex(tbl), 'package count', npk, flush=True)
                    for i in range(min(npk, 12)):
                        off = tbl + 0xa818 + i * 0x118
                        row = read_memory(handle, off, 0x118)
                        if not row or len(row) < 0x118:
                            break
                        print(f'row {i}: {row[:48].hex()}', flush=True)
                    # the first rows' tail (the +0x100 region)
                    for i in range(min(npk, 6)):
                        off = tbl + 0xa818 + i * 0x118
                        tail = read_memory(handle, off + 0x100, 0x18)
                        if tail:
                            print(f'row {i} tail(+0x100): {tail.hex()}', flush=True)
                if r64(tbl + 0x4408) is not None and r64(va(0x141F916D8)) != tbl:
                    print('original freed', flush=True)
                    break
            time.sleep(0.005)
        if seen:
            print('WATCHER DONE (package rows captured)', flush=True)
            break
        print('package table never captured (window expired)', flush=True)
        break
    time.sleep(0.1)
else:
    print('watcher deadline reached', flush=True)
