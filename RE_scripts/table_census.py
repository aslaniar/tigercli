import struct
import sys

sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\scripts')
from schema_walk import Schema

DUMP = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_healthy_inproc.dmp'
s = Schema(DUMP)
print('table 0x%X' % s.table)
live = []
for bkt in range(16384):
    ent = s.entry_fields(bkt)
    if ent['base'] and ent['stride']:
        live.append((bkt, ent['base'], ent['stride']))
print('live buckets in 0..16383: %d' % len(live))
for bkt, bse, st in live[:60]:
    print('  bucket %5d base %#x stride %d' % (bkt, bse, st))
if len(live) > 60:
    print('  ...')
    for bkt, bse, st in live[-10:]:
        print('  bucket %5d base %#x stride %d' % (bkt, bse, st))
