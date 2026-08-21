# iv_writer_hunt2.py -- pass 2: the cold hash-chain neighborhood + byte dumps.
# 1. Fix the byte-dump bug (JPype byte[] -> bytes conversion).
# 2. Memory block info for the IV region.
# 3. Disassemble around 0x14411cd5c (the only DATA xref to the IV) and 0x14423C189
#    (the movups reader), print raw instruction bytes.
# 4. Create + decompile the function containing 0x14423C189, decompile FUN_14411cd56
#    and its callers.
# 5. Hunt write instructions in the cold neighborhood (base+0xE0 / +0x4CE0 forms).
from ghidra.program.model.mem import Memory
from ghidra.app.decompiler import DecompInterface
import struct, os

IV_ADDR = 0x141F44CE0
STRUCT_ADDR = 0x141F44C00
READER_REF = 0x14411cd5c
MOVUPS_READER = 0x14423C189
LOG = r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\ghidra\iv_writer_hunt2.log"

out = None
decomp = None

def log(s):
    global out
    print(s)
    out.write(s + "\n")
    out.flush()

def addr_of(v):
    return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v)

def getb(a, n):
    """JPype-safe byte read via Java byte[] buffer."""
    try:
        from jpype import JArray, JByte
        buf = JArray(JByte)(n)
        mem = currentProgram.getMemory()
        got = mem.getBytes(addr_of(a), buf)
        if got != n:
            log("  getb short @0x%X: %d/%d" % (a, got, n))
        return b''.join(bytes([x & 0xFF]) for x in buf)
    except Exception as e:
        log("  getb ERROR @0x%X n=%d: %s" % (a, n, e))
        return None

def hexb(b):
    if b is None:
        return "(unreadable)"
    return " ".join("%02X" % x for x in b)

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

def callers_of(f, label):
    rm = currentProgram.getReferenceManager()
    log("=== CALLERS OF %s (%s @ %s) ===" % (label, f.getName(), hex(f.getEntryPoint().getOffset())))
    it = rm.getReferencesTo(f.getEntryPoint())
    callers = []
    while it.hasNext():
        r = it.next()
        t = str(r.getReferenceType())
        if "CALL" not in t.upper():
            continue
        fr = r.getFromAddress()
        cf = getFunctionContaining(fr)
        cname = cf.getName() + " @" + hex(cf.getEntryPoint().getOffset()) if cf is not None else "(no func)"
        log("  caller %s type=%s -> %s" % (hex(fr.getOffset()), t, cname))
        if cf is not None:
            callers.append(cf)
    return callers

def disasm_range(start, end, label):
    """Disassemble [start,end) and print each instruction with raw bytes."""
    log("=== DISASM %s : 0x%X..0x%X ===" % (label, start, end))
    cur = addr_of(start)
    last = addr_of(end)
    count = 0
    while cur is not None and cur.compareTo(last) < 0 and count < 4000:
        insn = getInstructionAt(cur)
        if insn is None:
            try:
                disassemble(cur)
                insn = getInstructionAt(cur)
            except Exception:
                cur = cur.add(1)
                continue
            if insn is None:
                cur = cur.add(1)
                continue
        ib = getb(insn.getAddress().getOffset(), insn.getLength())
        log("  0x%08X: %-40s %s" % (insn.getAddress().getOffset(), hexb(ib) if ib else "(n/a)", insn.toString()))
        cur = insn.getAddress().add(insn.getLength())
        count += 1
    log("instructions: %d" % count)

