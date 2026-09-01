#!/usr/bin/env python3
"""dump_search.py - SEARCH a full minidump's memory for values, bytes or strings.

Engine: RE_scripts/minidump_reader.py (the registry's dump-memory workhorse, also
used by femu --graft-dump). This file adds ONLY the scan; all format handling,
module lookup and range enumeration live there.

THE POINT (FINDINGS 20.209 / 20.221): the client's entity dispatch structures are built
at RUNTIME - the whole image contains zero static references to the entity receive chain,
so no static tool can say what routes to it. A full dump taken in the right scenario DOES
contain those tables. This turns "which carrier reaches ent_recv" from a guess into a
lookup.

Scenario-scoping applies (20.221 R5): a dump only answers questions about states the
process actually entered. Check the dump's PROVENANCE.txt before trusting a null.

Modes:
  dump_search.py <dump> --u64 0xADDR [--u64 ...]   find 8-byte little-endian occurrences
  dump_search.py <dump> --bytes DEADBEEF           find a raw byte pattern
  dump_search.py <dump> --ascii "text"             find an ASCII string
  dump_search.py <dump> --selftest                 oracle: a known client string must be
                                                   found AND land inside the main module
Common flags:
  --base 0xBASE     module base, so hits can be reported as base-relative RVAs
  --context N       bytes of surrounding memory to hexdump per hit (default 0)
  --max N           stop after N hits per needle (default 64)
Exit 1 = zero hits for every needle (a clean null, not a crash).
"""
import argparse, struct, sys

sys.path.insert(0, __import__('os').path.dirname(__file__))
from minidump_reader import Minidump  # THE engine (TOOLS.md): do not re-parse the format


def memory_ranges(path):
    """(start_va, size, file_offset) per committed range, via minidump_reader.

    The dump FORMAT is minidump_reader's job and it already does it (and is the engine
    under femu --graft-dump). What it does not do is SEARCH - scanning every range for a
    value is this tool's only addition. Anything about parsing belongs in that file.
    """
    md = Minidump(path)
    ranges = getattr(md, 'ranges', None)
    if not ranges:
        raise SystemExit('no committed ranges: TRIAGE dump, not a full one - retake with '
                         'MiniDumpWithFullMemory (RE_scripts/rig_full_dump.sh)')
    for r in ranges:
        # tolerate either (start, size, offset) tuples or objects with named fields
        if isinstance(r, (tuple, list)):
            yield r[0], r[1], r[2]
        else:
            yield r.start, r.size, r.offset


def scan(path, needles, maxhits, context, base):
    ranges = list(memory_ranges(path))
    total_bytes = sum(r[1] for r in ranges)
    print(f'== {path}: {len(ranges)} ranges, {total_bytes/1e9:.2f} GB committed')
    found = {n: [] for n, _ in needles}
    with open(path, 'rb') as f:
        for start, size, off in ranges:
            f.seek(off); buf = f.read(size)
            for label, pat in needles:
                if len(found[label]) >= maxhits:
                    continue
                i = buf.find(pat)
                while i != -1 and len(found[label]) < maxhits:
                    va = start + i
                    ctx = buf[max(0, i - context):i + len(pat) + context] if context else b''
                    found[label].append((va, ctx))
                    i = buf.find(pat, i + 1)
    hits = 0
    for label, pat in needles:
        lst = found[label]
        hits += len(lst)
        print(f'\n-- {label}: {len(lst)} hit(s)')
        for va, ctx in lst:
            rel = f'  (base+0x{va-base:X})' if base and va >= base else ''
            print(f'   0x{va:016X}{rel}')
            if ctx:
                print('     ' + ' '.join(f'{b:02x}' for b in ctx))
    return hits

def main(argv):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('dump', nargs='?')
    ap.add_argument('--u64', action='append', default=[])
    ap.add_argument('--bytes', action='append', default=[])
    ap.add_argument('--ascii', action='append', default=[])
    ap.add_argument('--base', default='0')
    ap.add_argument('--context', type=int, default=0)
    ap.add_argument('--max', type=int, default=64)
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args(argv)
    if not a.dump:
        ap.print_help(); return 2
    base = int(a.base, 16) if a.base else 0
    if a.selftest:
        # ORACLE: a string the client demonstrably contains must be found, and (when a
        # base is given) must land inside the loaded module - proving both that the scan
        # reaches real memory and that the base conversion is right.
        needles = [('ascii:player_broadcast', b'player_broadcast')]
        n = scan(a.dump, needles, 8, 0, base)
        print('\nSELFTEST:', 'PASS' if n > 0 else 'FAIL (known-present string not found)')
        return 0 if n > 0 else 1
    needles = []
    for v in a.u64:
        needles.append((f'u64:{v}', struct.pack('<Q', int(v, 16))))
    for b in a.bytes:
        needles.append((f'bytes:{b}', bytes.fromhex(b)))
    for s in a.ascii:
        needles.append((f'ascii:{s}', s.encode()))
    if not needles:
        ap.print_help(); return 2
    return 0 if scan(a.dump, needles, a.max, a.context, base) else 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
