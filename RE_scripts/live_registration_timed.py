import ctypes, struct, sys, time
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from dump_sunrise_memory import find_pid, find_module_base, open_process, read_memory

pid = find_pid('destiny2.exe')
if not pid:
    print('NO GAME PROCESS')
    sys.exit(1)
base = find_module_base(pid, 'destiny2.exe')
handle = open_process(pid)
print('pid', pid, 'base', hex(base), flush=True)

def r64(addr):
    d = read_memory(handle, addr, 8)
    return struct.unpack('<Q', d)[0] if d else None

def va(a):
    return base + (a - 0x140000000)

# Poll DAT_141f916d8 until it becomes non-null, then read the rows IMMEDIATELY.
deadline = time.time() + 180
seen = False
last_ts = 0
while time.time() < deadline:
    tbl = r64(va(0x141F916D8))
    if tbl and not seen:
        seen = True
        last_ts = time.time()
        print('TABLE APPEARED at', hex(tbl), flush=True)
        cnt = r64(tbl + 0x4408)
        print('row count @+0x4408:', cnt, flush=True)
        n = min(cnt or 0, 465)
        print('--- the first rows (id, sid, sig, expHash, kindByte) ---', flush=True)
        for i in range(n):
            off = tbl + 0x4410 + i * 400
            row = read_memory(handle, off, 400)
            if not row or len(row) < 400:
                break
            fid = struct.unpack_from('<I', row, 0)[0]
            sid = struct.unpack_from('<H', row, 4)[0]
            sig = struct.unpack_from('<I', row, 0x164)[0]
            exp = struct.unpack_from('<Q', row, 0x168)[0]
            kind = row[0x16c]
            if exp != 0 or kind != 0:
                print(f'row {i}: id=0x{fid:08X} sid=0x{sid:04X} sig=0x{sig:08X} expHash=0x{exp:016X} kindByte=0x{kind:02X}', flush=True)
        # keep polling the same table while it lives (the compaction will free it)
        while time.time() < deadline and r64(va(0x141F916D8)) == tbl:
            time.sleep(0.05)
        if time.time() < deadline:
            print('TABLE FREED at', time.time() - last_ts, 's after appearance', flush=True)
        break
    time.sleep(0.05)
if not seen:
    print('table never appeared within the window', flush=True)
