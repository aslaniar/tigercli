#!/usr/bin/env python3
"""logq.py - query a logindex.py database (2026-08-27). The replacement for
per-question grep+sed chains: one command, full-width output, every hit cited
as source file:line (claim-ready per the evidence rules).

Usage:
  /usr/bin/python3 RE_scripts/logq.py <index.db> [--ev E] [--stage S]
      [--grep P] [--source SRC] [--tail N] [--range T1 T2] [--aligned]

  --aligned  applies clock offsets from a sibling .drift.json (merge_timeline
             output with the same basename) so t-ranges and --tail order are
             comparable ACROSS machines; without it, t is native per source.

Exit codes: 0 = hits printed, 1 = no hits (and the query RAN - liveness is the
exit path, not silence), 2 = usage error. Full lines are never truncated.
"""
import json
import os
import sqlite3
import sys


def main(argv):
    if not argv or argv[0].startswith("--"):
        print(__doc__)
        return 2
    db = argv[0]
    if not os.path.exists(db):
        print("ERROR: no index at %s (build with logindex.py)" % db)
        return 2
    opts = {"--ev": None, "--stage": None, "--grep": None, "--source": None,
            "--tail": None, "--range": None, "--aligned": False}
    it = iter(argv[1:])
    for a in it:
        if a == "--aligned":
            opts["--aligned"] = True
        elif a in opts:
            opts[a] = next(it, None)
    offsets = {}
    if opts["--aligned"]:
        dpath = os.path.splitext(db)[0] + ".drift.json"
        if os.path.exists(dpath):
            with open(dpath) as fh:
                dj = json.load(fh)
            for s in dj["sources"]:
                if s.get("offset_ms") is not None:
                    offsets[s["source"]] = s["offset_ms"]
        else:
            print("WARN: --aligned requested but no %s" % dpath)
    q = "SELECT source, file, line, t_ms, ev, stage, kv, raw FROM events WHERE 1=1"
    params = []
    if opts["--ev"]:
        q += " AND ev=?"; params.append(opts["--ev"])
    if opts["--stage"]:
        q += " AND stage=?"; params.append(opts["--stage"])
    if opts["--source"]:
        q += " AND source=?"; params.append(opts["--source"])
    if opts["--grep"]:
        q += " AND raw LIKE ?"; params.append("%" + opts["--grep"] + "%")
    if opts["--range"]:
        lo, hi = opts["--range"].split(",") if "," in opts["--range"] \
            else (opts["--range"], None)
        if opts["--aligned"] and offsets:
            # per-source unified time: t_unified = t_ms - offset[source]
            con0 = sqlite3.connect(db)
            srcs = [r[0] for r in con0.execute("SELECT DISTINCT source "
                                               "FROM events")]
            con0.close()
            clauses = []
            for sname in srcs:
                off = offsets.get(sname, 0)
                clauses.append("(source=? AND t_ms>=? AND t_ms<=?)")
                params += [sname, int(lo) + off,
                           int(hi) + off if hi else 10**15]
            q += " AND (" + " OR ".join(clauses) + ")"
        else:
            q += " AND t_ms>=?"
            params.append(int(lo))
            if hi:
                q += " AND t_ms<=?"; params.append(int(hi))
    q += " ORDER BY t_ms" if not opts["--aligned"] else \
         " ORDER BY (t_ms - COALESCE(NULLIF(0,0),0))"
    # unified ordering: subtract per-source offset in SQL is messy; do it here
    con = sqlite3.connect(db)
    rows = list(con.execute(q, params))
    con.close()
    if opts["--aligned"] and offsets:
        rows = sorted(rows, key=lambda r: r[3] - offsets.get(r[0], 0))
    if opts["--tail"]:
        rows = rows[-int(opts["--tail"]):]
    for source, file, line, t, ev, stage, kv, raw in rows:
        uni = t - offsets.get(source, 0) if offsets else t
        print("%s t=%d %s:%s:%d | %s" % (source, uni, file, source, line, raw))
    print("-- %d hit(s) | filters: ev=%s stage=%s grep=%s source=%s "
          "aligned=%s" % (len(rows), opts["--ev"], opts["--stage"],
                          opts["--grep"], opts["--source"],
                          opts["--aligned"]))
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
