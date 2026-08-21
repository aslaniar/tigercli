import ctypes, struct, sys
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from dump_sunrise_memory import find_pid, find_module_base, open_process, read_memory

pid = find_pid('destiny2.exe')
if not pid:
    print('NO GAME PROCESS')
    sys.exit(1)
base = find_module_base(pid, 'destiny2.exe')
if not base:
    print('NO BASE')
    sys.exit(1)
handle = open_process(pid)
print('pid', pid, 'base', hex(base))

def r64(addr):
    d = read_memory(handle, addr, 8)
    return struct.unpack('<Q', d)[0] if d else None

def read(addr, n):
    return read_memory(handle, addr, n)

# DAT_141f916d8 = the content-manifest table pointer (image VA 0x141F916D8)
VA = 0x141F916D8
tbl = r64(base + (VA - 0x140000000))
print('DAT_141f916d8 ->', hex(tbl) if tbl else 'NULL')

if tbl:
    d = read(tbl + 0x4408, 8)
    count = struct.unpack('<Q', d)[0] if d else 0
    print('row count @+0x4408:', count)
    n = min(count or 0, 24)
    print('--- first', n, 'rows (400-B records at +0x4410) ---')
    for i in range(n):
        off = tbl + 0x4410 + i * 400
        row = read(off, 400)
        if not row or len(row) < 400:
            print(f'row {i}: UNREADABLE ({len(row) if row else 0}B)')
            break
        fid = struct.unpack_from('<I', row, 0)[0]
        sid = struct.unpack_from('<H', row, 4)[0]
        sig = struct.unpack_from('<I', row, 0x164)[0]
        exp = struct.unpack_from('<Q', row, 0x168)[0]
        kind = row[0x16c]
        b7 = row[7]
        print(f'row {i}: id=0x{fid:08X} sid=0x{sid:04X} flag7=0x{b7:02X} '
              f'sig=0x{sig:08X} expHash=0x{exp:016X} kindByte=0x{kind:02X}')
