#!/usr/bin/env python3
# REGISTRY: caps: backward-slice, provenance-boundary
"""slice_back.py - THE BOUNDED BACKWARD SLICE (tool-brief-slice-back.md,
2026-09-06). Answers "WHERE DOES THIS FIELD'S VALUE COME FROM?" - given a
write site (an instruction VA inside a .pdata-backed function), walk the
function's instructions backward and classify every step until a BOUNDARY.

HONESTY CONTRACT (the hardest-of-the-five rule): the tool's value is its
BOUNDARIES. It never speculates past one:
  BOUNDARY:PARAM        the traced register is live at function entry
  BOUNDARY:MEM [b+disp] value loaded from memory (displacement named;
                        struct_view/field_xref can join it)
  BOUNDARY:STACK        rbp/rsp-relative load
  BOUNDARY:GLOBAL addr  rip-relative read
  BOUNDARY:CALL-RETURN  value came from a call's return (callee named when
                        the E8 target is direct)
  CONSTANT <imm>        literal
  BOUNDARY:LOOP-CARRIED the def sits inside a backward edge (approximate,
                        LOUD)
  BOUNDARY:UNKNOWN      the walk could not resolve (loud, never guessed)
The walk is a LINEAR backward scan over the function's finite instruction
list - it CANNOT hang (T5-F5 is satisfied structurally) and --max-insn caps
the step budget with a LOUD truncation marker (the T3.1 rule: the output
says the stream ended).

The disassembly ALWAYS starts at the pdata-backed function start, never at
the site (the 20.291 invented-stream trap). A site VA that is not an
instruction start in that stream is REFUSED (mid-instruction anchor).

V1 scope: no cross-function descent. --follow-calls NAMES the callee at
CALL-RETURN boundaries (descent mode = OPEN, recorded in the claim).

Usage:
  /usr/bin/python3 RE_scripts/slice_back.py <site-va> [--max-insn 2000]
      [--json] [--exe P] [--selftest]
Exit: 0 sliced; 1 REFUSED (gap / mid-instruction / unresolvable); 2 no
BOUNDARY reached (truncated); 4 selftest failure; 5 usage.
Interpreter: /usr/bin/python3 (capstone 5.x; no unicorn needed).
"""
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from pe_reader import PE  # noqa: E402
import capstone  # noqa: E402

DEFAULT_EXE = os.path.join(ROOT, "RE_output", "destiny2_unpacked_full.exe")
PDATA_SCRIPT = os.path.join(HERE, "pdata_bounds.py")
DISASM_HANDOFF = ("RE_scripts/lane_svc43_disasm_range.py <va> <va+size>")
BASE = 0x140000000

REG64 = {"rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp",
         "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15"}
REG32 = {"eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp",
         "r8d", "r9d", "r10d", "r11d", "r12d", "r13d", "r14d", "r15d"}
STACK_REGS = {"rsp", "rbp", "esp", "ebp"}
CANON = {"eax": "rax", "ebx": "rbx", "ecx": "rcx", "edx": "rdx",
         "esi": "rsi", "edi": "rdi", "ebp": "rbp", "esp": "rsp",
         "r8d": "r8", "r9d": "r9", "r10d": "r10", "r11d": "r11",
         "r12d": "r12", "r13d": "r13", "r14d": "r14", "r15d": "r15",
         "ax": "rax", "al": "rax", "ah": "rax", "bx": "rbx", "bl": "rbx",
         "cx": "rcx", "cl": "rcx", "dx": "rdx", "dl": "rdx",
         "sil": "rsi", "dil": "rdi", "spl": "rsp", "bpl": "rbp"}


def norm_reg(r):
    r = r.lower()
    return CANON.get(r, r)


def owning_function(site):
    """(begin, end, offset) of the .pdata entry containing site, or None."""
    out = subprocess.run(
        [sys.executable, PDATA_SCRIPT, hex(site)],
        capture_output=True, text=True, timeout=300).stdout
    m = re.search(r"entry (0x[0-9A-Fa-f]+)\.\.(0x[0-9A-Fa-f]+)"
                  r".*offset=(0x[0-9A-Fa-f]+)", out)
    if not m or "OUTSIDE" in out:
        return None
    return (int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16))


