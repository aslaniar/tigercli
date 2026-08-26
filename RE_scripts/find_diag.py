"""Liveness diagnostics for the --find null result (2026-08-25).

For every bucket: how many (bucket, idx) slots yield a node, how many expand()
to a real total, and the min/max/median of those totals. If visited==0 the
walker never saw the heap; if expanded<<visited the expansion guard is dying;
if both are healthy the 29968 null is REAL (wrong target, not dead tool).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from minidump_reader import Minidump
from schema_walk import Schema, ENTRY_STRIDE


def main(dump_path):
    s = Schema(dump_path)
    print('registry 0x%X -> table 0x%X' % (s.registry, s.table))
    grand_nodes = 0
    grand_ok = 0
    all_totals = []
    for b in range(24):
        ent = s.entry_fields(b)
        if not ent['base'] or not ent['stride']:
            continue
        visited = 0
        ok = 0
        totals = []
        for idx in range(0x2000):
            node = s.node_at(ent, idx)
            if node is None:
                continue
            visited += 1
            t = s.expand(node, set(), 0)
            if t is not None:
                ok += 1
                totals.append(t)
        grand_nodes += visited
        grand_ok += ok
        all_totals.extend(totals)
        if visited or ent['stride'] >= 64:
            lo = min(totals) if totals else '-'
            hi = max(totals) if totals else '-'
            print('bucket %2d stride %4d: visited %5d  expanded %5d  '
                  'total range %s..%s' % (b, ent['stride'], visited, ok, lo, hi))
    all_totals.sort()
    n = len(all_totals)
    print('\nnodes seen: %d   expandable: %d   median total: %s'
          % (grand_nodes, grand_ok,
             all_totals[n // 2] if n else '-'))
    # Nearest totals to the old target, whatever they belong to.
    near = sorted(all_totals, key=lambda t: abs(t - 29968))[:8]
    print('closest expandable totals to 29968: %s' % near)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
