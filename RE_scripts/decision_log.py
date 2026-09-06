#!/usr/bin/env python3
# REGISTRY: caps: decision-log, action-pre-registration
"""decision_log.py - pre-register STATE-CHANGING actions before taking them
(enforcement-layer plan point 4; 08-30 A3: a server restart was invoked while
the user's clients were mid-launch - "launching" was read as "the reset has
not happened". One cheap state check would have shown the step complete; the
stronger form is that the action was registered with its hypothesis and its
expected outcome BEFORE it fired, and a later reader can compare).

Usage:
  decision_log.py register --action "restart server" \\
      --hypothesis "claims table is stale" \\
      --expected "port 8099 returns 0 claims after restart" [--note ...]
  decision_log.py complete <id> --result "0 claims, ports bound" [--note ...]
  decision_log.py show [N]          # last N entries (default 10)

Records append to RE_output/map/decisions.log as JSONL:
  {id, ts, action, hypothesis, expected, [result, result_ts]}

The register step is the gate-side discipline (ARH1 mechanical): an action
with no registered expectation cannot be judged afterwards. The complete
step closes the loop - and `show` makes an unfinished decision VISIBLE,
which is the part that catches the A3 class (act without checking state).

Exit: 0 ok; 2 usage.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = Path(os.environ.get("RE_DECISION_LOG",
                          str(ROOT / "RE_output/map/decisions.log")))


def load():
    if not LOG.exists():
        return []
    out = []
    for line in LOG.read_text(encoding="utf8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"warn: unparseable decision-log line skipped", file=sys.stderr)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="decision pre-registration (see docstring)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    reg = sub.add_parser("register")
    reg.add_argument("--action", required=True)
    reg.add_argument("--hypothesis", required=True)
    reg.add_argument("--expected", required=True)
    reg.add_argument("--note", default="")
    comp = sub.add_parser("complete")
    comp.add_argument("id")
    comp.add_argument("--result", required=True)
    comp.add_argument("--note", default="")
    sub.add_parser("show").add_argument("n", nargs="?", type=int, default=10)
    args = ap.parse_args(argv)

    recs = load()
    if args.cmd == "register":
        did = "D-%03d" % (len(recs) + 1)
        rec = {"id": did,
               "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "action": args.action,
               "hypothesis": args.hypothesis,
               "expected": args.expected}
        if args.note:
            rec["note"] = args.note
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf8") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(f"registered {did}: {args.action}")
        print(f"  hypothesis: {args.hypothesis}")
        print(f"  expected:   {args.expected}")
        print(f"  (close it with: decision_log.py complete {did} --result ...)")
        return 0
    if args.cmd == "complete":
        target = [r for r in recs if r.get("id") == args.id]
        if not target:
            print(f"ERROR: no decision {args.id} (see 'show')", file=sys.stderr)
            return 2
        if target[-1].get("result"):
            print(f"NOTE: {args.id} already completed "
                  f"({target[-1]['result'][:60]}); appending the new result.")
        rec = dict(target[-1])
        rec["result"] = args.result
        rec["result_ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if args.note:
            rec["result_note"] = args.note
        with LOG.open("a", encoding="utf8") as fh:
            fh.write(json.dumps(rec) + "\n")
        matched = "MATCHED the expectation" if args.result.lower() == \
            str(rec.get("expected", "")).lower() else "recorded"
        print(f"completed {args.id}: {args.result[:100]} ({matched})")
        return 0
    # show
    last = {}
    for r in recs:
        last[r["id"]] = r  # later records supersede (completion appended)
    items = list(last.values())[-args.n:]
    if not items:
        print(f"no decisions logged yet ({LOG})")
        return 0
    for r in items:
        state = "OPEN" if not r.get("result") else f"done -> {r['result'][:60]}"
        print(f"  {r['id']} {r['ts'][:16]} {r['action'][:50]:<50} [{state}]")
        print(f"      expected: {r.get('expected', '')[:100]}")
    open_n = sum(1 for r in last.values() if not r.get("result"))
    print(f"  ({len(items)} shown, {open_n} OPEN - an open decision on a "
          "state-changing action means it fired without a recorded expectation "
          "or was never closed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
