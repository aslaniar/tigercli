# decoder41c.py -- pass 3: (1) linear disasm of FUN_140E0F000 to pin the
# vtable+0x18 decoder call args (registers/stack); (2) dump the codec table
# DAT_141bcfc88 + decompile each codec; (3) decompile the protobuf primitives
# (varint reader, wire stores); (4) xrefs to the type-41/47 schema slots.
# Output: RE_output/content/decoder41_raw3.txt
from ghidra.app.decompiler import DecompInterface
import os

LOG = r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\decoder41_raw3.txt"
out = None
decomp = None

DECOMPILE = [
    (0x1403900F0, "varint/key reader (protobuf key)"),
    (0x140392230, "wire-0 varint store"),
    (0x140392010, "wire-1/5 fixed store"),
    (0x1403921F0, "wire-2 length-delimited store"),
    (0x140391F60, "packed-array element reader"),
    (0x140391A50, "submessage/array close"),
]


def log(s):
    out.write(s + "\n")
    out.flush()
    try:
        print(str(s)[:2500].encode("ascii", "replace").decode("ascii"))
    except Exception:
        pass


def addr_of(v):
    return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v)


def ensure_function(va):
    a = addr_of(va)
    f = getFunctionContaining(a)
    if f is not None and f.getEntryPoint().getOffset() == va:
        return f
    try:
        if getInstructionAt(a) is None:
            disassemble(a)
    except Exception:
        pass
    try:
        f = createFunction(a, None)
    except Exception:
        f = None
    if f is None:
        f = getFunctionContaining(a)
    return f


def decompile_fn(fn, tag):
    if fn is None:
        log("===== %s : NO FUNCTION" % tag)
        return
    ep = fn.getEntryPoint().getOffset()
    body = fn.getBody().getNumAddresses()
    log("===== %s %s @ 0x%X body=%dB" % (tag, fn.getName(), ep, body))
    try:
        res = decomp.decompileFunction(fn, 120, monitor)
        if res is not None and res.decompileCompleted():
            log(res.getDecompiledFunction().getC())
            log("")
        else:
            log("STATUS: " + (res.getErrorMessage() if res is not None else "null"))
    except Exception as e:
        log("ERROR: %s" % e)


def linear_asm(va, n_bytes, tag):
    log("===== ASM %s 0x%X..0x%X =====" % (tag, va, va + n_bytes))
    cur = addr_of(va)
    end = va + n_bytes
    lines = []
    while cur.getOffset() < end:
        ins = getInstructionAt(cur)
        if ins is None:
            try:
                disassemble(cur)
                ins = getInstructionAt(cur)
            except Exception:
                ins = None
        if ins is None:
            break
        lines.append("0x%08X  %s" % (ins.getAddress().getOffset(), ins.toString()))
        cur = ins.getAddress().add(ins.getLength())
    marks = []
    for i, s in enumerate(lines):
        if "CALL" in s.upper() and ("0x18" in s or "0x28" in s or "0x20" in s or "0x10" in s):
            marks.append(i)
    if marks:
        for m in marks:
            lo = max(0, m - 22)
            hi = min(len(lines), m + 4)
            log("-- context around %s --" % lines[m])
            for j in range(lo, hi):
                log(lines[j])
            log("")
    else:
        for s in lines:
            log(s)
    log("")


def dump_bytes(va, n, tag):
    a = addr_of(va)
    buf = bytearray(n)
    try:
        currentProgram.getMemory().getBytes(a, buf)
    except Exception as e:
        log("dump_bytes %s failed: %s" % (tag, e))
        return
    log("===== BYTES %s @ 0x%X n=%d =====" % (tag, va, n))
    for off in range(0, n, 16):
        chunk = buf[off:off + 16]
        hexs = " ".join("%02x" % b for b in chunk)
        asc = "".join(chr(b) if 0x20 <= b < 0x7F else "." for b in chunk)
        log("0x%06X  %-47s  %s" % (va + off, hexs, asc))
    log("")


def dump_codec_table():
    va = 0x141BCFC88
    buf = bytearray(0x80)
    currentProgram.getMemory().getBytes(addr_of(va), buf)
    log("===== codec table DAT_141bcfc88 (16 x 8B) =====")
    for i in range(16):
        v = int.from_bytes(buf[i * 8:i * 8 + 8], "little")
        log("codec[%d] = 0x%X" % (i, v))
    log("")
    for i in range(16):
        v = int.from_bytes(buf[i * 8:i * 8 + 8], "little")
        if v == 0 or not (0x140000000 <= v < 0x149000000):
            continue
        decompile_fn(ensure_function(v), "codec[%d]" % i)


def xrefs(va, tag):
    log("===== XREFS to 0x%X (%s) =====" % (va, tag))
    refs = currentProgram.getReferenceManager().getReferencesTo(addr_of(va))
    seen = set()
    for r in refs:
        fr = r.getFromAddress().getOffset()
        if fr in seen:
            continue
        seen.add(fr)
        f = getFunctionContaining(r.getFromAddress())
        log("  from 0x%X (%s) type=%s" % (fr, f.getName() if f else "?", r.getReferenceType()))
    if not seen:
        log("  (no static xrefs)")
    log("")


def main():
    global out, decomp
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    out = open(LOG, "w", encoding="utf-8")
    decomp = DecompInterface()
    decomp.openProgram(currentProgram)
    log("=== DECODER41 pass3: call-site regs + codec table + protobuf prims + schema xrefs ===")
    log("program: %s base=0x%X" % (currentProgram.getName(), currentProgram.getImageBase().getOffset()))

    linear_asm(0x140E0F000, 0x430, "FUN_140E0F000 full")

    dump_codec_table()

    for va, tag in DECOMPILE:
        decompile_fn(ensure_function(va), tag)

    xrefs(0x141C39320, "type41 schema slot")
    xrefs(0x141C31EC0, "type47 schema slot")
    xrefs(0x141BCFC88, "codec table")

    # surrounding data: before the pool and after
    dump_bytes(0x141C31000, 0xEC0, "pre-pool 0x141C31000..0x141C31EC0")
    dump_bytes(0x141C394C0, 0xB40, "post-pool 0x141C394C0..0x141C3A000")

    log("=== DECODER41-PASS3-COMPLETE ===")
    out.close()
    print("DONE")


main()
