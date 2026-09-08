#!/usr/bin/env python3
# REGISTRY: caps: gate-census, disp-scan
"""gate_census.py - verified READ/WRITE census of the gate cluster
(0x142037AF0..0x142037B40) across the carved runtime image.

Answers (2026-09-07, p2-211 front): WHO writes the gate bytes - specifically
who SETS them nonzero (the record's "no readable writer - VMP-set" claim),
who clears them, and who only reads. Every raw disp candidate is
shadow-window verified: an instruction must decode such that it CONTAINS the
4 disp bytes and capstone's rip-relative target equals the candidate target
(the verification the 09-03/09-08 misread classes demand).

Method: raw scan of every byte offset in every section (disp32 at offset i,
target = va_i + 4 + s32); shadow-window decode from up to 15 bytes back;
classify by mnemonic + operand order (R / W / RW) + immediate value.
Blind spot (declared): absolute-addressing forms (movabs reg,addr; mov [reg])
are covered by a separate 8-byte imm64 sweep, reported separately.

Usage: gate_census.py <carved_exe>
"""
import struct
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64, x86

IMG = 0x140000000
LO, HI = 0x142037AF0, 0x142037B40

READ_MNEMS = {"movzx", "movsx", "cmp", "test", "lea"}
RW_MNEMS = {"add", "sub", "and", "or", "xor", "inc", "dec", "neg", "not", "xadd"}


def main():
    exe = sys.argv[1]
    data = open(exe, "rb").read()
    e = struct.unpack_from("<I", data, 0x3C)[0]
    coff = e + 4
    nsec = struct.unpack_from("<H", data, coff + 2)[0]
    opt = coff + 20
    sec_off = opt + struct.unpack_from("<H", data, coff + 16)[0]
    secs = []
    for i in range(nsec):
        s = data[sec_off + i * 40: sec_off + (i + 1) * 40]
        name = s[:8].rstrip(b"\0").decode(errors="replace")
        vsz, vaddr, rsz, raddr, _ = struct.unpack_from("<IIIII", s, 8)
        secs.append((name, vaddr, vsz, raddr, min(rsz, vsz)))

    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True

    def mem_target(ins):
        """rip-relative target if the instruction has one, else None."""
        for op in ins.operands:
            if op.type == x86.X86_OP_MEM and op.mem.base == x86.X86_REG_RIP:
                return ins.address + ins.size + op.mem.disp
        return None

    def verify(va, tgt, secname, sec_vaddr, sec_data, sec_raddr):
        """shadow-window: an instruction containing the disp whose computed
        target == tgt. Returns (kind, size, imm, mnem) or None."""
        srel = va - IMG - sec_vaddr          # SECTION-relative offset
        PRE = 15
        start_idx = srel - PRE
        if start_idx < 0:
            PRE = srel
            start_idx = 0
            if PRE <= 0:
                return None
        back = sec_data[start_idx: srel + 8]
        for d in range(1, PRE + 1):
            try:
                for ins in md.disasm(back[PRE - d:], va - d):
                    if ins.address > va:
                        break          # this boundary never covers the disp
                    if ins.address + ins.size >= va + 4:
                        # covering decode: does it rip-reference our target?
                        t = mem_target(ins)
                        if t == tgt:
                            ops = ins.operands
                            memop = next((o for o in ops
                                          if o.type == x86.X86_OP_MEM
                                          and o.mem.base == x86.X86_REG_RIP), None)
                            mi = ops.index(memop)
                            size = memop.size
                            imm = None
                            if len(ops) > mi + 1 and ops[mi + 1].type == x86.X86_OP_IMM:
                                imm = ops[mi + 1].imm
                            if ins.mnemonic in READ_MNEMS:
                                kind = "R"
                            elif ins.mnemonic in RW_MNEMS:
                                kind = "RW"
                            elif ins.mnemonic == "mov":
                                kind = "W" if mi == 0 else "R"
                            else:
                                kind = "?"
                            return (kind, size, imm, f"{ins.mnemonic} {ins.op_str}")
                        break              # covers, different target: next d
                    # instruction ends before the disp: keep decoding linearly
            except Exception:
                continue
        return None

    results = []
    abs_hits = []
    for name, vaddr, vsz, raddr, n in secs:
        if "text" not in name and "vmp" not in name:
            continue
        sec = data[raddr:raddr + n]
        base_va = IMG + vaddr
        raw = 0
        for i in range(len(sec) - 4):
            dv = struct.unpack_from("<i", sec, i)[0]
            tgt = base_va + i + 4 + dv
            if LO <= tgt < HI:
                raw += 1
                va = base_va + i
                v = verify(va, tgt, name, vaddr, sec, raddr)
                if v:
                    results.append((va, name, tgt, *v))
        # absolute imm64 sweep
        for a in range(LO, HI):
            needle = struct.pack("<Q", a)
            j = sec.find(needle)
            while j != -1:
                abs_hits.append((base_va + j - 2, name, a))  # -2: movabs opcode+reg
                j = sec.find(needle, j + 1)
        print(f"  scanned {name}: {n} bytes", file=sys.stderr)

    results.sort()
    print(f"\nVERIFIED refs: {len(results)}   (absolute-imm64 candidates: {len(abs_hits)})")
    cur = None
    for va, secname, tgt, kind, size, imm, txt in results:
        fkey = va & ~0xFFF
        if fkey != cur:
            cur = fkey
            print(f"\n  -- around 0x{va:X} ({secname}):")
        val = f" imm={imm}" if imm is not None else ""
        print(f"  0x{va:X} {kind}  size={size}  ->0x{tgt:X}{val}   [{txt}]")
    for va, secname, a in abs_hits[:20]:
        print(f"  ABS 0x{va:X} ({secname}) holds address 0x{a:X}")


if __name__ == "__main__":
    main()
