#!/usr/bin/env python3
"""field_xref.py - find every .text access to a STRUCT FIELD displacement.

The gap this fills: xref_scan.py finds rip-relative references to a DATA RANGE,
and needle_scan.py searches a minidump for u32 values. Neither answers "who
touches [reg + 0xNNN]", which is the question every layout lane ends up asking
(member +181/+183 in 20.152, peer +0xD0 in ms-start-gate3, the transition
manager's +0x2c1 in 20.154). Three hand-rolled greps over ad-hoc disassembly
dumps motivated registering this instead of a fourth.

Method: x86-64 `[reg + disp32]` encodes the displacement as 4 little-endian
bytes inside the instruction, so every access to field +N contains those bytes.
Scan .text for them, then walk back over any SIB byte to the ModRM and the
opcode, and classify the access. Reports VA, classification and raw bytes.

2026-08-31: disp8 support added (mod=01, [reg+disp8] and [base+index+disp8]).
The +0x44 field (entity-index allocation) and the +0x38 field (entity receive
chain) are disp8-encoded and were invisible to the disp32-only scan. Every
disp8 hit is boundary-validated: linear disassembly of the enclosing function
(pdata bounds) confirms the hit address is a real instruction start with the
expected displacement. The 08-31 session's scratch disp8 scanner lacked this
and reported 0x1416F43F6 (mid-call rel32) as a field write — a false positive
that boundary validation eliminates.

False positives are expected and wanted for disp32: an immediate or unrelated
constant can carry the same 4 bytes. The classification column is the filter.
Never treat a bare hit count as an answer.

KNOWN BLIND SPOT (cost a wrong "no writers exist" conclusion on 08-31): this
scan finds only accesses whose encoding CONTAINS the displacement. An access
encoded [base + index*scale] with NO displacement (mod=00 + SIB) has no disp
bytes and is INVISIBLE here — pass --sib-scan BASE to sweep those forms before
concluding "nobody writes this field". Rip-relative forms are xref_scan.py's
territory.

Usage:
  field_xref.py <hex-disp> [more...]        e.g. field_xref.py 0x2c1 0x350
  field_xref.py --disp8 <hex-disp>          e.g. field_xref.py --disp8 0x44
  field_xref.py --sib-scan                  all [base+index*scale] accesses
  field_xref.py --selftest

Exit 1 = no hits for at least one displacement (a result, not silence).
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pe_reader import PE

EXE = Path(__file__).resolve().parent.parent / "RE_output" / "destiny2_unpacked_full.exe"

OPCODES = {
    0x88: ("mov  r/m8, r8", "WRITE"),
    0x89: ("mov  r/m, r", "WRITE"),
    0xC6: ("mov  r/m8, imm8", "WRITE"),
    0xC7: ("mov  r/m, imm32", "WRITE"),
    0x8A: ("mov  r8, r/m8", "read"),
    0x8B: ("mov  r, r/m", "read"),
    0x38: ("cmp  r/m8, r8", "read"),
    0x3A: ("cmp  r8, r/m8", "read"),
    0x39: ("cmp  r/m, r", "read"),
    0x3B: ("cmp  r, r/m", "read"),
    0x80: ("grp1 r/m8, imm8", "read"),
    0x81: ("grp1 r/m, imm32", "read"),
    0x83: ("grp1 r/m, imm8", "read"),
    0x84: ("test r/m8, r8", "read"),
    0x85: ("test r/m, r", "read"),
    0xFE: ("inc/dec r/m8", "RMW"),
    0xFF: ("inc/dec/call r/m", "RMW"),
}

SIB_REGS = ["rax", "rcx", "rdx", "rbx", "rsp", "rbp", "rsi", "rdi"]


# ---- disp32 (mod=10) ---------------------------------------------------------

def classify(data, pos):
    """@param pos Offset of the disp32's first byte. @return (mnemonic, access, start)."""
    for sib in (0, 1):
        modrm_at = pos - 1 - sib
        if modrm_at < 2:
            continue
        modrm = data[modrm_at]
        if modrm >> 6 != 0b10:
            continue
        if (modrm & 7 == 0b100) != bool(sib):
            continue
        op_at = modrm_at - 1
        op = data[op_at]
        if op == 0xB6 or op == 0xB7:
            if op_at >= 1 and data[op_at - 1] == 0x0F:
                return ("movzx r, r/m8", "read", op_at - 1)
            continue
        if op in OPCODES:
            m, a = OPCODES[op]
            return (m, a, op_at)
    return None


def scan(pe, disp):
    needle = struct.pack("<i", disp)
    hits = []
    for name, vaddr, vsize, rawptr, rawsize in pe.sections:
        if name != ".text":
            continue
        data = pe.data[rawptr:rawptr + rawsize]
        pos = 0
        while True:
            p = data.find(needle, pos)
            if p < 0:
                break
            pos = p + 1
            c = classify(data, p)
            if c is None:
                continue
            m, a, start = c
            va = pe.imagebase + vaddr + start
            hits.append((va, a, m, data[start:p + 8].hex()))
    return hits


