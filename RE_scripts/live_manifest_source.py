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

src = r64(va(0x141F916A0))
print('manifest source object @', hex(src) if src else 'NULL')
if src:
    head = read(src, 0x40)
    if head:
        print('head bytes:', head.hex())
        for i in range(0, 0x40, 8):
            q = struct.unpack_from('<Q', head, i)[0]
            print(f'  +0x{i:02X}: 0x{q:016X}')
    f8 = r32(src + 8)
    fc = r32(src + 0xc)
    f10 = r32(src + 0x10)
    print('state@+8:', f8, '| code@+0xc:', fc, '| @+0x10:', f10)
    p18 = r64(src + 0x18)
    p20 = r64(src + 0x20)
    print('ptr@+0x18:', hex(p18) if p18 else 0, '| ptr@+0x20:', hex(p20) if p20 else 0)
    if p20:
        buf = read(p20, 0x40)
        print('buffer@+0x20 head:', buf.hex() if buf else 'unreadable')
    if p18:
        buf = read(p18, 0x40)
        print('buffer@+0x18 head:', buf.hex() if buf else 'unreadable')
