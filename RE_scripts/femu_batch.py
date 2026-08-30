#!/usr/bin/env python3
"""femu_batch.py - batch purity/behavior classification over the binary's
functions using the femu rig (2026-08-29, night-runner T1/T3 support).

For each selected function: call it with a canned arg preset and classify
the outcome. Every verdict is from a fixed enum so downstream code can
trust the shape:

  returned        - completed; rax recorded (emulatable, pure)
  import:<name>   - touched an import (reason IS the classification)
  crash:read/write-unmapped - depends on memory it expects initialized;
                    fault_class further splits image-global / stack / wild
  crash:fetch-*   - jumped into non-code (bad indirect target)
  timeout         - looping/complex beyond the cap

DIRTY-STATE RULE: a function that WRITES image memory (.data) would pollute
every later classification in the same Rig. The batch hooks image writes and
restores the original file bytes after every call - each function is
classified against the pristine image, and the dirty count is reported
(heavy writers are their own interesting class).

Usage:
  python3 RE_scripts/femu_batch.py --sample N [--min-size S] [--max-size S]
      [--range LO HI] [--args-mode zeros|small] [--out PREFIX]
      [--binary PATH] [--selftest]

Interpreter: miniconda python3 (unicorn). Read-only on the binary.
Exit: 0 ok, 1 failure, 2 usage.
"""
import argparse
import csv
import json
import os
import random
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femu
from unicorn import UC_HOOK_MEM_WRITE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SPINE = os.path.join(ROOT, "RE_output", "export", "functions.csv")
DEFAULT_OUTDIR = os.path.join(ROOT, "RE_output", "logindex")
ARG_PRESETS = {"zeros": [0, 0, 0, 0], "small": [1, 2, 3, 4]}


class DirtyGuard(object):
    """Track image-memory writes during a call; restore pristine FILE bytes
    after. NOTE: unicorn's UC_HOOK_MEM_WRITE fires post-write, so the
    in-memory byte is already modified when the hook sees it - the pristine
    source is the file itself, which is also exactly the state we want to
    restore (the mapped image was loaded from it)."""

    def __init__(self, rig):
        self.rig = rig
        self.dirty = set()
        self.base = rig.pe.imagebase
        self.end = rig.pe.imagebase + rig.size_of_image
        self.hook = None
        self.restored = 0

    def __enter__(self):
        self.hook = self.rig.uc.hook_add(UC_HOOK_MEM_WRITE, self._on_write)
        return self

    def __exit__(self, *a):
        for va in sorted(self.dirty):
            orig = self.rig.pe.read(va, 1)
            if orig:
                self.rig.uc.mem_write(va, orig)
                self.restored += 1
        self.rig.uc.hook_del(self.hook)
        return False

    def _on_write(self, uc, access, address, size, value, user_data):
        if self.base <= address < self.end:
            for i in range(size):
                self.dirty.add(address + i)


def load_spine(path, min_size=None, max_size=None, rng=None, sample=None,
               addr_range=None):
    rows = []
    with open(path) as f:
        for r in csv.reader(f):
            if len(r) < 3:
                continue
            try:
                addr, size = int(r[0], 16), int(r[1])
            except ValueError:
                continue
            if min_size is not None and size < min_size:
                continue
            if max_size is not None and size > max_size:
                continue
            if addr_range and not (addr_range[0] <= addr <= addr_range[1]):
                continue
            rows.append((addr, size, r[2]))
    if sample is not None and rng and len(rows) > sample:
        rows = rng.sample(rows, sample)
    return rows


def classify(rig, addr, arg_mode="zeros", max_insn=50000):
    """Returns (verdict_dict, dirty_count). Verdicts from a fixed enum."""
    out = {"addr": "0x%x" % addr, "calls": []}
    worst = "returned"
    with DirtyGuard(rig) as guard:
        preset = ARG_PRESETS.get(arg_mode, ARG_PRESETS["zeros"])
        res = rig.call(addr, preset, max_insn=max_insn)
        reason = res.reason
        call_rec = {"args": preset, "reason": reason, "rax": res.rax}
        if res.fault_addr:
            call_rec["fault"] = "0x%x" % res.fault_addr
        if res.imports_called:
            call_rec["imports"] = res.imports_called[:3]
        out["calls"].append(call_rec)
        if reason.startswith("import:"):
            worst = reason
        elif reason.startswith("crash"):
            worst = reason
            if res.fault_addr:
                fb = rig.pe.imagebase
                fe = rig.pe.imagebase + rig.size_of_image
                sb = femu.STACK_BASE
                se = femu.STACK_BASE + femu.STACK_SIZE
                if fb <= res.fault_addr < fe:
                    out["fault_class"] = "image-global"
                elif sb <= res.fault_addr < se:
                    out["fault_class"] = "stack"
                else:
                    out["fault_class"] = "wild"
        elif reason == "timeout":
            worst = "timeout"
    out["verdict"] = worst
    out["dirty_image_bytes"] = len(guard.dirty)
    return out, len(guard.dirty)


