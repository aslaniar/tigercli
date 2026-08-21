# iv_writer_hunt4.py -- pass 4:
# (a) confirm the IV value in the d2_arrivals project (different capture session);
# (b) raw-byte scan of the WHOLE image for memory-WRITE instructions carrying
#     disp8 0xE4 / 0xE8 / 0xE0 (the IV offsets from the struct base) with an
#     UNRESOLVED base register -- the pass-3 operand scan cannot see these.
#     Also disp32 forms (0xE4/0xE8/0xE0 as 4-byte displacement).
import os

LOG = r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\ghidra\iv_writer_hunt4.log"
out = None

def log(s):
    global out
    print(s)
    out.write(s + "\n")
    out.flush()

def addr_of(v):
    return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v)

def hexb(b):
    return " ".join("%02X" % x for x in b) if b else "(none)"

def getb(a, n):
    try:
        from jpype import JArray, JByte
        buf = JArray(JByte)(n)
        got = currentProgram.getMemory().getBytes(addr_of(a), buf)
        return b''.join(bytes([x & 0xFF]) for x in buf)
    except Exception:
        return None

def fn_name(a):
    f = getFunctionContaining(a)
    if f is not None:
        return f.getName() + " @" + hex(f.getEntryPoint().getOffset())
    return "(no function)"

def main():
    global out
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    out = open(LOG, "w", encoding="utf-8")
    log("=== IV WRITER HUNT PASS 4 ===")
    log("program: %s" % currentProgram.getName())

    # (a) what is at the IV site in THIS project?
    ivb = getb(0x141F44CE0, 16)
    log("IV @0x141F44CE0: %s" % (hexb(ivb) if ivb else "(unreadable)"))
    log("  == healthy? %s" % (ivb == bytes.fromhex('d62ab2c10cc01bc535db7b8655c7dc3b') if ivb else "n/a"))
    log("  == failing? %s" % (ivb == bytes.fromhex('d62ab2c1f5dc168d3fdb7b8655c7dc3b') if ivb else "n/a"))

    # (b) raw-byte scan for write forms. Patterns of interest (any base reg):
    #   MOV r/m32,r32  with disp8 0xE4/0xE8 : 89 /r (modrm 40-7F with rm=base, disp8)
    #   MOV r/m64,r64  REX.W : 48 89 ... / 4C 89 ...
    #   MOV r/m8,r8    : 88 ...
    #   MOVUPS [r+disp8],xmm : 0F 11 40 E0/E4/E8
    #   MOVAPS : 0F 29 40 E0...
    #   MOVDQU : 66 0F 11 40 E0...
    #   MOV imm32 [r+disp8] : C7 40 E0/E4/E8 imm32
    #   MOV imm8  [r+disp8] : C6 40 E8 imm8
    # Strategy: scan for bytes {E0,E4,E8} as the LAST byte of a 4..12-byte window
    # where the preceding byte is a ModRM in 0x40..0x7F (disp8 form) and the byte
    # before that is a write opcode (88/89/C6/C7/0F 11/0F 29/66 0F 11/66 0F 29/66 0F D6/0F 10->no, read).
    # Simpler robust approach: list ALL instructions whose mnemonic is a write and
    # whose raw bytes END with E0/E4/E8 (disp8 at the end) -- then filter.
    listing = currentProgram.getListing()
    write_ops = ('MOV', 'MOVUPS', 'MOVAPS', 'MOVDQU', 'MOVDQA', 'MOVSS', 'MOVSD', 'MOVQ',
                 'XOR', 'AND', 'OR', 'ADD', 'SUB', 'XCHG', 'CMPXCHG', 'INC', 'DEC', 'NOT', 'NEG',
                 'PUSH', 'MOVNTI', 'MOVNTDQ', 'MOVNTPS', 'SHL', 'SHR', 'SAR', 'SAL', 'ROR', 'ROL',
                 'BT', 'BTS', 'BTR', 'BTC', 'STOS', 'SCAS', 'PEXT', 'PDEP', 'BEXTR', 'BZHI')
    hits = []
    total = 0
    insn_it = listing.getInstructions(True)
    while insn_it.hasNext() and not monitor.isCancelled():
        insn = insn_it.next()
        total += 1
        mnem = insn.getMnemonicString()
        if mnem not in write_ops:
            continue
        try:
            ib = getb(insn.getAddress().getOffset(), insn.getLength())
        except Exception:
            ib = None
        if ib is None or len(ib) < 3:
            continue
        # disp8 forms: instruction bytes end with E0/E4/E8 and the byte before is ModRM 0x40-0x7F
        if ib[-1] in (0xE0, 0xE4, 0xE8) and 0x40 <= ib[-2] <= 0x7F:
            hits.append((insn, ib, 'disp8=0x%02X' % ib[-1]))
        # disp32 forms: bytes end with E0/E4/E8 00 00 00 and before that ModRM 0x80-0xBF
        elif len(ib) >= 7 and ib[-4:-1] == bytes([0, 0, 0]) and ib[-5] in (0xE0, 0xE4, 0xE8) and 0x80 <= ib[-6] <= 0xBF:
            hits.append((insn, ib, 'disp32=0x%02X' % ib[-5]))
    log("instructions scanned: %d" % total)
    log("=== WRITE-FORM HITS (disp8/disp32 E0/E4/E8, any base) ===")
    for insn, ib, kind in hits:
        log("  0x%08X %-8s [%s] %s  |  %s" % (insn.getAddress().getOffset(), kind, hexb(ib), insn.toString(), fn_name(insn.getAddress())))
    log("write-form hits: %d" % len(hits))

    # (c) for completeness: all instructions with disp8 0xE4 (the EXACT failing
    #     dword offset) regardless of mnemonic -- the writer must use +0xE4.
    log("=== ALL disp8=0xE4 instructions (any mnemonic) ===")
    n2 = 0
    insn_it = listing.getInstructions(True)
    while insn_it.hasNext() and not monitor.isCancelled():
        insn = insn_it.next()
        try:
            ib = getb(insn.getAddress().getOffset(), insn.getLength())
        except Exception:
            ib = None
        if ib is None or len(ib) < 2:
            continue
        if ib[-1] == 0xE4 and 0x40 <= ib[-2] <= 0x7F:
            log("  0x%08X %-8s [%s] %s  |  %s" % (insn.getAddress().getOffset(), insn.getMnemonicString(), hexb(ib), insn.toString(), fn_name(insn.getAddress())))
            n2 += 1
    log("disp8=0xE4 hits: %d" % n2)

    log("=== IV-WRITER-HUNT4 COMPLETE ===")
    out.close()
    print("DONE")

main()
