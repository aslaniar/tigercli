#!/usr/bin/env python3
"""night_pull.py - pull N items from the map queue and emit a night-lane brief.

The night runner needs no scheduling infra: last thing before bed, run
`night_pull.py --n 10` in the working checkout, spawn one background lane
with the printed brief path, harvest in the morning. The brief follows the
lane-brief-template shape (evidence anchors, falsifiable question per item,
DEATH SAFETY pointer, output contract) and the queue records the claim.

Usage:
  /usr/bin/python3 RE_scripts/night_pull.py [--n 10] [--queue PATH]
      [--claimant SESSION-OR-NAME]

Morning: mark items done via --done ID1,ID2 (with a one-line verdict each
in the brief's FINAL section; the lane's claims doc carries the substance).

Exit: 0 brief written, 2 usage/queue-empty.
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_QUEUE = os.path.join(ROOT, "RE_output", "map", "queue.json")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--queue", default=DEFAULT_QUEUE)
    ap.add_argument("--claimant", default="night-lane")
    ap.add_argument("--done", default=None,
                    help="comma-separated item addrs to mark done")
    args = ap.parse_args(argv)

    with open(args.queue) as fh:
        queue = json.load(fh)
    if args.done:
        done = {a.strip() for a in args.done.split(",")}
        n = 0
        for item in queue["items"]:
            if item["addr"] in done and item.get("status") == "claimed":
                item["status"] = "done"
                n += 1
            elif item["addr"] in done:
                item["status"] = "done"
                n += 1
        with open(args.queue, "w") as fh:
            json.dump(queue, fh, indent=1)
        print("marked %d item(s) done" % n)
        return 0

    pulled = []
    for item in queue["items"]:
        if item.get("status") in (None, "open"):
            item["status"] = "claimed"
            item["claimant"] = args.claimant
            item["claimed_at"] = time.strftime("%Y-%m-%d %H:%M")
            pulled.append(item)
            if len(pulled) >= args.n:
                break
    if not pulled:
        print("queue empty (all items claimed/done) - seed more or raise --n")
        return 2
    with open(args.queue, "w") as fh:
        json.dump(queue, fh, indent=1)

    ts = time.strftime("%Y%m%d_%H%M")
    brief = os.path.join(os.path.dirname(args.queue),
                         "night_brief_%s.md" % ts)
    lines = [
        "# NIGHT LANE BRIEF (%s, claimant=%s)" % (ts, args.claimant),
        "",
        "FALSIFIABLE QUESTION (per item): what is this function's purpose,",
        "with evidence. Every verdict MUST carry a status mark",
        "(verified-by-execution / verified-by-reading / inferred).",
        "INFERRED names are quarantined: write them as suggestions, never",
        "as established names (a wrong name poisons the map - worse than",
        "no name).",
        "",
        "METHOD per item:",
        "  1. funcq the address (citations, strings, neighbors).",
        "  2. Read the function (disasm_fn.py / Ghidra decompile).",
        "  3. If pure-compute and ambiguous: femu.py --call it with sample",
        "     inputs (verified-by-execution).",
        "  4. Write one claims block per item: addr / claim / evidence /",
        "     confidence. Update the queue status via --done on completion.",
        "",
        "DEATH SAFETY: per-phase claims written as they land (raw first,",
        "claim right after). Near-limit = stop-and-write. 3-line",
        "report-back. Full shape: RE_output/claims/lane-brief-template.md",
        "",
        "## ITEMS (%d)" % len(pulled),
    ]
    for item in pulled:
        lines.append("- %s (size %d, prio %d): %s" %
                     (item["addr"], item["size"], item["prio"], item["why"]))
    lines += ["", "## FINAL", "(one paragraph: how many resolved, how many",
              "remain open, the single most useful discovery)"]
    with open(brief, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("brief: %s (%d items)" % (brief, len(pulled)))
    print("LIVENESS: pulled=%d remaining_open=%d" %
          (len(pulled), sum(1 for i in queue["items"]
                            if i.get("status") in (None, "open"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
