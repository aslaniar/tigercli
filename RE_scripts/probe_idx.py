import struct
import sys

sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\scripts')
from schema_walk import Schema

DUMP = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_healthy_inproc.dmp'
s = Schema(DUMP)

# collect live buckets
live = []
for bkt in range(16384):
    ent = s.entry_fields(bkt)
    if ent['base'] and ent['stride']:
        live.append(bkt)
print('live buckets: %d' % len(live))

IDX = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x6A8
print('probing idx %#x across live buckets:' % IDX)
hits = []
for bkt in live:
    node = s.node_at(s.entry_fields(bkt), IDX)
    if node is None:
        continue
    # plausibility: node must be heap, and count field sane
    cnt = s.u32(node + 0x14)
    ok = node is not None and 0x18CD0000000 <= node < 0x19000000000 \
        and cnt is not None and cnt < 4000
    hits.append((bkt, node, cnt, ok))
for bkt, node, cnt, ok in hits:
    print('  bucket %5d -> node %#x count=%s %s'
          % (bkt, node, cnt, 'PLAUSIBLE' if ok else ''))
print('total non-absent: %d, plausible: %d'
      % (len(hits), sum(1 for h in hits if h[3])))
