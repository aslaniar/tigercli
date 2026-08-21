# read_pe_regions.py -- read raw file bytes of destiny2_unpacked_full.exe at
# the decoder41-relevant RVAs (decoder code, schema pools, codec tables).
# Settles: are the Ghidra-map zeros a project artifact or genuine file zeros?
import struct, sys

PATH = r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\destiny2_unpacked_full.exe"

REGIONS = [
    ("type41 decoder code",       0x106E9E0, 0x60),
    ("type47 decoder code",       0x106E620, 0x60),
    ("pre-decoder zone (vtable?)",0x106E5F0, 0x30),
    ("type41 schema slot",        0x1C39320, 0x100),
    ("type47 schema slot",        0x1C31EC0, 0x100),
    ("schema band mid",           0x1C32000, 0x40),
    ("decode codec table",        0x1BCFC88, 0x80),
    ("encode codec table",        0x1BD0F10, 0x80),
    ("nsm schema slot",           0x1CA6A00, 0x80),
]

def main():
    with open(PATH, "rb") as f:
        data = f.read()
    print("file size: %d (0x%X)" % (len(data), len(data)))
    # PE headers
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[e_lfanew:e_lfanew+4] == b"PE\x00\x00", "not PE"
    nsec = struct.unpack_from("<H", data, e_lfanew + 6)[0]
    optsz = struct.unpack_from("<H", data, e_lfanew + 20)[0]
    sectab = e_lfanew + 24 + optsz
    secs = []
    for i in range(nsec):
        off = sectab + i * 40
        name = data[off:off+8].rstrip(b"\x00").decode("latin1")
        vsize, vaddr, rsize, roff = struct.unpack_from("<IIII", data, off + 8)
        secs.append((name, vaddr, vsize, roff, rsize))
    for name, vaddr, vsize, roff, rsize in secs:
        print("section %-8s va=0x%08X vsize=0x%X roff=0x%08X rsize=0x%X" % (name, vaddr, vsize, roff, rsize))

    def file_off(rva):
        for name, vaddr, vsize, roff, rsize in secs:
            if vaddr <= rva < vaddr + max(vsize, rsize):
                o = roff + (rva - vaddr)
                if o < len(data):
                    return o, name
        return None, None

    for tag, rva, n in REGIONS:
        o, sec = file_off(rva)
        print("\n===== %s rva=0x%X sec=%s fileoff=%s =====" % (tag, rva, sec, hex(o) if o is not None else "N/A"))
        if o is None:
            print("  (rva outside sections)")
            continue
        chunk = data[o:o+n]
        nonzero = sum(1 for b in chunk if b != 0)
        print("  nonzero bytes: %d/%d" % (nonzero, n))
        for off in range(0, len(chunk), 16):
            c = chunk[off:off+16]
            hexs = " ".join("%02x" % b for b in c)
            asc = "".join(chr(b) if 0x20 <= b < 0x7F else "." for b in c)
            print("  0x%06X  %-47s  %s" % (rva + off, hexs, asc))

if __name__ == "__main__":
    main()
