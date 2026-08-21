import ctypes, struct, sys, time, json
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from dump_sunrise_memory import find_pid, open_process, read_memory

def plausible(p):
    return p is not None and 0x10000000000 < p < 0x7FFFFFFFFFFF

KNOWN_BASE = 0x7FF641BF0000

print('relatching watcher armed (a fresh window for every new pid)', flush=True)
seen = {p for p in [find_pid('destiny2.exe')] if p}
print('current pid(s):', seen or 'none', flush=True)
deadline = time.time() + 1800
while time.time() < deadline:
    try:
        cur = find_pid('destiny2.exe')
    except Exception:
        cur = None
    if cur and cur not in seen:
        seen.add(cur)
        pid = cur
        print('NEW GAME PID', pid, flush=True)
        handle = open_process(pid)
        base = KNOWN_BASE

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

        got = False
        t_deadline = time.time() + 300
        while time.time() < t_deadline:
            tbl = r64(va(0x141F916D8))
            if plausible(tbl):
                npk = r32(tbl + 0xa810)
                if npk and npk > 20:
                    got = True
                    print('PACKAGE TABLE at', hex(tbl), 'count', npk, flush=True)
                    total = npk * 0x118
                    buf = read_memory(handle, tbl + 0xa818, total)
                    if buf and len(buf) == total:
                        with open(r'RE_output\content\full_package_table.bin', 'wb') as f:
                            f.write(buf)
                        print('dumped', len(buf), 'bytes (all', npk, 'rows)', flush=True)
                    else:
                        print('FULL-REGION READ FAILED (got', len(buf) if buf else 0, 'of', total, ')', flush=True)
                    nent = r64(tbl + 0x4408)
                    if nent and 0 < nent < 1000:
                        ebuf = read_memory(handle, tbl + 0x4410, nent * 400)
                        if ebuf and len(ebuf) == nent * 400:
                            with open(r'RE_output\content\full_entitlement_table.bin', 'wb') as f:
                                f.write(ebuf)
                            print('entitlement table dumped:', nent, 'rows', flush=True)
                    break
                if r64(va(0x141F916D8)) != tbl:
                    print('table freed before capture (compaction)', flush=True)
                    break
            time.sleep(0.005)
        if not got:
            print('no table for pid', pid, '(window expired or freed)', flush=True)
    time.sleep(0.1)
print('watcher deadline reached', flush=True)
