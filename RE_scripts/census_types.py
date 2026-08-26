"""Read the client's activity-message type-name table straight from the dump.

The table at .data 0x141f91ad0 is an array of char* indexed by wire type id
(Lane M 1a, consumed by getter 0x1404dc070). Pointers in this dump are LIVE
runtime addresses, so each is rebased before it is followed.
"""
import struct, sys
sys.path.insert(0, 'RE_scripts')

DUMP = 'RE_output/destiny2_unpacked_full.exe'
TABLE_VA = 0x141f91ad0
STATIC_BASE = 0x140000000
RUNTIME_BASE = 0x7FF6AF7F0000

data = open(DUMP, 'rb').read()
pe = struct.unpack_from('<I', data, 0x3c)[0]
nsec = struct.unpack_from('<H', data, pe + 6)[0]
optsz = struct.unpack_from('<H', data, pe + 20)[0]
tbl = pe + 24 + optsz

secs = []
for i in range(nsec):
    o = tbl + i * 40
    name = data[o:o+8].rstrip(b'\0').decode(errors='replace')
    vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', data, o + 8)
    secs.append((name, STATIC_BASE + va, vsize, rawptr, rawsize))

def off(va):
    for name, lo, vsize, rawptr, rawsize in secs:
        if lo <= va < lo + vsize:
            d = va - lo
            return rawptr + d if d < rawsize else None
    return None

def rebase(runtime_ptr):
    if runtime_ptr == 0:
        return 0
    return STATIC_BASE + (runtime_ptr - RUNTIME_BASE)

def cstr(va, cap=64):
    o = off(va)
    if o is None:
        return None
    end = data.find(b'\0', o, o + cap)
    if end < 0:
        return None
    s = data[o:end]
    try:
        t = s.decode('ascii')
    except UnicodeDecodeError:
        return None
    return t if t and all(32 <= ord(c) < 127 for c in t) else None

print("id   name")
print("---  ----")
base = off(TABLE_VA)
found = {}
for i in range(0, 96):
    o = base + i * 8
    ptr = struct.unpack_from('<Q', data, o)[0]
    s = cstr(rebase(ptr)) if ptr else None
    if s:
        found[i] = s
        print(f"{i:>3}  {s}")
print()
print(f"total named types: {len(found)}  (highest id {max(found) if found else '-'})")
