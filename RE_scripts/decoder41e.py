# decoder41e.py -- pass 5: verify decoder entry bytes (the vtable-cluster dump
# read zeros -- confirm code is really there), dump the ENCODER codec table
# 0x141BD0F10, decompile the key writer FUN_14039a460 + array writer
# FUN_1403967d0. Output: RE_output/content/decoder41_raw5.txt
from ghidra.app.decompiler import DecompInterface
import os

LOG = r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\decoder41_raw5.txt"
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


def dump_bytes(va, n, tag):
    buf = bytearray(n)
    currentProgram.getMemory().getBytes(addr_of(va), buf)
    log("===== BYTES %s @ 0x%X n=%d =====" % (tag, va, n))
    for off in range(0, n, 16):
        chunk = buf[off:off + 16]
        hexs = " ".join("%02x" % b for b in chunk)
        asc = "".join(chr(b) if 0x20 <= b < 0x7F else "." for b in chunk)
        log("0x%06X  %-47s  %s" % (va + off, hexs, asc))
    log("")


def dump_qwords(va, n, tag):
    buf = bytearray(n * 8)
    currentProgram.getMemory().getBytes(addr_of(va), buf)
    log("===== QWORDS %s @ 0x%X (%d x 8B) =====" % (tag, va, n))
    for i in range(n):
        v = int.from_bytes(buf[i * 8:i * 8 + 8], "little")
        log("0x%08X: 0x%016X" % (va + i * 8, v))
    log("")


def main():
    global out, decomp
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    out = open(LOG, "w", encoding="utf-8")
    decomp = DecompInterface()
    decomp.openProgram(currentProgram)
    log("=== DECODER41 pass5: entry-byte verify + encoder codec table + key/array writers ===")
    log("program: %s base=0x%X" % (currentProgram.getName(), currentProgram.getImageBase().getOffset()))

    dump_bytes(0x14106E9E0, 64, "type41 decoder entry (expect 40 55 53 56 prologue...)")
    dump_bytes(0x14106E620, 64, "type47 decoder entry")
    dump_bytes(0x14106E5F0, 64, "pre-decoder zone 0x14106E5F0 (vtable cluster?)")

    dump_qwords(0x141BD0F10, 16, "ENCODER codec table 0x141BD0F10")

    decompile_fn(ensure_function(0x14039A460), "key writer (field<<3 | wire -> varint)"),
    decompile_fn(ensure_function(0x1403967D0), "array writer"),

    log("=== DECODER41-PASS5-COMPLETE ===")
    out.close()
    print("DONE")


main()
