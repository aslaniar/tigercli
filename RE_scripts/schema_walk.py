"""Walk the client's runtime schema registry out of a full-memory minidump.

The resolver formula is read verbatim from FUN_1404c1930 (static 0x1404c1930):

    index    = key & 0x1FFF
    hi       = key >> 13                     (arithmetic)
    bucket   = ((hi | 0xFFC0000) >> 18) & (uint16)hi
    entry    = *DAT_142439c70 + bucket*0x40
    resolved = *(entry+8) + *(entry+0x30)*index
    resolved-= *(resolved+8) & (int32)*(entry+0x34)
    node     = (resolved+0x48) + *(resolved+0x48)      -- relative; 0 means absent
    count    = *(uint32*)(node+0x14) + 1

Field entries follow W1 CLAIM 3: bitCount@+0x28, type@+0x30, presence@+0x31,
subKey@+0x34, width@+0x3C.

Usage:
  schema_walk.py <dump.dmp> --table [n]        first n registry entries, interpreted
  schema_walk.py <dump.dmp> --key <k>          resolve one packed key and list fields
"""
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from minidump_reader import Minidump

GLOBAL_RVA = 0x2439C70
# 0x28, read off FUN_1404bd2a0: `lea rax,[rbx+rbx*4]` with `[r14+rax*8]` is r14+rbx*40,
# and `inc rbx` advances one field per iteration. The field offsets (+0x28 bits, +0x30 type,
# +0x31 presence, +0x34 sub-key, +0x3C width) are relative to node+idx*0x28, so the entry
# body begins one stride in - which is why they appear to overflow a 40-byte record and do
# not. Using 0x40 here is what made the first calibration search find nothing.
ENTRY_STRIDE = 0x28
# The REGISTRY table's own stride, which is NOT the field-entry stride. FUN_1404c1930 does
# `shl rcx,6` before adding the table base, so registry entries are 0x40 apart while field
# entries are 0x28 apart. Conflating the two silently misreads every bucket the moment one
# of them is corrected.
REGISTRY_STRIDE = 0x40


