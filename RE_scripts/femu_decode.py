#!/usr/bin/env python3
# REGISTRY: caps: femu-scaffold, decode-run, abi-args
"""femu_decode.py - THE DECODE SCAFFOLD (tool-brief-femu-decode.md, 2026-09-06).

One command for the EXACT-tier question "what does the client's own code
decode this blob to": run any .pdata-backed decode function against supplied
bytes under femu, offline, in seconds. Composition, not a fork: the engine is
femu.Rig; this tool is the pdata gate + argument marshalling + faithful
result presentation.

Measured reason to exist: 20.318 spent THREE boots (p2-185/186/187) confirming
the join record is the decoded JoinRequest struct - a question this tool
answers offline (femu contract: codecs = EXACT tier, boot-grade fidelity).

INTERPRETER: miniconda python3 (unicorn). /usr/bin/python3 lacks unicorn and
FAILS LOUD here (the documented matrix, femu.py docstring).

Usage:
  python3 RE_scripts/femu_decode.py <va> (--bytes HEX | --infile P | --string S)
      [--binary P] [--dump P] [--no-rebase]
      [--sig rcx=buf,rdx=len,r8=out,r9=0x10]   # default: rcx=buf,rdx=len
      [--stack-args 0xABCD,0x1234]              # 5th+ MS-x64 args (frame push)
      [--out-len N] [--max-insn N] [--wmem VA=HEX]...
      [--reader-init VA]                        # the ent bit-reader preset
      [--json] [--force]
      [--selftest]

--sig values: placeholders buf (input buffer VA), len (input length),
out (output buffer VA, requires --out-len); or integer literals (hex/dec).
Unbound registers default 0. --stack-args appends args 5..n to the call frame.

--reader-init VA: initialize VA as the ent-cluster MSB-first bit reader
(presets the reader object exactly as RE_output/scratch/
femu_ent_header_final.py's init_reader; the fixture for ent_header 0x141717EB0).

Exit codes: 0 returned+clean; 1 REFUSED (pdata gap / non-function-start
without --force); 2 returned but UNTRUSTED (holes); 3 NOT-RETURNED
(crash/import/timeout - the reason IS the finding); 4 selftest failure;
5 usage.

A hole never prints silently: any hole in the run marks the output UNTRUSTED.
Every report carries the provenance flags verbatim (pages_pulled, holes,
rebase_reads, imports_called) - a result that depended on the rebase
heuristic says so.
"""
import json
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    import unicorn  # noqa: F401
except ImportError:
    print("FEMU_DECODE FAIL: unicorn not importable under this interpreter.\n"
          "  INTERPRETER: miniconda python3 (e.g. /opt/miniconda3/bin/python3).\n"
          "  /usr/bin/python3 lacks unicorn - the documented matrix (femu.py).")
    sys.exit(5)

from femu import Rig, MAX_INSN_DEFAULT, SCRATCH_BASE  # noqa: E402
from pe_reader import PE  # noqa: E402

DEFAULT_BINARY = os.path.join(ROOT, "RE_output", "destiny2_unpacked_full.exe")
DEFAULT_DUMP = os.path.join(ROOT, "RE_output", "content",
                            "dump_healthy_inproc.dmp")
INPUT_VA = 0x600000300000          # project scratch convention (the acceptance)
OUT_VA = 0x600000310000
IN_REGION = 0x10000
OUT_REGION = 0x10000
PDATA_SCRIPT = os.path.join(HERE, "pdata_bounds.py")
DISASM_HANDOFF = ("RE_scripts/lane_svc43_disasm_range.py <va> <va+size> "
                  "(linear disassembly - do NOT invent a function boundary)")

# the synthetic XOR decoder (hand-assembled, ret at +26):
#   xor r9d,r9d; cmp r9,rdx; jae done; mov al,[rcx+r9]; xor al,0x20;
#   mov [r8+r9],al; inc r9; jmp loop; done: mov rax,r9; ret
XOR20_FN = (b"\x45\x31\xc9\x49\x39\xd1\x73\x0f\x42\x8a\x04\x09\x34\x20"
            b"\x43\x88\x04\x08\x49\xff\xc1\xeb\xec\x4c\x89\xc8\xc3")
