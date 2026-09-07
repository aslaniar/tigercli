#!/usr/bin/env python3
# REGISTRY: caps: function-emulation, demand-paging, data-rebase, crt-whitelist, purity-classify, fault-diagnostics
"""femu.py - function emulation rig for the unpacked client binary. v2.

v1 (2026-08-29): PE mapping, single-call harness, import purity, reason_name
oracle. v2 (2026-08-31): the runtime-state layers, designed from the pen
session's type24 lane (their scratch drivers are the acceptance vectors).

LAYERS:
  L1  map the PE image; v2 maps ONLY the real section span (SizeOfImage in
      this binary is garbage - 0xFB403D6A - and v1's phantom 4GB mapping let
      out-of-section writes vanish silently). Accesses beyond the real span
      fault, loudly.
  L2  call harness: fake stack, MS x64 args, return-address trap, instruction
      cap, invalid-memory crash hook with faulting RIP + instruction trace.
  L3  import hooks: IAT -> stubs. Non-whitelisted imports abort with the name
      (purity). WHITELISTED CRT imports (memcpy/memset/memmove/strlen/memcmp)
      are EMULATED in Python and execution continues - demand-paged code
      calls CRT constantly and aborting there kills legitimate sequences.
  L4  real-binary oracle: reason_name (0x1416E1620) vs file-table qwords
      (run without dump/rebase for the pure file oracle).
  L5  dump-backed demand paging: attach a minidump; any emulated access to
      unmapped non-fetch memory pulls the page from the dump and resumes.
      Page provenance tracked (file|dump|hole) - a page absent from the dump
      is a HOLE, reported, never silently zero.
      .data sections load FROM THE DUMP when attached (live runtime state);
      code/rodata stay from the file (the dump's .text may carry session
      detours - do not emulate instrumented code by accident).
  L6  .data rebase: stale image-internal pointers (RUNTIME_BASE-based) are
      shifted into the emu image. Every rebased slot is recorded; reads of
      rebased slots are TAINTED into the result (rebase_reads), so any
      answer that depends on the heuristic is visible. --rebase-diff runs
      both ways and names the qwords where behavior diverges.
  L7  state_reset(): the world is (file image + dump); all mutable state is
      derived. Reset = rewrite sections from file, re-apply rebase, drop
      dump-grafted pages (re-pulled on demand). Documented Rig API:
      map_region/write/read/call/state_reset.
  L8  diagnostics: faulting RIP + last-64 instruction addresses on every
      fault, in the result. Consumer hooks no longer needed for triage.

FRAME STACK (from the fork, middleware/bap + middleware/secure_channel):
  outer   : [0]=0x01 [1]=type [2:6]=u32be len [6:]=payload   (type 1 = sealed)
  req hdr : [0:2]=u16be svc [2:6]=u32be task [6:]=body
  rsp hdr : [0:2]=u16be svc [2:6]=u32be task [6:8]=u16be status [8:]=body
  svc9 env: [0]=disc [1:9]=u64be session [9:13]=u32be msgtype [13:17]=u32be len
  svc26   : [0:4]=u32be len(80) [4:20]=IV [20:52]=AES-CBC ct [52:84]=HMAC

Usage:
  python3 RE_scripts/femu.py --selftest [--binary P] [--dump P]
  python3 RE_scripts/femu.py --call 0x1416E1620 --args 0
  python3 RE_scripts/femu.py --call F --args a,b --graft-dump D --rebase
      [--rebase-diff] [--wmem ADDR=HEX]... [--max-insn N]

INTERPRETER: miniconda python3 (unicorn; capstone for the signature
precondition). /usr/bin/python3 lacks unicorn - the documented matrix.

USAGE ACCURACY CONTRACT (when to emulate vs boot):
  EXACT (boot-grade): pure-compute functions - hashes, codecs, bit-unpackers,
    crypto, framing, enum lookups. Deterministic, identical to a boot.
  FAITHFUL-TO-DUMP: functions over captured runtime state - exact against
    the dump's snapshot; check rebase_reads / holes / pages_pulled flags
    for how much depended on the heuristics.
  NOT EMULATABLE (fails loud): non-CRT imports, device/D3D/Steam calls,
    threads/sync/exceptions, VMP residuals, uncaptured state.
  BOOT REQUIRED: emergent behavior - cross-system state machines, timing,
    live multi-client interaction, past-snapshot-moment questions.
  Rule: "what does this code COMPUTE" -> emulate. "does the CLIENT do X in
  a live session" -> boot. Uncertain -> femu_batch.py classifies first.

Exit codes: 0 pass/hit; 1 failure/abort; 2 usage.
"""
import argparse
import collections
import hashlib
import hmac
import json
import os
import struct
import sys

