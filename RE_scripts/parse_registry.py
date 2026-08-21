# parse_registry.py -- from the RAW image file (live-captured), parse:
# (1) DAT_14280E3E0: the 308-qword decoder registry (runtime pointers frozen in)
# (2) the 15-object push table at 0x141C26E28 (0x30 stride): q0 type-getter stub
#     bytes -> the handled type ids; q4 decode-fail; q5 apply
# Normalization: img_va = raw - 0x7FF6AF7F0000 + 0x140000000
import struct

PATH = r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\destiny2_unpacked_full.exe"
BASE = 0x7FF6AF7F0000
IMG = 0x140000000

with open(PATH, "rb") as f:
    data = f.read()

def file_off(rva):
    # sections from PE
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, e_lfanew + 6)[0]
    optsz = struct.unpack_from("<H", data, e_lfanew + 20)[0]
    sectab = e_lfanew + 24 + optsz
    for i in range(nsec):
        off = sectab + i * 40
        name = data[off:off + 8].rstrip(b"\x00").decode("latin1")
        vsize, vaddr, rsize, roff = struct.unpack_from("<IIII", data, off + 8)
        if vaddr <= rva < vaddr + max(vsize, rsize):
            o = roff + (rva - vaddr)
            if o < len(data):
                return o
    return None

def rd(va, n):
    o = file_off(va - IMG)
    return data[o:o + n] if o is not None else None

def norm(raw):
    if raw == 0:
        return 0
    img = raw - BASE + IMG
    if 0x140000000 <= img < 0x149000000:
        return img
    return None  # heap/outside

def stub_type(va):
    """read the type-getter stub bytes: B8 imm32 C3 (mov eax,imm; ret) -> imm"""
    b = rd(va, 8)
    if not b:
        return None, None
    if b[0] == 0xB8 and b[5] == 0xC3:
        return struct.unpack_from("<I", b, 1)[0], "B8 imm32 C3"
    if b[0] == 0xE9:  # jmp rel32 -> follow
        t = va + 5 + struct.unpack_from("<i", b, 1)[0]
        return stub_type(t & 0xFFFFFFFF)
    return None, " ".join("%02x" % x for x in b[:8])

print("===== 15-object push table @ 0x141C26E28 (0x30 stride) =====")
for i in range(15):
    va = 0x141C26E28 + i * 0x30
    b = rd(va, 0x30)
    if not b:
        print("[%02d] (no data)" % i)
        continue
    q = struct.unpack_from("<6Q", b, 0)
    qn = [norm(x) for x in q]
    tid, how = None, None
    if qn[0]:
        tid, how = stub_type(qn[0])
    print("[%02d] q0=0x%08X(%s%s) q1=0x%08X q2=0x%08X q3=0x%08X q4=0x%08X q5=0x%08X"
          % (i, q[0], ("type=%d " % tid) if tid is not None else "", how or ("img=0x%X" % qn[0]) if qn[0] else "0",
             q[1], q[2], q[3], q[4], q[5]))
    if qn[1]:
        print("       q1 -> img 0x%X ; q4(decode-fail) -> img 0x%X ; q5(apply) -> img 0x%X"
              % (qn[1], qn[4] or 0, qn[5] or 0))

print("\n===== decoder registry DAT_14280E3E0 (first 60 of 308) =====")
b = rd(0x14280E3E0, 308 * 8)
for t in range(60):
    raw = struct.unpack_from("<Q", b, t * 8)[0]
    img = norm(raw)
    if img:
        print("type %3d: state obj img 0x%X" % (t, img))
print("... (rest parsed for vtable chain below)")

print("\n===== state-object vtable chain (registry -> obj.q0=vtable -> +0x18 decoder) =====")
for t in range(308):
    raw = struct.unpack_from("<Q", b, t * 8)[0]
    img = norm(raw)
    if not img:
        continue
    ob = rd(img, 0x20)
    if not ob:
        continue
    vt_raw = struct.unpack_from("<Q", ob, 0)[0]
    vt = norm(vt_raw)
    dec = None
    if vt:
        vb = rd(vt, 0x30)
        if vb:
            dec_raw = struct.unpack_from("<Q", vb, 0x18)[0]
            dec = norm(dec_raw)
    if dec:
        print("type %3d: obj=0x%X vtable=0x%X decoder(vt+0x18)=0x%X" % (t, img, vt, dec))
