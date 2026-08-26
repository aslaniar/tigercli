"""Read W1 OPEN #6's two global packed keys out of the full-memory dump and
resolve them through the registry (2026-08-25).

Static VAs from schema-walker-grammar.md CLAIM 2: *DAT_14204e7b8 and
*DAT_14204ee38 feed FUN_1409f4cd0's walks. Rebased here onto the dump's own
destiny2 base, read as u32 keys, then resolved with Schema.node_for().
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from minidump_reader import Minidump
from schema_walk import Schema, ENTRY_STRIDE

KEYS = [("DAT_14204e7b8", 0x14204E7B8), ("DAT_14204ee38", 0x14204EE38)]


def main(dump_path):
    md = Minidump(dump_path)
    s = Schema(dump_path)
    base = s.base
    print('registry 0x%X -> table 0x%X   (destiny2 base 0x%X)'
          % (s.registry, s.table, base))
    for name, static_va in KEYS:
        va = base + (static_va - 0x140000000)
        raw = md.read_va(va, 4)
        if raw is None:
            print('%s @%X: NOT MAPPED' % (name, va))
            continue
        key = int.from_bytes(raw, 'little')
        print('%s @runtime %#X = %#010x' % (name, va, key))
        if not key:
            continue
        node, info = s.node_for(key)
        if node is None:
            print('  resolve FAILED: %s' % info)
            continue
        count = info
        total = 0
        print('  resolved -> node 0x%X, %d fields' % (node, count))
        for idx in range(min(count, 60)):
            e = node + idx * ENTRY_STRIDE
            bits = s.i32(e + 0x28)
            head = s.md.read_va(e + 0x30, 2)
            width = s.u32(e + 0x3C)
            sub = s.u32(e + 0x34)
            if bits is None or head is None:
                print('    [%2d] unmapped' % idx)
                break
            total += bits + (1 if head[1] else 0)
            print('    [%2d] bits=%-7d type=%-3d presence=%-3d sub=0x%-6X width=%s'
                  % (idx, bits, head[0], head[1], sub or 0, width))
        print('  top-level total = %d bits' % total)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
