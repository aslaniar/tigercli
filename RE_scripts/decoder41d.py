# decoder41d.py -- pass 4: (1) state-vtable cluster dump around the type-41
# decoder (0x14106E9C8) to enumerate the script-band decoders; (2) for each
# 82B decoder, find its schema-slot LEA -> per-type schema slot map;
# (3) decompile the ENCODE side (FUN_14039a570 writer builder, FUN_14039a0e0
# encode walk) + the varint primitive FUN_140391e40; (4) check 0x141CA6A00.
# Output: RE_output/content/decoder41_raw4.txt
from ghidra.app.decompiler import DecompInterface
import os

LOG = r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\decoder41_raw4.txt"
out = None
decomp = None


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


def dump_qwords(va, n, tag):
    buf = bytearray(n * 8)
    currentProgram.getMemory().getBytes(addr_of(va), buf)
    log("===== QWORDS %s @ 0x%X (%d x 8B) =====" % (tag, va, n))
    for i in range(n):
        v = int.from_bytes(buf[i * 8:i * 8 + 8], "little")
        log("0x%08X: 0x%016X" % (va + i * 8, v))
    log("")


def find_schema_slot(decoder_va, tag):
    """linear-disasm the decoder, find LEA with a 0x141C/0x141CA target."""
    fn = ensure_function(decoder_va)
    if fn is None:
        log("-- %s: no function @ 0x%X" % (tag, decoder_va))
        return None
    cur = addr_of(decoder_va)
    slot = None
    lines = []
    for _ in range(64):
        ins = getInstructionAt(cur)
        if ins is None:
            try:
                disassemble(cur)
                ins = getInstructionAt(cur)
            except Exception:
                break
        if ins is None:
            break
        s = ins.toString()
        lines.append("0x%08X  %s" % (ins.getAddress().getOffset(), s))
        if "LEA" in s and ("0x141c" in s.lower()):
            # extract the hex address
            import re
            m = re.findall(r"0x141c[0-9a-f]+", s.lower())
            if m:
                slot = int(m[0], 16)
        if ins.getAddress().getOffset() - decoder_va > 0x200:
            break
        cur = ins.getAddress().add(ins.getLength())
    log("-- %s (%s) @ 0x%X schema_slot=0x%X" % (tag, fn.getName(), decoder_va, slot if slot else 0))
    for l in lines:
        log("    " + l)
    log("")
    return slot


def main():
    global out, decomp
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    out = open(LOG, "w", encoding="utf-8")
    decomp = DecompInterface()
    decomp.openProgram(currentProgram)
    log("=== DECODER41 pass4: vtable cluster + per-type schema map + encode side ===")
    log("program: %s base=0x%X" % (currentProgram.getName(), currentProgram.getImageBase().getOffset()))

    # state vtable cluster: type-41 state vtable image VA = decoder - 0x18
    # (state obj vtable+0x18 == decoder per FUN_140E0F000 call)
    dump_qwords(0x14106E5F0, 40, "state-vtable cluster around type41 (0x14106E5F0..0x14106EA30)")

    # script band: probe candidate decoders around the known ones.
    # type-47 decoder 0x14106E620, type-41 0x14106E9E0. The band likely has
    # more 82B decoders; find each vtable's +0x18 and its schema slot.
    candidates = []
    va = 0x14106E5F0
    buf = bytearray(0x440 * 8)
    try:
        currentProgram.getMemory().getBytes(addr_of(va), buf)
    except Exception:
        buf = None
    if buf is not None:
        for i in range(0x440):
            v = int.from_bytes(buf[i * 8:i * 8 + 8], "little")
            if 0x141000000 <= v < 0x141800000:
                # a plausible code pointer inside .text1; check function
                f = getFunctionContaining(addr_of(v))
                if f is not None and f.getEntryPoint().getOffset() == v:
                    candidates.append((va + i * 8, v))
    seen = set()
    for vtable_va, dec in candidates:
        if dec in seen:
            continue
        seen.add(dec)
        find_schema_slot(dec, "vtable@0x%X decoder" % vtable_va)

    # encode side
    decompile_fn(ensure_function(0x14039A570), "writer builder (encode side)"),
    decompile_fn(ensure_function(0x14039A0E0), "encode walk (schema -> wire)"),
    decompile_fn(ensure_function(0x140391E40), "varint primitive (key/value bytes)"),

    # third schema slot check
    dump_qwords(0x141CA6A00, 16, "network-session-membership schema slot 0x141CA6A00")

    log("=== DECODER41-PASS4-COMPLETE ===")
    out.close()
    print("DONE")


main()
