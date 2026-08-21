import struct, json, hashlib, sys

buf = open(r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\full_package_table.bin', 'rb').read()
n = len(buf) // 0x118
print('in-process .bin rows:', n)
print('in-process sha256:', hashlib.sha256(buf).hexdigest()[:16])

ext = json.load(open(r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\full_package_table.json'))
print('external json rows:', len(ext))

diff = []
for i in range(n):
    off = i * 0x118
    r = buf[off:off + 0x118]
    name = r[4:0x104].split(b'\x00')[0].decode('ascii', 'replace')
    tail = r[0x110:0x118]
    e = ext[i]
    if e['name'] != name:
        diff.append((i, 'name', e['name'], name))
    elif bytes.fromhex(e['tail']) != tail:
        diff.append((i, 'tail', e['tail'], tail.hex()))
    elif e['kind'] != r[0x10C]:
        diff.append((i, 'kind', e['kind'], r[0x10C]))
    elif e['marker'] != struct.unpack_from('<I', r, 0)[0]:
        diff.append((i, 'marker', e['marker'], struct.unpack_from('<I', r, 0)[0]))
    elif e['f108'] != struct.unpack_from('<I', r, 0x108)[0]:
        diff.append((i, 'f108', e['f108'], struct.unpack_from('<I', r, 0x108)[0]))

print()
print('rows differing:', len(diff))
for d in diff[:20]:
    print('  idx', d[0], 'field', d[1], 'ext:', d[2], 'inproc:', d[3])
if not diff:
    print('BYTE-FOR-BYTE IDENTICAL across modes')