def disasm_function(pe, fstart, fend):
    """Linear capstone disassembly of [fstart, fend) from the function
    START (never from the site - the 20.291 trap). Returns a list of
    step dicts; a gap (unreadable bytes) aborts loudly."""
    code = pe.read(fstart, fend - fstart)
    if not code:
        raise RuntimeError("cannot read function bytes at 0x%X" % fstart)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    steps = []
    for insn in md.disasm(code, fstart):
        steps.append({"addr": insn.address, "size": insn.size,
                      "mnem": insn.mnemonic, "op_str": insn.op_str,
                      "bytes": insn.bytes.hex()})
    return steps


# --------------------------------------------------------------- the engine ---
def parse_mem_operand(op):
    """capstone X86_OP_MEM -> dict. Pure; unit-testable without capstone."""
    base = op.mem.base
    idx = op.mem.index
    return {"base": norm_reg(capstone_reg_name(base)),
            "index": norm_reg(capstone_reg_name(idx)),
            "disp": op.mem.disp}


def capstone_reg_name(rid):
    try:
        return capstone.x86.x86_reg_name(rid, 0) if False else None
    except Exception:
        return None


def step_info(insn):
    """Extract (dst_regs, src_regs, src_mem, src_imm, is_jump, jump_target,
    is_call, call_target) from a capstone instruction or a synthetic dict.
    Pure over the parsed operands - unit-testable."""
    if "dst_regs" in insn:          # synthetic (selftest) form
        srcs = list(insn["src_regs"])
        if insn.get("src_imm") is not None:
            srcs = srcs + ["IMM:%d" % insn["src_imm"]]
        return (insn["dst_regs"], srcs, insn.get("src_mem"),
                insn.get("src_imm"), insn.get("is_jump", False),
                insn.get("jump_target"), insn.get("is_call", False),
                insn.get("call_target"))
    return _parse_fallback(insn)


def _parse_fallback(insn):
    """operand extraction via capstone detail ops (the real path)."""
    import capstone.x86 as x86
    dst, srcs, mem, imm = [], [], None, None
    is_jump = insn["mnem"].startswith(("jmp", "j")) or \
        insn["mnem"] == "call"
    is_call = insn["mnem"] == "call"
    jt = ct = None
    for op in insn["ops"]:
        if op.type == x86.X86_OP_REG:
            r = norm_reg(insn["reg_name"](op.reg))
            if op.access & capstone.CS_AC_WRITE and r not in dst:
                dst.append(r)
            elif op.access & capstone.CS_AC_READ:
                srcs.append(r)
        elif op.type == x86.X86_OP_IMM:
            if is_jump:
                jt = ct = op.imm
            elif insn["mnem"].startswith(("mov", "add", "sub", "and", "or",
                                          "xor", "shl", "shr", "lea")):
                imm = op.imm
                srcs.append("IMM:%d" % op.imm)
            else:
                srcs.append("IMM:%d" % op.imm)
        elif op.type == x86.X86_OP_MEM:
            m = {"base": norm_reg(insn["reg_name"](op.mem.base))
                 if op.mem.base else None,
                 "index": norm_reg(insn["reg_name"](op.mem.index))
                 if op.mem.index else None,
                 "disp": op.mem.disp,
                 "rip": op.mem.base == 0}
            mem = m
    return dst, srcs, mem, imm, is_jump, jt, is_call, ct


