#!/usr/bin/env python3
# REGISTRY: caps: outcome-ledger
"""boot_outcome.py - record one boot outcome to the outcome ledger
(RE_output/map/boot_outcomes.jsonl). The recording half of empty-mask
mechanism #6 (POSTMORTEM_2026-08-31: repeated third-branch outcomes were
processed as "on to the next lead" instead of "the causal model is wrong").

CONSUMER: gate_boot.py reads a front's trailing third-branch streak and
refuses the next boot at 2 unless the brief carries a MODEL REVIEW: section.

Usage:
  boot_outcome.py --boot <boot-id> --front <front-name> --class <class>
                  [--note "..."] [--force]
  boot_outcome.py --show [FRONT-SUBSTRING]

Classes (exact):
  hypothesis-survived  the pre-named effect appeared as claimed
  hypothesis-wrong     the pre-named effect did not appear
  third-branch         BEHAVIOUR CHANGED, OUTCOME DIDN'T - the dangerous one;
                       two in a row on one front force a model review

Idempotence: a duplicate boot_id is refused unless --force (a
reclassification should be an explicit act, not a fat-fingered re-run).

Ledger path override: env BOOT_OUTCOMES_LEDGER (used by the gate's self-test).
Exit: 0 recorded/shown; 1 refused; 2 usage.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLASSES = ("hypothesis-survived", "hypothesis-wrong", "third-branch")


def ledger_path():
    return Path(os.environ.get("BOOT_OUTCOMES_LEDGER", str(ROOT / "RE_output/map/boot_outcomes.jsonl")))


def load(path):
    if not path.exists():
        return []
    out = []
    for i, line in enumerate(path.read_text(encoding="utf8", errors="replace").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            print(f"warn: unparseable ledger line {i} skipped", file=sys.stderr)
            continue
        if isinstance(r, dict):
            r["_line"] = i
            out.append(r)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="outcome-ledger recorder (see docstring)")
    ap.add_argument("--boot", help="boot id, e.g. p2-177")
    ap.add_argument("--front", help="front name; MUST match the brief's FRONT: line (gate filters on it)")
    ap.add_argument("--class", dest="oclass", choices=CLASSES, help="outcome class")
    ap.add_argument("--note", default="", help="one-line context (optional)")
    ap.add_argument("--force", action="store_true", help="allow overwriting an existing boot_id's record by appending a corrected one")
    ap.add_argument("--close", action="store_true",
                    help="this record CLOSES the front (P5, wrong-question PM): "
                         "--verdict required and it must restate the brief's "
                         "PURPOSE terms - a front is closed by answering ITS "
                         "question, not a sub-question")
    ap.add_argument("--verdict", default="", help="the closing verdict (required with --close)")
    ap.add_argument("--brief", default="", help="the boot brief's path (required with --close: the verdict must share a PURPOSE term)")
    ap.add_argument("--show", nargs="?", const="", metavar="FRONT", help="print ledger records (optionally filtered by front substring)")
    args = ap.parse_args(argv)

    path = ledger_path()
    if args.show is not None and args.boot is None and args.front is None and args.oclass is None:
        recs = load(path)
        if not path.exists():
            print(f"ledger absent: {path}")
            return 0
        sel = [r for r in recs if args.show.lower() in str(r.get("front", "")).lower()] \
            if args.show else recs
        for r in sel:
            print(f"  {r.get('date', '?')}  boot={r.get('boot_id', '?')}  "
                  f"front={r.get('front', '?')}  class={r.get('outcome_class', '?')}"
                  + (f"  note={r['note']}" if r.get("note") else ""))
        streak = 0
        for r in reversed(sel):
            if r.get("outcome_class") == "third-branch":
                streak += 1
            else:
                break
        print(f"  ({len(sel)} record(s); trailing third-branch streak: {streak})")
        return 0

    missing = [a for a, v in (("--boot", args.boot), ("--front", args.front),
                               ("--class", args.oclass)) if not v]
    if missing:
        ap.error("missing required args: " + ", ".join(missing))

    # --- P5 (wrong-question PM): a front is closed by answering ITS question
    if args.close:
        if not (args.verdict and args.brief):
            ap.error("--close requires --verdict and --brief")
        bp = Path(args.brief)
        if not bp.exists():
            ap.error(f"--brief not found: {args.brief}")
        from gate_boot import section_text
        purpose = section_text(bp.read_text(encoding="utf8", errors="replace"),
                               "PURPOSE")
        stop = ("this", "that", "with", "from", "what", "which", "boot",
                "does", "test", "explicitly", "learn", "wins", "lose",
                "about", "their", "there", "every", "state", "client",
                "server", "brief", "under", "again", "still", "must",
                "each", "when", "where", "name", "names", "probe",
                "instrument", "boot")
        terms = {w for w in re.findall(r"[a-zA-Z_]\w{4,}", purpose.lower())
                 if w not in stop and not w.startswith("p2-")}
        verdict_terms = {w for w in re.findall(r"[a-zA-Z_]\w{4,}",
                                               args.verdict.lower())}
        if not terms & verdict_terms:
            print(f"REFUSED (P5): the closing verdict does not restate the "
                  f"brief's PURPOSE question. PURPOSE terms: "
                  f"{sorted(terms)[:12]}. The wrong-question postmortem: a "
                  "front is closed by answering ITS question, not a "
                  "sub-question - restate the question in the verdict.")
            return 1

    path.parent.mkdir(parents=True, exist_ok=True)
    recs = load(path)
    dup = [r for r in recs if r.get("boot_id") == args.boot]
    if dup and not args.force:
        print(f"REFUSED: boot_id {args.boot} already recorded "
              f"({dup[0].get('outcome_class')} on '{dup[0].get('front')}'). "
              "Use --force to append a corrected record.")
        return 1
    rec = {
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "boot_id": args.boot,
        "front": args.front,
        "outcome_class": args.oclass,
    }
    if args.note:
        rec["note"] = args.note
    with path.open("a", encoding="utf8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")
    front_recs = [r for r in recs + [rec]
                  if args.front.lower() in str(r.get("front", "")).lower()
                  or str(r.get("front", "")).lower() in args.front.lower()]
    streak = 0
    for r in reversed(front_recs):
        if r.get("outcome_class") == "third-branch":
            streak += 1
        else:
            break
    print(f"recorded: {args.boot} | front '{args.front}' | {args.oclass}")
    print(f"front trailing third-branch streak now: {streak}"
          + ("  <- gate will REFUSE the next boot on this front without a MODEL REVIEW section"
             if streak >= 2 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
