# iv_writer_hunt5.py -- pass 5: RAW-BYTE hunt for write instructions targeting
# struct offsets 0xE0/0xE4/0xE8 from ANY base register, over ALL memory blocks
# (including undisassembled regions). Scan the raw bytes for the exact ModRM
# encodings, then disassemble + report + decompile the containing function of
# any candidate found inside the second .text / cold regions.
from ghidra.program.model.mem import Memory
from ghidra.app.decompiler import DecompInterface
import os

LOG = r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\ghidra\iv_writer_hunt5.log"
out = None
decomp = None

def log(s):
    global out
    # stdout may be cp1252; write to file first (crash-safe), then try print
    out.write(s + "\n")
    out.flush()
    try:
        print(s[:4000].encode('ascii', 'replace').decode('ascii'))
    except Exception:
        pass

def addr_of(v):
    return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v)

def getb(a, n):
    try:
        from jpype import JArray, JByte
        buf = JArray(JByte)(n)
        got = currentProgram.getMemory().getBytes(addr_of(a), buf)
        return b''.join(bytes([x & 0xFF]) for x in buf)
    except Exception:
        return None

def hexb(b):
    return " ".join("%02X" % x for x in b) if b else "(none)"

def fn_name(a):
    f = getFunctionContaining(addr_of(a))
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

    log("=== IV WRITER HUNT PASS 5 (raw-byte write-form scan, ALL blocks) ===")
    log("program: %s" % currentProgram.getName())

    # patterns: (opcode bytes, ModRM range, disp bytes, label)
    # ModRM 0x40..0x7F = [r+disp8], 0x80..0xBF = [r+disp32]
    patterns = []
    for modrm_lo, modrm_hi, disp, dlab in [
        (0x40, 0x7F, bytes([0xE4]), 'disp8=0xE4'),
        (0x40, 0x7F, bytes([0xE8]), 'disp8=0xE8'),
        (0x40, 0x7F, bytes([0xE0]), 'disp8=0xE0'),
        (0x80, 0xBF, bytes([0xE4, 0x00, 0x00, 0x00]), 'disp32=0xE4'),
        (0x80, 0xBF, bytes([0xE8, 0x00, 0x00, 0x00]), 'disp32=0xE8'),
        (0x80, 0xBF, bytes([0xE0, 0x00, 0x00, 0x00]), 'disp32=0xE0'),
    ]:
        for opcode, olabel in [
            (bytes([0x89]), 'MOV r/m32,r32'),
            (bytes([0x88]), 'MOV r/m8,r8'),
            (bytes([0xC7]), 'MOV r/m32,imm32'),
            (bytes([0xC6]), 'MOV r/m8,imm8'),
            (bytes([0x48, 0x89]), 'MOV r/m64,r64 (REX.W)'),
            (bytes([0x48, 0xC7]), 'MOV r/m64,imm32 (REX.W)'),
            (bytes([0x4C, 0x89]), 'MOV r/m64,r64 (REX.W+R)'),
            (bytes([0x0F, 0x11]), 'MOVUPS [r],xmm'),
            (bytes([0x0F, 0x29]), 'MOVAPS [r],xmm'),
            (bytes([0x66, 0x0F, 0x11]), 'MOVDQU [r],xmm'),
            (bytes([0x66, 0x0F, 0x29]), 'MOVDQA [r],xmm'),
            (bytes([0xF3, 0x0F, 0x11]), 'MOVSS [r],xmm'),
            (bytes([0xF2, 0x0F, 0x11]), 'MOVSD [r],xmm'),
            (bytes([0x31]), 'XOR r/m32,r32'),
            (bytes([0x33]), 'XOR r/m64,r64'),
        ]:
            patterns.append((opcode, modrm_lo, modrm_hi, disp, '%s %s' % (olabel, dlab)))

    # scan each initialized block
    mem = currentProgram.getMemory()
    total_candidates = 0
    candidates = []  # (address, pattern_label)
    for blk in mem.getBlocks():
        if not blk.isInitialized():
            continue
        s = blk.getStart().getOffset()
        e = blk.getEnd().getOffset()
        # read the block in chunks
        chunk = 1 << 22
        cur = s
        log("scanning block %s 0x%X..0x%X" % (blk.getName(), s, e))
        while cur <= e:
            n = min(chunk, e - cur + 1)
            data = getb(cur, n)
            if data is None:
                cur += n
                continue
            for opcode, lo, hi, disp, label in patterns:
                pat = opcode + bytes([0]) + disp  # placeholder modrm
                # brute scan: for every position i, check opcode then modrm then disp
                i = 0
                while i < n:
                    i = data.find(opcode, i)
                    if i < 0:
                        break
                    mi = i + len(opcode)
                    if mi < n and lo <= data[mi] <= hi:
                        di = mi + 1
                        if data[di:di+len(disp)] == disp:
                            addr = cur + i
                            candidates.append((addr, label))
                            total_candidates += 1
                            log("  CAND %s @0x%X in %s" % (label, addr, fn_name(addr)))
                    i += 1
            cur += n

    log("total raw candidates: %d" % len(candidates))

    # disassemble + decompile the unique containing functions
    seen = set()
    for addr, label in candidates:
        try:
            insn = getInstructionAt(addr_of(addr))
            if insn is None:
                disassemble(addr_of(addr))
                insn = getInstructionAt(addr_of(addr))
            if insn is not None:
                ib = getb(insn.getAddress().getOffset(), insn.getLength())
                log("  INS @0x%08X [%s] %s | %s" % (insn.getAddress().getOffset(), hexb(ib), insn.toString(), fn_name(insn.getAddress())))
        except Exception as ex:
            log("  disasm fail @0x%X: %s" % (addr, ex))
        f = getFunctionContaining(addr_of(addr))
        if f is not None and f.getEntryPoint().getOffset() not in seen:
            seen.add(f.getEntryPoint().getOffset())
            log("---- CANDIDATE FUNCTION %s @ %s ----" % (f.getName(), hex(f.getEntryPoint().getOffset())))
            log(decompile_func(f))

    log("=== IV-WRITER-HUNT5 COMPLETE ===")
    out.close()
    print("DONE")

main()