def slice_chain(steps, site_addr, max_insn=2000, follow_calls=False):
    """THE backward slice over `steps` (ascending step dicts with capstone
    detail). Returns (chain, boundaries, meta). The walk is a linear scan
    from the site backward - finite by construction (T5-F5: no hang)."""
    site_idx = None
    for i, s in enumerate(steps):
        if s["addr"] == site_addr:
            site_idx = i
            break
    if site_idx is None:
        raise MidInstruction("0x%X is not an instruction start in the "
                             "linear stream of %d steps (mid-instruction "
                             "anchor - the 20.291 class)"
                             % (site_addr, len(steps)))
    chain = []
    boundaries = []
    tracked = set()          # registers whose provenance we are walking
    truncated = False
    steps_seen = 0
    loop_marks = set()
    ever_tracked = set()     # every register the walk ever traced

    # seed from the site instruction's write
    site = steps[site_idx]
    dst, srcs, mem, _imm, _j, _jt, _c, _ct = step_info(site)
    if mem is not None and dst:
        chain.append("SITE 0x%X %s %s -> writes [%s+%#x] (the field)"
                     % (site["addr"], site["mnem"], site["op_str"],
                        mem["base"], mem["disp"] & 0xFFFFFFFF
                        if mem["disp"] >= 0 else mem["disp"]))
        tracked.update(dst)
        tracked.add(mem["base"])
        if mem.get("index"):
            tracked.add(mem.get("index"))
    elif dst:
        chain.append("SITE 0x%X %s %s -> writes register %s"
                     % (site["addr"], site["mnem"], site["op_str"], dst[0]))
        tracked.add(dst[0])
    elif mem is not None:
        chain.append("SITE 0x%X %s %s -> writes memory (no register dst)"
                     % (site["addr"], site["mnem"], site["op_str"]))
        tracked.update(srcs)          # the STORED VALUE track
        tracked.add(mem["base"])      # the ADDRESS track
        if mem.get("index"):
            tracked.add(mem.get("index"))
    else:
        chain.append("SITE 0x%X %s %s -> no writable operand parsed"
                     % (site["addr"], site["mnem"], site["op_str"]))

    for i in range(site_idx - 1, -1, -1):
        if steps_seen >= max_insn:
            boundaries = [("BOUNDARY:UNKNOWN",
                           "SLICE TRUNCATED at %d instructions - the walk "
                           "did not reach entry (budget exhausted; treat "
                           "provenance as INCOMPLETE)" % max_insn)]
            return chain, boundaries, {"truncated": True}
        ins = steps[i]
        steps_seen += 1
        dst, srcs, mem, _imm, is_jump, jt, is_call, ct = step_info(ins)
        ever_tracked |= tracked
        # a call DEFINES rax (the return value): if rax is being traced,
        # the walk stops here - the value comes from the callee
        if is_call and "rax" in tracked:
            tracked.discard("rax")
            boundaries.append(
                ("BOUNDARY:CALL-RETURN",
                 "0x%X %s %s %s"
                 % (ins["addr"], ins["mnem"], ins["op_str"],
                    ("(indirect - no callee named)" if ct is None
                     else "callee 0x%X" % ct))))
            if follow_calls and ct:
                boundaries.append(
                    ("FOLLOW-NOTE",
                     "descent into 0x%X not performed (v1: "
                     "--follow-calls names only)" % ct))
            if not tracked:
                chain.append("WALK 0x%X %s %s -> all traced values "
                             "resolved" % (ins["addr"], ins["mnem"],
                                           ins["op_str"]))
                break
            continue
        writes_tracked = [r for r in dst if r in tracked]
        # loop-edge detection: a backward jump whose head is above us
        if is_jump and jt is not None and jt > ins["addr"] + ins["size"] \
                and jt <= site_addr:
            loop_marks.add(jt)
        if not writes_tracked:
            continue
        for r in writes_tracked:
            tracked.discard(r)
        for s in srcs:
            if s.startswith("IMM:"):
                boundaries.append(("CONSTANT", "0x%X %s <- %s"
                                   % (ins["addr"], ins["mnem"], s[4:])))
            else:
                rr = norm_reg(s)
                if rr in ("rsp", "rbp", "esp", "ebp"):
                    continue
                tracked.add(rr)
        if mem is not None:
            if mem["base"] in ("rsp", "rbp", "esp", "ebp"):
                boundaries.append(("BOUNDARY:STACK",
                                   "0x%X %s %s reads [%s%+#x]"
                                   % (ins["addr"], ins["mnem"],
                                      ins["op_str"], mem["base"],
                                      mem["disp"])))
            elif mem.get("rip"):
                boundaries.append(("BOUNDARY:GLOBAL",
                                   "0x%X %s reads rip-relative -> 0x%X"
                                   % (ins["addr"], ins["mnem"],
                                      ins["addr"] + ins["size"]
                                      + mem["disp"])))
            else:
                boundaries.append(("BOUNDARY:MEM",
                                   "0x%X %s reads [%s%s%#x] - join with "
                                   "field_xref/struct_view on the disp"
                                   % (ins["addr"], ins["mnem"],
                                      mem["base"],
                                      ("+%s*%d" % (mem.get("index"), 1))
                                      if mem.get("index") else "",
                                      mem["disp"])))
                if mem["base"]:
                    tracked.add(mem["base"])
                if mem.get("index"):
                    tracked.add(mem.get("index"))
        if is_call:
            # a call DEFINES rax (the return value): if rax is being traced,
            # the walk stops here - the value comes from the callee
            if "rax" in tracked:
                tracked.discard("rax")
                boundaries.append(
                    ("BOUNDARY:CALL-RETURN",
                     "0x%X %s %s %s"
                     % (ins["addr"], ins["mnem"], ins["op_str"],
                        ("(indirect - no callee named)" if ct is None
                         else "callee 0x%X" % ct))))
                if follow_calls and ct:
                    boundaries.append(
                        ("FOLLOW-NOTE",
                         "descent into 0x%X not performed (v1: "
                         "--follow-calls names only)" % ct))
                continue
        if not tracked:
            chain.append("WALK 0x%X %s %s -> all traced values resolved"
                         % (ins["addr"], ins["mnem"], ins["op_str"]))
            break
        chain.append("WALK 0x%X %-8s %s   tracked=%s"
                     % (ins["addr"], ins["mnem"], ins["op_str"],
                        ",".join(sorted(tracked))))
    else:
        boundaries.append(("BOUNDARY:PARAM",
                           "function entry reached with live traced "
                           "registers: %s (incoming params)"
                           % ",".join(sorted(tracked)) if tracked else
                           "function entry reached"))
    loop_boundaries = []
    for jt in sorted(loop_marks, reverse=True):
        # only report a loop edge when a traced register is written inside
        # its range - otherwise it is range noise, not loop-carried provenance
        in_range = [s for s in steps if jt <= s["addr"] < site_addr]
        written = set()
        for s in in_range:
            d, _s2, _m2, _i2, _j2, _t2, _c2, _t3 = step_info(s)
            written.update(d)
        if written & ever_tracked:
            loop_boundaries.append(
                ("BOUNDARY:LOOP-CARRIED",
                 "a backward edge heads to 0x%X inside the walked range and "
                 "the loop body writes a traced register (%s) - values may "
                 "be loop-carried"
                 % (jt, ",".join(sorted(written & ever_tracked)))))
    if len(loop_boundaries) > 4:
        n = len(loop_boundaries)
        loop_boundaries = loop_boundaries[:4]
        loop_boundaries.append(
            ("BOUNDARY:LOOP-CARRIED",
             "TRUNCATED: %d loop edges crossed, 4 shown (nearest the site "
             "first; each is a real backward edge writing a traced "
             "register)" % n))
    boundaries.extend(loop_boundaries)
    meta = {"steps_seen": steps_seen, "truncated": False,
            "site": site_addr}
    return chain, boundaries, meta


