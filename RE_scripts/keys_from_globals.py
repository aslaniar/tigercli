import struct
import sys

sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\scripts')
from minidump_reader import Minidump
from schema_walk import Schema, ENTRY_STRIDE

DUMP = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_healthy_inproc.dmp'
GLOBS = [0x141fa0030, 0x141fa01c0, 0x141fa0760, 0x141fa09d0, 0x141fa0a10,
         0x141fa2e80, 0x141fa32e0, 0x141fa3ec8, 0x141fa3f88, 0x141fa3fa8,
         0x141fa4010, 0x141fa4028, 0x141fa4180, 0x141fa41a0, 0x141fa41b0,
         0x141fa4530, 0x14204a1a8, 0x14204a328, 0x14204a348, 0x14204a3f8,
         0x14204fc60, 0x14204fcb0, 0x14206af00, 0x14206af20, 0x14206af38,
         0x14206af40, 0x14206af90, 0x14206afc8, 0x1420822e0, 0x14209ed00,
         0x14209ed28]

md = Minidump(DUMP)
s = Schema(DUMP)
b = s.base
print('registry 0x%X -> table 0x%X' % (s.registry, s.table))
seen = set()
for g in GLOBS:
    gva = b + (g - 0x140000000)
    raw = md.read_va(gva, 8)
    if not raw:
        print('%#x global unmapped' % g)
        continue
    ptr = struct.unpack('<Q', raw)[0]
    kraw = md.read_va(ptr, 4) if ptr > 0x10000 else None
    if not kraw:
        print('%#x -> ptr %#x UNMAPPED' % (g, ptr))
        continue
    key = struct.unpack('<I', kraw)[0]
    if key == 0 or key in seen:
        continue
    seen.add(key)
    node, info = s.node_for(key)
    if node is None:
        print('%#x key=%#010x -> FAIL (%s)' % (g, key, info))
    else:
        print('%#x key=%#010x -> NODE %#x fields=%d' % (g, key, node, info))
        total = 0
        for i in range(min(info, 48)):
            e = node + i * ENTRY_STRIDE
            bits = s.i32(e + 0x28)
            head = s.md.read_va(e + 0x30, 2)
            w = s.u32(e + 0x3C)
            sub = s.u32(e + 0x34)
            if bits is None or head is None:
                break
            total += bits + (1 if head[1] else 0)
            print('   [%2d] bits=%-7d type=%-3d presence=%-3d sub=0x%-6X width=%s'
                  % (i, bits, head[0], head[1], sub or 0, w))
        print('   top-level total = %d bits' % total)
