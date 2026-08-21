import struct, sys

b = open(r'C:\Users\rasla\Downloads\destiny-preservation\dcv build\cache_phr_0000f7ea.dat.bak', 'rb').read()
print('size:', len(b))
guid = b[:36].decode()
print('guid:', guid)
rest = b[36:]
print('after guid: NUL then:', rest[:64].hex())

pos = 37
print('--- interpreting from 0x25 (37) ---')
for off in range(37, 48):
    print(f'  @0x{off:02X}: {b[off]:02X}')

print()
print('--- candidate record parse (id u16 @2C, kind @2E, sig u64 @30, h2 u32 @38) ---')
idv = struct.unpack_from('<H', b, 0x2C)[0]
kind = b[0x2E]
sig = struct.unpack_from('<Q', b, 0x30)[0]
h2 = struct.unpack_from('<I', b, 0x38)[0]
print(f'id=0x{idv:04X} kind=0x{kind:02X} sig=0x{sig:016X} h2=0x{h2:08X}')

print()
print('--- bytes 0x40..0x120 ---')
print(b[0x40:0x120].hex())
