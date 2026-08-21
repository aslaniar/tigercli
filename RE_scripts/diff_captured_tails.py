import struct, sys
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\claims')
from s1_signature_diff import walk

b = open(r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\s1_config3.bin', 'rb').read()
top = walk(b)
rows = [v for f, wt, v in top if f == 3]
cfg = {}
for r in rows:
    fields = walk(r)
    name = sig = None
    for f, wt, v in fields:
        if f == 2:
            name = v.decode('utf-8', errors='replace')
        elif f == 4:
            sig = v
    if name:
        cfg[name] = sig
print('config rows:', len(cfg))

tails = {
    'w64_activities_0199_0': '9fe57c12e73f31ea',
    'w64_activities_0199_1': '832fdbbbaad75462',
    'w64_activities_0199_2': '9340040e94bc994b',
    'w64_activities_0199_3': 'ee593f6dbf3c15ec',
    'w64_activities_0199_4': '395a797f767df1f6',
    'w64_activities_0199_5': '1702a57d8d21f6d8',
}
print()
print(f'{"name":<28} {"tail LE u64":<20} {"config field-4":<20} match?')
for n, t in tails.items():
    tv = struct.unpack('<Q', bytes.fromhex(t))[0]
    cv = cfg.get(n)
    print(f'{n:<28} 0x{tv:016X} 0x{cv:016X} {tv == cv}')
