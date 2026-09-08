#!/usr/bin/env python3
# REGISTRY: caps: ptr-decrypt-emulation, dump-read
"""decrypt_manager_ptr.py - Lane A: emulate FUN_1416c0ba0 (the singleton
pointer decryption) on the REAL code and recover the manager object pointer.

Setup (all at their true addresses):
  - the carved image at preferred base 0x140000000 (code VAs = record VAs,
    .data holds the dump's runtime values)
  - every dump memory range mapped at its RUNTIME address (heap, stacks, TEB)
  - FUN_1416c0ba0 called with a synthetic stack
Oracle: the decrypted pointer must be a plausible heap address, and the
manager's +0x206c8 sub-structures should relate to the three runtime
fragment lists (0x21DF607B515 etc.). If the runtime nibble from
func_144f9d1fb matters, all 16 variants are tried and the oracle picks.
"""
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from minidump_reader import Minidump

from unicorn import *
from unicorn.x86_const import *

DUMP = "RE_output/dumps/p2-206-setup-flags/dump_p2-206-setup-flags.dmp"
EXE = "RE_output/destiny2_runtime_p2-206.exe"
IMG = 0x140000000
STACK_BASE = 0x148B00000
STACK_SIZE = 0x100000
ENTRY = 0x1416C0BA0
RET_MAGIC = 0x2000000000

TARGET_FN = 0x1416C0BA0   # 0 = c0ba0, 1 = a8c70 (cond helper)


def main():
    which = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    entry = ENTRY if which == 0 else 0x1412A8C70

    md = Minidump(DUMP)
    game = md.module("destiny2")
    img_base_rt = game["base"]
    p2r = img_base_rt - IMG

    image = open(EXE, "rb").read()
    img_size = game["size"]

    uc = Uc(UC_ARCH_X86, UC_MODE_64)
    # image at preferred base (size rounded to page)
    img_alloc = (img_size + 0xFFF) & ~0xFFF
    uc.mem_map(IMG, img_alloc)
    uc.mem_write(IMG, image[:img_size])
    # dump ranges at runtime VAs (skipping the module range itself)
    mapped = []
    for start, size, off in md.ranges:
        rt = start
        pref = start - p2r
        if IMG <= pref < IMG + img_alloc:
            continue  # module pages already mapped from the carved exe
        try:
            uc.mem_map(start, (size + 0xFFF) & ~0xFFF)
            uc.mem_write(start, md.read_va(start, size))
            mapped.append((start, size))
        except Exception:
            pass
    print(f"mapped image 0x{IMG:X}+0x{img_size:X} and {len(mapped)} dump ranges")

    # stack (fragments expect a caller frame in rbp)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    rsp = STACK_BASE + STACK_SIZE - 0x10000
    uc.mem_write(rsp, struct.pack("<Q", RET_MAGIC))
    uc.reg_write(UC_X86_REG_RSP, rsp)
    uc.reg_write(UC_X86_REG_RBP, rsp)
    uc.reg_write(UC_X86_REG_RSI, 0)

    # REAL TEB + GS base (the failing access was a gs-relative TLS read)
    _, trva = md.streams[3]
    tcount = struct.unpack_from("<I", md._read(trva, 4), 0)[0]
    best = None
    for i in range(tcount):
        t = md._read(trva + 4 + i*48, 48)
        teb = struct.unpack_from("<Q", t, 16)[0]
        ssz = struct.unpack_from("<I", t, 32)[0]
        if best is None or ssz > best[1]: best = (teb, ssz)
    teb = best[0]
    teb_page = teb & ~0xFFF
    d = md.read_va(teb_page, 0x1000)
    if d:
        try:
            uc.mem_map(teb_page, 0x1000)
            uc.mem_write(teb_page, d)
        except Exception:
            pass
    try:
        uc.reg_write(UC_X86_REG_GS_BASE, teb)
        print("GS base = TEB 0x%X" % teb)
    except Exception as e:
        print("GS base write failed:", e)

    trace = []
    done = []

    def hook_code(uc, address, size, user):
        trace.append(address)
        if len(trace) > 64:
            trace.pop(0)
        if address == RET_MAGIC:
            uc.emu_stop()

    uc.hook_add(UC_HOOK_CODE, hook_code)

    # after the run, print trace and registers even on failure

    def hook_unmapped(uc, access, address, size, value, user):
        print(f"  UNMAPPED access at 0x{address:X} (rip=0x{uc.reg_read(UC_X86_REG_RIP):X})",
              file=sys.stderr)
        return False

    uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_unmapped)

    try:
        uc.emu_start(entry, RET_MAGIC, timeout=10 * 1000000, count=5_000_000)
    finally:
        rax = uc.reg_read(UC_X86_REG_RAX)
        print(f"FUN_{entry:X} stopped with rax = 0x{rax:X}, rsp=0x{uc.reg_read(UC_X86_REG_RSP):X}")
        print("last 40 PCs:")
        for a in trace:
            print(f"  0x{a:X}")
    # decrypt chain check: rax should be the manager pointer (heap addr)
    if 0x100000000 < rax < 0x7FFFFFFFFFFF:
        # read manager fields from the DUMP at this runtime address
        print("manager fields from dump:")
        for off, label in [(0x8, "state_a(+8)"), (0x2c, "state(+2c)"), (0x38, "armed(+38)"),
                           (0x44, "cond(+44)"), (0x68, "ts(+68)"), (0x80, "x80"),
                           (0x206a0, "206a0"), (0x206a4, "206a4"), (0x206ac, "count(206ac)"),
                           (0x206b0, "206b0"), (0x206b8, "list(206b8)"),
                           (0x560e0, "idx(560e0)"), (0x560f0, "ident(560f0)"),
                           (0x59608, "59608"), (0x5960c, "5960c"), (0x59820, "59820"),
                           (0xC118, "pool8192?(C118)"), (0xC520, "lease?(C520)")]:
            d = md.read_va(rax + off, 8)
            print(f"  +0x{off:X}: {d.hex() if d else 'UNMAPPED'}")
        # the 0x100-byte buffer copy target: obj+0x560f0 vs b18
        d = md.read_va(rax + 0x560f0, 0x20)
        print(f"  +0x560f0[..0x20]: {d.hex() if d else 'UNMAPPED'}")
        # sub-structures at +0x206c8 + k*0x11e08
        for k in range(3):
            a2 = rax + 0x206c8 + k * 0x11e08
            print(f"  +0x{0x206c8 + k*0x11e08:X}: {md.read_va(a2, 16).hex() if md.read_va(a2,16) else 'UNMAPPED'}")


if __name__ == "__main__":
    main()
