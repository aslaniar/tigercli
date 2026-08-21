# decoder41f.py -- pass 6: decompile the schema-codec functions actually used by
# the type-41 schema: codec[0]=0x14038C650 (varint scalar), codec[4]=0x14038C800
# (bytes blob), codec[6]=0x14038C950 (nested submessage). Output: content/decoder41_raw6.txt
from ghidra.app.decompiler import DecompInterface
import os

LOG = r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\decoder41_raw6.txt"
out = None
decomp = None

TARGETS = [
    (0x14038C650, "decode codec[0] (type41 field1: varint scalar)"),
    (0x14038C800, "decode codec[4] (nested f3: bytes blob)"),
    (0x14038C950, "decode codec[6] (type41 field2: nested submessage)"),
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


def main():
    global out, decomp
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    out = open(LOG, "w", encoding="utf-8")
    decomp = DecompInterface()
    decomp.openProgram(currentProgram)
    log("=== DECODER41 pass6: the 3 codecs used by the type-41 schema ===")
    log("program: %s base=0x%X" % (currentProgram.getName(), currentProgram.getImageBase().getOffset()))
    for va, tag in TARGETS:
        decompile_fn(ensure_function(va), tag)
    log("=== DECODER41-PASS6-COMPLETE ===")
    out.close()
    print("DONE")


main()
