import struct, sys

b = open(r'C:\Users\rasla\Downloads\destiny-preservation\dcv build\cache_phr_0000f7ea.dat.bak', 'rb').read()
print('size:', len(b))

sig0 = bytes.fromhex('9fe57c13e73f31ea')
positions = []
start = 0
while True:
    i = b.find(sig0, start)
    if i < 0:
        break
    positions.append(i)
    start = i + 1
print('occurrences of sig0 (slot-0 sig):', len(positions))
print('first 10 positions:', positions[:10])
if len(positions) > 1:
    print('gaps between the first occurrences:', [positions[i+1] - positions[i] for i in range(min(9, len(positions)-1))])

print()
print('--- the bytes around the 2nd occurrence (the next record) ---')
if len(positions) > 1:
    p = positions[1]
    print(b[p-8:p+16].hex())

print()
print('--- the file tail ---')
print('last 64 bytes:', b[-64:].hex())
print('last 16 as ascii:', repr(b[-16:]))
