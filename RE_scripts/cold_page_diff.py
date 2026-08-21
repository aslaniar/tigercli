import struct, sys, hashlib
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from diff_minidumps import read_minidump_regions, extract

BASE = 0x7FF641BF0000
A = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_healthy_inproc.dmp'
B = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_failing_external.dmp'
REF = r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\destiny2_unpacked_full.exe'
DISK = r'C:\Users\rasla\Downloads\destiny-preservation\dcv build\destiny2.exe'

CHAIN = [
    ('thunk_FUN_14480a10f', 0x14480a10f),
    ('FUN_14689840b', 0x14689840b),
    ('FUN_1453de4c4', 0x1453de4c4),
    ('FUN_147ffd25d', 0x147ffd25d),
]
TEXT2_VA = 0x03CC9000
TEXT2_RAW = 0x027B0000
SPAN = 0x1000

ra = read_minidump_regions(A)
rb = read_minidump_regions(B)
ref_img = open(REF, 'rb')
disk_img = open(DISK, 'rb')

def read_ref(off_img, size):
    ref_img.seek(off_img)
    return ref_img.read(size)

def read_disk(off_img, size):
    disk_img.seek(off_img)
    return disk_img.read(size)

for name, va_img in CHAIN:
    off_img = va_img - 0x140000000
    raw = TEXT2_RAW + (off_img - TEXT2_VA)
    runtime = BASE + off_img
    h = extract(A, ra, runtime - 0x800, SPAN)
    f = extract(B, rb, runtime - 0x800, SPAN)
    r = read_ref(raw - 0x800, SPAN)
    d = read_disk(raw - 0x800, SPAN)
    print(f'{name} (img 0x{va_img:X}, runtime 0x{runtime:X}, raw 0x{raw:X})')
    if h is None or f is None:
        print('  DUMP REGION MISSING: healthy', 'ok' if h else 'MISSING', '| failing', 'ok' if f else 'MISSING')
        continue
    hh = hashlib.sha256(h).hexdigest()[:12]
    ff = hashlib.sha256(f).hexdigest()[:12]
    rr = hashlib.sha256(r).hexdigest()[:12]
    dd = hashlib.sha256(d).hexdigest()[:12]
    print(f'  healthy sha {hh} | failing sha {ff} | ref(unpacked_full) sha {rr} | disk sha {dd}')
    print(f'  healthy vs failing  : {"IDENTICAL" if h == f else "DIFFER"}')
    print(f'  healthy vs ref      : {"IDENTICAL" if h == r else "DIFFER"}')
    print(f'  failing vs ref      : {"IDENTICAL" if f == r else "DIFFER"}')
    print(f'  healthy vs disk     : {"IDENTICAL (encrypted)" if h == d else "DIFFER (decrypted?)"}')
    print(f'  failing vs disk     : {"IDENTICAL (encrypted)" if f == d else "DIFFER (decrypted?)"}')
    print(f'  ref vs disk         : {"IDENTICAL (encrypted)" if r == d else "DIFFER (plaintext ref)"}')
    nz_h = sum(1 for b in h if b != 0)
    nz_f = sum(1 for b in f if b != 0)
    print(f'  nonzero bytes: healthy {nz_h}, failing {nz_f}, ref {sum(1 for b in r if b != 0)}, disk {sum(1 for b in d if b != 0)}')
    print(f'  first 16: healthy {h[:16].hex()} | failing {f[:16].hex()}')
    print()
