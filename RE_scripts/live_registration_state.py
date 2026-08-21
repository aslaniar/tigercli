import struct, sys
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from dump_sunrise_memory import find_pid, find_module_base, open_process, read_memory

pid = find_pid('destiny2.exe')
base = find_module_base(pid, 'destiny2.exe')
handle = open_process(pid)
print('pid', pid, 'base', hex(base))

def r64(addr):
    d = read_memory(handle, addr, 8)
    return struct.unpack('<Q', d)[0] if d else None

def r32(addr):
    d = read_memory(handle, addr, 4)
    return struct.unpack('<I', d)[0] if d else None

def read(addr, n):
    return read_memory(handle, addr, n)

def va(addr):
    return base + (addr - 0x140000000)

print('--- registration state globals ---')
print('DAT_141f916fc (state)      :', r32(va(0x141F916FC)))
print('DAT_141f91700 (result code):', r32(va(0x141F91700)), ' (2=init 3=ok 4=reject 5/6=read-err 8=404)')
print('DAT_141f91704 (ready?)     :', r32(va(0x141F91704)))
print('DAT_141f91706 (container)  :', hex(r32(va(0x141F91706)) or 0))
print('DAT_141f916d8 (orig table) :', hex(r64(va(0x141F916D8)) or 0))
print('DAT_141f916e0 (compacted)  :', hex(r64(va(0x141F916E0)) or 0))
print('DAT_141f916e8 (comp count) :', r64(va(0x141F916E8)))
print('DAT_141f916f0 (aux)        :', hex(r64(va(0x141F916F0)) or 0))
print('DAT_141f916f8 (aux count)  :', r64(va(0x141F916F8)))
print('DAT_141f916a0 (manifest src):', hex(r64(va(0x141F916A0)) or 0))
print('DAT_141f91698 (enc flag?)  :', r32(va(0x141F91698)))
print('DAT_141f916d5 (guid gate?) :', r32(va(0x141F916D5)))
print('--- registration result globals ---')
print('DAT_14267aa50 (result)     :', r32(va(0x14267AA50)), ' (signed:', struct.unpack('<i', struct.pack('<I', r32(va(0x14267AA50))))[0], ')')
print('DAT_14267aa74 (pending)    :', r32(va(0x14267AA74)))
print('--- the compacted rows (if any) ---')
comp = r64(va(0x141F916E0))
cnt = r64(va(0x141F916E8)) or 0
if comp and cnt:
    n = min(cnt, 10)
    for i in range(n):
        row = read(comp + i * 400, 400)
        if not row or len(row) < 400:
            print(f'row {i}: unreadable')
            break
        fid = struct.unpack_from('<I', row, 0)[0]
        sid = struct.unpack_from('<H', row, 4)[0]
        sig = struct.unpack_from('<I', row, 0x164)[0]
        exp = struct.unpack_from('<Q', row, 0x168)[0]
        kind = row[0x16c]
        print(f'row {i}: id=0x{fid:08X} sid=0x{sid:04X} sig=0x{sig:08X} expHash=0x{exp:016X} kindByte=0x{kind:02X}')
else:
    print('compacted table empty/absent')
