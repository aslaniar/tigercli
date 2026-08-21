# iv_blob_sources.py -- scan BOTH full dumps for the kind0 IV blobs and their
# pieces. If the failing value was memcpy'd from another buffer, that source
# (with the same bytes) exists elsewhere in the failing dump. Same for healthy.
import struct, sys, time
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from diff_minidumps import read_minidump_regions, extract

BASE = 0x7FF641BF0000
A = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_healthy_inproc.dmp'
B = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_failing_external.dmp'

HEALTHY = bytes.fromhex('d62ab2c10cc01bc535db7b8655c7dc3b')
FAILING = bytes.fromhex('d62ab2c1f5dc168d3fdb7b8655c7dc3b')
MID_H = bytes.fromhex('0cc01bc535db7b86')
MID_F = bytes.fromhex('f5dc168d3fdb7b86')
PREFIX = bytes.fromhex('d62ab2c1')
SUFFIX = bytes.fromhex('55c7dc3b')

def iter_region_data(path, regions, chunk=1 << 26):
    """Yield (base_va, bytes) per region, chunked."""
    f = open(path, 'rb')
    for start, sz, rva in regions:
        f.seek(rva)
        remain = sz
        while remain > 0:
            n = min(remain, chunk)
            data = f.read(n)
            if not data:
                break
            yield start + (sz - remain), data
            remain -= n
    f.close()

def scan(path, label, pats, skip_va=None):
    t0 = time.time()
    regions = read_minidump_regions(path)
    hits = {k: [] for k in pats}
    for base, data in iter_region_data(path, regions):
        for key, pat in pats.items():
            start = 0
            while True:
                i = data.find(pat, start)
                if i < 0:
                    break
                va = base + i
                off = va - BASE
                if skip_va is not None and abs(va - skip_va) < 0x1000:
                    start = i + 1
                    continue
                hits[key].append((va, off))
                start = i + 1
    print('=== %s ===' % label)
    for key, lst in hits.items():
        print('  %s: %d hits' % (key, len(lst)))
        for va, off in lst[:40]:
            print('    runtime 0x%X  (image offset 0x%X)' % (va, off))
    print('  (%.1fs)' % (time.time() - t0))
    return hits

# skip the IV's own region (the known location) to find OTHER occurrences
scan(A, 'HEALTHY dump (excluding IV site)', {'healthy16': HEALTHY, 'mid_h8': MID_H, 'prefix4': PREFIX, 'suffix4': SUFFIX}, skip_va=BASE + 0x1F44CE0)
scan(B, 'FAILING dump (excluding IV site)', {'failing16': FAILING, 'mid_f8': MID_F, 'prefix4': PREFIX, 'suffix4': SUFFIX}, skip_va=BASE + 0x1F44CE0)