def main():
    global out, decomp
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    out = open(LOG, "w", encoding="utf-8")
    decomp = DecompInterface()
    decomp.openProgram(currentProgram)

    log("=== IV WRITER HUNT PASS 2 ===")
    log("program: %s" % currentProgram.getName())

    # 1. byte dumps (fixed conversion)
    log("=== BYTE DUMPS ===")
    ivb = getb(IV_ADDR, 16)
    log("  IV @0x%X: %s" % (IV_ADDR, hexb(ivb)))
    sb = getb(STRUCT_ADDR, 0x100)
    log("  struct head @0x%X (256B): %s" % (STRUCT_ADDR, hexb(sb)))
    cst = getb(0x141BCCA00, 0x200)
    log("  const area @0x141BCCA00 (512B): %s" % hexb(cst))
    c010 = getb(0x14263C010, 16)
    log("  DAT_14263c010 (16B): %s" % hexb(c010))

    # 2. memory block info around the IV
    log("=== MEMORY BLOCKS (around IV) ===")
    mem = currentProgram.getMemory()
    for blk in mem.getBlocks():
        s = blk.getStart().getOffset()
        e = blk.getEnd().getOffset()
        if (s <= IV_ADDR <= e) or (s <= STRUCT_ADDR <= e):
            log("  block %s 0x%X..0x%X init=%s" % (blk.getName(), s, e, blk.isInitialized()))
            try:
                fb = blk.getFileBytes()
                log("    fileBytes: %s" % (fb.getSize() if fb is not None else None))
            except Exception as ex:
                log("    fileBytes err: %s" % ex)

    # 3. disassemble the reader neighborhood
    disasm_range(0x14411CD00, 0x14411CE00, "reader xref site 0x14411cd5c")
    disasm_range(0x14423C100, 0x14423C220, "movups reader 0x14423C189")

    # 4. decompile the containing function of the movups reader + FUN_14411cd56
    log("=== FUNCTION DECOMPILES ===")
    rf = getFunctionContaining(addr_of(MOVUPS_READER))
    if rf is None:
        log("no function at 0x14423C189; creating one (Phase10 pattern)")
        try:
            rf = createFunction(addr_of(0x14423C160), None)
        except Exception:
            rf = None
    if rf is not None:
        log("---- MOVUPS READER FUNCTION %s @ %s ----" % (rf.getName(), hex(rf.getEntryPoint().getOffset())))
        log(decompile_func(rf))
        c1 = callers_of(rf, "movups-reader")
        for c in c1:
            log("---- CALLER-1 %s @ %s ----" % (c.getName(), hex(c.getEntryPoint().getOffset())))
            log(decompile_func(c))
    else:
        log("FAILED to create function at 0x14423C189")

    f2 = getFunctionContaining(addr_of(READER_REF))
    if f2 is not None:
        log("---- XREF-OWNER FUN_14411cd56 ----")
        log(decompile_func(f2))
        c2 = callers_of(f2, "xref-owner")
        for c in c2:
            log("---- CALLER-1 %s @ %s ----" % (c.getName(), hex(c.getEntryPoint().getOffset())))
            log(decompile_func(c))
    else:
        log("no function at 0x14411cd5c")

    # 5. hunt write instructions in the cold neighborhood: any instruction whose
    #    target could be the IV (struct base + 0xE0, or base + 0x4CE0). Search for
    #    disp8=0xE0 write forms near the reader + whole-image disp32=0x4CE0 (the
    #    offset of the IV within a 0x141F44C00-based struct... actually IV=+0xE0).
    log("=== WRITE-FORM HUNT (disp8 0xE0 / movups-family) in reader neighborhood ===")
    for blk in mem.getBlocks():
        s = blk.getStart().getOffset()
        e = blk.getEnd().getOffset()
        if not (0x14400000 <= s <= 0x145D0000):
            continue
        log("  scanning block %s 0x%X..0x%X" % (blk.getName(), s, e))
        cur = addr_of(s)
        count = 0
        while cur is not None and cur.getOffset() <= e and count < 200000:
            insn = getInstructionAt(cur)
            if insn is None:
                cur = cur.add(1)
                continue
            mnem = insn.getMnemonicString()
            if mnem.startswith("MOV") or mnem.startswith("XOR") or mnem.startswith("AND") or mnem.startswith("OR") or mnem.startswith("LEA"):
                ib = getb(insn.getAddress().getOffset(), insn.getLength())
                bs = " ".join("%02X" % x for x in ib) if ib else ""
                # look for disp8 0xE0 as the LAST byte (typical [reg+0xE0] store)
                if ib is not None and len(ib) >= 4 and ib[-1] == 0xE0 and ib[-2] in (0x40,0x44,0x48,0x4C,0x41,0x45,0x49,0x4D):
                    log("  %s @0x%08X: %s  %s" % (mnem, insn.getAddress().getOffset(), bs, insn.toString()))
                    count += 1
                elif ib is not None and len(ib) >= 7 and ib[-4:-1] == bytes([0x00,0x00,0x00]) and ib[-5] == 0xE0:
                    log("  %s @0x%08X (disp32=0xE0): %s  %s" % (mnem, insn.getAddress().getOffset(), bs, insn.toString()))
                    count += 1
            cur = insn.getAddress().add(insn.getLength())
        log("  write-form hits: %d" % count)

    log("=== IV-WRITER-HUNT2 COMPLETE ===")
    out.close()
    print("DONE")

main()
