import ctypes, struct, sys, json, time
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from dump_sunrise_memory import find_pid, open_process, read_memory

pid = find_pid('destiny2.exe')
if not pid:
    print('no game')
    sys.exit(1)
base = 0x7FF641BF0000
handle = open_process(pid)
print('pid', pid, 'base', hex(base))

def r64(a):
    try:
        d = read_memory(handle, a, 8)
    except Exception:
        return None
    return struct.unpack('<Q', d)[0] if d and len(d) == 8 else None

def va(a):
    return base + (a - 0x140000000)

print('globals now:')
for g, n in [(0x141F916D8, 'orig'), (0x141F916E0, 'compacted'), (0x141F916E8, 'compacted_count'),
             (0x141F916F0, 'aux'), (0x141F916F8, 'aux_count')]:
    v = r64(va(g))
    print(f'  {n} ({hex(g)}):', hex(v) if v else 'NULL')

FREED = 0x204B879C580
print('freed table @', hex(FREED))
rows = []
for i in range(2199):
    off = FREED + i * 0x118
    row = read_memory(handle, off, 0x118)
    if not row or len(row) < 0x118:
        print(f'  row {i}: unreadable (stopping at {i})')
        break
    name = row[4:44].split(b'\x00')[0].decode('ascii', 'replace')
    rows.append({
        'idx': i,
        'marker': struct.unpack_from('<I', row, 0)[0],
        'name': name,
        'f104': struct.unpack_from('<I', row, 0x104)[0],
        'f108': struct.unpack_from('<I', row, 0x108)[0],
        'kind': row[0x10C],
        'tail': row[0x110:0x118].hex(),
    })
print('rows readable:', len(rows))
if rows:
    with open(r'RE_output\content\freed_table_reread.json', 'w') as f:
        json.dump(rows, f, indent=1)
    print('wrote freed_table_reread.json')
    print('first 3:', json.dumps(rows[:3])[:400])
    print('last 3 names:', [r['name'] for r in rows[-3:]])