# ---- disp8 (mod=01) ----------------------------------------------------------

def classify8(data, pos):
    """Walk back from a disp8 byte at data[pos] to classify the instruction.
    mod=01 is the [reg+disp8] form; with SIB it's [base+index*scale+disp8].
    Returns (mnemonic, access, start) or None."""
    for sib in (0, 1):
        modrm_at = pos - 1 - sib
        if modrm_at < 2:
            continue
        modrm = data[modrm_at]
        if modrm >> 6 != 0b01:
            continue
        if (modrm & 7 == 0b100) != bool(sib):
            continue
        op_at = modrm_at - 1
        op = data[op_at]
        if op in (0xB6, 0xB7, 0xBE, 0xBF):
            if op_at >= 1 and data[op_at - 1] == 0x0F:
                names = {0xB6: "movzx r32, r/m8", 0xB7: "movzx r32, r/m16",
                         0xBE: "movsx r32, r/m8", 0xBF: "movsx r32, r/m16"}
                return (names[op], "read", op_at - 1)
            continue
        if op in OPCODES:
            m, a = OPCODES[op]
            return (m, a, op_at)
    return None


def scan8_raw(pe, disp8_byte):
    """Byte-scan .text for disp8 candidates (unvalidated).
    Returns list of (va, access, mnemonic, data, pos)."""
    needle = bytes([disp8_byte & 0xFF])
    hits = []
    for name, vaddr, vsize, rawptr, rawsize in pe.sections:
        if name != ".text":
            continue
        data = pe.data[rawptr:rawptr + rawsize]
        pos = 0
        while True:
            p = data.find(needle, pos)
            if p < 0:
                break
            pos = p + 1
            c = classify8(data, p)
            if c is None:
                continue
            m, a, start = c
            va = pe.imagebase + vaddr + start
            hits.append((va, a, m, data, p))
    return hits


def validate8(pe, candidates, disp8_signed):
    """Boundary-validate disp8 candidates: for each enclosing function
    (pdata bounds), linear-disassemble once and check which candidate
    addresses are real instruction starts with the expected displacement.
    Returns dict: candidate_va -> (confirmed, instruction_str)."""
    from collections import defaultdict
    import capstone
    by_func = defaultdict(list)
    for va, _a, _m, _d, _p in candidates:
        bounds = pe.pdata_bounds(va)
        if bounds:
            by_func[bounds].append(va)
        else:
            by_func[("no-pdata", va)].append(va)

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    results = {}
    for bounds, vas in by_func.items():
        if bounds[0] == "no-pdata":
            # no pdata: fall back to capstone forward-decode at the candidate
            # address - a valid decode with the right disp is evidence the
            # address is a real instruction boundary (weaker than the pdata
            # sweep but stronger than "cannot validate")
            for va in vas:
                code = pe.read(va, 16)
                if not code:
                    results[va] = (False, "no pdata + cannot read bytes")
                    continue
                matched = False
                detail = ""
                for insn in md.disasm(code, va):
                    has_disp = any(
                        op.type == capstone.x86.X86_OP_MEM and
                        op.mem.disp == disp8_signed
                        for op in insn.operands)
                    if has_disp:
                        matched = True
                        detail = f"decoded (no pdata): {insn.mnemonic} {insn.op_str}"
                    break
                results[va] = (matched, detail or "no pdata, no disp match")
            continue
        fstart, fend = bounds
        code = pe.read(fstart, fend - fstart)
        if not code:
            for va in vas:
                results[va] = (False, "cannot read function bytes")
            continue
        insn_map = {}
        for insn in md.disasm(code, fstart):
            has_disp = any(
                op.type == capstone.x86.X86_OP_MEM and
                op.mem.disp == disp8_signed
                for op in insn.operands)
            insn_map[insn.address] = (insn.mnemonic, insn.op_str, has_disp)
        for va in vas:
            if va in insn_map:
                m, ops, dm = insn_map[va]
                results[va] = (dm, f"{m} {ops}")
            else:
                results[va] = (False, "mid-instruction in linear sweep")
    return results


def scan8(pe, disp8_signed, validate=True):
    """Full disp8 pipeline: raw scan → classify8 → boundary validation.
    Returns list of (va, access, mnemonic, validated, instruction_str)."""
    candidates = scan8_raw(pe, disp8_signed)
    if not validate:
        return [(va, a, m, False, "unvalidated")
                for va, a, m, _d, _p in candidates]
    vresults = validate8(pe, candidates, disp8_signed)
    out = []
    for va, a, m, _d, _p in candidates:
        confirmed, detail = vresults.get(va, (False, "not checked"))
        out.append((va, a, m, confirmed, detail))
    return out


# ---- sib (mod=00, no displacement) -------------------------------------------

