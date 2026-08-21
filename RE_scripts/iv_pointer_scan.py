# iv_pointer_scan.py -- scan both dumps for runtime pointers to the IV site and
# struct head. A mode-dependent pointer's owner names the writer.
import struct, sys, time
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from diff_minidumps import read_minidump_regions

BASE = 0x7FF641BF0000
A = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_healthy_inproc.dmp'
B = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_failing_external.dmp'

def le8(v):
    return struct.pack('<Q', v)

PATS = {
    'ptr->IV   (base+0x1F44CE0)': le8(BASE + 0x1F44CE0),
    'ptr->struct(base+0x1F44C00)': le8(BASE + 0x1F44C00),
    'ptr->+0xD8 (base+0x1F44CD8)': le8(BASE + 0x1F44CD8),
    'ptr->+0xF0 (base+0x1F44CF0)': le8(BASE + 0x1F44CF0),
    'ptr->const 0x141BCCAA0 runtime': le8(BASE + 0x1BCCAA0),
}

def scan(path, label):
    t0 = time.time()
    regions = read_minidump_regions(path)
    hits = {k: [] for k in PATS}
    f = open(path, 'rb')
    for start, sz, rva in regions:
        f.seek(rva)
        data = f.read(sz)
        for key, pat in PATS.items():
            i = data.find(pat)
            if i >= 0:
                hits[key].append((start + i, start + i - BASE))
    f.close()
    print('=== %s ===' % label)
    for key, lst in hits.items():
        print('  %s: %d hits' % (key, len(lst)))
        for va, off in lst[:20]:
            print('    runtime 0x%X (image off 0x%X)' % (va, off))
    print('  (%.1fs)' % (time.time() - t0))

scan(A, 'HEALTHY dump: pointers to IV/struct')
scan(B, 'FAILING dump: pointers to IV/struct')