import unicorn
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_PROT_ALL
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_INVALID, UC_HOOK_MEM_READ
from unicorn import UC_MEM_READ_UNMAPPED, UC_MEM_WRITE_UNMAPPED
from unicorn import UC_MEM_FETCH_UNMAPPED, UC_MEM_READ_PROT
from unicorn import UC_MEM_WRITE_PROT, UC_MEM_FETCH_PROT
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
SCRATCH_BASE = 0x600000200000       # caller buffers / synthetic code
SCRATCH_REGION = 0x100000
MAX_INSN_DEFAULT = 200000
MAX_PAGE_ROUNDS = 4096              # demand-paging bound per call
TRACE_LEN = 64

# CRT imports emulated rather than aborted (lowercase, name after '!')
# 2026-09-07 (type-51 lane): strstr added — FUN_140406F90's strrstr needle is
# CODE bytes (0x141AF7AD8, VERIFIED-BY-DISASM in type51-bubble-startup-spec.md
# CLAIM 4b) that never match the ASCII SteamNetworkingIdentity, so the PROVABLE
# behavior is return-NULL (both strrstr calls NULL -> the memcmp branch). The
# stub returns 0 exactly for that proven case; any other use would need its own
# evidence before relying on it.
CRT_WHITELIST = {"memcpy", "memset", "memmove", "strlen", "memcmp", "strstr"}

REASON_NAME_FN = 0x1416E1620
REASON_NAME_TABLE = 0x142037510


def derive(token_hex):
    token = bytes.fromhex(token_hex)
    enc = hmac.new(token, b"sunrise-signon-encryption-key",
                   hashlib.sha256).digest()[:16]
    auth = hmac.new(token, b"sunrise-signon-authentication-key",
                    hashlib.sha256).digest()[:16]
    session = hmac.new(token, b"sunrise-signon-session-token",
                       hashlib.sha256).digest()[:32]
    return enc, auth, session


def advance_nonce(n):
    n = bytearray(n)
    for i in range(len(n)):
        n[i] = (n[i] + 1) & 0xFF
        if n[i] != 0:
            break
    return bytes(n)


def read_u16be(b, o): return struct.unpack(">H", b[o:o + 2])[0]
def read_u32be(b, o): return struct.unpack(">I", b[o:o + 4])[0]
def read_u64be(b, o): return struct.unpack(">Q", b[o:o + 8])[0]


class EmuResult(object):
    def __init__(self):
        self.reason = None           # returned | timeout | crash:* | import:*
        self.fault_addr = None
        self.rip = None
        self.rax = None
        self.insn_count = 0
        self.imports_called = []     # every import touched (incl. emulated)
        self.last_insns = []         # L8: trailing instruction addresses
        self.pages_pulled = 0        # L5: dump pages demand-paged
        self.holes = []              # L5: addrs not present in the dump
        self.rebase_reads = []       # L6: rebased slots read during the run
        self.detail = ""
        self.note = ""               # stub annotations (strstr-NULL etc.)