class Schema:
    """Resolves packed schema keys against a dumped registry."""

    def __init__(self, dump_path):
        self.md = Minidump(dump_path)
        game = self.md.module('destiny2')
        if game is None:
            raise ValueError('destiny2.exe not in this dump')
        self.base = game['base']
        # TWO dereferences, per FUN_1404c1930:
        #   mov rax, [rip+X]      -> rax = *(0x142439C70)   the registry object
        #   add rcx, [rax]        -> table base = *(rax)
        # Reading only the first level gives a struct whose +0x30 is zero, which is what
        # made a 4096-bucket scan report no live entries at all.
        raw = self.md.read_va(self.base + GLOBAL_RVA, 8)
        if raw is None:
            raise ValueError('the registry global is not mapped in this dump')
        self.registry = struct.unpack('<Q', raw)[0]
        raw = self.md.read_va(self.registry, 8)
        if raw is None:
            raise ValueError('registry object 0x%X not mapped' % self.registry)
        self.table = struct.unpack('<Q', raw)[0]

    def u32(self, va):
        raw = self.md.read_va(va, 4)
        return None if raw is None or len(raw) < 4 else struct.unpack('<I', raw)[0]

    def i32(self, va):
        v = self.u32(va)
        return None if v is None else (v - (1 << 32) if v & 0x80000000 else v)

    def u64(self, va):
        raw = self.md.read_va(va, 8)
        return None if raw is None or len(raw) < 8 else struct.unpack('<Q', raw)[0]

    def bucket_of(self, key):
        hi = key >> 13
        if hi & 0x80000000:
            hi -= 1 << 32
        return ((hi | 0xFFC0000) >> 18) & (hi & 0xFFFF)

    def entry_fields(self, bucket):
        e = self.table + bucket * REGISTRY_STRIDE
        return {'va': e, 'base': self.u64(e + 8), 'stride': self.u32(e + 0x30),
                'mask': self.i32(e + 0x34)}

    def node_at(self, ent, idx):
        """@return Node VA for one registry entry + index, or None when absent."""
        resolved = ent['base'] + ent['stride'] * idx
        adj = self.u64(resolved + 8)
        if adj is None:
            return None
        resolved -= adj & (ent['mask'] & 0xFFFFFFFFFFFFFFFF)
        rel = self.u64(resolved + 0x48)
        if rel is None or rel == 0:
            return None
        return (resolved + 0x48 + rel) & 0xFFFFFFFFFFFFFFFF

    def expand(self, node, seen, depth):
        """Sums a schema's wire width with nested walks expanded.

        Field type 1 is a NESTED WALK through the sub-key at +0x34 (W1 CLAIM 3), so a
        schema's own entries do NOT sum to its message size - the first calibration search
        compared against an unexpanded total and matched nothing. The walker's own stack is
        4 deep, so that is the recursion bound.
        """
        if depth > 4 or node in seen:
            return None
        seen = seen | {node}
        count = self.u32(node + 0x14)
        if count is None or count > 4000:
            return None
        total = 0
        for f in range(count + 1):
            e = node + f * ENTRY_STRIDE
            bits = self.i32(e + 0x28)
            head = self.md.read_va(e + 0x30, 2)
            if bits is None or head is None or bits < 0 or bits > (1 << 20):
                return None
            ftype, presence = head[0], head[1]
            total += bits + (1 if presence else 0)
            if ftype == 1:
                sub = self.u32(e + 0x34)
                if sub:
                    child, _ = self.node_for(sub)
                    if child is not None:
                        inner = self.expand(child, seen, depth + 1)
                        if inner:
                            total += inner
        return total

    def node_for(self, key):
        """@return (node_va, field_count) or (None, reason)."""
        ent = self.entry_fields(self.bucket_of(key))
        if not ent['base'] or not ent['stride']:
            return None, 'registry entry empty (base=%s stride=%s)' % (ent['base'], ent['stride'])
        resolved = ent['base'] + ent['stride'] * (key & 0x1FFF)
        adj = self.u64(resolved + 8)
        if adj is None:
            return None, 'resolved 0x%X not mapped' % resolved
        resolved -= adj & (ent['mask'] & 0xFFFFFFFFFFFFFFFF)
        rel = self.u64(resolved + 0x48)
        if rel is None:
            return None, 'node slot at 0x%X not mapped' % (resolved + 0x48)
        if rel == 0:
            return None, 'node absent (relative pointer 0)'
        node = (resolved + 0x48 + rel) & 0xFFFFFFFFFFFFFFFF
        count = self.u32(node + 0x14)
        if count is None:
            return None, 'node 0x%X not mapped' % node
        return node, count + 1


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    s = Schema(sys.argv[1])
    print('registry 0x%X -> table 0x%X   (destiny2 base 0x%X)' % (s.registry, s.table, s.base))

    if '--table' in sys.argv:
        i = sys.argv.index('--table')
        n = int(sys.argv[i + 1], 0) if len(sys.argv) > i + 1 else 16
        print('\n%-4s %-18s %-18s %-10s %s' % ('idx', 'entry va', 'base', 'stride', 'mask'))
        live = 0
        for b in range(n):
            e = s.entry_fields(b)
            if e['base'] is None:
                print('%-4d %-18s NOT MAPPED' % (b, '0x%X' % e['va']))
                continue
            flag = ''
            if e['base'] and e['stride']:
                live += 1
                flag = '  <-- live'
            print('%-4d 0x%-16X 0x%-16X %-10s %s%s'
                  % (b, e['va'], e['base'], e['stride'], e['mask'], flag))
        print('\nlive registry entries in first %d: %d' % (n, live))
        return 0

    if '--node' in sys.argv:
        i = sys.argv.index('--node')
        b = int(sys.argv[i + 1], 0)
        idx = int(sys.argv[i + 2], 0)
        ent = s.entry_fields(b)
        print('bucket %d: base 0x%X stride %s mask %s' % (b, ent['base'] or 0, ent['stride'], ent['mask']))
        node = s.node_at(ent, idx)
        if node is None:
            print('  no node at idx %d' % idx)
            return 1
        count = s.u32(node + 0x14)
        print('  node 0x%X  count field=%s -> %d entries' % (node, count, (count or 0) + 1))
        total = 0
        for f in range(min((count or 0) + 1, 40)):
            e = node + f * ENTRY_STRIDE
            bits = s.i32(e + 0x28)
            head = s.md.read_va(e + 0x30, 2)
            width = s.u32(e + 0x3C)
            sub = s.u32(e + 0x34)
            if bits is None or head is None:
                print('    [%2d] not mapped' % f); break
            total += (bits or 0) + (1 if head[1] else 0)
            print('    [%2d] bits=%-7s type=%-4d presence=%-3d subkey=0x%-10X width=%s'
                  % (f, bits, head[0], head[1], sub or 0, width))
        print('  running total (unexpanded) = %d bits' % total)
        return 0

    if '--find' in sys.argv:
        i = sys.argv.index('--find')
        want = int(sys.argv[i + 1], 0)
        tol = int(sys.argv[i + 2], 0) if len(sys.argv) > i + 2 else 64
        buckets = int(sys.argv[i + 3], 0) if len(sys.argv) > i + 3 else 24
        print('\nscanning for a schema totalling %d bits (+/- %d), nested walks expanded, '
              'across %d buckets\n' % (want, tol, buckets))
        hits = 0
        for b in range(buckets):
            ent = s.entry_fields(b)
            if not ent['base'] or not ent['stride']:
                continue
            for idx in range(0, 0x2000):
                node = s.node_at(ent, idx)
                if node is None:
                    continue
                total = s.expand(node, set(), 0)
                if total is not None and abs(total - want) <= tol:
                    hits += 1
                    count = s.u32(node + 0x14)
                    print('  MATCH bucket=%d idx=%d node=0x%X fields=%d expanded=%d bits'
                          % (b, idx, node, (count or 0) + 1, total))
                    if hits >= 12:
                        return 0
        print('\nmatches: %d' % hits)
        return 0

    if '--key' in sys.argv:
        i = sys.argv.index('--key')
        key = int(sys.argv[i + 1], 0)
        node, info = s.node_for(key)
        if node is None:
            print('key 0x%X -> %s' % (key, info))
            return 1
        print('key 0x%X -> node 0x%X, %d fields' % (key, node, info))
        total = 0
        for idx in range(min(info, 400)):
            ent = node + idx * ENTRY_STRIDE
            bits = s.i32(ent + 0x28)
            raw = s.md.read_va(ent + 0x30, 2)
            if bits is None or raw is None:
                print('  [%3d] entry 0x%X not mapped' % (idx, ent))
                break
            ftype, presence = raw[0], raw[1]
            width = s.u32(ent + 0x3C)
            total += (bits or 0) + (1 if presence else 0)
            print('  [%3d] bits=%-6s type=%-3d presence=%-3d width=%s'
                  % (idx, bits, ftype, presence, width))
        print('  total bits (incl. presence) = %d' % total)
        return 0
    print(__doc__)
    return 1


if __name__ == '__main__':
    sys.exit(main())
