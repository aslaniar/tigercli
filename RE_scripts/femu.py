#!/usr/bin/env python3
"""femu.py - function emulation rig for the unpacked client binary.

Layer-by-layer (each layer has its own selftest section):
  L1  map the PE image at its virtual addresses into a Unicorn x86-64 VM
  L2  call harness: fake stack, MS x64 arg registers, return-address trap,
      instruction cap, invalid-memory crash hook (all failures fail LOUD
      with a reason - never hang, never guess)
  L3  import hooks: IAT slots are redirected to stubs; any import call is
      recorded and stops the run (purity classification falls out of this)
  L4  real-binary verification: the documented reason_name accessor
      (0x1416E1620, FINDINGS 20.85/20.86) must return table pointers that
      MATCH the file bytes - execution vs file, an independent oracle.

The point: night-agent questions of the form "what does this function DO"
get answered by EXECUTION for pure-compute functions, marked
verified-by-execution, without a boot. Impure functions fail LOUD with the
reason (which import / which fault) - that classification is itself
map-worthy output.

INTERPRETER: miniconda python3 (needs `unicorn`; capstone for the signature
precondition check).

Usage:
  python3 RE_scripts/femu.py --selftest
  python3 RE_scripts/femu.py --call 0x1416E1620 --args 0
  python3 RE_scripts/femu.py --call ADDR --args a,b,c --max-insn 200000
      [--binary PATH] [--wmem ADDR=HEXBYTES]...

Exit codes: 0 pass/hit; 1 failure/abort; 2 usage.
"""
import argparse
import struct
import sys
import os

import unicorn
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_PROT_ALL
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_INVALID
from unicorn.x86_const import (UC_X86_REG_RAX, UC_X86_REG_RCX,
                               UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9,
                               UC_X86_REG_RSP, UC_X86_REG_RIP)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe_reader import PE

try:
    import capstone
    HAVE_CAPSTONE = True
except ImportError:
    HAVE_CAPSTONE = False

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BINARY = os.path.join(ROOT, "RE_output", "destiny2_unpacked_full.exe")

STACK_BASE = 0x500000000000
STACK_SIZE = 0x100000
RET_MAGIC = 0x600000000000          # return-address trap page
STUB_BASE = 0x600000001000          # import stubs land here
STUB_REGION = 0x10000
SCRATCH_BASE = 0x600000200000       # caller-provided buffers (--wmem etc.)
MAX_INSN_DEFAULT = 200000

REASON_NAME_FN = 0x1416E1620
REASON_NAME_TABLE = 0x142037510


class EmuResult(object):
    def __init__(self):
        self.reason = None           # returned | timeout | crash:<kind> | import:<name>
        self.fault_addr = None
        self.rax = None
        self.insn_count = 0
        self.imports_called = []
        self.detail = ""