def sib_scan(pe):
    """All [base + index*scale] accesses (mod=00 + SIB, no displacement).
    The disp32 scan cannot see these - they are the allocator/indexed-write
    class that motivated the blind-spot note. Returns (va, mnem, sib_desc)."""
    hits = []
    for name, vaddr, vsize, rawptr, rawsize in pe.sections:
        if name != ".text":
            continue
        data = pe.data[rawptr:rawptr + rawsize]
        n = len(data) - 2
        for p in range(n):
            modrm = data[p]
            if modrm >> 6 != 0b00 or (modrm & 7) != 0b100:
                continue
            sib = data[p + 1]
            scale = 1 << (sib >> 6)
            index = (sib >> 3) & 7
            breg = sib & 7
            if index == 0b100:
                continue
            if breg == 0b101:
                continue
            op_at = p - 1
            op = data[op_at]
            m, a = OPCODES.get(op, (None, None))
            if m is None:
                continue
            va = pe.imagebase + vaddr + op_at
            desc = "[%s+%s*%d]" % (SIB_REGS[breg], SIB_REGS[index], scale)
            hits.append((va, a, m, desc))
    return hits


# ---- selftest ----------------------------------------------------------------

def selftest():
    """Oracle: disp32 accesses from 20.152/20.154 + disp8 accesses from the
    +0x44 entity-index lane. The false positive 0x1416F43F6 must NOT appear
    as a validated hit."""
    pe = PE(str(EXE))
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print(f"  {'PASS' if cond else 'FAIL'} {name:<52s} {detail}")
        if not cond:
            ok = False

    print("== disp32 (existing oracle) ==")
    cases = [
        (0x2c1, 0x140E23002, "read"),
        (0x350, 0x140E2B405, "WRITE"),
        (0x53c, 0x140E289EF, "WRITE"),
    ]
    for disp, want_va, want_access in cases:
        hits = {va: acc for va, acc, _m, _b in scan(pe, disp)}
        got = hits.get(want_va)
        good = got == want_access
        check(f"disp32 {disp:#x} at {want_va:#x}", good,
              f"expect={want_access} got={got}")
    bogus = scan(pe, 0x7FFFFF)
    stores = [h for h in bogus if h[1] == "WRITE"]
    check("negative disp=0x7fffff -> 0 classified writes", not stores,
          f"{len(stores)} found")

    print("== disp8 (mod=01, the +0x44 entity-index field) ==")
    d8 = 0x44
    results = scan8(pe, d8)
    validated = {va: (conf, det) for va, a, m, conf, det in results
                 if conf}
    for want_va in (0x1416E9CF0, 0x1416EBD51, 0x14171812A):
        conf, det = validated.get(want_va, (False, ""))
        check(f"disp8 confirmed hit at {want_va:#x}", conf, det[:60])
    fp = 0x1416F43F6
    fp_conf, fp_det = validated.get(fp, (False, "not in results"))
    check(f"false positive {fp:#x} NOT validated", not fp_conf,
          fp_det[:60] if fp_det else "correctly absent")

    print("SELFTEST", "OK" if ok else "FAILED")
    return 0 if ok else 1


# ---- CLI ---------------------------------------------------------------------

def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "--selftest":
        return selftest()
    pe = PE(str(EXE))
    if argv[0] == "--sib-scan":
        hits = sib_scan(pe)
        for va, access, mnem, desc in sorted(hits):
            print(f"  {va:#012x}  {access:<5}  {mnem:<18} {desc}")
        print(f"-- {len(hits)} indexed access(es) (no displacement)")
        return 0
    if argv[0] == "--disp8":
        if len(argv) < 2:
            print("usage: --disp8 <hex-displacement>")
            return 2
        disp = int(argv[1], 16)
        signed = disp if disp < 0x80 else disp - 0x100
        results = scan8(pe, signed)
        confirmed = [(va, a, m, det) for va, a, m, c, det in results if c]
        rejected = [(va, a, m, det) for va, a, m, c, det in results if not c]
        print(f"=== disp8 field +{disp:#x} ({signed}): "
              f"{len(confirmed)} confirmed, {len(rejected)} rejected ===")
        for va, access, mnem, det in sorted(confirmed):
            print(f"  {va:#012x}  {access:<5}  {mnem:<18} CONFIRMED  {det}")
        for va, access, mnem, det in sorted(rejected):
            print(f"  {va:#012x}  REJECTED  {det}")
        return 0
    empty = False
    for arg in argv:
        disp = int(arg, 16)
        hits = scan(pe, disp)
        writes = [h for h in hits if h[1] in ("WRITE", "RMW")]
        print(f"\n=== field +{disp:#x}: {len(hits)} classified access(es), "
              f"{len(writes)} write/RMW ===")
        for va, access, mnem, raw in sorted(hits):
            print(f"  {va:#012x}  {access:<5}  {mnem:<18} {raw}")
        if not hits:
            empty = True
            print("  NOTE: disp32 scans cannot see [base+index*scale] forms "
                  "(no disp bytes) or rip-relative forms — use --sib-scan / "
                  "xref_scan.py before concluding 'nobody touches this'.")
            if disp <= 0x7F:
                print("  NOTE: disp fits in disp8 range — also run "
                      f"--disp8 {disp:#x} for mod=01 encodings.")
    return 1 if empty else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
