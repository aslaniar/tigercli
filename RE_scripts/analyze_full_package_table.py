import struct, sys, json, collections
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\claims')
from s1_signature_diff import walk

buf = open(r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\full_package_table.bin', 'rb').read()
n = len(buf) // 0x118
print('rows in dump:', n, 'bytes:', len(buf))

b = open(r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\s1_config3.bin', 'rb').read()
cfg = {}
for r in [v for f, wt, v in walk(b) if f == 3]:
    fields = walk(r)
    name = sig = None
    for f, wt, v in fields:
        if f == 2:
            name = v.decode('utf-8', errors='replace')
        elif f == 4:
            sig = v
    if name:
        cfg[name] = sig

rows = []
for i in range(n):
    off = i * 0x118
    r = buf[off:off + 0x118]
    name = r[4:0x104].split(b'\x00')[0].decode('ascii', 'replace')
    rows.append({
        'idx': i,
        'marker': struct.unpack_from('<I', r, 0)[0],
        'name': name,
        'f104': struct.unpack_from('<I', r, 0x104)[0],
        'f108': struct.unpack_from('<I', r, 0x108)[0],
        'kind': r[0x10C],
        'tail': r[0x110:0x118].hex(),
        'tailval': struct.unpack_from('<Q', r, 0x110)[0],
    })

json.dump(rows, open(r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\full_package_table.json', 'w'), indent=1)
print('json saved')

print()
print('--- kind-byte histogram ---')
for k, c in collections.Counter(r['kind'] for r in rows).most_common():
    print(f'  kind=0x{k:02X}: {c}')

print()
print('--- +0x104 histogram ---')
for k, c in collections.Counter(r['f104'] for r in rows).most_common():
    print(f'  +0x104=0x{k:08X}: {c}')

print()
print('--- +0x108 (package id) histogram (top 12) ---')
for k, c in collections.Counter(r['f108'] for r in rows).most_common(12):
    print(f'  +0x108=0x{k:08X}: {c}')

print()
print('--- failing-package candidates (bootstrap / investment) ---')
for r in rows:
    nm = r['name'].lower()
    if 'bootstrap' in nm or 'investment' in nm or 'globals' in nm:
        print(f"  idx {r['idx']}: {r['name']} kind=0x{r['kind']:02X} f104=0x{r['f104']:X} f108=0x{r['f108']:X} tail=0x{r['tailval']:016X}")

print()
print('--- tail vs config field-4 diff (all rows) ---')
mism = []
missing_cfg = []
for r in rows:
    cv = cfg.get(r['name'])
    if cv is None:
        missing_cfg.append(r['name'])
        continue
    if cv != r['tailval']:
        mism.append((r['idx'], r['name'], r['tailval'], cv))
print('  exact matches:', n - len(mism) - len(missing_cfg))
print('  mismatches:', len(mism))
print('  not in config:', len(missing_cfg))
for idx, nm, tv, cv in mism:
    print(f'    idx {idx}: {nm} tail=0x{tv:016X} cfg=0x{cv:016X} xor=0x{tv ^ cv:016X}')
for nm in missing_cfg[:10]:
    print(f'    not-in-config: {nm}')

print()
print('--- row 0 recheck (the 1-bit diff from the earlier partial capture) ---')
r0 = rows[0]
print('  tail:', r0['tail'], 'cfg:', f"0x{cfg.get(r0['name'], 0):016X}", 'match:', cfg.get(r0['name']) == r0['tailval'])

print()
print('--- first/last 5 names ---')
for r in rows[:5] + rows[-5:]:
    print(f"  idx {r['idx']}: {r['name']}")
