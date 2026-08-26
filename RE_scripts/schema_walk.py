"""Walk the client's runtime schema registry out of a full-memory minidump.

The resolver formula is read verbatim from FUN_1404c1930 (static 0x1404c1930):

    index    = key & 0x1FFF
    hi       = key >> 13                     (arithmetic)
    bucket   = ((hi | 0xFFC0000) >> 18) & (uint16)hi
    entry    = *DAT_142439c70 + bucket*0x40
    resolved = *(entry+8) + *(entry+0x30)*index
    resolved-= *(resolved+8) & (int32)*(entry+0x34)
    node     = (resolved+0x48) + *(resolved+0x48)      -- relative; 0 means absent
    key      = *(uint32*)(node+0x08)                  -- the node names itself
    count    = *(int32*)(node+0x18) if > 0 else *(uint64*)node   (FUN_1404bd2a0)

All of the pointer arithmetic above is modular: the index scale is a 32-bit imul
and the adjustment subtract is a 64-bit sub that routinely borrows.

Field entries follow W1 CLAIM 3: bitCount@+0x28, type@+0x30, presence@+0x31,
subKey@+0x34, width@+0x3C.

Usage:
  schema_walk.py <dump.dmp> --table [n]        first n registry entries, interpreted
  schema_walk.py <dump.dmp> --key <k>          resolve one packed key and list fields
  schema_walk.py <dump.dmp> --tree <k> [depth] resolve a key and expand nested walks
  schema_walk.py <dump.dmp> --find <bits> [tol] [lo] [hi]   search by wire width

Registry population (census, 2026-08-25): 6,765 self-verifying nodes, ALL in
buckets 1024..1028. Buckets 0..23 hold none - anything that looks live there is
heap noise.
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
        """Mirrors `sar esi,0xd` in FUN_1404c1930 (and the identical sequence at
        FUN_1404c72e0+0x39, which is where the type-12 walk actually enters).

        `sar` on a 32-bit register shifts the value right by 13 and fills the
        THIRTEEN VACATED HIGH BITS - 31..19 - with the key's sign bit. `key >> 13`
        in Python already places the surviving bits at 18..0, so the sign fill is
        `0xFFF80000`. An earlier version used `0xFFFFE000`, which fills from bit 13
        and so overwrites bits 18..13 - six real key bits - putting every high-bit
        key eight thousand buckets away from its own data. That is what produced
        the "no key resolves" wall: the arithmetic, not the dump.

        Note `movzx eax, si` keeps only the LOW 16 bits of the shifted value, so
        bits 31..29 of the key never reach the bucket. The bucket is therefore NOT
        a lossless encoding of the key and `(bucket << 13) | idx` does NOT
        reconstruct it - read the key back from node+0x08 instead (see node_for)."""
        key &= 0xFFFFFFFF
        hi = key >> 13           # the low 19 bits of the sar result
        if key & 0x80000000:     # sar copied the KEY's sign bit into bits 31..19
            hi |= 0xFFF80000
        return (((hi | 0xFFC0000) & 0xFFFFFFFFFFFFFFFF) >> 18) & (hi & 0xFFFF)

    def entry_fields(self, bucket):
        e = self.table + bucket * REGISTRY_STRIDE
        return {'va': e, 'base': self.u64(e + 8), 'stride': self.u32(e + 0x30),
                'mask': self.i32(e + 0x34)}

    def node_at(self, ent, idx):
        """@return Node VA for one registry entry + index, or None when absent.

        Every arithmetic step here wraps the way the hardware does. `imul eax,edi`
        is a 32-bit multiply and `sub rax,rcx` is 64-bit modular, and the stored
        adjustment at slot+8 is routinely LARGER than the slot address - in Python
        that silently yields a negative VA, which read_va then reports as "not
        mapped". Every node in a live bucket looked absent for that reason alone."""
        resolved = ent['base'] + ((ent['stride'] * idx) & 0xFFFFFFFF)
        adj = self.u64(resolved + 8)
        if adj is None:
            return None
        resolved = (resolved - (adj & (ent['mask'] & 0xFFFFFFFFFFFFFFFF))) & 0xFFFFFFFFFFFFFFFF
        rel = self.u64(resolved + 0x48)
        if rel is None or rel == 0:
            return None
        return (resolved + 0x48 + rel) & 0xFFFFFFFFFFFFFFFF

    def node_shape(self, node):
        """@return ('struct'|'array', count) - THERE ARE TWO KINDS OF NODE.

        FUN_1404bd2a0's prologue picks the count:

            movsxd rdx,[rcx+0x18] ; test edx,edx ; setg al   ; al = kind flag
            mov rax,rdx ; jne .keep ; mov rax,[rcx]          ; limit

        and its loop then branches on that SAME saved flag:

          flag 0 - STRUCT. `lea rax,[rbx+rbx*4]` / `[r14+rax*8+0x31]`, i.e. one
                   0x28-byte record per field at node + 0x28 + i*0x28. Count is
                   *(u64*)node.
          flag 1 - ARRAY (branch 0x1404bd525). ONE element descriptor, read at a
                   FIXED offset, whose three dwords at +0x20/+0x24/+0x28 are then
                   `imul`-ed by the loop index. Count is node+0x18 and it is an
                   ELEMENT count, not a field count.

        Reading an array node as a struct walks the index-scaling dwords as if they
        were field records and yields pure noise - which is what made 0x808086A9
        (a 32-slot member array) look like 32 garbage fields.

        The dword at node+0x14 is neither count: it is the message's TOTAL BIT SIZE
        (1000 for type-12, whose own field offsets 992..999 sit inside it)."""
        n = self.i32(node + 0x18)
        if n is not None and n > 0:
            return 'array', n
        return 'struct', self.u64(node)

    def field_count(self, node):
        """@return the number of records to walk at node + 0x28 + i*0x28.

        An array node has exactly ONE such record however many elements it holds."""
        kind, n = self.node_shape(node)
        return 1 if kind == 'array' else n

    def elem_bits(self, node):
        """An array element's bit stride, at node+0x28 - the dword the loop scales
        by the index. 31 for the type-12 member row, x32 slots = its 992 bits."""
        return self.i32(node + 0x28)

    def node_key(self, node):
        """The node stores its own packed key at +0x08. This is the anchor that
        makes a resolution self-verifying: if it does not equal the key asked for,
        the walk landed on the wrong record."""
        return self.u32(node + 8)

    def total_bits(self, node):
        """@return the schema's wire width in bits, which the node STATES at +0x14.

        1000 for type-12, 992 for its 32-slot roster, 31 for a member row, 3 for
        the trailer - each consistent with its children. This is what `expand()`
        below was built to reconstruct, and it was never necessary."""
        return self.u32(node + 0x14)

    def expand(self, node, seen, depth):
        """SUPERSEDED by total_bits() - kept only because find_diag.py calls it.

        DO NOT use this to identify a schema by width. It sums the per-field dword
        at +0x28, which is NOT a per-field size: for a struct it is the field's bit
        OFFSET (type-12's are 0, 992, 996..999 inside a 1000-bit message) and for
        an array it is the element stride. Summing offsets is meaningless, which is
        why an exact --find on a schema whose width we already knew returned zero
        matches. Read +0x14 instead.

        Original (incorrect) intent follows.

        Sums a schema's wire width with nested walks expanded.

        Field type 1 is a NESTED WALK through the sub-key at +0x34 (W1 CLAIM 3), so a
        schema's own entries do NOT sum to its message size - the first calibration search
        compared against an unexpanded total and matched nothing. The walker's own stack is
        4 deep, so that is the recursion bound.
        """
        if depth > 4 or node in seen:
            return None
        seen = seen | {node}
        kind, n = self.node_shape(node)
        if n is None or n > 4000:
            return None
        count = self.field_count(node)
        total = 0
        for f in range(count):
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
        # An array's single record describes every element; the loop scales it.
        return total * n if kind == 'array' else total

    def node_for(self, key):
        """@return (node_va, field_count) or (None, reason).

        The resolution is checked against the key the node carries at +0x08, so a
        hit is proof rather than a plausible-looking address."""
        ent = self.entry_fields(self.bucket_of(key))
        if not ent['base'] or not ent['stride']:
            return None, 'registry entry empty (base=%s stride=%s)' % (ent['base'], ent['stride'])
        node = self.node_at(ent, key & 0x1FFF)
        if node is None:
            return None, 'node absent'
        kind, count = self.node_shape(node)
        if count is None:
            return None, 'node 0x%X not mapped' % node
        got = self.node_key(node)
        if got != key:
            return None, 'node 0x%X carries key 0x%X, not 0x%X' % (node, got or 0, key)
        return node, self.field_count(node)


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
        count = s.field_count(node)
        print('  node 0x%X  key=0x%X  fields=%s'
              % (node, s.node_key(node) or 0, count))
        total = 0
        for f in range(min(count or 0, 40)):
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
        # THE SCHEMA REGISTRY LIVES IN BUCKETS 1024..1028 AND NOWHERE ELSE.
        # Census over 0..1199: 6,765 self-verifying nodes, all of them in those
        # five buckets, ZERO in 0..23. An earlier default of `24` scanned exactly
        # the range that holds none of them, and an earlier census read the low
        # buckets' heap noise as "the only populated ones" and the real range as
        # false positives - it had the picture precisely backwards.
        lo = int(sys.argv[i + 3], 0) if len(sys.argv) > i + 3 else 1024
        hi = int(sys.argv[i + 4], 0) if len(sys.argv) > i + 4 else 1029
        print('\nscanning for a schema whose stated width is %d bits (+/- %d), '
              'across buckets %d..%d\n' % (want, tol, lo, hi - 1))
        hits = 0
        for b in range(lo, hi):
            ent = s.entry_fields(b)
            if not ent['base'] or not ent['stride']:
                continue
            for idx in range(0, 0x2000):
                node = s.node_at(ent, idx)
                if node is None:
                    continue
                # The node states its own wire width; do not re-derive it.
                key = s.node_key(node)
                if key is None or (key & 0x1FFF) != idx or s.bucket_of(key) != b:
                    continue                      # not a real node in this slot
                total = s.total_bits(node)
                if total is not None and abs(total - want) <= tol:
                    hits += 1
                    count = s.field_count(node)
                    # movzx drops key bits 31..29 on the way to the bucket, so the
                    # bucket cannot be inverted back into a key. The node stores its
                    # own key at +0x08; that is the only honest source.
                    kind, n = s.node_shape(node)
                    print('  MATCH bucket=%d idx=%d key=0x%08X node=0x%X %s(%d) '
                          '%d bits'
                          % (b, idx, key, node, kind, n, total))
                    if hits >= 12:
                        return 0
        print('\nmatches: %d' % hits)
        return 0

    if '--tree' in sys.argv:
        i = sys.argv.index('--tree')
        key = int(sys.argv[i + 1], 0)
        maxdepth = int(sys.argv[i + 2], 0) if len(sys.argv) > i + 2 else 3

        def walk(k, depth, seen):
            pad = '  ' * depth
            node, info = s.node_for(k)
            if node is None:
                print('%s0x%08X -> %s' % (pad, k, info))
                return
            if k in seen:
                print('%s0x%08X -> node 0x%X (already expanded above)' % (pad, k, node))
                return
            seen.add(k)
            kind, n = s.node_shape(node)
            if kind == 'array':
                print('%s0x%08X  node=0x%X ARRAY of %d x %s bits total_bits=%s'
                      % (pad, k, node, n, s.elem_bits(node), s.u32(node + 0x14)))
            else:
                print('%s0x%08X  node=0x%X struct, %d fields total_bits=%s'
                      % (pad, k, node, n, s.u32(node + 0x14)))
            for f in range(info):
                e = node + f * ENTRY_STRIDE
                bits = s.i32(e + 0x28)
                head = s.md.read_va(e + 0x30, 2)
                if bits is None or head is None:
                    print('%s  [%d] not mapped' % (pad, f))
                    break
                ftype, pres = head[0], head[1]
                sub = s.u32(e + 0x34)
                print('%s  %s bits=%-6d type=%-3d presence=%d width=%-5s sub=%s'
                      % (pad, '[elem]' if kind == 'array' else '[%d]' % f,
                         bits, ftype, pres, s.u32(e + 0x3C),
                         '0x%08X' % sub if sub not in (None, 0, 0xFFFFFFFF) else '-'))
                # Type 1 is a nested walk through the sub-key (W1 CLAIM 3).
                if ftype == 1 and sub not in (None, 0, 0xFFFFFFFF) and depth < maxdepth:
                    walk(sub, depth + 2, seen)

        walk(key, 0, set())
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
