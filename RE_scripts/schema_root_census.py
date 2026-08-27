"""Census the schema descriptors by shape, hunting message ROOTS.

A message root should look like type 12's: several fields with presence flags and
a real wire width. Children are bare scalars and arrays.

ORACLE: 0x808086A8 must resolve to a STRUCT of 9 fields. If it does not, the
scan is broken and nothing below is evidence.
"""
import struct
import sys

sys.path.insert(0, 'RE_scripts')
from schema_walk import Schema

DUMP = 'RE_output/content/dump_healthy_inproc.dmp'
ARRAY_LO = 0x7FF6443B4EE0
ARRAY_HI = 0x7FF6443D2560
STRIDE = 0x20
KNOWN = 0x808086A8

s = Schema(DUMP)
md = s.md

def u32(va):
    raw = md.read_va(va, 4)
    return None if raw is None or len(raw) < 4 else struct.unpack('<I', raw)[0]

def shape(key):
    node, info = s.node_for(key)
    if node is None:
        return None
    kind, n = s.node_shape(node)
    try:
        width = s.presence_bits(node)
    except Exception:
        width = None
    return kind, n, width

o = shape(KNOWN)
print(f"ORACLE 0x{KNOWN:08X} -> {o}   (want ('struct', 9, ...))")
if not o or o[0] != 'struct' or o[1] != 9:
    raise SystemExit("scan refuted by its own oracle; results discarded")

rows = []
va = ARRAY_LO
while va < ARRAY_HI:
    key = u32(va)
    if key is not None and 0x80800000 <= key <= 0x8080FFFF:
        sh = shape(key)
        if sh is not None:
            rows.append((key, va, sh[0], sh[1], sh[2]))
    va += STRIDE

print(f"resolved descriptors: {len(rows)}")
hist = {}
for _k, _v, kind, n, _w in rows:
    b = n if n is not None and n <= 12 else '13+'
    hist[(kind, b)] = hist.get((kind, b), 0) + 1
print("kind/field-count histogram:")
for k in sorted(hist, key=lambda x: (x[0], str(x[1]))):
    print(f"   {k[0]:6s} {str(k[1]):>4s}: {hist[k]}")

roots = [r for r in rows if r[2] == 'struct' and r[3] is not None and r[3] >= 5]
print(f"\ncandidate roots (struct, >=5 fields): {len(roots)}")
roots.sort(key=lambda r: -(r[4] or 0))
print("widest 30:")
for k, v, kind, n, w in roots[:30]:
    print(f"   0x{k:08X}  fields={n:3d}  width={w}")
