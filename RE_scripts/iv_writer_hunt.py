# iv_writer_hunt.py -- ZERO-BOOT Ghidra hunt for the WRITER of the 16-byte kind0 IV
# buffer at image VA 0x141F44CE0 (struct head 0x141F44C00).
#
# Mission: find WHO writes those 16 bytes, WHERE the bytes come from, WHO CALLS the
# writer, and whether any caller path is in-process-only vs external-server-shared.
#
# Runs under PyGhidra (Ghidra 12.1.2, venv at %APPDATA%\ghidra\ghidra_12.1.2_PUBLIC\venv):
#   pyghidraRun.bat -H <projectdir> <project> -process <program> -noanalysis
#       -postScript iv_writer_hunt.py
#
# Raw output: RE_output/ghidra/iv_writer_hunt.log (written incrementally, crash-safe).
from ghidra.program.model.mem import Memory
from ghidra.program.model.address import Address
from ghidra.app.decompiler import DecompInterface
import struct
import os

IV_ADDR = 0x141F44CE0
STRUCT_ADDR = 0x141F44C00
STRING_ADDR = 0x141BCCAA0           # "async_task_add_size_task_data_unsafe" string in const area
CONST_AREA = 0x141BCCA00

HEALTHY_IV = bytes([0xD6,0x2A,0xB2,0xC1, 0x0C,0xC0,0x1B,0xC5, 0x35,0xDB,0x7B,0x86, 0x55,0xC7,0xDC,0x3B])
FAILING_IV = bytes([0xD6,0x2A,0xB2,0xC1, 0xF5,0xDC,0x16,0x8D, 0x3F,0xDB,0x7B,0x86, 0x55,0xC7,0xDC,0x3B])

LOG = r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\ghidra\iv_writer_hunt.log"

out = None
decomp = None

def log(s):
    global out
    print(s)
    out.write(s + "\n")
    out.flush()

def hexb(b):
    return " ".join("%02X" % x for x in b)

def signed32(b):
    return struct.unpack("<i", bytes(b))[0]

def addr_of(v):
    return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v)

def fn_name(a):
    f = getFunctionContaining(a)
    if f is not None:
        return f.getName() + " @" + hex(f.getEntryPoint().getOffset())
    return "(no function)"

def dump_bytes(a, n):
    try:
        b = currentProgram.getMemory().getBytes(addr_of(a), n)
        return bytes(b)
    except Exception as e:
        return None

def scan_bytes(pat, label, resolve_rip=False, cap=400):
    """Scan whole image for a byte pattern. If resolve_rip, treat 4-byte hits as
    possible disp32 fields of instructions and compute target = insn_end + disp32."""
    mem = currentProgram.getMemory()
    log("=== SCAN %s : %s ===" % (label, hexb(pat)))
    if len(pat) == 4:
        disp_val = signed32(pat)
    hits = 0
    cur = mem.getMinAddress()
    while cur is not None and hits < cap:
        hit = mem.findBytes(cur, pat, None, True, monitor)
        if hit is None:
            break
        hits += 1
        insn = currentProgram.getListing().getInstructionContaining(hit)
        extra = ""
        if insn is not None:
            ib = bytes(currentProgram.getMemory().getBytes(insn.getAddress(), insn.getLength()))
            extra = "  insn@%s len=%d [%s]" % (hex(insn.getAddress().getOffset()), insn.getLength(), hexb(ib))
            if resolve_rip and len(pat) == 4:
                # disp32 sits at the END of the instruction for RIP-relative forms
                off = int(hit.subtract(insn.getAddress()))
                if off + 4 == insn.getLength():
                    insn_end = insn.getAddress().add(insn.getLength())
                    target = insn_end.add(signed32(pat))
                    extra += "  -> RIP-target " + hex(target.getOffset())
                    if target.getOffset() in (IV_ADDR, STRUCT_ADDR):
                        extra += "  <<<< IV/STRUCT RIP-REF"
        line = "hit %s in %s%s" % (hex(hit.getOffset()), fn_name(hit), extra)
        if resolve_rip and "RIP-REF" not in extra:
            # still print but lower priority
            pass
        log(line)
        cur = hit.add(1)
    log("hits: %d" % hits)
    return hits

def xrefs_to(target, label):
    rm = currentProgram.getReferenceManager()
    log("=== XREFS TO %s (%s) ===" % (hex(target), label))
    it = rm.getReferencesTo(addr_of(target))
    n = 0
    while it.hasNext():
        r = it.next()
        n += 1
        fr = r.getFromAddress()
        t = str(r.getReferenceType())
        log("  ref from %s type=%s %s" % (hex(fr.getOffset()), t, fn_name(fr)))
    log("xref count: %d" % n)
    return n