class Rig(object):
    """One Rig = one mapped image; reusable across calls (fresh stack per call)."""

    def __init__(self, binary_path):
        self.pe = PE(binary_path)
        self.path = binary_path
        # SizeOfImage: optional header + 56 (PE32+)
        opt = 0x3C + 4 + 20
        self.size_of_image = struct.unpack_from("<I", self.pe.data, opt + 56)[0]
        self.uc = Uc(UC_ARCH_X86, UC_MODE_64)
        self.imports = {}            # stub_addr -> name
        self.imports_by_slot = {}    # iat_slot_va -> name
        self._load_image()
        self._map_support()
        self._parse_imports()
        self.last_result = None

    # ---- L1 -------------------------------------------------------------
    def _load_image(self):
        span = (self.size_of_image + 0xFFF) & ~0xFFF
        self.uc.mem_map(self.pe.imagebase, span, UC_PROT_ALL)
        for name, vaddr, vsize, rawptr, rawsize in self.pe.sections:
            if rawsize:
                self.uc.mem_write(self.pe.imagebase + vaddr,
                                  self.pe.data[rawptr:rawptr + rawsize])
        self.span = span

    def file_bytes(self, va, n):
        return self.pe.read(va, n)

    # ---- L3 -------------------------------------------------------------
    def _parse_imports(self):
        """Parse the import directory; redirect every IAT slot to a stub.
        Any call into the stub region is recorded + stops (purity abort).
        NOTE: this unpacked binary's DataDirectory is DESTROYED (all 16
        entries junk - unpacker artifact); the unpacker rebuilt the real
        import table into an appended .idata section, which is the fallback.
        """
        base = self.pe.imagebase
        opt = 0x3C + 4 + 20
        dir_rva, dir_size = struct.unpack_from("<II", self.pe.data, opt + 112 + 8)
        start = None
        if dir_rva and self.pe.section_of(base + dir_rva):
            start = dir_rva
        else:
            idata = [s for s in self.pe.sections if s[0] == ".idata"]
            if idata:
                start = idata[0][1]
        if start is None:
            return
        d = start
        while True:
            doff = self.pe.off(base + d)
            if doff is None:
                break
            oft, _ts, _fc, name_rva, ft = struct.unpack_from(
                "<IIIII", self.pe.data, doff)
            if oft == 0 and ft == 0:
                break
            dll = ""
            nb = self.pe.read(base + name_rva, 64) or b""
            dll = nb.split(b"\0")[0].decode("ascii", "replace")
            i = 0
            while True:
                entry = self.pe.read(base + oft + 8 * i, 8) if oft else \
                    self.pe.read(base + ft + 8 * i, 8)
                if not entry or struct.unpack("<Q", entry)[0] == 0:
                    break
                val = struct.unpack("<Q", entry)[0]
                if val & (1 << 63):
                    fname = "%s!ordinal%d" % (dll, val & 0xFFFF)
                else:
                    nb = self.pe.read(base + (val & 0x7FFFFFFF), 64) or b""
                    fname = "%s!%s" % (dll, nb[2:].split(b"\0")[0].decode(
                        "ascii", "replace"))
                stub = STUB_BASE + 8 * len(self.imports)
                self.uc.mem_write(base + ft + 8 * i,
                                  struct.pack("<Q", stub))
                # stub body: 'ret' (the code hook stops execution before it runs)
                self.uc.mem_write(stub, b"\xc3")
                self.imports[stub] = fname
                self.imports_by_slot[base + ft + 8 * i] = fname
                i += 1
            d += 20

    def _map_support(self):
        self.uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_ALL)
        self.uc.mem_map(RET_MAGIC, 0x1000, UC_PROT_ALL)
        self.uc.mem_map(STUB_BASE, STUB_REGION, UC_PROT_ALL)
        self.uc.mem_map(SCRATCH_BASE, 0x10000, UC_PROT_ALL)
        self.uc.mem_write(RET_MAGIC, b"\xc3")
        self.uc.hook_add(UC_HOOK_CODE, self._hook_code)
        self.uc.hook_add(UC_HOOK_MEM_INVALID, self._hook_mem_invalid)

    def _hook_code(self, uc, address, size, user_data):
        if address == RET_MAGIC:
            uc.emu_stop()
        elif STUB_BASE <= address < STUB_BASE + STUB_REGION:
            name = self.imports.get(address, "unknown-import")
            r = self.last_result
            r.imports_called.append(name)
            r.reason = "import:" + name
            uc.emu_stop()

    def _hook_mem_invalid(self, uc, access, address, size, value, user_data):
        r = self.last_result
        kinds = {
            unicorn.UC_MEM_READ_UNMAPPED: "read",
            unicorn.UC_MEM_WRITE_UNMAPPED: "write",
            unicorn.UC_MEM_FETCH_UNMAPPED: "fetch",
            unicorn.UC_MEM_READ_PROT: "read-prot",
            unicorn.UC_MEM_WRITE_PROT: "write-prot",
            unicorn.UC_MEM_FETCH_PROT: "fetch-prot",
        }
        r.reason = "crash:%s-unmapped" % kinds.get(access, "?%d" % access)
        r.fault_addr = address
        uc.emu_stop()
        return False

    # ---- L2 -------------------------------------------------------------
    def call(self, addr, args, max_insn=MAX_INSN_DEFAULT, wmem=None):
        """Call the function at addr with int args (MS x64: RCX,RDX,R8,R9).
        wmem: list of (addr, bytes) written before the run (buffers/grafts)."""
        res = EmuResult()
        self.last_result = res
        regs = [UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9]
        for r in self.imports:
            pass  # stubs persist across calls (idempotent mapping)
        for r_ in ():
            pass
        self._fresh_stack()
        for reg, val in zip(regs, args):
            self.uc.reg_write(reg, val & 0xFFFFFFFFFFFFFFFF)
        if wmem:
            for a, data in wmem:
                self.uc.mem_write(a, data)
        rsp = self.stack_top
        self.uc.mem_write(rsp, struct.pack("<Q", RET_MAGIC))  # return address
        self.uc.reg_write(UC_X86_REG_RSP, rsp)
        stopped_at = None
        try:
            self.uc.emu_start(addr, RET_MAGIC, 0, max_insn)
        except unicorn.UcError as exc:
            res.reason = res.reason or "crash:uc-%s" % exc
        rip = self.uc.reg_read(UC_X86_REG_RIP)
        res.rax = self.uc.reg_read(UC_X86_REG_RAX)
        if res.reason is None:
            if rip == RET_MAGIC:
                res.reason = "returned"
            else:
                res.reason = "timeout"
                res.detail = "stopped at 0x%x after %d insns" % (rip, max_insn)
        return res

    def _fresh_stack(self):
        if not hasattr(self, "stack_top"):
            self.stack_top = STACK_BASE + STACK_SIZE // 2
        # 64KB of untouched stack per call (old frames abandoned, not reused)
        self.stack_top -= 0x10000
        if self.stack_top < STACK_BASE + 0x1000:
            self.stack_top = STACK_BASE + STACK_SIZE // 2
        self.uc.reg_write(UC_X86_REG_RSP, self.stack_top + 0x10000)


