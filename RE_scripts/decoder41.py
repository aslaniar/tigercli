# decoder41.py -- lane: decompile the type-41 script_event payload decoder
# FUN_14106E9E0 (image VA 0x14106E9E0, RVA 0x106E9E0; the DAT_14280E3E0[41]
# state object's vtable+0x18) + sibling decoders + the apply thunk, and follow
# the payload-buffer reads into the immediate callees.
# Run: pyghidraRun.bat -H <project dir> d2_full -process destiny2_unpacked_full.exe
#      -noanalysis -postScript decoder41.py -log <run log>
# Output: RE_output/content/decoder41_raw.txt
from ghidra.app.decompiler import DecompInterface
import os

LOG = r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\decoder41_raw.txt"
out = None
decomp = None

TARGETS = [
    (0x14106E9E0, "TARGET type41 script_event DECODER (state-obj vtable+0x18)"),
    (0x14106E620, "SIBLING type47 decoder (82B, per lane brief)"),
    (0x140E80830, "APPLY thunk (table-obj vtable+0x28, 4B)"),
    (0x14106E680, "BIG-NEIGHBOR 857B parser after type-47 decoder"),
]


def log(s):
    out.write(s + "\n")
    out.flush()
    try:
        print(str(s)[:4000].encode("ascii", "replace").decode("ascii"))
    except Exception:
        pass


def addr_of(v):
    return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v)


def ensure_function(va):
    a = addr_of(va)
    f = getFunctionContaining(a)
    if f is not None:
        if f.getEntryPoint().getOffset() == va:
            return f, "existing"
        log("NOTE: 0x%X sits INSIDE %s @ 0x%X" % (va, f.getName(), f.getEntryPoint().getOffset()))
        return f, "inside"
    try:
        if getInstructionAt(a) is None:
            disassemble(a)
    except Exception as e:
        log("disassemble 0x%X failed: %s" % (va, e))
    try:
        f = createFunction(a, None)
    except Exception as e:
        log("createFunction 0x%X failed: %s" % (va, e))
        f = None
    if f is None:
        f = getFunctionContaining(a)
    return f, ("created" if f is not None else "STILL-NONE")


def decompile_fn(fn, tag, depth):
    if fn is None:
        log("===== %s : NO FUNCTION" % tag)
        return
    ep = fn.getEntryPoint().getOffset()
    body = fn.getBody().getNumAddresses()
    log("===== %s %s @ 0x%X body=%dB" % (tag, fn.getName(), ep, body))
    try:
        res = decomp.decompileFunction(fn, 120, monitor)
        if res is not None and res.decompileCompleted():
            c = res.getDecompiledFunction().getC()
            log(c)
            log("")
            if depth > 0:
                callees = fn.getCalledFunctions(monitor)
                names = sorted([(cf.getEntryPoint().getOffset(), cf.getName()) for cf in callees])
                log("-- callees (%d): %s" % (len(names), ", ".join("%s@0x%X" % (n, a) for a, n in names)))
                for a, n in names:
                    cf = getFunctionContaining(addr_of(a))
                    if cf is not None and cf.getEntryPoint().getOffset() == a:
                        sz = cf.getBody().getNumAddresses()
                        if sz <= 0x2000:
                            decompile_fn(cf, "callee %s" % n, depth - 1)
                        else:
                            log("===== callee %s @ 0x%X SKIPPED (body %d > 0x2000)" % (n, a, sz))
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
    log("=== DECODER41 lane: type-41 script_event decoder FUN_14106E9E0 ===")
    log("program: %s base=0x%X" % (currentProgram.getName(), currentProgram.getImageBase().getOffset()))
    for va, tag in TARGETS:
        blk = currentProgram.getMemory().getBlock(addr_of(va))
        log("target 0x%X (%s): block=%s" % (va, tag, blk.getName() if blk else "NONE"))
        try:
            b = currentProgram.getMemory().getBytes(addr_of(va), 16)
            log("  entry bytes: " + " ".join("%02x" % (x & 0xFF) for x in b))
        except Exception as e:
            log("  entry bytes read failed: %s" % e)
    for va, tag in TARGETS:
        fn, how = ensure_function(va)
        log("ensure 0x%X -> %s (%s)" % (va, fn.getName() if fn else "NONE", how))

    fn = getFunctionContaining(addr_of(0x14106E9E0))
    decompile_fn(fn, "TARGET type41 decoder", 2)
    fn = getFunctionContaining(addr_of(0x14106E620))
    decompile_fn(fn, "SIBLING type47 decoder", 1)
    fn = getFunctionContaining(addr_of(0x140E80830))
    decompile_fn(fn, "APPLY thunk", 0)
    fn = getFunctionContaining(addr_of(0x14106E680))
    decompile_fn(fn, "BIG-NEIGHBOR parser", 1)
    log("=== DECODER41-COMPLETE ===")
    out.close()
    print("DONE")


main()