def xrefs_to_range(start, end, label):
    rm = currentProgram.getReferenceManager()
    log("=== XREFS TO RANGE %s..%s (%s) ===" % (hex(start), hex(end), label))
    n = 0
    a = start
    while a <= end:
        it = rm.getReferencesTo(addr_of(a))
        while it.hasNext():
            r = it.next()
            n += 1
            fr = r.getFromAddress()
            t = str(r.getReferenceType())
            isw = ""
            try:
                if r.getReferenceType().isWrite():
                    isw = " WRITE"
            except Exception:
                pass
            log("  ref to %s from %s type=%s%s %s" % (hex(a), hex(fr.getOffset()), t, isw, fn_name(fr)))
        a += 1
    log("range xref count: %d" % n)
    return n

def decompile_func(f, depth_label):
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
    """Print + return callers of function f (call-type refs to its entry)."""
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
        log("  caller %s type=%s" % (hex(fr.getOffset()), t))
        log("    -> %s" % cname)
        if cf is not None and cf.getEntryPoint().getOffset() != f.getEntryPoint().getOffset():
            callers.append(cf)
    return callers

def main():
    global out, decomp
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    out = open(LOG, "w", encoding="utf-8")
    decomp = DecompInterface()
    decomp.openProgram(currentProgram)

    log("=== IV WRITER HUNT ===")
    log("program: %s" % currentProgram.getName())
    log("image base: %s" % hex(currentProgram.getImageBase().getOffset()))
    log("IV addr 0x%X, struct head 0x%X, string 0x%X" % (IV_ADDR, STRUCT_ADDR, STRING_ADDR))

    # 0. what's currently stored at the IV / struct in the STATIC image
    ivb = dump_bytes(IV_ADDR, 16)
    log("=== STATIC IMAGE BYTES @ IV ===")
    log("  @0x%X: %s" % (IV_ADDR, hexb(ivb) if ivb else "(unreadable)"))
    log("  healthy match: %s" % (ivb == HEALTHY_IV if ivb else "n/a"))
    log("  failing match: %s" % (ivb == FAILING_IV if ivb else "n/a"))
    sb = dump_bytes(STRUCT_ADDR, 0x100)
    if sb:
        log("  struct head dump (0x%X, 256B):" % STRUCT_ADDR)
        for i in range(0, 0x100, 16):
            chunk = sb[i:i+16]
            log("    +%03X: %s" % (i, hexb(chunk)))
    sb2 = dump_bytes(CONST_AREA, 0x200)
    if sb2:
        log("  const area head dump (0x%X, 512B):" % CONST_AREA)
        for i in range(0, 0x200, 16):
            chunk = sb2[i:i+16]
            log("    +%03X: %s" % (i, hexb(chunk)))

    # 1. direct xrefs to the IV and the struct head (every write ref is gold)
    xrefs_to(IV_ADDR, "IV buffer")
    xrefs_to(STRUCT_ADDR, "struct head")
    xrefs_to_range(STRUCT_ADDR, STRUCT_ADDR + 0x100, "struct head + 0x100")
    xrefs_to(STRING_ADDR, "const string")

    # 2a. whole-image scan: healthy IV blob
    scan_bytes(HEALTHY_IV, "healthy 16B IV blob")
    # 2b. whole-image scan: failing IV blob
    scan_bytes(FAILING_IV, "failing 16B IV blob")
    # 2c. dword pieces, BOTH byte orders (mem order + value order)
    scan_bytes(bytes([0x0C,0xC0,0x1B,0xC5]), "healthy dword[1] mem-order")
    scan_bytes(bytes([0xC5,0x1B,0xC0,0x0C]), "healthy dword[1] value-order")
    scan_bytes(bytes([0x35,0xDB,0x7B,0x86]), "healthy dword[2] mem-order")
    scan_bytes(bytes([0x86,0x7B,0xDB,0x35]), "healthy dword[2] value-order")
    scan_bytes(bytes([0xF5,0xDC,0x16,0x8D]), "failing dword[1] mem-order")
    scan_bytes(bytes([0x8D,0x16,0xDC,0xF5]), "failing dword[1] value-order")
    scan_bytes(bytes([0x3F,0xDB,0x7B,0x86]), "failing dword[2] mem-order")
    scan_bytes(bytes([0x86,0x7B,0xDB,0x3F]), "failing dword[2] value-order")
    # 8-byte halves, both variants
    scan_bytes(bytes([0xD6,0x2A,0xB2,0xC1,0x0C,0xC0,0x1B,0xC5]), "healthy [0:8)")
    scan_bytes(bytes([0x35,0xDB,0x7B,0x86,0x55,0xC7,0xDC,0x3B]), "healthy [8:16)")
    scan_bytes(bytes([0xD6,0x2A,0xB2,0xC1,0xF5,0xDC,0x16,0x8D]), "failing [0:8)")
    scan_bytes(bytes([0x3F,0xDB,0x7B,0x86,0x55,0xC7,0xDC,0x3B]), "failing [8:16)")
    # 2d. low-32 of the target address as LE (rip-relative disp32 / lea / mov forms)
    scan_bytes(bytes([0xE0,0x4C,0xF4,0x41]), "addr low32 E0 4C F4 41 (RIP-resolve)", resolve_rip=True)
    # full 64-bit LE address (movabs forms)
    scan_bytes(bytes([0xE0,0x4C,0xF4,0x41,0x01,0x00,0x00,0x00]), "addr 8B LE (movabs/data ptr)")
    scan_bytes(bytes([0x00,0x4C,0xF4,0x41]), "struct low32 00 4C F4 41 (RIP-resolve)", resolve_rip=True)
    scan_bytes(bytes([0x00,0x4C,0xF4,0x41,0x01,0x00,0x00,0x00]), "struct 8B LE (movabs/data ptr)")
    scan_bytes(bytes([0xA0,0xCA,0xBC,0x41]), "string low32 A0 CA BC 41 (RIP-resolve)", resolve_rip=True)
    scan_bytes(bytes([0xA0,0xCA,0xBC,0x41,0x01,0x00,0x00,0x00]), "string 8B LE (movabs/data ptr)")

    # 3. writer discovery: any function containing a WRITE ref to the IV/struct range
    rm = currentProgram.getReferenceManager()
    log("=== WRITE-REF FUNCTIONS (IV/struct range) ===")
    writers = []
    a = STRUCT_ADDR
    while a <= STRUCT_ADDR + 0x100:
        it = rm.getReferencesTo(addr_of(a))
        while it.hasNext():
            r = it.next()
            try:
                if not r.getReferenceType().isWrite():
                    continue
            except Exception:
                continue
            fr = r.getFromAddress()
            f = getFunctionContaining(fr)
            wname = f.getName() + " @" + hex(f.getEntryPoint().getOffset()) if f is not None else "(no func)"
            log("WRITE ref to %s from %s type=%s" % (hex(a), hex(fr.getOffset()), str(r.getReferenceType())))
            log("  in %s" % wname)
            if f is not None and f not in writers:
                writers.append(f)
        a += 1
    if not writers:
        log("NO DIRECT WRITE-REFS FOUND in the analyzed reference set (writes may be computed/undiscovered).")

    # 4. decompile writers + their callers
    log("=== DECOMPILES ===")
    processed = set()
    for w in writers:
        if w.getEntryPoint().getOffset() in processed:
            continue
        processed.add(w.getEntryPoint().getOffset())
        log("---- WRITER CANDIDATE %s @ %s ----" % (w.getName(), hex(w.getEntryPoint().getOffset())))
        log(decompile_func(w, "writer"))
        c1 = callers_of(w, "writer")
        for c in c1:
            if c.getEntryPoint().getOffset() in processed:
                continue
            processed.add(c.getEntryPoint().getOffset())
            log("---- CALLER-1 %s @ %s ----" % (c.getName(), hex(c.getEntryPoint().getOffset())))
            log(decompile_func(c, "caller-1"))
            c2 = callers_of(c, "caller-1")
            for cc in c2:
                if cc.getEntryPoint().getOffset() in processed:
                    continue
                processed.add(cc.getEntryPoint().getOffset())
                log("---- CALLER-2 %s @ %s ----" % (cc.getName(), hex(cc.getEntryPoint().getOffset())))
                log(decompile_func(cc, "caller-2"))

    # 5. orientation: the known reader (movups @ 0x14423C189) + the validator
    log("---- KNOWN READER FUNCTION (contains movups @ 0x14423C189) ----")
    rf = getFunctionContaining(addr_of(0x14423C189))
    if rf is not None:
        log("reader: %s @ %s" % (rf.getName(), hex(rf.getEntryPoint().getOffset())))
        if rf.getEntryPoint().getOffset() not in processed:
            processed.add(rf.getEntryPoint().getOffset())
            log(decompile_func(rf, "reader"))
        callers_of(rf, "reader")
    else:
        log("reader function NOT FOUND at 0x14423C189 (cold code may not be disassembled in this program)")
    log("---- VALIDATOR FUN_140381dd0 ----")
    vf = getFunctionAt(addr_of(0x140381DD0))
    if vf is not None:
        log(decompile_func(vf, "validator"))
    else:
        log("validator FUN_140381dd0 not found by getFunctionAt")

    log("=== IV-WRITER-HUNT COMPLETE ===")
    out.close()
    print("DONE")

main()