#   mov rax,[rsp+0x28]; ret  (reads the 5th arg from the pushed frame)
STACK_ARG_FN = b"\x48\x8b\x44\x24\x28\xc3"


def gate_va(va, force=False):
    """THE pdata gate. Returns (ok, msg). GAP -> refuse with the
    linear-disassembler handoff (the 20.291 invented-stream class cannot
    happen). Non-function-start -> refuse unless --force (ANCHOR FIRST)."""
    out = subprocess.run(
        [sys.executable, PDATA_SCRIPT, hex(va)],
        capture_output=True, text=True, timeout=300).stdout
    if "OUTSIDE" in out or not out.strip():
        return False, ("GAP: 0x%X is outside every .pdata entry - REFUSED. "
                       "Use %s" % (va, DISASM_HANDOFF))
    m = re.search(r"entry (0x[0-9A-Fa-f]+)\.\.(0x[0-9A-Fa-f]+)"
                  r".*offset=(0x[0-9A-Fa-f]+)", out)
    if not m:
        return False, ("GAP: 0x%X has no .pdata entry - REFUSED. Use %s"
                       % (va, DISASM_HANDOFF))
    begin, end, off = (int(m.group(i), 16) for i in (1, 2, 3))
    if off != 0 and not force:
        return False, ("NOT-A-START: 0x%X is +0x%X inside 0x%X..0x%X - "
                       "REFUSED (ANCHOR FIRST; re-run with --force to "
                       "override, the report carries the offset)"
                       % (va, off, begin, end))
    return True, "entry 0x%X..0x%X offset=0x%X" % (begin, end, off)


def reader_init(rig, reader_va, buf_va, n, data):
    """The ent-cluster bit-reader preset (femu_ent_header_final.init_reader):
    a packed MSB-first bit stream behind a reader object."""
    window = struct.unpack(">Q", data[:8].ljust(8, b"\x00"))[0]
    rig.write(reader_va, b"\x00" * 0x100)
    for off, val, fmt in [(0x00, buf_va, "<Q"), (0x08, buf_va + n, "<Q"),
                          (0x10, n, "<I"), (0x24, 0, "<I"),
                          (0x28, window, "<Q"), (0x30, 0, "<I"),
                          (0x38, buf_va + 8, "<Q")]:
        rig.write(reader_va + off, struct.pack(fmt, val))


def parse_sig(sig, buf_va, n, out_va):
    """--sig tokens -> [rcx, rdx, r8, r9] + validation errors."""
    args = [0, 0, 0, 0]
    regidx = {"rcx": 0, "rdx": 1, "r8": 2, "r9": 3}
    errors = []
    for tok in (sig or "").split(","):
        tok = tok.strip()
        if not tok:
            continue
        if "=" not in tok:
            errors.append("bad --sig token %r (want reg=value)" % tok)
            continue
        reg, val = tok.split("=", 1)
        reg = reg.lower().strip()
        val = val.lower().strip()
        if reg not in regidx:
            errors.append("unknown register %r (rcx/rdx/r8/r9)" % reg)
            continue
        if val == "buf":
            args[regidx[reg]] = buf_va
        elif val == "len":
            args[regidx[reg]] = n
        elif val == "out":
            if out_va is None:
                errors.append("--sig uses 'out' but --out-len is not given")
            else:
                args[regidx[reg]] = out_va
        else:
            try:
                args[regidx[reg]] = int(val, 0)
            except ValueError:
                errors.append("bad --sig value %r" % val)
    return args, errors


def hexdump(data, base=0):
    lines = []
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16]
        hx = " ".join("%02x" % b for b in chunk)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append("  %08x  %-47s  |%s|" % (base + i, hx, asc))
    return lines


