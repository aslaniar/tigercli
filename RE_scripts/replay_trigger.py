#!/usr/bin/env python3
# REGISTRY: caps: trigger-replay, fixture-replay
"""replay_trigger.py - replay a probe's TRIGGER over a recorded log BEFORE
deploying it (TOOLING_AUDIT M1; the rule three postmortems converge on).

A probe's trigger is executable logic over a known input format; a recorded
run is a fixture. Shipping an instrument change to a boot without replaying
it against a previous boot's output is spending the user's launch to run a
unit test (POSTMORTEM_2026-09-01 INSTRUMENTATION addendum; 09-05 FAILURE 3:
the one of four rebuild changes NOT replayed shipped an unreachable
threshold, and p2-175's own log already contained the lines that falsified
it).

Usage:
  replay_trigger.py <log-or-dir> --pred <pred.py> [--window N]
                    [--sample K] [--quiet]

  <log-or-dir> : a .log file, or a directory (every *.log in it, archived
                 manifests skipped). Bare `grep` is NOT used; lines are read
                 with Python (binary-safe, no shell tool in the path).
  --pred       : a Python fixture module defining either:
                   class Trigger:            # stateful (recommended)
                       def feed(self, ctx):  # called once per line, in order
                           return emit_or_None   # str = fires with this note
                   or def check(ctx): -> bool|str   # stateless predicate
                 ctx = {"t": int|None, "line": str, "kv": dict, "raw": str}
                 where kv is the `k=v` fields of the line (client/server log
                 convention: space-separated key=value tokens; t= parsed when
                 present). The fixture is USER code - it may keep state.
  --window N   : sanity cap: abort a run that emits more than N times
                 (default 100000; a runaway predicate is a fixture bug).
  --sample K   : print first K and last 2 emit lines (default 5).
  --quiet      : suppress the emit samples; keep the summary.

Output: fire count, first/last fire timestamps, top emit notes, samples.
Exit: 0 = trigger fired >=1 time on this fixture; 1 = ZERO fires (U13: a
trigger that never fires on recorded data is a boot-killer - do not ship
it; first suspect is the trigger's own placement, per the p2-160 lesson);
2 = usage/fixture error.

Worked example (the 09-05 FAILURE 3 fixture, in RE_output/map/fixtures/):
the re-arm was gated on 8 acknowledged bodies after a withdrawal; the
recorded logs show ONE ack per withdrawal - replay proves the threshold
unreachable before any launch is spent.
"""
import argparse
import importlib.util
import re
import sys
from collections import Counter
from pathlib import Path

KV_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_.-]*)=([^\s]+)")
T_RE = re.compile(r"\bt=(\d+)")


def parse_ctx(raw):
    kv = {m.group(1): m.group(2) for m in KV_RE.finditer(raw)}
    t = None
    tm = T_RE.search(raw)
    if tm:
        try:
            t = int(tm.group(1))
        except ValueError:
            pass
    return {"t": t, "line": raw.rstrip("\n"), "kv": kv, "raw": raw}


def load_pred(path):
    spec = importlib.util.spec_from_file_location("replay_pred", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # a fixture that cannot import is a fixture bug
        print(f"FIXTURE ERROR: {path}: {e}", file=sys.stderr)
        return None
    return mod


def logs_from_target(target):
    p = Path(target)
    if p.is_file():
        return [p]
    if p.is_dir():
        return sorted(f for f in p.glob("*.log"))
    return []


def main(argv=None):
    ap = argparse.ArgumentParser(description="trigger-replay harness (see docstring)")
    ap.add_argument("target", help="log file or directory of *.log archives")
    ap.add_argument("--pred", required=True, help="fixture module: class Trigger or def check(ctx)")
    ap.add_argument("--window", type=int, default=100000, help="max fires before aborting (runaway guard)")
    ap.add_argument("--sample", type=int, default=5, help="emit samples to print")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    logs = logs_from_target(args.target)
    if not logs:
        print(f"no logs at {args.target}", file=sys.stderr)
        return 2
    mod = load_pred(args.pred)
    if mod is None:
        return 2
    if hasattr(mod, "Trigger"):
        state, stateless = mod.Trigger(), None
    elif hasattr(mod, "check"):
        state, stateless = None, mod.check
    else:
        print("FIXTURE ERROR: module defines neither class Trigger nor check(ctx)", file=sys.stderr)
        return 2

    fires, notes, first_t, last_t, lines_seen = [], Counter(), None, None, 0
    for lf in logs:
        with lf.open("rb") as fh:
            for raw in fh:
                lines_seen += 1
                try:
                    line = raw.decode("utf8", errors="replace")
                except Exception:
                    continue
                ctx = parse_ctx(line)
                try:
                    emit = state.feed(ctx) if state is not None else stateless(ctx)
                except Exception as e:
                    print(f"FIXTURE ERROR at {lf.name} line {lines_seen}: {e}", file=sys.stderr)
                    return 2
                if emit:
                    if emit is True:
                        emit = "fired"
                    fires.append((lf.name, ctx["t"], str(emit)))
                    notes[str(emit)] += 1
                    first_t = ctx["t"] if first_t is None else first_t
                    last_t = ctx["t"]
                    if len(fires) > args.window:
                        print(f"ABORT: runaway trigger - {len(fires)} fires exceeds "
                              f"--window {args.window} (a fixture bug, not a result)",
                              file=sys.stderr)
                        return 2

    print(f"REPLAY over {len(logs)} log(s), {lines_seen} lines, pred {args.pred}")
    print(f"  fires: {len(fires)}"
          + (f"  | first t={first_t}  last t={last_t}" if fires else ""))
    for note, n in notes.most_common(8):
        print(f"    {n:>8}x  {note[:120]}")
    if fires and not args.quiet:
        k = min(args.sample, len(fires))
        for name, t, note in fires[:k]:
            print(f"    sample {name} t={t}: {note[:160]}")
        if len(fires) > k:
            for name, t, note in fires[-2:]:
                print(f"    last    {name} t={t}: {note[:160]}")
    if not fires:
        print("REPLAY RESULT: ZERO fires - the trigger never fires on this recorded "
              "data. Do NOT ship it: the trigger is unreachable by construction "
              "until proven otherwise (p2-160 / 09-05 FAILURE 3).")
        return 1
    print("REPLAY RESULT: trigger fires on recorded data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
