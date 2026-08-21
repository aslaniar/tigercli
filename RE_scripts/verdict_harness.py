import json, struct, sys
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\claims')
from s1_signature_diff import walk

def load_table():
    rows = json.load(open(r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\full_package_table.json'))
    return rows

def load_config():
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
    return cfg

def failing_rows(table):
    out = []
    for r in table:
        nm = r['name'].lower()
        if 'bootstrap' in nm or ('investment_globals' in nm) or ('investment' in nm and 'globals' in nm):
            out.append(r)
    return out

def main():
    table = load_table()
    cfg = load_config()
    rows = failing_rows(table)
    print('failing-candidate rows:', len(rows))
    print()
    print(f'{"idx":<5} {"name":<48} {"id":<8} {"kind":<4} {"tail":<20} {"cfg sig match"}')
    for r in rows:
        tail = struct.unpack('<Q', bytes.fromhex(r['tail']))[0]
        c = cfg.get(r['name'])
        print(f"{r['idx']:<5} {r['name']:<48} 0x{r['f108']:04X} 0x{r['kind']:02X}  0x{tail:016X} {tail == c}")
    print()
    ids = sorted(set(r['f108'] for r in rows))
    print('distinct failing ids:', [hex(i) for i in ids])
    json.dump({'ids': [hex(i) for i in ids], 'rows': rows},
              open(r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\verdict_candidates.json', 'w'), indent=1)
    print('saved verdict_candidates.json')

if __name__ == '__main__':
    main()
