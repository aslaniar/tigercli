# iv_disasm_gaps.py -- measure disassembly coverage of the second .text block,
# then disassemble the gaps (Phase10-style 64-byte stride sweep) and re-run the
# resolved-operand write scan on the newly disassembled code.
from ghidra.program.model.mem import Memory
from ghidra.app.decompiler import DecompInterface
import os

LOG = r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\ghidra\iv_writer_hunt6.log"
out = None
decomp = None

def log(s):
    global out
    out.write(s + "\n")
    out.flush()
    try:
        print(s[:4000].encode('ascii', 'replace').decode('ascii'))
    except Exception:
        pass

def addr_of(v):
    return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v)

def fn_name(a):
    f = getFunctionContaining(addr_of(a))
    if f is not None:
        return f.getName() + " @" + hex(f.getEntryPoint().getOffset())
    return "(no function)"

def main():
    global out, decomp
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    out = open(LOG, "w", encoding="utf-8")
    decomp = DecompInterface()
    decomp.openProgram(currentProgram)

    log("=== IV WRITER HUNT PASS 6 (disasm-gap fill + write scan) ===")
    log("program: %s" % currentProgram.getName())

    mem = currentProgram.getMemory()
    listing = currentProgram.getListing()

    # measure coverage per block
    for blk in mem.getBlocks():
        if not blk.isInitialized():
            continue
        s = blk.getStart().getOffset()
        e = blk.getEnd().getOffset()
        if not (0x140000000 <= s < 0x149000000):
            continue
        # sample coverage: count instruction-start addresses at 0x1000-stride
        n_ins = 0
        n_sam = 0
        cur = s
        while cur <= e:
            if getInstructionAt(addr_of(cur)) is not None:
                n_ins += 1
            n_sam += 1
            cur += 0x100
        log("block %s 0x%X..0x%X coverage %.1f%% (sample %d)" % (blk.getName(), s, e, 100.0 * n_ins / n_sam, n_sam))

    # disassemble the second .text gaps: 0x143CC9000..0x148A5F000
    start = 0x143CC9000
    end = 0x148A5F000
    log("=== disassembling 0x%X..0x%X (64-byte stride) ===" % (start, end))
    cur = start
    done = 0
    while cur < end:
        if getInstructionAt(addr_of(cur)) is None:
            try:
                disassemble(addr_of(cur))
            except Exception:
                pass
            done += 1
        cur += 64
    log("disassemble calls: %d" % done)

    # now re-scan ALL instructions for resolved operands into the struct/IV range
    hits = []
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
            if 0x141F44C00 <= off <= 0x141F44D20:
                hits.append((insn, oi, off, str(insn.getFlowType())))
    log("instructions scanned: %d" % total)
    log("=== ALL RESOLVED REFS TO STRUCT/IV RANGE ===")
    for insn, oi, off, t in hits:
        log("  0x%08X op%d -> 0x%X %s | %s | %s" % (insn.getAddress().getOffset(), oi, off, t, insn.toString(), fn_name(insn.getAddress())))
    log("struct-range hit count: %d" % len(hits))

    log("=== IV-WRITER-HUNT6 COMPLETE ===")
    out.close()
    print("DONE")

main()