def emulate(rig, va, sig_args, stack_args, out_len, max_insn, wmem=None,
            reader_va=None, n=None, buf_va=None, input_data=None):
    """The shared run path (CLI + selftest). Returns (result, report_dict)."""
    if reader_va is not None:
        reader_init(rig, reader_va, buf_va, n, input_data)
    res = rig.call(va, sig_args, max_insn=max_insn, wmem=wmem,
                   stack_args=stack_args)
    out_bytes = None
    if out_len and res.reason == "returned":
        try:
            out_bytes = rig.read(OUT_VA, out_len)
        except Rig.FemuFault as exc:
            res.holes.append(OUT_VA)
            res.detail = (res.detail or "") + \
                " | output read fault: %s" % exc
    report = {
        "va": va,
        "reason": res.reason,
        "rax": res.rax,
        "detail": res.detail,
        "fault_addr": res.fault_addr,
        "rip": res.rip,
        "pages_pulled": res.pages_pulled,
        "holes": [hex(h) for h in res.holes],
        "rebase_reads": [hex(v) for v in res.rebase_reads[:16]],
        "rebase_reads_total": len(res.rebase_reads),
        "imports_called": res.imports_called,
        "out_len": out_len,
        "out_hex": out_bytes.hex() if out_bytes is not None else None,
    }
    return res, report


def classify(report):
    """0 = returned+clean, 2 = returned+UNTRUSTED(holes), 3 = not-returned."""
    if report["reason"] == "returned":
        return 2 if report["holes"] else 0
    return 3


def present(report, as_json=False):
    if as_json:
        return json.dumps(report, indent=2)
    lines = ["== femu_decode =="]
    lines.append("va         : 0x%X" % report["va"])
    lines.append("reason     : %s" % report["reason"])
    if report["detail"]:
        lines.append("detail     : %s" % report["detail"])
    lines.append("rax        : %s" % (hex(report["rax"])
                                      if report["rax"] is not None else None))
    if report["fault_addr"] and report["reason"].startswith("crash"):
        lines.append("fault      : 0x%X (rip 0x%X)"
                     % (report["fault_addr"], report["rip"] or 0))
    lines.append("provenance : pages_pulled=%d holes=%d rebase_reads=%d "
                 "imports=%s" % (report["pages_pulled"],
                                 len(report["holes"]),
                                 report["rebase_reads_total"],
                                 report["imports_called"] or "none"))
    if report["holes"]:
        lines.append("HOLES      : %s (pages absent from the dump)" %
                     ", ".join(report["holes"]))
    if report["rebase_reads_total"]:
        lines.append("REBASE-TAINTED reads: %s%s"
                     % (", ".join(report["rebase_reads"]),
                        " ..." if report["rebase_reads_total"] > 16 else ""))
    if report["out_hex"] is not None:
        raw = bytes.fromhex(report["out_hex"])
        lines.append("-- output buffer (%d bytes) --" % len(raw))
        lines += hexdump(raw, OUT_VA)
    return "\n".join(lines)


