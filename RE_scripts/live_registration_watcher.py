import ctypes, struct, sys, time
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from dump_sunrise_memory import find_pid, find_module_base, open_process, read_memory

def plausible(p):
    return p is not None and 0x10000000000 < p < 0x7FFFFFFFFFFF

KNOWN_BASE = 0x7FF641BF0000

print('watcher armed (instant base, waiting for a new destiny2.exe)', flush=True)
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
        print('base (hardcoded)', hex(base), flush=True)

        def r64(a):
            try:
                d = read_memory(handle, a, 8)
            except Exception:
                return None
            return struct.unpack('<Q', d)[0] if d and len(d) == 8 else None

        def va(a):
            return base + (a - 0x140000000)

        seen_full = False
        t_deadline = time.time() + 300
        while time.time() < t_deadline:
            tbl = r64(va(0x141F916D8))
            if plausible(tbl):
                cnt = r64(tbl + 0x4408)
                if cnt is not None and 20 < cnt < 10000 and not seen_full:
                    seen_full = True
                    print('FULL TABLE at', hex(tbl), 'count', cnt, flush=True)
                    for i in range(min(cnt, 40)):
                        off = tbl + 0x4410 + i * 400
                        row = read_memory(handle, off, 400)
                        if not row or len(row) < 400:
                            break
                        fid = struct.unpack_from('<I', row, 0)[0]
                        sid = struct.unpack_from('<H', row, 4)[0]
                        sig = struct.unpack_from('<I', row, 0x164)[0]
                        exp = struct.unpack_from('<Q', row, 0x168)[0]
                        kind = row[0x16c]
                        print(f'row {i}: id=0x{fid:08X} sid=0x{sid:04X} sig=0x{sig:08X} expHash=0x{exp:016X} kindByte=0x{kind:02X}', flush=True)
                if cnt is not None and cnt <= 20:
                    print('COMPACTED state at', hex(tbl), flush=True)
                    break
            time.sleep(0.005)
        if seen_full:
            print('WATCHER DONE (captured the full table)', flush=True)
            break
        print('no full table this session (window expired)', flush=True)
        break
    time.sleep(0.1)
else:
    print('watcher deadline reached', flush=True)
