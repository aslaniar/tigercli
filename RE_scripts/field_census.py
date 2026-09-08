#!/usr/bin/env python3
# REGISTRY: caps: field-census, disp-scan
"""field_census.py - every [reg + disp32] access to a displacement across the
carved runtime image (shadow-window verified). The identity discriminator for
the gate-machine's singleton manager: whose code touches ITS field offsets
names its owner (candidate A = entity-index manager, candidate B = sibling).

Usage: field_census.py <carved_exe> <disp> [more...]   e.g. 0x206b8 0x560f0
Same verification rules as gate_census.py (a covering decode must rip- or
base-reference the exact displacement; misaligned decodes rejected).
"""
import struct
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64, x86

IMG = 0x140000000


def main():
    exe = sys.argv[1]
    disps = [int(x, 16) for x in sys.argv[2:]]
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

    def verify(base_va, sec, sec_vaddr, va, disp):
        srel = va - IMG - sec_vaddr
        PRE = 15
        start_idx = srel - PRE
        if start_idx < 0:
            PRE = srel
            start_idx = 0
            if PRE <= 0:
                return None
        back = sec[start_idx: srel + 8]
        for d in range(1, PRE + 1):
            try:
                for ins in md.disasm(back[PRE - d:], va - d):
                    if ins.address > va:
                        break
                    if ins.address + ins.size >= va + 4:
                        for op in ins.operands:
                            if op.type == x86.X86_OP_MEM and op.mem.disp == disp:
                                memop = op
                                mi = ins.operands.index(memop)
                                size = memop.size
                                if ins.mnemonic in ("movzx", "movsx", "cmp", "test", "lea"):
                                    kind = "R" if ins.mnemonic != "lea" else "LEA"
                                elif ins.mnemonic in ("add", "sub", "and", "or", "xor",
                                                      "inc", "dec", "neg", "not"):
                                    kind = "RW"
                                elif ins.mnemonic == "mov":
                                    kind = "W" if mi == 0 else "R"
                                else:
                                    kind = "?"
                                return (kind, size, f"{ins.mnemonic} {ins.op_str}")
                        break
            except Exception:
                continue
        return None

    results = []
    for name, vaddr, vsz, raddr, n in secs:
        if "text" not in name and "vmp" not in name:
            continue
        sec = data[raddr:raddr + n]
        base_va = IMG + vaddr
        disp_used = {}
        hits = []
        for disp in disps:
            dbytes = struct.pack("<I", disp)
            j = sec.find(dbytes)
            while j != -1:
                va = base_va + j
                disp_used[va] = disp
                v = verify(base_va, sec, vaddr, va, disp)
                if v:
                    hits.append((va, *v))
                j = sec.find(dbytes, j + 1)
        for va, kind, size, txt in sorted(hits):
            results.append((va, name, disp_used.get(va, 0), kind, size, txt))
        print(f"  scanned {name}: {n} bytes", file=sys.stderr)

    results.sort()
    cur = None
    for va, secname, disp, kind, size, txt in results:
        fkey = (va >> 16) << 16
        if fkey != cur:
            cur = fkey
            print(f"\n  -- around 0x{va:X} ({secname}):")
        print(f"  0x{va:X} [{disp:+#x}] {kind} size={size}   [{txt}]")


if __name__ == "__main__":
    main()