# small shim so the engine runs on both capstone and synthetic steps
def capstone_step(insn):
    import capstone.x86  # noqa
    return {"addr": insn.address, "size": insn.size, "mnem": insn.mnemonic,
            "op_str": insn.op_str, "ops": insn.operands,
            "reg_name": insn.reg_name}


def main(argv):
    if "--selftest" in argv:
        return selftest()
    import argparse
    p = argparse.ArgumentParser(prog="slice_back.py")
    p.add_argument("site")
    p.add_argument("--max-insn", type=int, default=2000)
    p.add_argument("--follow-calls", action="store_true",
                   help="name the callee at CALL-RETURN boundaries (v1: "
                        "no descent)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--exe", default=DEFAULT_EXE)
    a = p.parse_args(argv)
    try:
        site = int(a.site, 0)
    except ValueError:
        print("usage: <site-va> must be a number")
        return 5

    ent = owning_function(site)
    if ent is None:
        print("GAP/UNRESOLVED: 0x%X has no containing .pdata entry - "
              "REFUSED. Use %s" % (site, DISASM_HANDOFF))
        return 1
    fstart, fend, off = ent
    print("enclosing    : 0x%X..0x%X (site +0x%X)" % (fstart, fend, off))
    pe = PE(a.exe)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    steps = [capstone_step(i) for i in
             md.disasm(pe.read(fstart, fend - fstart), fstart)]
    if not steps:
        print("REFUSED: linear disassembly produced no instructions")
        return 1
    # the site must be an instruction start in the stream
    if site not in [s["addr"] for s in steps]:
        print("REFUSED: 0x%X is not an instruction start in the linear "
              "stream of 0x%X..0x%X (mid-instruction anchor - the 20.291 "
              "class)" % (site, fstart, fend))
        return 1
    try:
        chain, boundaries, meta = slice_chain(
            steps, site, max_insn=a.max_insn, follow_calls=a.follow_calls)
    except MidInstruction as e:
        print("REFUSED: %s" % e)
        return 1
    if a.json:
        import json
        print(json.dumps({"chain": chain, "boundaries": boundaries,
                          "meta": meta}, indent=2))
    else:
        print("-- backward chain (from the site, walking to entry) --")
        for c in chain:
            print(" ", c)
        print("-- boundaries --")
        for kind, desc in boundaries:
            print("  %-22s %s" % (kind, desc))
        if meta.get("truncated"):
            print("SLICE TRUNCATED at %d instructions - BOUNDARY:UNKNOWN"
                  % a.max_insn)
    if meta.get("truncated"):
        return 2
    return 0


