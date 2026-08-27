"""Is the .data pointer array around 0x141FA4180 indexed by MESSAGE TYPE?

FINDINGS 20.61 read the type-12 packed key 0x808086A8 through the global at
0x141FA4180. That global sits inside a stride-8 array of pointers into heap the
UNPACKED EXE DOES NOT CONTAIN - the pointers are live, so the read has to happen
against the minidump.

ORACLE, per the "give every reader something it can fail against" rule: a node
stores its own key at +0x08, so index 12 must come back 0x808086A8. Anything
else refutes the hypothesis and nothing below is usable.
"""
import struct
import sys

sys.path.insert(0, 'RE_scripts')
from minidump_reader import Minidump

DUMP = 'RE_output/content/dump_healthy_inproc.dmp'
STATIC_BASE = 0x140000000
ARRAY_VA = 0x141FA4180
KNOWN_TYPE = 12
KNOWN_KEY = 0x808086A8

md = Minidump(DUMP)
game = md.module('destiny2')
if game is None:
    raise SystemExit('destiny2.exe not in this dump')
base = game['base']
print(f"module base 0x{base:X}")

def rva(va):
    return va - STATIC_BASE

def u32(va):
    raw = md.read_va(va, 4)
    return None if raw is None or len(raw) < 4 else struct.unpack('<I', raw)[0]

def u64(va):
    raw = md.read_va(va, 8)
    return None if raw is None or len(raw) < 8 else struct.unpack('<Q', raw)[0]

def key_for_index(index, array_base_va):
    p = u64(base + rva(array_base_va) + index * 8)
    if not p:
        return None, None
    return u32(p + 0x00), p

ARRAY_BASE = ARRAY_VA - KNOWN_TYPE * 8
k, node = key_for_index(KNOWN_TYPE, ARRAY_BASE)
print(f"candidate array base 0x{ARRAY_BASE:X}")
print(f"ORACLE type {KNOWN_TYPE}: node=0x{(node or 0):X} key="
      + ("None" if k is None else f"0x{k:08X}")
      + f"  want 0x{KNOWN_KEY:08X}  -> "
      + ("MATCH" if k == KNOWN_KEY else "REFUTED"))

if k != KNOWN_KEY:
    # Legible refutation: what DOES the global's own node hold?
    p = u64(base + rva(ARRAY_VA))
    print(f"  global 0x{ARRAY_VA:X} -> 0x{(p or 0):X}")
    if p:
        for d in range(0, 0x20, 4):
            v = u32(p + d)
            print(f"    +0x{d:02X}: " + ("-" if v is None else f"0x{v:08X}"))
    # And which index in a +/-64 window, if any, yields the known key?
    hits = []
    for i in range(-64, 65):
        kk, _ = key_for_index(i, ARRAY_VA)
        if kk == KNOWN_KEY:
            hits.append(i)
    print(f"  offsets from 0x{ARRAY_VA:X} yielding the known key: {hits}")
    raise SystemExit(1)

print()
print("type  key")
for t in range(0, 59):
    kk, _ = key_for_index(t, ARRAY_BASE)
    print(f"{t:4d}  " + ("-" if kk is None else f"0x{kk:08X}"))