def main(argv):
    if "--selftest" in argv:
        return selftest()
    import argparse
    p = argparse.ArgumentParser(prog="femu_decode.py")
    p.add_argument("va")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--bytes", help="input as hex")
    src.add_argument("--infile", help="input as file")
    src.add_argument("--string")
    p.add_argument("--binary", default=DEFAULT_BINARY)
    p.add_argument("--dump", default=None)
    p.add_argument("--no-rebase", action="store_true")
    p.add_argument("--sig", default="rcx=buf,rdx=len")
    p.add_argument("--stack-args", default=None,
                   help="comma list of 5th+ args")
    p.add_argument("--out-len", type=lambda x: int(x, 0), default=None)
    p.add_argument("--max-insn", type=int, default=2_000_000)
    p.add_argument("--wmem", action="append", default=[],
                   help="VA=HEX pre-write (repeatable)")
    p.add_argument("--reader-init", type=lambda x: int(x, 0), default=None)
    p.add_argument("--json", action="store_true")
    p.add_argument("--force", action="store_true")
    a = p.parse_args(argv)

    try:
        va = int(a.va, 0)
    except ValueError:
        print("usage: <va> must be a number")
        return 5
    if a.bytes:
        try:
            data = bytes.fromhex(a.bytes.replace(" ", ""))
        except ValueError:
            print("usage: --bytes must be hex")
            return 5
    elif a.infile:
        with open(a.infile, "rb") as f:
            data = f.read()
    else:
        data = a.string.encode()

    ok, msg = gate_va(va, force=a.force)
    print("pdata gate  : %s" % msg)
    if not ok:
        return 1

    dump = a.dump
    rig = Rig(a.binary, dump_path=dump,
              rebase=bool(dump) and not a.no_rebase)
    for w in rig.warnings:
        print("WARN:", w)
    rig.map_region(INPUT_VA, IN_REGION)
    out_va = OUT_VA if a.out_len else None
    if a.out_len:
        rig.map_region(OUT_VA, OUT_REGION)
    rig.write(INPUT_VA, data + b"\x00" * (IN_REGION - len(data)))
    for spec in a.wmem:
        vah, _, hx = spec.partition("=")
        rig.write(int(vah, 0), bytes.fromhex(hx))

    sig_args, errs = parse_sig(a.sig, INPUT_VA, len(data), out_va)
    if errs:
        for e in errs:
            print("SIG ERROR:", e)
        return 5
    stack_args = ([int(x, 0) for x in a.stack_args.split(",")]
                  if a.stack_args else None)
    if a.out_len and "out" not in a.sig:
        print("SIG ERROR: --out-len given but --sig does not bind 'out'")
        return 5

    res, report = emulate(rig, va, sig_args, stack_args, a.out_len,
                          a.max_insn, reader_va=a.reader_init, n=len(data),
                          buf_va=INPUT_VA, input_data=data)
    print(present(report, as_json=a.json))
    rc = classify(report)
    if rc == 2:
        print("VERDICT: UNTRUSTED (holes - the dump did not capture the "
              "memory this answer touched)")
    elif rc == 3:
        print("VERDICT: NOT-RETURNED (reason above is the finding)")
    else:
        print("VERDICT: OK")
    return rc