def selftest(binary_path):
    fails = []

    def check(name, cond, detail=""):
        print("%s %-52s %s" % ("PASS" if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    rig = femu.Rig(binary_path)
    print("== A. verdict enum on known functions ==")
    out, dirty = classify(rig, femu.REASON_NAME_FN)
    check("pure known function -> returned", out["verdict"] == "returned" and
          dirty == 0, "verdict=%s dirty=%d" % (out["verdict"], dirty))
    slot = sorted(rig.imports_by_slot)[0]
    scratch = femu.SCRATCH_BASE
    rig.uc.mem_write(scratch, b"\x48\xa1" +
                     struct.pack("<Q", slot) + b"\xff\xd0\xc3")
    out, dirty = classify(rig, scratch)
    check("import-calling code -> import:<name> verdict",
          out["verdict"].startswith("import:"), out["verdict"])

    print("== B. dirty-restore guard ==")
    # NOTE: unicorn hooks fire for EMULATED accesses only - uc.mem_write()
    # bypasses hooks, so the test must emulate a real store instruction.
    data_sec = [s for s in rig.pe.sections if s[0] == ".data"][0]
    dva = rig.pe.imagebase + data_sec[1] + 0x40
    orig = rig.uc.mem_read(dva, 1)[0]
    store = b"\x48\xb8" + struct.pack("<Q", dva) + b"\xc6\x00\x7e\xc3"
    rig.uc.mem_write(femu.SCRATCH_BASE + 0x400, store)
    with DirtyGuard(rig) as guard:
        res = rig.call(femu.SCRATCH_BASE + 0x400, [])
        check("emulated store dirtied the byte", rig.uc.mem_read(dva, 1)[0] ==
              0x7e and len(guard.dirty) == 1,
              "read=%02x dirty=%d" % (rig.uc.mem_read(dva, 1)[0],
                                      len(guard.dirty)))
    check("guard restored pristine FILE byte", rig.uc.mem_read(dva, 1)[0] ==
          orig, "orig=%02x now=%02x" % (orig, rig.uc.mem_read(dva, 1)[0]))

    print("== C. determinism ==")
    o1, _ = classify(rig, femu.REASON_NAME_FN)
    o2, _ = classify(rig, femu.REASON_NAME_FN)
    check("same function -> same verdict twice", o1["verdict"] == o2["verdict"]
          and o1["calls"][0]["rax"] == o2["calls"][0]["rax"])

    print("== D. spine loader ==")
    rows = load_spine(DEFAULT_SPINE, sample=5, rng=random.Random(1))
    check("spine sample returns 5 rows", len(rows) == 5, str(len(rows)))

    print("FEMU-BATCH SELFTEST %s" % ("PASS" if not fails else "FAIL: %s" % fails))
    return 0 if not fails else 1


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sample", type=int, default=100)
    ap.add_argument("--min-size", type=int, default=None)
    ap.add_argument("--max-size", type=int, default=None)
    ap.add_argument("--range", nargs=2, type=lambda s: int(s, 0), default=None)
    ap.add_argument("--args-mode", choices=list(ARG_PRESETS), default="zeros")
    ap.add_argument("--max-insn", type=int, default=50000)
    ap.add_argument("--seed", type=int, default=20260829)
    ap.add_argument("--spine", default=DEFAULT_SPINE,
                    help="functions.csv spine (worktrees: pass main's path)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--binary", default=femu.DEFAULT_BINARY)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        if not os.path.exists(args.binary):
            print("ERROR: binary missing: %s" % args.binary)
            return 2
        return selftest(args.binary)

    rng = random.Random(args.seed)
    rows = load_spine(DEFAULT_SPINE, args.min_size, args.max_size, rng,
                      args.sample, args.range)
    if not rows:
        print("ERROR: no functions selected (check --min/--max-size/--range)")
        return 2
    rig = femu.Rig(args.binary)
    t0 = time.time()
    results = []
    tally = {}
    for i, (addr, size, auto) in enumerate(rows):
        out, dirty = classify(rig, addr, args.args_mode, args.max_insn)
        out["size"] = size
        results.append(out)
        key = out["verdict"].split("!")[0]
        tally[key] = tally.get(key, 0) + 1
        if (i + 1) % 25 == 0:
            print("progress: %d/%d (%.1fs)" % (i + 1, len(rows),
                                               time.time() - t0))
    outdir = DEFAULT_OUTDIR
    os.makedirs(outdir, exist_ok=True)
    prefix = args.out or os.path.join(
        outdir, "femu_batch_%s" % time.strftime("%Y%m%d_%H%M%S"))
    with open(prefix + "_batch.json", "w") as fh:
        json.dump({"seed": args.seed, "args_mode": args.args_mode,
                   "max_insn": args.max_insn, "results": results},
                  fh, indent=1)
    print("LIVENESS: classified=%d elapsed=%.1fs report=%s_batch.json" %
          (len(results), time.time() - t0, prefix))
    for k in sorted(tally, key=lambda k: -tally[k]):
        print("  %-34s %d" % (k, tally[k]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