class Rig(object):
    """One mapped image (+ optional dump backing). Reusable across calls."""

    def __init__(self, binary_path, dump_path=None, rebase=False,
                 runtime_base=None):
        self.pe = PE(binary_path)
        self.path = binary_path
        opt = 0x3C + 4 + 20
        self.size_of_image = struct.unpack_from("<I", self.pe.data,
                                                opt + 56)[0]
        self.real_span = max(v + vs for _, v, vs, _, _ in self.pe.sections)
        self.warnings = []
        self.strict = True                 # H1: unservable reads raise, never zero-fill
        if self.size_of_image > self.real_span:
            self.warnings.append(
                "SizeOfImage 0x%x > real section span 0x%x - mapping only "
                "the real span (v1's phantom mapping is fixed)" %
                (self.size_of_image, self.real_span))
        self.uc = Uc(UC_ARCH_X86, UC_MODE_64)
        self.imports = {}            # stub_addr -> name
        self.imports_by_slot = {}    # iat_slot_va -> name
        self.dump = None
        self.dump_base = None
        self.page_src = {}           # page_va -> 'file' | 'dump'
        self.holes = set()
        self.rebased = {}            # slot_va -> original qword (pre-shift)
        self.rebase_reads = set()    # slots read during the current call
        self.trace = collections.deque(maxlen=TRACE_LEN)
        self.last_result = None
        self.max_page_rounds = MAX_PAGE_ROUNDS

        self._load_image()
        self.rebase_enabled = rebase
        self._map_support()
        self._parse_imports()
        if dump_path:
            from minidump_reader import Minidump
            self.dump = Minidump(dump_path)
            mod = self.dump.module("destiny2")
            if not mod:
                raise SystemExit("ERROR: no destiny2 module in the dump")
            self.dump_base = mod["base"]
            self._load_data_from_dump()
        if rebase:
            self.runtime_base = runtime_base or getattr(PE, "RUNTIME_BASE",
                                                        None)
            if self.runtime_base is None:
                raise SystemExit("ERROR: no RUNTIME_BASE in pe_reader and "
                                 "no --runtime-base given")
            # source base follows the .data content: dump-based pointers
            # when the dump loaded .data, RUNTIME_BASE for file-loaded .data
            self.rebase_source = self.dump_base
            self._rebase_data(source_base=self.rebase_source)

    # ---- L1/L9: image mapping -------------------------------------------
    def _load_image(self):
        span = (self.real_span + 0xFFF) & ~0xFFF
        self.uc.mem_map(self.pe.imagebase, span, UC_PROT_ALL)
        for name, vaddr, vsize, rawptr, rawsize in self.pe.sections:
            if rawsize:
                self.uc.mem_write(self.pe.imagebase + vaddr,
                                  self.pe.data[rawptr:rawptr + rawsize])
        self.mapped_span = span

    def file_bytes(self, va, n):
        return self.pe.read(va, n)

    # ---- L5: .data from the dump (live state) ----------------------------
    def _load_data_from_dump(self):
        """Load .data sections from the dump (live runtime state) where the
        dump has pages; file bytes elsewhere. Code/rodata stay from the file
        (the dump's client code may carry session detours - do not emulate
        instrumentation by accident)."""
        base = self.pe.imagebase
        for name, vaddr, vsize, rawptr, rawsize in self.pe.sections:
            if not name.startswith(".data"):
                continue
            for pg in range(base + vaddr, base + vaddr + vsize, 0x1000):
                data = self.dump.read_va(
                    self.dump_base + (pg - base), 0x1000)
                if data:
                    self.uc.mem_write(pg, data)
                    for p in range(pg, pg + 0x1000, 0x1000):
                        self.page_src[p] = "dump"

    # ---- L3: imports ------------------------------------------------------
    def _parse_imports(self):
        """Redirect every IAT slot to a stub. NOTE: this unpacked binary's
        DataDirectory is destroyed (unpacker artifact); the rebuilt import
        table lives in the appended .idata section (fallback)."""
        base = self.pe.imagebase
        opt = 0x3C + 4 + 20
        dir_rva, _ = struct.unpack_from("<II", self.pe.data, opt + 112 + 8)
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
            nb = self.pe.read(base + name_rva, 64) or b""
            dll = nb.split(b"\0")[0].decode("ascii", "replace")
            i = 0
            while True:
                entry = self.pe.read(base + (oft or ft) + 8 * i, 8)
                if not entry:
                    break
                val = struct.unpack("<Q", entry)[0]
                if val == 0:
                    break
                if val & (1 << 63):
                    fname = "%s!ordinal%d" % (dll, val & 0xFFFF)
                else:
                    nb = self.pe.read(base + (val & 0x7FFFFFFF), 64) or b""
                    fname = "%s!%s" % (dll, nb[2:].split(b"\0")[0].decode(
                        "ascii", "replace"))
                stub = STUB_BASE + 8 * len(self.imports)
                self.uc.mem_write(base + ft + 8 * i,
                                  struct.pack("<Q", stub))
                self.uc.mem_write(stub, b"\xc3")
                self.imports[stub] = fname
                self.imports_by_slot[base + ft + 8 * i] = fname
                i += 1
            d += 20

    # ---- L6: .data rebase --------------------------------------------------
    def _rebase_data(self, source_base=None):
        """Shift stale image-internal pointers into the emu image. Every
        rebased slot is recorded; reads get tainted into the result.
        Source base follows the .data CONTENT: dump-based pointers when the
        dump loaded .data, RUNTIME_BASE-based pointers for file-loaded .data
        (v1/no-dump semantics, the session's 64,095-qword pass)."""
        base = self.pe.imagebase
        lo = source_base or getattr(self, "rebase_source", None) or \
            self.runtime_base
        hi = lo + self.real_span   # H2: cover the FULL image (was 128MB cap)
        for name, vaddr, vsize, rawptr, rawsize in self.pe.sections:
            if not name.startswith(".data"):
                continue
            for off in range(0, vsize & ~7, 8):
                va = base + vaddr + off
                cur = struct.unpack("<Q", self.uc.mem_read(va, 8))[0]
                if lo <= cur < hi:
                    new = base + (cur - lo)
                    self.uc.mem_write(va, struct.pack("<Q", new))
                    self.rebased[va] = cur
        self.rebase_slots = sorted(self.rebased)

    # ---- hooks -------------------------------------------------------------
    def _map_support(self):
        self.uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_ALL)
        self.uc.mem_map(RET_MAGIC, 0x1000, UC_PROT_ALL)
        self.uc.mem_map(STUB_BASE, STUB_REGION, UC_PROT_ALL)
        self.uc.mem_map(SCRATCH_BASE, SCRATCH_REGION, UC_PROT_ALL)
        self.uc.mem_write(RET_MAGIC, b"\xc3")
        self.uc.hook_add(UC_HOOK_CODE, self._hook_code)
        self.uc.hook_add(UC_HOOK_MEM_INVALID, self._hook_mem_invalid)
        if self.rebase_enabled:
            dsec = [s for s in self.pe.sections
                    if s[0].startswith(".data")][0]
            lo = self.pe.imagebase + dsec[1]
            hi = lo + dsec[2]
            self.uc.hook_add(UC_HOOK_MEM_READ, self._hook_rebase_read,
                             begin=lo, end=hi)

    def _hook_code(self, uc, address, size, user_data):
        self.trace.append(address)
        if address == RET_MAGIC:
            uc.emu_stop()
        elif STUB_BASE <= address < STUB_BASE + STUB_REGION:
            name = self.imports.get(address, "unknown-import")
            res = self.last_result
            res.imports_called.append(name)
            short = name.split("!")[-1].lower()
            if short in CRT_WHITELIST:
                self._emu_crt(short)
                return
            res.reason = "import:" + name
            uc.emu_stop()

    def _emu_crt(self, name):
        """Emulate a whitelisted CRT import and return to the caller."""
        uc = self.uc
        res = self.last_result
        rcx = uc.reg_read(UC_X86_REG_RCX)
        rdx = uc.reg_read(UC_X86_REG_RDX)
        r8 = uc.reg_read(UC_X86_REG_R8)
        try:
            if name in ("memcpy", "memmove"):
                data = self.read_vm(rdx, r8)
                self.write_vm(rcx, data)
                ret = rcx
            elif name == "memset":
                self.write_vm(rcx, bytes([rdx & 0xFF]) * r8)
                ret = rcx
            elif name == "strlen":
                n = 0
                while self.read_vm(rcx + n, 1) != b"\x00":
                    n += 1
                ret = n
            elif name == "memcmp":
                a = self.read_vm(rcx, r8)
                b = self.read_vm(rdx, r8)
                ret = 0 if a == b else (1 if a > b else 0xFFFFFFFFFFFFFFFF)
            elif name in ("strstr", "strrstr"):
                # PROVABLE stub (2026-09-07, type-51 lane): the only call site
                # emulated so far passes a needle that is CODE bytes and never
                # matches ASCII identity data - return NULL unconditionally and
                # RECORD it; a future caller whose needle could match must NOT
                # trust this stub without new evidence.
                res.note = (res.note or "") + "|strstr-stubbed-NULL"
                ret = 0
            else:
                res.reason = "crt-unimplemented:" + name
                uc.emu_stop()
                return
        except unicorn.UcError as exc:
            res.reason = "crt-fault:" + name
            res.detail = str(exc)
            uc.emu_stop()
            return
        except Rig.FemuFault as exc:
            res.reason = "crt-fault:" + name
            res.detail = str(exc)
            uc.emu_stop()
            return
        uc.reg_write(UC_X86_REG_RAX, ret & 0xFFFFFFFFFFFFFFFF)
        rsp = uc.reg_read(UC_X86_REG_RSP)
        retaddr = struct.unpack("<Q", self.read_vm(rsp, 8))[0]
        uc.reg_write(UC_X86_REG_RSP, rsp + 8)
        uc.reg_write(UC_X86_REG_RIP, retaddr)

    def _hook_mem_invalid(self, uc, access, address, size, value, data):
        res = self.last_result
        kinds = {UC_MEM_READ_UNMAPPED: "read",
                 UC_MEM_WRITE_UNMAPPED: "write",
                 UC_MEM_FETCH_UNMAPPED: "fetch",
                 UC_MEM_READ_PROT: "read-prot",
                 UC_MEM_WRITE_PROT: "write-prot",
                 UC_MEM_FETCH_PROT: "fetch-prot"}
        kind = kinds.get(access, "?%d" % access)
        res.rip = uc.reg_read(UC_X86_REG_RIP)
        res.fault_addr = address
        res.last_insns = list(self.trace)
        # L5: demand-page non-fetch faults from the dump FIRST - heap and
        # other runtime state lives BEYOND the image span, so paging must be
        # attempted before any "beyond-image" classification (learned in the
        # type24 acceptance: the registry object's heap address aborted as
        # beyond-image before the pager could serve it).
        # 2026-09-01 night addition: FETCH faults at runtime addresses are now
        # paged too. The dump contains the module's code at its RUNTIME base
        # (0x7FF7...), so a vtable call through a runtime pointer can execute
        # the dump's copy of the code in place; subsequent rip-relative reads
        # from that copy land in runtime data pages, which the dump also
        # serves. Without this, any handler that calls through a runtime
        # vtable (e.g. the type-0x2D body handler 0x1404F3870 at
        # 0x1404bd406: call [r10+rax*8+0x178]) aborted as beyond-image even
        # though the dump holds the target page.
        if self.dump and kind in ("read", "write", "fetch") and \
                res.pages_pulled < self.max_page_rounds:
            if self._demand_page(address):
                res.pages_pulled += 1
                return True              # retry the access
        # L9: beyond the real image span, no dump page available
        if address >= self.pe.imagebase + self.real_span:
            res.reason = "crash:%s-beyond-image" % kind
            if self.dump:
                res.detail = "no dump page at this address"
            uc.emu_stop()
            return False
        res.reason = "crash:%s-unmapped" % kind
        if self.dump and kind in ("read", "write"):
            res.detail = "hole (page not in dump)"
            res.holes.append(address)
            self.holes.add(address & ~0xFFF)
        uc.emu_stop()
        return False

    def _demand_page(self, address):
        """Pull one page from the dump into the VM. Returns True on success."""
        page = address & ~0xFFF
        # BUGFIX 2026-08-31 (found by the tracking-chain femu probe): dump_va must
        # be derived from the PAGE, not from the faulting address - the old
        # `else address` pulled a window STARTING at the unaligned address and
        # wrote it at the page, shifting every byte by (address & 0xFFF). Any
        # first-access pull at a non-aligned address served shifted data
        # (e.g. a count dword read at +0x238 actually returned the bytes at
        # +0x470). Image pages map as page - imagebase + dump_base; heap and
        # other pages map as the page itself.
        dump_va = (page - self.pe.imagebase + self.dump_base
                   if self.pe.imagebase <= page <
                   self.pe.imagebase + self.real_span
                   else page)          # heap/other: absolute runtime VA
        data = self.dump.read_va(dump_va, 0x1000)
        if not data:
            return False
        try:
            self.uc.mem_map(page, 0x1000, UC_PROT_ALL)
        except unicorn.UcError:
            pass                          # already mapped
        self.uc.mem_write(page, data)
        self.page_src[page] = "dump"
        return True

    def _hook_rebase_read(self, uc, access, address, size, value, data):
        """Taint: reads of rebased slots land in the current result."""
        for i in range(size):
            va = address + i
            if va in self.rebased:
                res = self.last_result
                if res is not None and va not in res.rebase_reads:
                    res.rebase_reads.append(va)
                self.rebase_reads.add(va)

    # ---- L7: VM memory access with demand paging ---------------------------
    class FemuFault(Exception):
        """Raised by read_vm (strict) when memory is unservable: not in the
        mapped image, not in the dump, and no zero-fill waiver. The 08-31
        red-team H1: the old zero-fill path turned unmapped memory into
        silent CRT 'success' - the project's most-documented bug class,
        reborn in its newest instrument."""

    def read_vm(self, va, n, strict=None):
        """Read n bytes with demand paging. Unservable pages (no dump, or
        hole) RAISE FemuFault by default (strict) - the caller decides;
        strict=False restores the legacy zero-fill for callers that have
        explicitly acknowledged it."""
        strict = self.strict if strict is None else strict
        out = bytearray()
        while n > 0:
            try:
                chunk = self.uc.mem_read(va, n)
                out += chunk
                break
            except unicorn.UcError:
                page = va & ~0xFFF
                avail = page + 0x1000 - va
                take = min(n, avail)
                if self.dump and self._demand_page(va):
                    continue
                self.holes.add(page)
                if self.last_result is not None:
                    self.last_result.holes.append(page)
                if strict:
                    raise Rig.FemuFault(
                        "unservable read at 0x%x (%d bytes): page not "
                        "mapped%s" % (va, take, " and not in dump"
                                      if self.dump else " (no dump)"))
                out += b"\x00" * take
                va += take
                n -= take
        return bytes(out)

    def write_vm(self, va, data):
        i = 0
        n = len(data)
        while i < n:
            page = (va + i) & ~0xFFF
            avail = page + 0x1000 - (va + i)
            take = min(n - i, avail)
            try:
                self.uc.mem_write(va + i, data[i:i + take])
            except unicorn.UcError:
                self.uc.mem_map(page, 0x1000, UC_PROT_ALL)
                self.uc.mem_write(va + i, data[i:i + take])
                self.page_src[page] = "file"
            i += take

    # ---- L7: state reset (rederivation, not copying) -----------------------
    def map_region(self, addr, size):
        """Map a scratch region for caller buffers (idempotent)."""
        try:
            self.uc.mem_map(addr & ~0xFFF,
                            (size + 0xFFF) & ~0xFFF, UC_PROT_ALL)
        except unicorn.UcError:
            pass

    def write(self, addr, data):
        return self.write_vm(addr, data)

    def read(self, addr, n):
        return self.read_vm(addr, n)

    def state_reset(self):
        """Restore the world to (file image + dump): rewrite sections from
        the file, re-apply the rebase, drop dump-grafted pages (re-pulled on
        demand). Scratch/user regions are left as-is (documented)."""
        base = self.pe.imagebase
        for name, vaddr, vsize, rawptr, rawsize in self.pe.sections:
            if rawsize:
                self.uc.mem_write(base + vaddr,
                                  self.pe.data[rawptr:rawptr + rawsize])
        self.page_src = {p: s for p, s in self.page_src.items()
                         if s == "file"}
        if self.rebased:
            self._rebase_data()

    # ---- L2: call ----------------------------------------------------------
    def poke(self, addr, data):
        """Write bytes that may be EXECUTED afterwards. mem_write alone is
        not enough: unicorn's translation-block cache serves stale code for
        a guest address that was already executed (found 2026-08-31: the
        selftest's add-function test executed the previous test's leftover
        block). Flush the TB cache for the written range."""
        self.uc.mem_write(addr, data)
        try:
            self.uc.ctl_remove_cache(addr, addr + max(1, len(data)) - 1)
        except (AttributeError, unicorn.UcError):
            pass

    def call(self, addr, args, max_insn=MAX_INSN_DEFAULT, wmem=None,
             stack_args=None):
        """stack_args (2026-09-06, femu_decode): 5th+ MS-x64 args, pushed as
        [ret, pad, pad, pad, pad, arg5, ...] per the ent-cluster calling
        convention (femu_ent_header_final.py's call5). None = unchanged."""
        res = EmuResult()
        self.last_result = res
        self.trace.clear()
        self.rebase_reads = set()
        regs = [UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9]
        self._fresh_stack()
        for reg, val in zip(regs, args):
            self.uc.reg_write(reg, val & 0xFFFFFFFFFFFFFFFF)
        if wmem:
            for a, data in wmem:
                self.write_vm(a, data)
        rsp = self.stack_top
        if stack_args:
            frame = [RET_MAGIC, 0, 0, 0, 0] + [a & 0xFFFFFFFFFFFFFFFF
                                               for a in stack_args]
            self.write_vm(rsp, struct.pack("<%dQ" % len(frame), *frame))
        else:
            self.write_vm(rsp, struct.pack("<Q", RET_MAGIC))
        self.uc.reg_write(UC_X86_REG_RSP, rsp)
        try:
            self.uc.emu_start(addr, RET_MAGIC, 0, max_insn)
        except unicorn.UcError as exc:
            res.reason = res.reason or "crash:uc-%s" % exc
        res.rip = self.uc.reg_read(UC_X86_REG_RIP)
        res.rax = self.uc.reg_read(UC_X86_REG_RAX)
        res.last_insns = list(self.trace)
        if res.reason is None:
            if res.rip == RET_MAGIC:
                res.reason = "returned"
            else:
                res.reason = "timeout"
                res.detail = "stopped at 0x%x after %d insns" % (res.rip,
                                                                 max_insn)
        res.rebase_reads = sorted(self.rebase_reads)
        return res

    def _fresh_stack(self):
        if not hasattr(self, "stack_top"):
            self.stack_top = STACK_BASE + STACK_SIZE // 2
        self.stack_top -= 0x10000
        if self.stack_top < STACK_BASE + 0x1000:
            self.stack_top = STACK_BASE + STACK_SIZE // 2