# ------------------------------------------------------------- selftest ---
def selftest(binary_path):
    fails = []

    def check(name, cond, detail=""):
        print("%s %-52s %s" % ("PASS" if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    rig = Rig(binary_path)

    print("== L1: image mapping matches file bytes ==")
    import random
    random.seed(20260829)
    text = [s for s in rig.pe.sections if s[0] == ".text"][0]
    base = rig.pe.imagebase
    ok = True
    for _ in range(16):
        va = base + text[1] + random.randrange(0, text[2] - 16)
        if rig.uc.mem_read(va, 16) != rig.pe.read(va, 16):
            ok = False
            break
    check("16 random .text VAs: mapped == file", ok, "at 0x%x" % va)
    rdata = [s for s in rig.pe.sections if s[0] == ".rdata"]
    if rdata:
        va = base + rdata[0][1] + 0x100
        check(".rdata mapped == file", rig.uc.mem_read(va, 16) ==
              rig.pe.read(va, 16))

    print("== L2: call harness (synthetic code) ==")
    scratch = SCRATCH_BASE
    # addends: mov eax, ecx; add eax, edx; ret
    rig.uc.mem_write(scratch, b"\x89\xc8\x01\xd0\xc3")
    res = rig.call(scratch, [5, 7])
    check("synthetic add(5,7) == 12", res.reason == "returned" and
          res.rax == 12, "reason=%s rax=%s" % (res.reason, res.rax))
    # infinite loop: jmp $ -> must hit the instruction cap, not hang
    rig.uc.mem_write(scratch + 0x100, b"\xeb\xfe")
    res = rig.call(scratch + 0x100, [], max_insn=10000)
    check("infinite loop -> timeout (cap honored)", res.reason == "timeout",
          "reason=%s" % res.reason)
    # unmapped read: movabs rax,0x123456789; mov eax,[rax]; ret -> crash hook
    # (0x123456789 LE = 89 67 45 23 01 00 00 00 - this test line went through
    # two hand-encoding errors before passing; the rig's fault reporting was
    # byte-accurate on every attempt, which is exactly why it is trusted)
    rig.uc.mem_write(scratch + 0x200,
                     b"\x48\xb8\x89\x67\x45\x23\x01\x00\x00\x00\x8b\x00\xc3")
    res = rig.call(scratch + 0x200, [])
    check("unmapped read -> loud crash w/ fault addr",
          res.reason == "crash:read-unmapped" and
          res.fault_addr == 0x123456789,
          "reason=%s addr=%s" % (res.reason, hex(res.fault_addr or 0)))

    print("== L3: import hooks ==")
    # synthetic call through a real IAT slot (find one with a name)
    if rig.imports_by_slot:
        slot = sorted(rig.imports_by_slot)[0]
        iname = rig.imports_by_slot[slot]
        # mov rax, [slot]; call rax; ret   (call THROUGH the IAT slot)
        code = b"\x48\xa1" + struct.pack("<Q", slot) + b"\xff\xd0\xc3"
        rig.uc.mem_write(scratch + 0x300, code)
        res = rig.call(scratch + 0x300, [])
        check("IAT call -> recorded + purity abort",
              res.reason == "import:" + iname and
              res.imports_called == [iname],
              "reason=%s" % res.reason)
    else:
        check("imports present in binary", False, "none parsed?")

    print("== L4: real binary - reason_name accessor (FINDINGS 20.85) ==")
    table_bytes = rig.pe.read(REASON_NAME_TABLE, 8 * 0x24)
    check("reason table readable from file", table_bytes is not None and
          len(table_bytes) == 8 * 0x24)
    if HAVE_CAPSTONE:
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        insns = list(md.disasm(rig.pe.read(REASON_NAME_FN, 16),
                               REASON_NAME_FN))
        sig = insns[0].mnemonic == "cmp" and insns[0].op_str == "ecx, 0x23"
        check("documented signature precondition (cmp ecx,0x23)", sig,
              insns[0].mnemonic + " " + insns[0].op_str if insns else "none")
    for idx in (0, 1, 0x22):
        expected = struct.unpack_from("<Q", table_bytes, 8 * idx)[0]
        res = rig.call(REASON_NAME_FN, [idx])
        check("reason_name(%d) == file table qword" % idx,
              res.reason == "returned" and res.rax == expected,
              "reason=%s rax=%s want=%s" % (res.reason, hex(res.rax or 0),
                                            hex(expected)))
    res = rig.call(REASON_NAME_FN, [0x30])
    check("out-of-range index completes loudly (any outcome)",
          res.reason in ("returned", "crash:read-unmapped"),
          "reason=%s" % res.reason)

    print("SELFTEST %s" % ("PASS" if not fails else "FAIL: %s" % fails))
    return 0 if not fails else 1


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--binary", default=DEFAULT_BINARY)
    ap.add_argument("--call", type=lambda s: int(s, 0))
    ap.add_argument("--args", default="",
                    help="comma-separated int/hex args (MS x64 order)")
    ap.add_argument("--wmem", action="append", default=[],
                    help="ADDR=HEXBYTES written before the call (repeatable)")
    ap.add_argument("--max-insn", type=int, default=MAX_INSN_DEFAULT)
    args = ap.parse_args(argv)

    if args.selftest:
        if not os.path.exists(args.binary):
            print("ERROR: binary missing: %s" % args.binary)
            return 2
        return selftest(args.binary)
    if args.call is None:
        ap.print_help()
        return 2
    if not os.path.exists(args.binary):
        print("ERROR: binary missing: %s" % args.binary)
        return 2
    rig = Rig(args.binary)
    wmem = []
    for spec in args.wmem:
        addr, _, hexb = spec.partition("=")
        wmem.append((int(addr, 0), bytes.fromhex(hexb)))
    args_list = [int(a, 0) for a in args.args.split(",") if a.strip()]
    res = rig.call(args.call, args_list, args.max_insn, wmem)
    print("reason : %s" % res.reason)
    print("rax    : %s" % (hex(res.rax) if res.rax is not None else None))
    if res.fault_addr:
        print("fault  : 0x%x" % res.fault_addr)
    if res.imports_called:
        print("imports: %s" % ", ".join(res.imports_called))
    if res.detail:
        print("detail : %s" % res.detail)
    return 0 if res.reason == "returned" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