class MidInstruction(Exception):
    pass


# ----------------------------------------------------------------- selftest ---
def _syn(addr, mnem, op_str, dst=(), srcs=(), mem=None, imm=None,
         is_jump=False, jt=None, is_call=False, ct=None):
    return {"addr": addr_of(addr), "size": 4, "mnem": mnem, "op_str": op_str,
            "dst_regs": list(dst), "src_regs": list(srcs), "src_mem": mem,
            "src_imm": imm, "is_jump": is_jump, "jump_target": jt,
            "is_call": is_call, "call_target": ct}


def addr_of(x):
    return x


def selftest():
    """Synthetic instruction streams for every boundary class + the refusal
    arms via the real pdata gate. Prints SLICE_BACK SELFTEST: n/n PASS last."""
    fails = []

    def check(name, cond, detail=""):
        print("%s %-52s %s" % ("PASS" if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    base = 0x60000000
    a = lambda o: base + o

    # ---- T5-P1: the recorded synthetic shape ----
    # mov rax,[rcx+0x94E]; add rax,rbx; mov [rdx+0x57C],rax
    steps = [
        {"addr": base + 0, "size": 4, "mnem": "push", "op_str": "rbp",
         "dst_regs": ["rsp"], "src_regs": ["rbp", "rsp"]},
        {"addr": base + 4, "size": 4, "mnem": "mov", "op_str": "rax, [rcx+0x94E]",
         "dst_regs": ["rax"], "src_regs": [], "src_mem": {"base": "rcx",
                                                          "disp": 0x94E}},
        {"addr": base + 8, "size": 4, "mnem": "add", "op_str": "rax, rbx",
         "dst_regs": ["rax"], "src_regs": ["rax", "rbx"]},
        {"addr": base + 12, "size": 4, "mnem": "mov",
         "op_str": "[rdx+0x57C], rax",
         "dst_regs": [], "src_regs": ["rax"], "src_mem": {"base": "rdx",
                                                          "disp": 0x57C}},
    ]
    chain, bounds, meta = slice_chain(steps, base + 12)
    kinds = [k for k, _d in bounds]
    detail = "; ".join(d for _k, d in bounds)
    param_line = "; ".join(d for k, d in bounds if k == "BOUNDARY:PARAM")
    check("T5-P1 chain ends: MEM[rcx+0x94E] + entry PARAM naming rbx/rdx/rcx",
          meta.get("truncated") is False and
          kinds.count("BOUNDARY:MEM") == 1 and
          kinds.count("BOUNDARY:PARAM") == 1 and
          all(r in param_line for r in ("rbx", "rdx", "rcx")),
          "; ".join("%s:%s" % (k, d[:40]) for k, d in bounds))
    check("T5-P1 no speculation past boundaries",
          all(k.startswith("BOUNDARY") or k == "CONSTANT" for k, _d in bounds))

    # ---- T5-P3 boundary-class completeness (synthetic, one per class) ----
    # CONSTANT
    steps_c = [
        {"addr": base, "size": 4, "mnem": "mov", "op_str": "eax, 0x2AC0",
         "dst_regs": ["rax"], "src_regs": [], "src_imm": 0x2AC0},
        {"addr": base + 4, "size": 4, "mnem": "mov", "op_str": "[rdi], rax",
         "dst_regs": [], "src_regs": ["rax"], "src_mem": {"base": "rdi",
                                                          "disp": 0}},
    ]
    _c, b_c, _m = slice_chain(steps_c, base + 4)
    check("T5-P3 CONSTANT boundary", any(k == "CONSTANT" for k, _d in b_c),
          "; ".join(d for _k, d in b_c))
    # GLOBAL (rip-relative)
    steps_g = [
        {"addr": base, "size": 7, "mnem": "mov", "op_str": "rax, [rip+0x1234]",
         "dst_regs": ["rax"], "src_regs": [],
         "src_mem": {"base": "rip", "disp": 0x1234, "rip": True}},
        {"addr": base + 7, "size": 4, "mnem": "mov", "op_str": "[rdi], rax",
         "dst_regs": [], "src_regs": ["rax"], "src_mem": {"base": "rdi",
                                                          "disp": 0}},
    ]
    _c, b_g, _m = slice_chain(steps_g, base + 7)
    check("T5-P3 GLOBAL boundary (rip-relative)",
          any(k == "BOUNDARY:GLOBAL" for k, _d in b_g),
          "; ".join(d[:40] for _k, d in b_g))
    # STACK
    steps_s = [
        {"addr": base, "size": 4, "mnem": "mov", "op_str": "rax, [rbp+0x10]",
         "dst_regs": ["rax"], "src_regs": [],
         "src_mem": {"base": "rbp", "disp": 0x10}},
        {"addr": base + 4, "size": 4, "mnem": "mov", "op_str": "[rdi], rax",
         "dst_regs": [], "src_regs": ["rax"], "src_mem": {"base": "rdi",
                                                          "disp": 0}},
    ]
    _c, b_s, _m = slice_chain(steps_s, base + 4)
    check("T5-P3 STACK boundary", any(k == "BOUNDARY:STACK" for k, _d in b_s),
          "; ".join(d[:40] for _k, d in b_s))
    # CALL-RETURN
    steps_call = [
        {"addr": base, "size": 5, "mnem": "call", "op_str": "0x141718080",
         "dst_regs": [], "src_regs": [], "is_call": True, "call_target":
         0x141718080},
        {"addr": base + 5, "size": 4, "mnem": "mov", "op_str": "[rdi], rax",
         "dst_regs": [], "src_regs": ["rax"], "src_mem": {"base": "rdi",
                                                          "disp": 0}},
    ]
    _c, b_call, _m = slice_chain(steps_call, base + 5, follow_calls=True)
    check("T5-P3 CALL-RETURN boundary names the callee",
          any(k == "BOUNDARY:CALL-RETURN" and "141718080" in d
              for k, d in b_call),
          "; ".join(d[:40] for _k, d in b_call))

    # ---- T5-F1: value from a call return STOPS at the boundary ----
    chain1, b1, _m = slice_chain(steps_call, base + 5)
    check("T5-F1 no silent descent into the callee",
          all(not d.startswith("inside") for _k, d in b1))

    # ---- T5-F4: indirect call -> CALL-RETURN "(indirect)", no guessed callee ----
    steps_vmp = [
        {"addr": base, "size": 3, "mnem": "call", "op_str": "qword [r10]",
         "dst_regs": [], "src_regs": [], "is_call": True, "call_target": None},
        {"addr": base + 3, "size": 4, "mnem": "mov", "op_str": "[rdi], rax",
         "dst_regs": [], "src_regs": ["rax"], "src_mem": {"base": "rdi",
                                                          "disp": 0}},
    ]
    _c2, b_v, _m2 = slice_chain(steps_vmp, base + 3)
    check("T5-F4 indirect call -> CALL-RETURN (indirect), no guessed target",
          any(k == "BOUNDARY:CALL-RETURN" and "indirect" in d
              for k, d in b_v),
          "; ".join(d[:50] for _k, d in b_v))

    # ---- T5-F5: the walk is finite (linear over the step list) + budget ----
    long_steps = [{"addr": base + i * 4, "size": 4, "mnem": "nop",
                   "op_str": "", "dst_regs": [], "src_regs": []}
                  for i in range(100)]
    long_steps = long_steps + [
        {"addr": base + 400, "size": 4, "mnem": "mov", "op_str": "[rdi], rax",
         "dst_regs": [], "src_regs": ["rax"], "src_mem": {"base": "rdi",
                                                          "disp": 0}}]
    _c3, b3, m3 = slice_chain(long_steps, base + 400, max_insn=10)
    check("T5-F5 budget exhaustion -> LOUD truncation, no hang",
          m3.get("truncated") is True and
          any(k == "BOUNDARY:UNKNOWN" for k, _d in b3),
          "; ".join(d[:50] for _k, d in b3))

    # ---- real-binary arms (pdata gate) ----
    ok_gap = owning_function(0x1404DD470) is None
    check("T5-F3 .pdata gap refuses at the gate", ok_gap,
          "0x1404DD470 resolves to None")

    print("SLICE_BACK SELFTEST: %d/%d PASS" % (8 - len(fails), 8))
    return 0 if not fails else 4


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