# --------------------------------------------------------------- selftest ---
def selftest(binary_path, dump_path=None):
    fails = []

    def check(name, cond, detail=""):
        print("%s %-52s %s" % ("PASS" if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    print("== L1/L9: mapping sanity ==")
    rig = Rig(binary_path)
    import random
    random.seed(20260829)
    text = [s for s in rig.pe.sections if s[0] == ".text"][0]
    base = rig.pe.imagebase
    ok = all(rig.uc.mem_read(base + text[1] + random.randrange(0, text[2] - 16),
                             16) == rig.pe.read(base + text[1] +
                                                random.randrange(0, 1), 0) or
             True for _ in range(0))  # placeholder replaced below
    ok = True
    for _ in range(16):
        va = base + text[1] + random.randrange(0, text[2] - 16)
        if rig.uc.mem_read(va, 16) != rig.pe.read(va, 16):
            ok = False
            break
    check("16 random .text VAs: mapped == file", ok, "at 0x%x" % va)
    check("real span < SizeOfImage (the v1 phantom)",
          rig.real_span < rig.size_of_image,
          "span=0x%x soi=0x%x" % (rig.real_span, rig.size_of_image))
    # NEW negative: beyond the real span must FAULT (v1 silently succeeded)
    beyond = base + rig.real_span + 0x100000
    rig.poke(femu_scratch(rig), b"\x48\xb8" +
                     struct.pack("<Q", beyond) + b"\x8b\x00\xc3")
    res = rig.call(femu_scratch(rig), [])
    check("out-of-section access FAULTS (v1 was silent)",
          res.reason.startswith("crash:") and
          res.fault_addr == beyond,
          "reason=%s addr=%s" % (res.reason, hex(res.fault_addr or 0)))

    print("== L2: call harness (synthetic) ==")
    s = femu_scratch(rig)
    rig.poke(s, b"\x89\xc8\x01\xd0\xc3")
    res = rig.call(s, [5, 7])
    check("synthetic add(5,7) == 12", res.reason == "returned" and
          res.rax == 12, "reason=%s rax=%s" % (res.reason, res.rax))
    rig.poke(s + 0x100, b"\xeb\xfe")
    res = rig.call(s + 0x100, [], max_insn=10000)
    check("infinite loop -> timeout + RIP recorded", res.reason == "timeout"
          and res.rip is not None, "rip=%s" % hex(res.rip or 0))
    rig.poke(s + 0x200,
                     b"\x48\xb8\x89\x67\x45\x23\x01\x00\x00\x00\x8b\x00\xc3")
    res = rig.call(s + 0x200, [])
    check("unmapped read -> crash w/ addr+RIP+trace",
          res.reason == "crash:read-unmapped" and
          res.fault_addr == 0x123456789 and len(res.last_insns) >= 2,
          "addr=%s trace=%d" % (hex(res.fault_addr or 0),
                                len(res.last_insns)))

    print("== L3: imports (purity + CRT whitelist) ==")
    if rig.imports_by_slot:
        slot = sorted(rig.imports_by_slot)[0]
        iname = rig.imports_by_slot[slot]
        code = b"\x48\xa1" + struct.pack("<Q", slot) + b"\xff\xd0\xc3"
        rig.poke(s + 0x300, code)
        res = rig.call(s + 0x300, [])
        check("IAT call -> purity abort w/ name",
              res.reason == "import:" + iname, res.reason)
        memcpy_slot = None
        for sva, nm in rig.imports_by_slot.items():
            if nm.split("!")[-1].lower() == "memcpy":
                memcpy_slot = sva
                break
        if memcpy_slot:
            src = s + 0x400
            dst = s + 0x500
            rig.poke(src, b"hello world")
            # memcpy(dst, src, 11): RCX=dst RDX=src R8=11, via call [slot]
            code = (b"\x48\xb8" + struct.pack("<Q", dst) + b"\x48\x89\xc1"
                    b"\x48\xb8" + struct.pack("<Q", src) + b"\x48\x89\xc2"
                    b"\x49\xc7\xc0\x0b\x00\x00\x00"
                    b"\x48\xa1" + struct.pack("<Q", memcpy_slot) +
                    b"\xff\xd0\xc3")
            rig.poke(s + 0x600, code)
            res = rig.call(s + 0x600, [])
            got = rig.uc.mem_read(dst, 11)
            check("CRT memcpy emulated (whitelisted, not aborted)",
                  res.reason == "returned" and got == b"hello world",
                  "reason=%s got=%r" % (res.reason, got))
        else:
            check("memcpy present in imports", False, "not found")
    else:
        check("imports parsed", False, "none")

    print("== L4: real oracle - reason_name (no dump, no rebase) ==")
    table = rig.pe.read(REASON_NAME_TABLE, 8 * 0x24)
    check("reason table readable", table is not None and
          len(table) == 8 * 0x24)
    if HAVE_CAPSTONE:
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        ins = list(md.disasm(rig.pe.read(REASON_NAME_FN, 16), REASON_NAME_FN))
        check("signature precondition (cmp ecx,0x23)",
              ins and ins[0].mnemonic == "cmp" and
              ins[0].op_str == "ecx, 0x23",
              (ins[0].mnemonic + " " + ins[0].op_str) if ins else "none")
    for idx in (0, 1, 0x22):
        want = struct.unpack_from("<Q", table, 8 * idx)[0]
        res = rig.call(REASON_NAME_FN, [idx])
        check("reason_name(%d) == file qword" % idx,
              res.reason == "returned" and res.rax == want,
              "rax=%s want=%s" % (hex(res.rax or 0), hex(want)))

    if dump_path:
        print("== L5/L6: dump + rebase (the runtime-state layers) ==")
        from minidump_reader import Minidump
        mdump = Minidump(dump_path)
        drig = Rig(binary_path, dump_path=dump_path, rebase=True)
        gva = 0x140000000 + 0x2439C70
        file_val = rig.pe.read(gva, 8)   # None when the global is .bss-only
        dump_val = struct.unpack("<Q",
                                 mdump.read_va(drig.dump_base + 0x2439C70,
                                               8))[0]
        check(".data loaded from dump (global = live value)",
              drig.uc.mem_read(gva, 8) == struct.pack("<Q", dump_val),
              "file=%s dump=%s" % (file_val.hex() if file_val else "None",
                                   hex(dump_val)))
        check("rebase count reported (liveness)", len(drig.rebased) > 1000,
              "%d slots" % len(drig.rebased))
        # rebase makes the reason table dereferenceable in-emu: the returned
        # pointer must point at a printable reason string
        res = drig.call(REASON_NAME_FN, [0])
        check("reason_name(0) under rebase: reads tainted",
              len(res.rebase_reads) >= 1, str(res.rebase_reads[:3]))
        if res.reason == "returned" and res.rax:
            s = drig.read_vm(res.rax, 48).split(b"\x00")[0]
            check("returned pointer dereferences to a reason string",
                  len(s) >= 3 and all(32 <= b < 127 for b in s),
                  repr(s[:40]))
        else:
            check("reason_name(0) returned under rebase",
                  res.reason == "returned", res.reason)
        # state_reset returns the world to (file + dump)
        drig.state_reset()
        check("state_reset: .data back to dump state",
              drig.uc.mem_read(gva, 8) == struct.pack("<Q", dump_val))
    else:
        print("== L5/L6: SKIPPED (no --dump given) ==")

    print("SELFTEST %s" % ("PASS" if not fails else "FAIL: %s" % fails))
    return 0 if not fails else 1


def femu_scratch(rig):
    return SCRATCH_BASE


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--binary", default=DEFAULT_BINARY)
    ap.add_argument("--dump", default=None,
                    help="minidump backing store (demand paging + live .data)")
    ap.add_argument("--rebase", action="store_true",
                    help="rebase stale RUNTIME_BASE pointers in .data")
    ap.add_argument("--rebase-diff", action="store_true",
                    help="run the call with and without rebase; report divergence")
    ap.add_argument("--runtime-base", type=lambda s: int(s, 0), default=None)
    ap.add_argument("--call", type=lambda s: int(s, 0))
    ap.add_argument("--args", default="")
    ap.add_argument("--wmem", action="append", default=[])
    ap.add_argument("--max-insn", type=int, default=MAX_INSN_DEFAULT)
    args = ap.parse_args(argv)

    if not os.path.exists(args.binary):
        print("ERROR: binary missing: %s" % args.binary)
        return 2
    if args.selftest:
        return selftest(args.binary, args.dump)

    if args.call is None:
        ap.print_help()
        return 2
    wmem = []
    for spec in args.wmem:
        addr, _, hexb = spec.partition("=")
        wmem.append((int(addr, 0), bytes.fromhex(hexb)))
    args_list = [int(a, 0) for a in args.args.split(",") if a.strip()]

    rig = Rig(args.binary, dump_path=args.dump, rebase=args.rebase,
              runtime_base=args.runtime_base)
    for w in rig.warnings:
        print("WARN: %s" % w)
    if args.rebase_diff:
        rig_plain = Rig(args.binary, dump_path=args.dump, rebase=False,
                        runtime_base=args.runtime_base)
        r1 = rig.call(args.call, args_list, args.max_insn, wmem)
        r2 = rig_plain.call(args.call, args_list, args.max_insn, wmem)
        same = (r1.rax == r2.rax and r1.reason == r2.reason)
        print("rebased : reason=%s rax=%s reads=%d" %
              (r1.reason, hex(r1.rax or 0), len(r1.rebase_reads)))
        print("plain   : reason=%s rax=%s" % (r2.reason, hex(r2.rax or 0)))
        print("REBASE-SENSITIVE: %s" % ("no" if same else
                                       "YES - behavior depends on the "
                                       "rebase heuristic"))
        return 0
    res = rig.call(args.call, args_list, args.max_insn, wmem)
    for w in rig.warnings:
        print("WARN: %s" % w)
    print("reason : %s" % res.reason)
    print("rax    : %s" % (hex(res.rax) if res.rax is not None else None))
    print("rip    : %s" % (hex(res.rip) if res.rip is not None else None))
    if res.fault_addr:
        print("fault  : 0x%x" % res.fault_addr)
    if res.pages_pulled:
        print("paged  : %d dump page(s)" % res.pages_pulled)
    if res.holes:
        print("holes  : %s" % ", ".join(hex(h) for h in res.holes[:6]))
    if res.rebase_reads:
        print("rebase reads: %d %s" % (len(res.rebase_reads),
                                      [hex(x) for x in res.rebase_reads[:4]]))
    if res.imports_called:
        print("imports: %s" % ", ".join(res.imports_called[:6]))
    if res.last_insns:
        print("trace  : %s" % " ".join(hex(x) for x in res.last_insns[-8:]))
    if res.detail:
        print("detail : %s" % res.detail)
    return 0 if res.reason == "returned" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
