# decoder41b.py -- pass 2: (1) disassemble FUN_140E0F000 around the vtable+0x18
# decoder call to pin the real arg count/registers; (2) decompile the shared
# schema-codec machinery (reader primitive + field walk + stores);
# (3) raw-dump the type-41/type-47 schema descriptors in .rdata.
# Output: RE_output/content/decoder41_raw2.txt
from ghidra.app.decompiler import DecompInterface
import os

LOG = r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\decoder41_raw2.txt"
out = None
decomp = None

DECOMPILE = [
    (0x14038D020, "reader codec primitive (the reader.fn)"),
    (0x140390180, "reader builder (2nd family)"),
    (0x140390220, "reader step/next"),
    (0x140391DA0, "field read from payload reader"),
    (0x140392150, "field store scalar"),
    (0x14038E400, "field store w/ schema reader"),
    (0x140390130, "schema field lookup"),
    (0x140390370, "schema init walk (have pass1, refresh)"),
]


def log(s):
    out.write(s + "\n")
    out.flush()
    try:
        print(str(s)[:3000].encode("ascii", "replace").decode("ascii"))
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


def dump_asm(va, tag, n_after=40):
    fn = ensure_function(va)
    if fn is None:
        log("===== ASM %s: NO FUNCTION @ 0x%X" % (tag, va))
        return
    log("===== ASM %s %s @ 0x%X" % (tag, fn.getName(), va))
    insn_it = currentProgram.getListing().getInstructions(fn.getBody(), True)
    lines = []
    while insn_it.hasNext():
        ins = insn_it.next()
        lines.append("0x%08X  %s" % (ins.getAddress().getOffset(), ins.toString()))
    # find the indirect calls through vtable +0x18 / +0x28 (the decoder/apply)
    marks = set()
    for i, s in enumerate(lines):
        if ("call" in s and ("[0x18]" in s or "[0x28]" in s or "[0x20]" in s)) or ("0x18]" in s and "call" in s):
            marks.add(i)
    for m in sorted(marks):
        lo = max(0, m - 18)
        hi = min(len(lines), m + 6)
        log("-- context around line %d (%s) --" % (m, lines[m]))
        for j in range(lo, hi):
            log(lines[j])
    if not marks:
        # dump the tail (the dispatch block is at the end)
        for s in lines[-n_after:]:
            log(s)
    log("")


def dump_bytes(va, n, tag):
    a = addr_of(va)
    buf = bytearray(n)
    try:
        currentProgram.getMemory().getBytes(a, buf)
        log("===== BYTES %s @ 0x%X n=%d =====" % (tag, va, n))
        for off in range(0, n, 16):
            chunk = buf[off:off + 16]
            hexs = " ".join("%02x" % b for b in chunk)
            asc = "".join(chr(b) if 0x20 <= b < 0x7F else "." for b in chunk)
            log("0x%06X  %-47s  %s" % (va + off, hexs, asc))
        log("")
    except Exception as e:
        log("dump_bytes %s failed: %s" % (tag, e))


def main():
    global out, decomp
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    out = open(LOG, "w", encoding="utf-8")
    decomp = DecompInterface()
    decomp.openProgram(currentProgram)
    log("=== DECODER41 pass2: call-site asm + codec machinery + schema dumps ===")
    log("program: %s base=0x%X" % (currentProgram.getName(), currentProgram.getImageBase().getOffset()))

    dump_asm(0x140E0F000, "FUN_140E0F000 dispatch (find vtable+0x18 call)")

    for va, tag in DECOMPILE:
        decompile_fn(ensure_function(va), tag)

    # schema descriptors: type-41 = 0x141C39320, type-47 = 0x141C31EC0
    # dump the band between them + 0x100 past the type-41 one
    dump_bytes(0x141C31EC0, 0x600, "schema band 0x141C31EC0..0x141C394C0 (type47 + type41 descriptors)")

    log("=== DECODER41-PASS2-COMPLETE ===")
    out.close()
    print("DONE")


main()
