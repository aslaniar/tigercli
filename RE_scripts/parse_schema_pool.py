# parse_schema_pool.py -- parse the type-41/47 schema pool + codec tables from
# the RAW image file (destiny2_unpacked_full.exe). The Ghidra project map reads
# zeros for these regions (map artifact) but the file is the live-captured image
# with runtime pointers frozen in. Normalization base: 0x7FF6AF7F0000 (observed).
import struct

PATH = r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\destiny2_unpacked_full.exe"
BASE = 0x7FF6AF7F0000  # capture base (observed in domain brief); img_va = raw - BASE + 0x140000000
IMG = 0x140000000

SECS = []
with open(PATH, "rb") as f:
    data = f.read()
e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
nsec = struct.unpack_from("<H", data, e_lfanew + 6)[0]
optsz = struct.unpack_from("<H", data, e_lfanew + 20)[0]
sectab = e_lfanew + 24 + optsz
for i in range(nsec):
    off = sectab + i * 40
    name = data[off:off + 8].rstrip(b"\x00").decode("latin1")
    vsize, vaddr, rsize, roff = struct.unpack_from("<IIII", data, off + 8)
    SECS.append((name, vaddr, vsize, roff, rsize))


def file_off(rva):
    for name, vaddr, vsize, roff, rsize in SECS:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            o = roff + (rva - vaddr)
            if o < len(data):
                return o
    return None


def sec_of(rva):
    for name, vaddr, vsize, roff, rsize in SECS:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            return name
    return "?"


def rd(va, n):
    rva = va - IMG
    o = file_off(rva)
    if o is None:
        return None
    return data[o:o + n]


def norm(raw):
    if raw == 0:
        return "0"
    img = raw - BASE + IMG
    if 0x140000000 <= img < 0x149000000:
        return "IMG 0x%X [%s]" % (img, sec_of(img - IMG))
    return "HEAP 0x%X" % raw


def parse_fields(va, count, label):
    print("\n===== %s @ IMG 0x%X =====" % (label, va))
    for i in range(count):
        o = file_off(va - IMG + i * 0x20)
        if o is None or o + 0x20 > len(data):
            print("  (out of file)")
            break
        num, flags, d8, d9, size, cap, u14, ptr = struct.unpack_from("<IIbB2xIIIQ", data, o)
        if num == 0 and flags == 0 and size == 0 and cap == 0 and ptr == 0:
            print("  [%02d] TERMINATOR (num=0)" % i)
            break
        codec = flags & 0xF
        hi = flags & 0xF0
        print("  [%02d] num=%d flags=0x%02X (hi=0x%02X codec=%d) delta=%d present=%d size=0x%X cap=0x%X u14=0x%X ptr=%s"
              % (i, num, flags, hi, codec, d8, d9, size, cap, u14, norm(ptr)))
    else:
        print("  (no terminator in %d entries)" % count)


print("base for normalization: 0x%X" % BASE)

parse_fields(0x141C39320, 8, "type41 schema (decoder reference)")
parse_fields(0x141C392A0, 4, "pre-type41 area (nested schema for field2?)")
parse_fields(0x141C39480, 8, "post-type41 area")
parse_fields(0x141C31EC0, 8, "type47 schema (decoder reference)")

print("\n===== pointer band @ 0x141C32000 =====")
b = rd(0x141C32000, 0x40)
if b:
    for i in range(8):
        raw = struct.unpack_from("<Q", b, i * 8)[0]
        print("  0x141C320%02X: %s" % (i * 8, norm(raw)))

print("\n===== decode codec table 0x141BCFC88 (from file) =====")
b = rd(0x141BCFC88, 0x80)
if b:
    for i in range(16):
        raw = struct.unpack_from("<Q", b, i * 8)[0]
        print("  codec[%d] = %s" % (i, norm(raw) if raw else "0"))

print("\n===== encode codec table 0x141BD0F10 (from file) =====")
b = rd(0x141BD0F10, 0x80)
if b:
    for i in range(16):
        raw = struct.unpack_from("<Q", b, i * 8)[0]
        print("  codec[%d] = %s" % (i, norm(raw) if raw else "0"))

print("\n===== raw bytes 0x140391EFE..0x140391F20 (call-target delta check) =====")
b = rd(0x140391EFE, 0x22)
if b:
    print("  " + " ".join("%02x" % x for x in b))

print("\n===== raw bytes 0x140391A6E..0x140391A90 (2nd delta check) =====")
b = rd(0x140391A6E, 0x22)
if b:
    print("  " + " ".join("%02x" % x for x in b))
