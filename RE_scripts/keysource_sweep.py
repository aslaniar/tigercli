"""Sweep every call site of the four schema-walk entries (byte-level E8 scan)
and classify each site's key operand source.

v2: v1 used a single linear capstone pass that stalls on embedded data after
~6k insns of 28 MB (.text). Call sites are found here by scanning raw bytes
for E8 rel32 whose target equals an entry - no decode needed - and only then
decoding a 64-B window before each site.
"""
import sys
import os
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe_reader import PE
import capstone

IMAGE = ("/Users/rubenaslanian/Documents/opencode/sunrise-fork/"
         "RE_output/destiny2_unpacked_full.exe")
ENTRIES = {0x1404C72E0: "c72e0", 0x1404C74B0: "c74b0",
           0x1404C74D0: "c74d0", 0x1404C1930: "c1930"}


def main():
    pe = PE(IMAGE)
    for name, vaddr, vsize, rawptr, rawsize in pe.sections:
        if name == ".text":
            base = pe.imagebase + vaddr
            code = pe.data[rawptr:rawptr + rawsize]
            break
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True

    sites = []
    n = len(code)
    for p in range(n - 5):
        if code[p] != 0xE8:
            continue
        disp = struct.unpack_from("<i", code, p + 1)[0]
        tgt = base + p + 5 + disp
        if tgt in ENTRIES:
            sites.append((base + p, tgt))
    print("walk call sites found: %d" % len(sites))

    candidates = {}
    for site_va, tgt in sites:
        off = site_va - base
        wstart = max(0, off - 64)
        window = code[wstart:off]
        insns = list(md.disasm(window, base + wstart))
        # walk backwards through decoded window
        keyreg = (capstone.x86.X86_REG_R9D if tgt in (0x1404C72E0, 0x1404C74D0)
                  else capstone.x86.X86_REG_ECX)
        src = None
        for j in range(len(insns) - 1, -1, -1):
            q = insns[j]
            if q.mnemonic == "call" and q.address != site_va:
                break
            if q.mnemonic not in ("mov", "lea") or len(q.operands) != 2:
                continue
            dst, srcop = q.operands
            if dst.type != capstone.x86.X86_OP_REG:
                continue
            # mov KEYREG, imm32 -> immediate key
            if dst.reg == keyreg and srcop.type == capstone.x86.X86_OP_IMM \
                    and q.mnemonic == "mov":
                src = ("imm", srcop.imm & 0xFFFFFFFF)
                break
            # mov REG, [rip+d]  -> pointer global (key read through it)
            if srcop.type == capstone.x86.X86_OP_MEM \
                    and srcop.mem.base == capstone.x86.X86_REG_RIP:
                tgtg = q.address + q.size + srcop.mem.disp
                # does a later insn deref THIS reg into KEYREG?
                for q2 in insns[j + 1:]:
                    if q2.address >= site_va:
                        break
                    if q2.mnemonic == "mov" and len(q2.operands) == 2 \
                            and q2.operands[0].type == capstone.x86.X86_OP_REG \
                            and q2.operands[0].reg == keyreg \
                            and q2.operands[1].type == capstone.x86.X86_OP_MEM \
                            and q2.operands[1].mem.base == dst.reg \
                            and q2.operands[1].mem.index == 0 \
                            and q2.operands[1].mem.disp == 0:
                        src = ("ptr_global", tgtg)
                        break
                if src:
                    break
            # mov REG, imm ; ... mov KEYREG, REG  (track one hop)
            if srcop.type == capstone.x86.X86_OP_IMM and q.mnemonic == "mov":
                nxt = insns[j + 1:j + 4]
                for q2 in nxt:
                    if q2.mnemonic == "mov" and \
                            q2.operands[0].type == capstone.x86.X86_OP_REG and \
                            q2.operands[1].type == capstone.x86.X86_OP_REG and \
                            q2.operands[1].reg == dst.reg:
                        # reg copied onward; remember imm candidate anyway
                        src = ("imm_via_%s" % q.mnemonic,
                               srcop.imm & 0xFFFFFFFF)
        label = "%s@%X" % (ENTRIES[tgt], site_va)
        if src:
            kind, val = src
            candidates.setdefault("%s:%#x" % (kind, val), []).append(label)
        else:
            candidates.setdefault("unclassified", []).append(label)
    print("unique sources: %d" % len(candidates))
    for k in sorted(candidates):
        lst = candidates[k]
        print("  %-24s %d site(s)  e.g. %s" % (k, len(lst), lst[:3]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