# ----------------------------------------------------------------- selftest ---
def selftest():
    """Every FAIL arm of the brief that is synthesizable without the dump,
    plus the synthetic PASS oracles. Prints FEMU_DECODE SELFTEST: n/n PASS
    as the LAST line (liveness: silence = did not run)."""
    fails = []

    def check(name, cond, detail=""):
        print("%s %-52s %s" % ("PASS" if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    rig = Rig(DEFAULT_BINARY)
    s = SCRATCH_BASE + 0x80000

    # ---- T2-P1 (synthetic oracle): the XOR decoder, exact tier ----
    rig.map_region(s, 0x10000)
    rig.poke(s, XOR20_FN)
    inp = b"Hello World"
    rig.map_region(0x600000320000, 0x2000)   # input page + output page
    rig.write(0x600000320000, inp)
    res = rig.call(s, [0x600000320000, len(inp), 0x600000321000],
                   stack_args=None)
    got = rig.read(0x600000321000, len(inp))
    check("synthetic xor-0x20 decode, exact output",
          res.reason == "returned" and got == bytes(c ^ 0x20 for c in inp)
          and res.rax == len(inp),
          "reason=%s out=%r" % (res.reason, got))

    # ---- T2-P4: determinism (identical bytes AND flags on re-run) ----
    res2 = rig.call(s, [0x600000320000, len(inp), 0x600000321000])
    got2 = rig.read(0x600000321000, len(inp))
    check("determinism: re-run identical (bytes+reason+rax)",
          res2.reason == res.reason and res2.rax == res.rax and got2 == got,
          "reason=%s" % res2.reason)

    # ---- T2-F1: the pdata gap refuses (0x1404DD470, the documented leaf) --
    ok, msg = gate_va(0x1404DD470)
    check("T2-F1 gap VA refuses with handoff",
          (not ok) and "GAP" in msg and "lane_svc43_disasm_range" in msg,
          msg[:70])

    # ---- T2-F1b: non-function-start refuses (ANCHOR FIRST) ----
    ok2, msg2 = gate_va(0x1404DC0A0)   # +0x20 inside 0x1404DC080..0x1404DC126
    check("T2-F1b non-start VA refuses",
          (not ok2) and "NOT-A-START" in msg2, msg2[:70])
    ok3, msg3 = gate_va(0x1404DC0A0, force=True)
    check("T2-F1b --force overrides with the offset named",
          ok3 and "offset=0x20" in msg3, msg3[:70])

    # ---- T2-F3: import abort surfaces verbatim, rc=3 class ----
    slot = sorted(rig.imports_by_slot)[0]
    iname = rig.imports_by_slot[slot]
    code = b"\x48\xa1" + struct.pack("<Q", slot) + b"\xff\xd0\xc3"
    rig.poke(s + 0x1000, code)
    res3 = rig.call(s + 0x1000, [])
    rep3 = {"reason": res3.reason, "holes": [], "rax": res3.rax}
    check("T2-F3 import abort -> NOT-RETURNED rc-class",
          res3.reason == "import:" + iname and classify(rep3) == 3,
          res3.reason)

    # ---- T2-F4: a fault surfaces with diagnostics, never empty output ----
    rig.poke(s + 0x2000, b"\x48\xb8\x89\x67\x45\x23\x01\x00\x00\x00"
                         b"\x8b\x00\xc3")
    res4 = rig.call(s + 0x2000, [])
    check("T2-F4 unmapped read -> crash + addr (no silent result)",
          res4.reason == "crash:read-unmapped"
          and res4.fault_addr == 0x123456789,
          "reason=%s addr=%s" % (res4.reason, hex(res4.fault_addr or 0)))

    # ---- T2-F2: holes -> UNTRUSTED (classification unit) ----
    rep_hole = {"reason": "returned", "holes": ["0x1234000"], "rax": 5}
    check("T2-F2 returned+holes classifies UNTRUSTED (rc=2)",
          classify(rep_hole) == 2, "holes=%s" % rep_hole["holes"])
    rep_clean = {"reason": "returned", "holes": [], "rax": 5}
    check("T2-F2 returned+clean classifies OK (rc=0)",
          classify(rep_clean) == 0)

    # ---- T2-F5: rebase_reads surface in the report (provenance honesty) --
    rig.map_region(0x600000330000, 0x2000)
    res5, rep5 = emulate(rig, s, [0x600000320000, len(inp),
                                  0x600000321000], None, 16, 2_000_000)
    check("T2-F5 report carries provenance fields",
          all(k in rep5 for k in ("pages_pulled", "holes", "rebase_reads",
                                  "rebase_reads_total", "imports_called")),
          "keys present")

    # ---- stack_args engine arm: 5th arg readable from the frame ----
    rig.poke(s + 0x3000, STACK_ARG_FN)
    res6 = rig.call(s + 0x3000, [1, 2, 3, 4], stack_args=[0x1234])
    check("stack_args: 5th arg lands at [rsp+0x28]",
          res6.reason == "returned" and res6.rax == 0x1234,
          "reason=%s rax=%s" % (res6.reason, hex(res6.rax or 0)))

    # ---- reader-init preset: fields land where ent_header expects ----
    data = bytes.fromhex("01000000")
    rig.map_region(0x600000340000, 0x2000)
    rig.write(0x600000340000, data)
    reader_init(rig, 0x600000350000, 0x600000340000, len(data), data)
    r0 = struct.unpack("<Q", rig.read(0x600000350000, 8))[0]
    r10 = struct.unpack("<I", rig.read(0x600000350000 + 0x10, 4))[0]
    r28 = struct.unpack("<Q", rig.read(0x600000350000 + 0x28, 8))[0]
    window_expected = struct.unpack(">Q", data[:8].ljust(8, b"\x00"))[0]
    check("reader-init preset: buf/end/len/window fields",
          r0 == 0x600000340000 and r10 == len(data)
          and r28 == window_expected,
          "buf=%#x len=%d win=%#x want=%#x" % (r0, r10, r28,
                                               window_expected))

    print("FEMU_DECODE SELFTEST: %d/%d PASS" % (12 - len(fails), 12))
    return 0 if not fails else 4


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
