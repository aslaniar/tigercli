# iv_writer_hunt3.py -- pass 3: full-image instruction scan for refs to the
# struct/IV range [0x141F44C00, 0x141F44D00] using per-operand resolved addresses
# (works on unanalyzed cold code). Also refs to the const area 0x141BCCA00-0xCB00
# and the string 0x141BCCAA0. Decompile the reader function + struct-head readers.
from ghidra.program.model.mem import Memory
from ghidra.app.decompiler import DecompInterface
import os

STRUCT_ADDR = 0x141F44C00
IV_ADDR = 0x141F44CE0
RANGE_LO = 0x141F44C00
RANGE_HI = 0x141F44D20
CONST_LO = 0x141BCCA00
CONST_HI = 0x141BCCB00
STR_ADDR = 0x141BCCAA0
LOG = r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\ghidra\iv_writer_hunt3.log"

out = None
decomp = None

def log(s):
    global out
    print(s)
    out.write(s + "\n")
    out.flush()

def addr_of(v):
    return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v)

def fn_name(a):
    f = getFunctionContaining(a)
    if f is not None:
        return f.getName() + " @" + hex(f.getEntryPoint().getOffset())
    return "(no function)"

def decompile_func(f):
    global decomp
    if f is None:
        return "(none)"
    try:
        res = decomp.decompileFunction(f, 90, monitor)
        if res is not None and res.decompileCompleted() and res.getDecompiledFunction() is not None:
            return res.getDecompiledFunction().getC()
        return "(decompile failed: %s)" % (res.getErrorMessage() if res is not None else "no result")
    except Exception as e:
        return "(decompile exception: %s)" % e

def main():
    global out, decomp
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    out = open(LOG, "w", encoding="utf-8")
    decomp = DecompInterface()
    decomp.openProgram(currentProgram)

    log("=== IV WRITER HUNT PASS 3 (full-image operand scan) ===")
    log("program: %s" % currentProgram.getName())

    listing = currentProgram.getListing()
    hits_struct = []
    hits_const = []
    total = 0
    insn_it = listing.getInstructions(True)
    while insn_it.hasNext() and not monitor.isCancelled():
        insn = insn_it.next()
        total += 1
        n = insn.getNumOperands()
        if n == 0:
            continue
        for oi in range(n):
            try:
                a = insn.getAddress(oi)
            except Exception:
                a = None
            if a is None:
                continue
            off = a.getOffset()
            if RANGE_LO <= off <= RANGE_HI:
                t = str(insn.getFlowType())
                hits_struct.append((insn, oi, off, t))
            elif CONST_LO <= off <= CONST_HI:
                hits_const.append((insn, oi, off, str(insn.getFlowType())))
    log("instructions scanned: %d" % total)

    log("=== HITS: refs into struct/IV range 0x%X..0x%X ===" % (RANGE_LO, RANGE_HI))
    for insn, oi, off, t in hits_struct:
        log("  0x%08X op%d -> 0x%X %s | %s | %s" % (insn.getAddress().getOffset(), oi, off, t, insn.toString(), fn_name(insn.getAddress())))
    log("struct-range hit count: %d" % len(hits_struct))

    log("=== HITS: refs into const area 0x%X..0x%X (incl. async string 0x%X) ===" % (CONST_LO, CONST_HI, STR_ADDR))
    for insn, oi, off, t in hits_const:
        log("  0x%08X op%d -> 0x%X %s | %s | %s" % (insn.getAddress().getOffset(), oi, off, t, insn.toString(), fn_name(insn.getAddress())))
    log("const-range hit count: %d" % len(hits_const))

    # decompile: struct-head reader FUN_1403447a0, +0xA8 refs owner FUN_140346060,
    # and try to create/decompile the movups reader function
    log("=== DECOMPILES ===")
    for target, label in [(0x1403447A0, "struct-head reader FUN_1403447a0"),
                          (0x140346060, "FUN_140346060 (+0xA8 DATA refs)"),
                          (0x14411CD56, "FUN_14411cd56 (IV LEA xref owner)")]:
        f = getFunctionAt(addr_of(target))
        if f is None:
            log("no function at 0x%X (%s)" % (target, label))
            continue
        log("---- %s @ %s ----" % (label, hex(f.getEntryPoint().getOffset())))
        log(decompile_func(f))

    rf = getFunctionContaining(addr_of(0x14423C189))
    if rf is None:
        log("no function at 0x14423C189; creating at the MOVUPS itself")
        try:
            rf = createFunction(addr_of(0x14423C189), None)
        except Exception as e:
            log("createFunction at MOVUPS failed: %s" % e)
    if rf is not None:
        log("---- MOVUPS READER FUNC %s @ %s ----" % (rf.getName(), hex(rf.getEntryPoint().getOffset())))
        log(decompile_func(rf))
        rm = currentProgram.getReferenceManager()
        it = rm.getReferencesTo(rf.getEntryPoint())
        while it.hasNext():
            r = it.next()
            t = str(r.getReferenceType())
            if "CALL" in t.upper():
                fr = r.getFromAddress()
                cf = getFunctionContaining(fr)
                log("  caller %s type=%s -> %s" % (hex(fr.getOffset()), t, fn_name(fr)))
                if cf is not None and cf.getEntryPoint().getOffset() != rf.getEntryPoint().getOffset():
                    log("  ---- CALLER-1 %s ----" % cf.getName())
                    log(decompile_func(cf))

    log("=== IV-WRITER-HUNT3 COMPLETE ===")
    out.close()
    print("DONE")

main()
