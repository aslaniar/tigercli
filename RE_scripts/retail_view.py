# -*- coding: utf-8 -*-
"""retail_view.py — the retail-only triage window (Bungie's own diagnostic stream).

Filters ONE client log down to its ev=retail lines and renders text= alone
(ev=retail site=N text=<human-readable narration>; the 2026-08-22 boot carried
914 such lines: networking:session/online/stun/logic/managed_session/bap/
simulation/composition/activity_client/platform_friends).

The stream is written at core.logging.levels.client=info, so a boot at client=warn
(the lane-cockpit default) produces NO retail lines: replay the archive or flip the
channel back to info for the boot that needs retail. See
RE_output/claims/lane_cockpit.md for the level trade-off.

Usage:  python -X utf8 RE_scripts/retail_view.py [--log LOG] [--tail] [--lines N]
Reads the repo's client log by default; --lines N = replay the last N retail lines
of a finished log; --tail = follow the live file (the game rotates it each boot,
so start --tail AFTER the game launches).
Quit:   Ctrl+C
"""
import argparse
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLIENT_LOG = str(REPO_ROOT / "Game" / "bin" / "x64" / "Sunrise" / "logs" / "sunrise.log")

R, G, Y, B, M, C, W, D = "\x1b[31m", "\x1b[32m", "\x1b[33m", "\x1b[34m", \
    "\x1b[35m", "\x1b[36m", "\x1b[37m", "\x1b[90m"
X, BOLD = "\x1b[0m", "\x1b[1m"


def parse(path, tail=False, lines=None):
    """Yield (t, text) for every ev=retail line, newest-first for the archive. """
    if tail:
        pos = os.path.getsize(path) if os.path.exists(path) else 0
        while True:
            size = os.path.getsize(path) if os.path.exists(path) else 0
            if size < pos:
                pos = 0
            if size > pos:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(pos)
                    for line in f:
                        line = line.rstrip("\n")
                        if " ev=retail " not in line:
                            continue
                        m = _match(line)
                        if m:
                            yield m
                    pos = f.tell()
            time.sleep(0.25)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        hits = []
        for line in f:
            if " ev=retail " in line:
                m = _match(line)
                if m:
                    hits.append(m)
        if lines:
            hits = hits[-lines:]
        for m in reversed(hits):
            yield m


def _match(line):
    # client level=info t=15180 ev=retail site=5 text=networking:stun: ...
    if " ev=retail " not in line:
        return None
    head, tail = line.split(" ev=retail ", 1)
    t = head.rsplit(" t=", 1)[1].split(" ", 1)[0] if " t=" in head else "?"
    site = tail.split("site=", 1)[1].split(" ", 1)[0] if "site=" in tail else "?"
    text = tail.split("text=", 1)[1] if "text=" in tail else tail
    return (t, site, text.rstrip("\r"))


def main():
    ap = argparse.ArgumentParser(description="the retail-only triage window")
    ap.add_argument("--log", default=CLIENT_LOG)
    ap.add_argument("--tail", action="store_true", help="follow the live log")
    ap.add_argument("--lines", type=int, default=None,
                    help="archive replay: only the last N retail lines")
    args = ap.parse_args()
    try:
        for t, site, text in parse(args.log, tail=args.tail, lines=args.lines):
            sys.stdout.write("%s[t=%s site=%s]%s %s\n" % (D, t, site, X, text))
            sys.stdout.flush()
    except KeyboardInterrupt:
        sys.stdout.write("retail view stopped.\n")


if __name__ == "__main__":
    main()