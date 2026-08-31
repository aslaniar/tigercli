#!/usr/bin/env python3
# REGISTRY: caps: obf-fold, chain-analysis
"""obf_fold.py - bounded stack-slot xor/ror chain folder for obfuscated code.

Generalizer for the constant-obfuscation pass (svc43 region 0x1407DA000..0x1407DC000
and anywhere else the same scheme shows up). This is INSTRUMENTATION OF OBFUSCATED
CODE, not a decompiler: fold what is provably foldable (a register/stack-slot XORed
with immediates across straight-line blocks until consumption), mark everything else
UNRESOLVED. Reads a PE process dump through RE_scripts/pe_reader.py; never touches
a process.

What it tracks (per basic block, straight-line):
  - stack slots [rsp+K]: mov [rsp+K],reg / mov reg,[rsp+K] / mov dword [rsp+K],imm
  - regs rax/rcx/rdx/r8..: chains like mov r64,[rsp+X]; xor r64,imm32; mov [rsp+X],r64
  - ror/rol reg,imm on a tracked slot (rotational component of the chain)
  - marker writes  mov dword [rsp+Y], imm32  (step-identity constants)
  - fold: xor-of-constants, xor-of-xor (chain merge), rotate-of-constant, masks,
    zx32 (32-bit reg ops), cdqe, imul x,x,0/1, add-const on constant bases
  - the slot chain map PERSISTS across blocks, so a xor applied in block A shows up
    in the annotation of a later consumer block that reads the same slot.

Modes:
  obf_fold.py --self-test          run against the KNOWN chain 0x1407DA8F0..0x1407DA970
                                   (must recognize >=2 xor-folds + the ror 0x20 event)
  obf_fold.py LO HI [--steps]      fold the range; --steps additionally simulates the
                                   obfuscated dispatch (tail acc ^= marker; head cmp/je
                                   tree) and prints the ORDERED step table with per-step
                                   folded slot expressions and resolved marker/acc values.
                                   (No Ghidra. No process. Read-only on the dump.)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe_reader import PE

from capstone import Cs, CS_ARCH_X86, CS_MODE_64, x86

EXE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "RE_output", "destiny2_unpacked_full.exe")

# --------------------------------------------------------------------------
# symbolic expression mini-language for slot/reg values
# --------------------------------------------------------------------------

def C(v):
    """constant node"""
    return ("c", v & ((1 << 64) - 1))


def V(name):
    """variable node (runtime-sourced value)"""
    return ("v", name)


def xor_terms(e):
    """flatten a nested xor into a term list (const nodes and var nodes)."""
    if isinstance(e, tuple) and e[0] == "x":
        return xor_terms(e[1]) + xor_terms(e[2])
    return [e]


def simp_xor(a, b):
    """XOR two exprs with pair cancellation: x^x=0, constants merge."""
    terms = xor_terms(a) + xor_terms(b)
    out = []
    for t in terms:
        if t in out:
            out.remove(t)
        else:
            out.append(t)
    c = 0
    vars_ = []
    for t in out:
        if t[0] == "c":
            c ^= t[1]
        else:
            vars_.append(t)
    if not vars_:
        return C(c)
    e = vars_[0]
    for t in vars_[1:]:
        e = ("x", e, t)
    if c:
        e = ("x", e, C(c))
    return e


def Xor(a, b):
    if a == b:
        return C(0)
    return ("x", a, b)


def Rot(e, n):
    """rotate LEFT by n (64-bit). Negative n = rotate right."""
    n = n % 64
    if n == 0:
        return e
    return ("r", e, n)


def Mask(e, m):
    m &= (1 << 64) - 1
    if m == (1 << 64) - 1:
        return e
    return ("m", e, m)


def is_const(e):
    return isinstance(e, tuple) and e[0] == "c"


def zx32(e):
    """zero-extend a 32-bit reg value to 64-bit semantics."""
    if is_const(e):
        return C(e[1] & 0xFFFFFFFF)
    return Mask(e, 0xFFFFFFFF)


def sx64(v):
    """sign-extend a 32-bit immediate the way xor r64,imm32 does."""
    v &= 0xFFFFFFFF
    if v & 0x80000000:
        v |= ~0xFFFFFFFF
    return v & ((1 << 64) - 1)


def cir_rot(v, n):
    n %= 64
    v &= (1 << 64) - 1
    return ((v << n) | (v >> (64 - n))) & ((1 << 64) - 1) if n else v


def simp(e):
    """constant-fold / normalize a symbolic expression."""
    if not isinstance(e, tuple):
        return e
    k = e[0]
    if k == "c":
        return e
    if k == "v":
        return e
    if k == "x":
        a, b = simp(e[1]), simp(e[2])
        return simp_xor(a, b)
    if k == "r":
        inner = simp(e[1])
        if is_const(inner):
            return C(cir_rot(inner[1], e[2]))
        if inner[0] == "r":
            return simp(Rot(inner[1], (inner[2] + e[2]) % 64))
        if e[2] == 0:
            return inner
        return Rot(inner, e[2])
    if k == "m":
        inner = simp(e[1])
        m = e[2]
        if is_const(inner):
            return C(inner[1] & m)
        if inner[0] == "m":
            return simp(Mask(inner[1], inner[2] & m))
        if inner[0] == "x" and is_const(inner[2]):
            # (a ^ c) & m  ->  (a & m) ^ (c & m)
            return simp(Xor(Mask(inner[1], m), C(inner[2][1] & m)))
        return Mask(inner, m)
    return e


def expr_str(e):
    e = simp(e)
    if e[0] == "c":
        v = e[1]
        if v <= 0xFFFFFFFF:
            return f"0x{v:X}"
        return f"0x{v:016X}"
    if e[0] == "v":
        return str(e[1])
    if e[0] == "x":
        a, b = simp(e[1]), simp(e[2])
        if is_const(a) and not is_const(b):
            a, b = b, a
        return f"({expr_str(a)} ^ {expr_str(b)})"
    if e[0] == "r":
        return f"rotl({expr_str(e[1])},{e[2]})"
    if e[0] == "m":
        return f"({expr_str(e[1])} & 0x{e[2]:X})"
    return "?" + str(e)


# --------------------------------------------------------------------------
# instruction model
# --------------------------------------------------------------------------

TRACKED_REGS = {x86.X86_REG_RAX, x86.X86_REG_RCX, x86.X86_REG_RDX,
                x86.X86_REG_R8, x86.X86_REG_R9, x86.X86_REG_R10,
                x86.X86_REG_R11}
REG32 = {x86.X86_REG_EAX: x86.X86_REG_RAX, x86.X86_REG_ECX: x86.X86_REG_RCX,
         x86.X86_REG_EDX: x86.X86_REG_RDX, x86.X86_REG_R8D: x86.X86_REG_R8,
         x86.X86_REG_R9D: x86.X86_REG_R9, x86.X86_REG_R10D: x86.X86_REG_R10,
         x86.X86_REG_R11D: x86.X86_REG_R11}
ALL_REGS = TRACKED_REGS | set(REG32)

MEM = x86.X86_OP_MEM
IMM = x86.X86_OP_IMM
REG = x86.X86_OP_REG


def mem_rsp_disp(op):
    """@return (disp, size) when op is [rsp + disp32], else None."""
    if op.type != MEM:
        return None
    m = op.mem
    if m.base != x86.X86_REG_RSP or m.index != 0 or m.scale != 1:
        return None
    return (m.disp, op.size)


class Event:
    __slots__ = ("addr", "kind", "detail")

    def __init__(self, addr, kind, detail):
        self.addr = addr
        self.kind = kind
        self.detail = detail

    def __repr__(self):
        return f"{self.addr:#x} {self.kind} {self.detail}"


class Block:
    __slots__ = ("start", "insns", "term")

    def __init__(self, start):
        self.start = start
        self.insns = []       # capstone insns
        self.term = None      # last insn


# --------------------------------------------------------------------------
# per-block fold engine
# --------------------------------------------------------------------------

class FoldEngine:
    """Runs over a list of blocks; keeps a persistent slot-chain map and a
    per-block register/slot state. Events are appended to self.events.
    persist=False gives a pure per-block fold (execution-order lane for the
    dispatch simulator: slots are only what the carried state provides)."""

    def __init__(self, pe, md, persist=True):
        self.pe = pe
        self.md = md
        self.persist = persist
        self.chains = {}          # slot disp -> net symbolic expr (persistent)
        self.slot_dtype = {}      # slot disp -> 'q'|'d'
        self.events = []
        self.use_sites = []       # (addr, slot_disp, expr, consumer)
        self.marker_writes = []   # (addr, slot_disp, imm)

    # -- state helpers ------------------------------------------------------

    def _slot(self, disp, st=None):
        """current net expr for slot disp (slot-state first, chain fallback)."""
        if st is not None:
            if disp in st["slot"]:
                return st["slot"][disp]
            return V(f"s[{disp:#x}]")
        e = self.chains.get(disp)
        if e is None:
            e = V(f"s[{disp:#x}]")
        return e

    # -- instruction handling -------------------------------------------------

    def fold_block(self, block, entry_state=None):
        """Fold one straight-line block. entry_state: dict reg->expr, slot->expr.
        Returns (exit_state, events_in_block)."""
        st = {"reg": {}, "slot": {}} if entry_state is None else entry_state
        local = []
        for ins in block.insns:
            ev = self.on_insn(ins, st)
            if ev:
                local.extend(ev)
        return st, local

    def on_insn(self, ins, st):
        """Handle one instruction. @return list of events (may be empty)."""
        evs = []
        regs = st["reg"]
        slots = st["slot"]
        mnem = ins.mnemonic
        ops = ins.operands

        def slot_of(k):
            """slot value visible in this block state, else the persistent chain."""
            if self.persist:
                return slots.get(k, self._slot(k))
            return self._slot(k, st)

        # --- stack-displacement memory ops ---------------------------------
        if len(ops) >= 1 and mnem in ("mov", "xor", "and", "or", "add", "sub", "imul", "ror", "rol"):
            src = ops[-1]
            dst = ops[0]
            m = mem_rsp_disp(dst) if dst.type == MEM else None
            if m is not None and mnem == "mov" and src.type == IMM:
                k, sz = m
                val = src.imm & 0xFFFFFFFF
                slots[k] = C(val)
                self.slot_dtype[k] = "d"
                if self.persist:
                    self.chains[k] = C(val)
                self.marker_writes.append((ins.address, k, val))
                evs.append(Event(ins.address, "MARKER_SET", f"[rsp+{k:#x}] = 0x{val:X}"))
                return evs
            if m is not None and mnem == "mov" and src.type == REG:
                k, sz = m
                sreg = REG32.get(src.reg, src.reg)
                v = simp(regs.get(sreg, V("?")))
                if v == V("?"):
                    v = V(f"entry:{self.md.reg_name(sreg)}")
                if sz == 4 and not is_const(v):
                    v = zx32(v)
                slots[k] = v
                prev = self.chains.get(k) if self.persist else st["slot"].get(k)
                # delta vs the previous chain value: a constant delta = one folded step
                if prev is not None:
                    delta = simp(Xor(v, prev))
                    if is_const(delta) and delta[1] != 0:
                        evs.append(Event(ins.address, "SLOT_XOR_FOLD",
                                         f"[rsp+{k:#x}] ^= 0x{delta[1] & 0xFFFFFFFF:X} "
                                         f"-> {expr_str(v)}"))
                elif isinstance(v, tuple) and v[0] == "x" and is_const(v[2]):
                    evs.append(Event(ins.address, "SLOT_XOR_FOLD",
                                     f"[rsp+{k:#x}] ^= 0x{v[2][1] & 0xFFFFFFFF:X} "
                                     f"-> {expr_str(v)}"))
                if isinstance(v, tuple) and v[0] == "r" and \
                        (prev is None or simp(v[1]) == simp(prev)):
                    evs.append(Event(ins.address, "SLOT_ROR_FOLD",
                                     f"[rsp+{k:#x}] rot by 0x{v[2]:X} -> {expr_str(v)}"))
                if self.persist:
                    self.chains[k] = v
                return evs
            if m is not None and mnem in ("xor", "and", "or", "add", "sub", "imul") and src.type == IMM:
                k, sz = m
                v = slot_of(k)
                imm = src.imm
                if mnem == "xor":
                    if sz == 8:
                        imm = sx64(imm)
                    nv = simp(Xor(v, C(imm)))
                    slots[k] = nv
                    self.chains[k] = nv
                    evs.append(Event(ins.address, "XOR_FOLD",
                                     f"[rsp+{k:#x}] ^= 0x{imm & 0xFFFFFFFF:X}  ->  {expr_str(nv)}"))
                elif mnem == "and":
                    nv = simp(Mask(v, imm & 0xFFFFFFFF))
                    slots[k] = nv
                    self.chains[k] = nv
                    evs.append(Event(ins.address, "MASK_FOLD", f"[rsp+{k:#x}] &= 0x{imm:X} -> {expr_str(nv)}"))
                else:
                    evs.append(Event(ins.address, "UNTRACKED", f"{mnem} [rsp+{k:#x}], imm"))
                return evs

        # --- register ops ----------------------------------------------------
        if len(ops) >= 1 and ops[0].type == REG:
            dreg = REG32.get(ops[0].reg, ops[0].reg)
            if dreg not in TRACKED_REGS:
                return evs
            if mnem == "mov" and len(ops) == 2:
                src = ops[1]
                if src.type == IMM:
                    v = C(src.imm if src.size == 8 and ops[0].size == 8 else src.imm & 0xFFFFFFFF)
                    regs[dreg] = simp(v)
                elif src.type == MEM:
                    m = mem_rsp_disp(src)
                    v = V("?") if m is None else slot_of(m[0])
                    if m and m[1] == 4 and not is_const(v):
                        v = zx32(v)
                    regs[dreg] = simp(v)
                elif src.type == REG:
                    sreg = REG32.get(src.reg, src.reg)
                    regs[dreg] = simp(regs.get(sreg, V("?")))
            elif mnem == "xor" and len(ops) == 2:
                s = ops[1]
                d = regs.get(dreg, V("?"))
                if s.type == IMM:
                    imm = s.imm if ops[0].size == 4 else sx64(s.imm)
                    v = simp(Xor(d, C(imm)))
                elif s.type == REG:
                    sreg = REG32.get(s.reg, s.reg)
                    v = simp(Xor(d, regs.get(sreg, V("?"))))
                elif s.type == MEM:
                    m = mem_rsp_disp(s)
                    v = simp(Xor(d, V("?"))) if m is None else simp(Xor(d, slot_of(m[0])))
                else:
                    return evs
                regs[dreg] = zx32(v) if ops[0].size == 4 else v
                # if this reg's value came FROM a tracked slot, record the fold on the slot
                evs.append(Event(ins.address, "REG_XOR", f"{ins.op_str} -> {expr_str(regs[dreg])}"))
            elif mnem in ("ror", "rol") and len(ops) == 2:
                n = ops[1].imm if ops[1].type == IMM else 1
                d = regs.get(dreg, V("?"))
                rot = (-n) % 64 if mnem == "ror" else n % 64
                v = simp(Rot(d, rot))
                regs[dreg] = v
                kind = "ROR_FOLD" if mnem == "ror" else "ROL_FOLD"
                evs.append(Event(ins.address, kind, f"{ins.op_str} -> {expr_str(v)}"))
            elif mnem == "and" and len(ops) == 2 and ops[1].type == IMM:
                v = simp(Mask(regs.get(dreg, V("?")), ops[1].imm))
                regs[dreg] = v
                evs.append(Event(ins.address, "AND_FOLD", f"{ins.op_str} -> {expr_str(v)}"))
            elif mnem == "and" and len(ops) == 2 and ops[1].type == REG:
                # and reg, reg: fold when the mask side is a constant, else taint
                sreg = REG32.get(ops[1].reg, ops[1].reg)
                mask = regs.get(sreg, V("?"))
                if is_const(mask):
                    v = simp(Mask(regs.get(dreg, V("?")), mask[1]))
                    regs[dreg] = v
                    evs.append(Event(ins.address, "AND_FOLD", f"{ins.op_str} -> {expr_str(v)}"))
                else:
                    regs[dreg] = V("?")
                    evs.append(Event(ins.address, "UNTRACKED", f"{ins.op_str} (non-const mask)"))
            elif mnem == "imul" and len(ops) == 3 and ops[1].type == REG:
                # imul r, r, imm  - obfuscator identity/zero writes
                if ops[1].reg == ops[0].reg and ops[1].size == ops[0].size:
                    imm = ops[2].imm
                    if imm == 0:
                        regs[dreg] = C(0)
                        evs.append(Event(ins.address, "IMUL_ZERO", f"{ins.op_str} -> 0"))
                    elif imm == 1:
                        evs.append(Event(ins.address, "IMUL_IDENT", f"{ins.op_str} (identity)"))
                    else:
                        v = regs.get(dreg, V("?"))
                        regs[dreg] = simp(v) if not is_const(v) else C((v[1] * imm) & ((1 << 64) - 1))
            elif mnem == "cdqe":
                d = regs.get(dreg, V("?"))
                if is_const(d):
                    v = d[1] & 0xFFFFFFFF
                    if v & 0x80000000:
                        v |= ~0xFFFFFFFF
                    regs[dreg] = C(v & ((1 << 64) - 1))
                # else: slot provenance survives (rax already 64-bit canonical)
            elif mnem == "add" and len(ops) == 2 and ops[1].type == IMM:
                v = regs.get(dreg, V("?"))
                if is_const(v):
                    regs[dreg] = C((v[1] + ops[1].imm) & ((1 << 64) - 1))
                elif v[0] == "v" and ops[1].imm != 0:
                    regs[dreg] = simp(Xor(v, C(ops[1].imm)))  # keep provenance; add on var ~ opaque
            elif mnem == "lea":
                # lea reg, [rsp+K] or [rip+disp] (address value, not deref)
                src = ops[1]
                if src.type == MEM:
                    m = src.mem
                    if m.base == x86.X86_REG_RSP and m.index == 0:
                        regs[dreg] = V(f"rsp+{m.disp:#x}")
        return evs

    # -- use-site detection ----------------------------------------------------

    def detect_uses(self, block, st):
        """Any tracked-slot value consumed by branch/call/address-use: annotate."""
        for ins in block.insns:
            mnem = ins.mnemonic
            ops = ins.operands
            if mnem in ("cmp", "test") and len(ops) >= 2:
                for op, other in ((ops[0], ops[1]), (ops[1], ops[0])):
                    other_s = self._op_str(other)
                    m = mem_rsp_disp(op) if op.type == MEM else None
                    if m:
                        self.record_use(ins.address, m[0], self._slot(m[0], st),
                                        f"compare against {other_s}")
                    if op.type == REG:
                        dreg = REG32.get(op.reg, op.reg)
                        if dreg in st["reg"]:
                            e = st["reg"][dreg]
                            if isinstance(e, tuple) and e[0] == "v" and str(e[1]).startswith("s["):
                                self.record_use(ins.address, int(e[1][3:-1], 16), e,
                                                f"compare against {other_s}")
            if mnem == "call":
                for op in ops:
                    if op.type == REG and REG32.get(op.reg, op.reg) in st["reg"]:
                        e = st["reg"][REG32.get(op.reg, op.reg)]
                        if isinstance(e, tuple) and e[0] == "v" and str(e[1]).startswith("s["):
                            self.record_use(ins.address, int(e[1][3:-1], 16), e, "call argument")
                    m = mem_rsp_disp(op) if op.type == MEM else None
                    if m:
                        self.record_use(ins.address, m[0], self._slot(m[0], st),
                                        "call via memory")
            if mnem in ("jmp", "je", "jne", "ja", "jb", "jae", "jbe", "jz", "jnz"):
                if ops and ops[0].type == IMM:
                    self.record_use(ins.address, None, None,
                                    f"branch to 0x{ops[0].imm:X}")

    def _op_str(self, op):
        """x86 operand -> short string."""
        if op.type == IMM:
            return f"0x{op.imm:X}"
        if op.type == REG:
            return self.md.reg_name(op.reg)
        if op.type == MEM:
            m = op.mem
            b = self.md.reg_name(m.base) if m.base else ""
            i = self.md.reg_name(m.index) if m.index else ""
            seg = ""
            if m.segment:
                seg = self.md.reg_name(m.segment)
            disp = f"{m.disp:X}" if m.disp else ""
            inner = f"{seg}:"
            if b:
                inner += b
            if i:
                inner += f"+{i}"
                if m.scale > 1:
                    inner += f"*{m.scale}"
            if disp:
                inner += ("+" if not inner.endswith(":") and inner and m.disp > 0 else "") + disp
            return f"[{inner}]"
        return "?"

    def record_use(self, addr, disp, expr, consumer):
        self.use_sites.append((addr, disp, simp(expr) if expr else None, consumer))

    # -- block splitting --------------------------------------------------------

    def recover_starts(self, lo, hi, extra=()):
        """Instruction-start recovery: decode from lo, from every decoded
        fallthrough, and from every intra-range branch/call target (jmp/jcc/call
        imm operands), plus any explicit seed starts. This resolves the
        linear-sweep alignment ambiguity that variable-length x86 introduces in
        this obfuscated region."""
        starts = {lo}
        work = [lo]
        for x in extra:
            if lo <= x < hi:
                starts.add(x)
                work.append(x)
        decoded_ends = {}
        while work:
            va = work.pop()
            if va in decoded_ends or not (lo <= va < hi):
                continue
            ins = next(self.md.disasm(self.pe.read(va, 15), va), None)
            if ins is None:
                decoded_ends[va] = va
                continue
            end = va + ins.size
            decoded_ends[va] = end
            if ins.mnemonic in ("jmp", "je", "jne", "ja", "jb", "jae", "jbe",
                                "jz", "jnz", "js", "jns", "jpe", "jpo", "jl",
                                "jge", "jg", "jle", "call"):
                if ins.operands and ins.operands[0].type == IMM:
                    t = ins.operands[0].imm
                    if lo <= t < hi and t not in decoded_ends:
                        work.append(t)
                        starts.add(t)
                if ins.mnemonic != "jmp":      # conditional/call: fallthrough
                    if end < hi and end not in decoded_ends:
                        work.append(end)
                        starts.add(end)
            elif ins.mnemonic in ("ret", "retq", "hlt"):
                pass
            else:
                if end < hi and end not in decoded_ends:
                    work.append(end)
                    starts.add(end)
        return sorted(starts)

    def split_blocks(self, lo, hi, extra=()):
        """Block partition over recovered instruction starts. Each block is a
        maximal straight-line run ending at a jmp/jcc/call/ret. Overlapping
        starts (branch target landing inside the primary chain) keep the
        primary chain; gaps start a fresh block."""
        starts = self.recover_starts(lo, hi, extra)
        blocks = []
        cur = None
        cur_end = 0
        for s in starts:
            if cur is not None and s < cur_end:
                continue  # overlapping decode start: keep the primary chain
            ins = next(self.md.disasm(self.pe.read(s, 15), s), None)
            if ins is None:
                continue
            if cur is None or s > cur_end:
                cur = Block(ins.address)
            cur.insns.append(ins)
            cur_end = ins.address + ins.size
            if ins.mnemonic in ("jmp", "je", "jne", "ja", "jb", "jae", "jbe",
                                "jz", "jnz", "js", "jns", "jpe", "jpo", "jl",
                                "jge", "jg", "jle", "call", "ret", "retq", "hlt"):
                cur.term = ins
                blocks.append(cur)
                cur = None
        if cur is not None:
            cur.term = None
            blocks.append(cur)
        return blocks

    # -- top-level ---------------------------------------------------------------

    def fold_range(self, lo, hi, extra=()):
        """Fold every block in [lo,hi) in linear order; event list is cumulative."""
        blocks = self.split_blocks(lo, hi, extra)
        evs = []
        for b in blocks:
            st, local = self.fold_block(b)
            self.detect_uses(b, st)
            evs.extend(local)
        return evs


# --------------------------------------------------------------------------
# obfuscated dispatch step simulation (--steps)
# --------------------------------------------------------------------------

class StepSim:
    """Simulate each obfuscated dispatch forest: acc_init -> head cmp/je tree ->
    case block (fold) -> tail (acc ^= marker) -> back to head.
    Emits the ORDERED step table with per-step folded slot expressions and
    fully-resolved marker/acc constants."""

    def __init__(self, pe, md, engine):
        self.pe = pe
        self.md = md
        self.engine = engine

    def _find_tails(self, lo, hi, seeds=()):
        """Return [(tail_start, acc_slot, marker_slot, head_target), ...] for every
        block matching the tail signature: load acc slot + load marker slot,
        xor reg,reg, store acc slot, jmp back to the head."""
        out = []
        for b in self.engine.split_blocks(lo, hi, extra=seeds):
            if b.term is None or b.term.mnemonic != "jmp":
                continue
            tgt = b.term.operands[0].imm
            loads, store, xor = [], None, False
            for ins in b.insns:
                for op in ins.operands:
                    m = mem_rsp_disp(op) if op.type == MEM else None
                    if m:
                        if ins.mnemonic == "mov":
                            if op is ins.operands[0]:
                                store = m[0]
                            else:
                                loads.append(m[0])
                        elif ins.mnemonic == "xor":
                            loads.append(m[0])
                if ins.mnemonic == "xor" and len(ins.operands) == 2 and \
                   ins.operands[0].type == REG and ins.operands[1].type == REG:
                    xor = True
            if xor and store is not None and loads:
                markers = [l for l in loads if l != store]
                if markers:
                    out.append((b.start, store, markers[0], tgt))
        return out

    def _acc_init(self, lo, hi, acc):
        """Find the initial acc value: mov dword [rsp+acc], imm. Byte-exact
        pattern C7 84 24 <disp32> <imm32>, so block-recovery alignment never
        matters for this lookup."""
        blob = self.pe.read(lo, hi - lo)
        if blob is None:
            return None
        import struct as _s
        needle = bytes([0xC7, 0x84, 0x24]) + _s.pack("<I", acc & 0xFFFFFFFF)
        i = blob.find(needle)
        if i < 0:
            return None
        return _s.unpack_from("<I", blob, i + 7)[0]

    def _head_cmps_acc(self, head_va, acc, hi):
        """True when the head chain's first cmps reference [rsp+acc] (a valid
        dispatch head), not some other slot (bogus candidate)."""
        for _ in range(24):
            ins = next(self.md.disasm(self.pe.read(head_va, 15), head_va), None)
            if ins is None or ins.address >= hi:
                return False
            if ins.mnemonic == "cmp" and len(ins.operands) >= 2 and \
               ins.operands[0].type == MEM and ins.operands[1].type == IMM:
                m = ins.operands[0].mem
                return m.base == x86.X86_REG_RSP and m.disp == acc
            if ins.mnemonic == "jmp":
                head_va = ins.operands[0].imm
                continue
            head_va = ins.address + ins.size
        return False

    def _dispatch(self, acc, head_va, hi, depth=0):
        """Walk the cmp/ja/je binary-search tree from head_va for one acc value.
        @return (cmp_va, case_va) or ('sink', sink_va) or None."""
        if depth > 64:
            return None
        va = head_va
        for _ in range(200):
            ins = next(self.md.disasm(self.pe.read(va, 15), va), None)
            if ins is None or ins.address >= hi:
                return None
            if ins.mnemonic == "cmp" and len(ins.operands) >= 2 and \
               ins.operands[0].type == MEM and ins.operands[1].type == IMM:
                imm = ins.operands[1].imm & 0xFFFFFFFF
                ja_va = je_va = None
                # scan the immediate continuation for ja / je bound to this cmp
                nxt = ins.address + ins.size
                for _ in range(3):
                    i2 = next(self.md.disasm(self.pe.read(nxt, 15), nxt), None)
                    if i2 is None:
                        break
                    if i2.mnemonic == "ja":
                        ja_va = i2.operands[0].imm
                        nxt = i2.address + i2.size
                    elif i2.mnemonic == "je":
                        je_va = i2.operands[0].imm
                        nxt = i2.address + i2.size
                    else:
                        break
                if acc == imm and je_va is not None:
                    return (ins.address, je_va)
                if acc > imm and ja_va is not None:
                    return self._dispatch(acc, ja_va, hi, depth + 1)
                if acc > imm and ja_va is None:
                    pass  # fall through; a later cmp may still match
                va = nxt
                continue
            if ins.mnemonic == "jmp" and len(ins.operands) == 1:
                return ("sink", ins.operands[0].imm)
            if ins.mnemonic in ("je", "ja", "jne") and len(ins.operands) == 1:
                va = ins.address + ins.size  # equality already handled above
                continue
            va = ins.address + ins.size
        return None

    def _is_continuation(self, jmp_tgt, acc, head, hi):
        """True when jmp_tgt leads back into the dispatcher loop: the targeted
        block carries the tail signature (xors acc with the marker slot then
        jmps to head), or jmp_tgt IS the head."""
        if jmp_tgt == head:
            return True
        if jmp_tgt is None or jmp_tgt < hi and self.pe.off(jmp_tgt) is None:
            return False
        if not (jmp_tgt < hi):
            return False
        saw_xor = saw_store_acc = False
        va = jmp_tgt
        for _ in range(16):
            ins = next(self.md.disasm(self.pe.read(va, 15), va), None)
            if ins is None or ins.address >= hi:
                return False
            if ins.mnemonic == "xor" and len(ins.operands) == 2 and \
               ins.operands[0].type == REG and ins.operands[1].type == REG:
                saw_xor = True
            elif ins.mnemonic == "mov" and ins.operands[0].type == MEM:
                m = ins.operands[0].mem
                if m.base == x86.X86_REG_RSP and m.disp == acc:
                    saw_store_acc = True
            elif ins.mnemonic == "jmp":
                return saw_xor and saw_store_acc and ins.operands[0].imm == head
            elif ins.mnemonic in ("call", "ret", "retq"):
                return False
            va = ins.address + ins.size
        return False

    def _head_all_cases(self, head_va, hi):
        """Enumerate EVERY cmp-imm case in the dispatch head (DFS over both the
        ja branch and the fallthrough branch). @return {imm: je_target}."""
        seen_va = set()
        cases = {}

        def walk(va):
            if va in seen_va or not (va < hi):
                return
            seen_va.add(va)
            for _ in range(64):
                ins = next(self.md.disasm(self.pe.read(va, 15), va), None)
                if ins is None or ins.address >= hi:
                    return
                if ins.mnemonic == "cmp" and len(ins.operands) >= 2 and \
                   ins.operands[0].type == MEM and ins.operands[1].type == IMM:
                    imm = ins.operands[1].imm & 0xFFFFFFFF
                    ja_va = je_va = None
                    nxt = ins.address + ins.size
                    for _ in range(3):
                        i2 = next(self.md.disasm(self.pe.read(nxt, 15), nxt), None)
                        if i2 is None:
                            break
                        if i2.mnemonic == "ja":
                            ja_va = i2.operands[0].imm
                            nxt = i2.address + i2.size
                        elif i2.mnemonic == "je":
                            je_va = i2.operands[0].imm
                            nxt = i2.address + i2.size
                        else:
                            break
                    if je_va is not None:
                        cases[imm] = je_va
                    if ja_va is not None:
                        walk(ja_va)
                    va = nxt
                    continue
                if ins.mnemonic == "jmp":
                    return
                if ins.mnemonic in ("je", "ja", "jne") and len(ins.operands) == 1:
                    va = ins.address + ins.size
                    continue
                va = ins.address + ins.size
        walk(head_va)
        return cases

    def _fold_case(self, case_va, hi, entry_state=None):
        """Fold one case block: straight-line to first terminator, with the
        carried execution-order slot state (empty = runtime fresh symbols)."""
        engine = self.engine
        blk = Block(case_va)
        for ins in engine.md.disasm(engine.pe.read(case_va, hi - case_va), case_va):
            blk.insns.append(ins)
            if ins.mnemonic in ("jmp", "je", "jne", "ja", "jb", "call", "ret", "retq"):
                blk.term = ins
                break
        st, evs = engine.fold_block(blk, entry_state)
        marker_imm = jmp_tgt = None
        for e in evs:
            if e.kind == "MARKER_SET":
                marker_imm = int(e.detail.split("= 0x")[1], 16)
        if blk.term and blk.term.mnemonic == "jmp":
            jmp_tgt = blk.term.operands[0].imm
        return {"marker_imm": marker_imm, "jmp_tgt": jmp_tgt,
                "events": evs, "block": blk, "exit_state": st}

    def _prelude_state(self, prelude_va, head_va):
        """Fold the straight-line run [prelude_va, head_va) as the forest entry
        slot state (key derivation, -1 flags, selector hash, acc init)."""
        pe, md = self.pe, self.md
        blk = Block(prelude_va)
        for ins in md.disasm(pe.read(prelude_va, head_va - prelude_va), prelude_va):
            if ins.address >= head_va:
                break
            blk.insns.append(ins)
            if ins.mnemonic in ("jmp", "ret", "retq", "call"):
                blk.term = ins
                break
        eng = FoldEngine(pe, md, persist=False)
        st, _ = eng.fold_block(blk)
        return st

    def run(self, lo, hi, seeds=(), preludes=None):
        """Simulate every forest in [lo,hi). preludes: {head_va: prelude_va} -
        the pre-head straight-line run (key derivation, flags, acc init) whose
        folded slot writes seed the execution-order state.
        @return dict with per-forest steps."""
        out = {"forests": []}
        # dedupe by (acc_slot, head); prefer the candidate whose block starts
        # the earliest (the pure tail block, not a tail-fused case block)
        cands = {}
        for c in self._find_tails(lo, hi, seeds):
            key = (c[1], c[3])
            if key not in cands or c[0] < cands[key][0]:
                cands[key] = c
        for tail_start, acc, marker, head in cands.values():
            f = {"tail": tail_start, "acc_slot": acc, "marker_slot": marker,
                 "head": head, "steps": [], "terminal": None}
            # validate: a real dispatch head compares [rsp+acc] against immediates
            if not self._head_cmps_acc(head, acc, hi):
                f["terminal"] = ("not-a-dispatch-head", head)
                out["forests"].append(f)
                continue
            f["acc_init"] = self._acc_init(lo, hi, acc)
            if f["acc_init"] is None:
                f["terminal"] = ("no-acc-init", None)
                out["forests"].append(f)
                continue
            # execution-order fold engine: no persistent-chain leakage across
            # the linear pass; slot state is carried step by step instead
            fold_eng = FoldEngine(self.pe, self.md, persist=False)
            self.engine = fold_eng       # sim folds stay in the sim engine
            carry = {"reg": {}, "slot": {}}
            if preludes and head in preludes:
                st0 = self._prelude_state(preludes[head], head)
                if st0 is not None:
                    carry["slot"].update(st0["slot"])
            accv = f["acc_init"]
            for step_no in range(400):
                hit = self._dispatch(accv, head, hi)
                if hit is None:
                    f["terminal"] = ("lookup-failed", accv)
                    break
                if hit[0] == "sink":
                    f["terminal"] = ("no-case", accv, hit[1])
                    break
                cmp_va, case_va = hit
                cb = self._fold_case(case_va, hi, entry_state=carry)
                f["steps"].append({"n": step_no, "acc": accv, "cmp_va": cmp_va,
                                   "case_va": case_va, "marker": cb["marker_imm"],
                                   "jmp_tgt": cb["jmp_tgt"], "events": cb["events"]})
                # slots written by this step are the next step's slot state
                if cb["exit_state"] is not None:
                    carry["slot"].update(cb["exit_state"]["slot"])
                # Continue when the case funnels into the dispatcher loop:
                # jmp to the shared tail (tail signature), or jmp straight to
                # the head (tail-fused case blocks end by falling into the tail,
                # whose jmp goes to head).
                if not self._is_continuation(cb["jmp_tgt"], acc, head, hi) \
                        or cb["marker_imm"] is None:
                    f["terminal"] = ("case-terminates", case_va, cb["jmp_tgt"],
                                     "no-marker" if cb["marker_imm"] is None else "jumps-away")
                    break
                accv = (accv ^ cb["marker_imm"]) & 0xFFFFFFFF
            f["executed_cases"] = [s["case_va"] for s in f["steps"]]
            all_cases = self._head_all_cases(head, hi).values()
            f["decoy_cases"] = sorted(set(all_cases) - set(f["executed_cases"]))
            f["final_slots"] = {k: expr_str(v) for k, v in carry["slot"].items()}
            out["forests"].append(f)
        return out


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def run_fold(lo, hi, steps=False, seeds=(), preludes_raw=()):
    pe = PE(EXE)
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    eng = FoldEngine(pe, md)
    evs = eng.fold_range(lo, hi, extra=seeds)
    blocks = eng.split_blocks(lo, hi, extra=seeds)
    print(f"range 0x{lo:X}..0x{hi:X}: {len(blocks)} blocks, {len(evs)} fold events "
          f"(seeds: {', '.join(hex(s) for s in seeds) or 'none'})")
    xor_folds = [e for e in evs if e.kind == "XOR_FOLD"]
    rot_folds = [e for e in evs if e.kind in ("ROR_FOLD", "ROL_FOLD")]
    print(f"  xor-folds: {len(xor_folds)}   rots: {len(rot_folds)}")
    print("\n== chain map (persistent slot expressions) ==")
    for k in sorted(eng.chains):
        print(f"  [rsp+{k:#x}]: {expr_str(eng.chains[k])}")
    print("\n== events (first 120) ==")
    for e in evs[:120]:
        print(f"  {e.addr:#x}  {e.kind:12s} {e.detail}")
    print("\n== use sites ==")
    for addr, disp, expr, consumer in eng.use_sites:
        tag = f"[rsp+{disp:#x}]" if disp is not None else "-"
        e = expr_str(expr) if expr is not None else "-"
        print(f"  {addr:#x}  {tag:14s} {e:40s} {consumer}")
    if steps:
        preludes = {}
        for p in preludes_raw:
            hp, pv = p.split(":", 1)
            preludes[int(hp, 0)] = int(pv, 0)
        sim = StepSim(pe, md, eng)
        res = sim.run(lo, hi, seeds=seeds, preludes=preludes)
        print("\n== dispatch simulation ==")
        if not res["forests"]:
            print("  no dispatch tail/head pattern found in range")
        for f in res["forests"]:
            ini = f.get("acc_init")
            print(f"  forest: acc [rsp+{f['acc_slot']:#x}]  marker [rsp+{f['marker_slot']:#x}]  "
                  f"head 0x{f['head']:#x}  init {('0x%08X' % ini) if ini is not None else 'NONE'}  "
                  f"tail 0x{f['tail']:#x}")
            for s in f["steps"]:
                if s["marker"] is not None:
                    nxt = (s["acc"] ^ s["marker"]) & 0xFFFFFFFF
                    print(f"    step {s['n']:2d}: acc=0x{s['acc']:08X} cmp@0x{s['cmp_va']:#x} "
                          f"case@0x{s['case_va']:#x} marker=0x{s['marker']:08X} -> acc'=0x{nxt:08X}")
                else:
                    print(f"    step {s['n']:2d}: acc=0x{s['acc']:08X} cmp@0x{s['cmp_va']:#x} "
                          f"case@0x{s['case_va']:#x} TERMINAL (no marker)")
                for e in s["events"]:
                    if e.kind in ("SLOT_XOR_FOLD", "SLOT_ROR_FOLD", "ROL_FOLD",
                                  "ROR_FOLD", "AND_FOLD", "MASK_FOLD"):
                        d = e.detail if len(e.detail) <= 110 else e.detail[:107] + "..."
                        print(f"      {e.addr:#x} {e.kind}: {d}")
            print(f"    terminal: {f['terminal']}")
            if f.get("executed_cases"):
                print(f"    executed cases: {len(f['executed_cases'])} "
                      f"({', '.join(hex(c) for c in sorted(f['executed_cases']))})")
            if f.get("decoy_cases") is not None:
                print(f"    DECOY cases (head targets never dispatched): "
                      f"{len(f['decoy_cases'])} ({', '.join(hex(c) for c in f['decoy_cases'])})")
            if f.get("final_slots"):
                print("    final slot exprs (execution order, compact):")
                for k, v in sorted(f["final_slots"].items()):
                    if len(v) <= 120:
                        print(f"      [rsp+{k:#x}] = {v}")
                    else:
                        print(f"      [rsp+{k:#x}] = <symbolic rot/xor tree, depth {v.count('rotl')}>")
    return eng


def self_test():
    pe = PE(EXE)
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    eng = FoldEngine(pe, md)
    # seed: the case block at 0x1407DA922 is a je target from the head (0x1407DA473)
    # outside this fold sub-range; its start is verified by the branch graph.
    evs = eng.fold_range(0x1407DA8F0, 0x1407DA980, extra=(0x1407DA922,))
    xor_folds = [e for e in evs if e.kind in ("XOR_FOLD", "SLOT_XOR_FOLD")]
    rot20 = [e for e in evs if e.kind in ("ROR_FOLD", "SLOT_ROR_FOLD") and "0x20" in e.detail]
    ok_xor = len(xor_folds) >= 2
    ok_ror = len(rot20) >= 1
    folded_consts = set()
    for e in xor_folds:
        d = e.detail
        if "^= 0x" in d:
            folded_consts.add(int(d.split("^= 0x")[1][:8], 16))
    ok_consts = (0x2EAABAC2 in folded_consts) and (0xC4A1CDBF in folded_consts)
    print(f"selftest events: xor-folds={len(xor_folds)} ror20={len(rot20)}")
    for e in evs:
        print(f"   {e.addr:#x} {e.kind} {e.detail}")
    chain_f0 = expr_str(eng.chains.get(0x145F0, V("?")))
    chain_e0 = expr_str(eng.chains.get(0x145E0, V("?")))
    print(f"chain[145f0] = {chain_f0}")
    print(f"chain[145e0] = {chain_e0}")
    verdict = ok_xor and ok_ror and ok_consts
    print("ORACLE " + ("PASS" if verdict else "FAIL"))
    if not ok_xor:
        print("   reason: expected >=2 xor-fold events (chain ^= imm) in the known chain")
    if not ok_ror:
        print("   reason: expected a ror reg,0x20 event in the known chain")
    if not ok_consts:
        print("   reason: expected folded constants 0x2EAABAC2 and 0xC4A1CDBF in the "
              "slot-0x145f0 chain (missing: " +
              ", ".join(f"0x{c:X}" for c in (0x2EAABAC2, 0xC4A1CDBF) if c not in folded_consts) +
              ")")
    return 0 if verdict else 1


def main():
    argv = sys.argv[1:]
    if argv and argv[0] == "--self-test":
        return self_test()
    if len(argv) < 2:
        print(__doc__)
        return 2
    lo = int(argv[0], 0)
    hi = int(argv[1], 0)
    seeds = []
    preludes = []
    steps = False
    i = 2
    while i < len(argv):
        a = argv[i]
        if a == "--steps":
            steps = True
        elif a == "--seeds":
            i += 1
            while i < len(argv) and not argv[i].startswith("--"):
                seeds.append(int(argv[i], 0))
                i += 1
            continue
        elif a == "--prelude":
            i += 1
            while i < len(argv) and not argv[i].startswith("--"):
                preludes.append(argv[i])
                i += 1
            continue
        i += 1
    run_fold(lo, hi, steps=steps, seeds=tuple(seeds), preludes_raw=tuple(preludes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())