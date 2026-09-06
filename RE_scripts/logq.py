#!/usr/bin/env python3
# REGISTRY: caps: log-query, cross-machine-align
"""logq.py - query a logindex.py database (2026-08-27; v2 2026-09-05). The
replacement for per-question grep+sed chains: one command, every hit cited
as source file:line (claim-ready per the evidence rules).

Usage:
  /usr/bin/python3 RE_scripts/logq.py <index.db> [--ev E] [--stage S] [--fn F]
      [--grep P] [--source SRC] [--tail N] [--range T1,T2] [--aligned]
      [--bare | --full]

  --aligned  applies clock offsets from a sibling .drift.json (merge_timeline
             output with the same basename) so t-ranges and --tail order are
             comparable ACROSS machines; without it, t is native per source.
             If the drift file is missing this is LOUD: the query runs
             UNALIGNED and cross-machine ranges would be wrong.
  --fn F     match the probe/function field (kv "fn") - the mtrace field
             order is `stage=` BEFORE `fn=` (T3.3), so grep patterns on the
             raw line lie; this flag queries the parsed field instead.
  --bare     print `t=<unified> <raw line>` without the path citation
             (T3.2: the ~200-char path prefix destroyed every cut/regex).
             DEFAULT when --grep is used; --full restores the citation.

  --tail N   keeps the LAST N hits and prints a TRUNCATED marker (empty-mask
             #9: a conclusion from a truncated view must be visibly standing
             on one; re-run without --tail to confirm).

Exit codes: 0 = hits printed, 1 = no hits (the query RAN - liveness is the
exit path, not silence), 2 = usage error. Full lines are never truncated
except by --tail, which says so.
"""
import json
import os
import sqlite3
import sys


def main(argv):
    if not argv or "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0 if argv else 2
    db = argv[0]
    if db.startswith("--"):
        print("ERROR: first positional arg must be the index.db path "
              "(got %s). Usage: logq.py <index.db> [filters]" % db)
        return 2
    if not os.path.exists(db):
        print("ERROR: no index at %s (build with logindex.py)" % db)
        return 2
    opts = {"--ev": None, "--stage": None, "--fn": None, "--grep": None,
            "--source": None, "--tail": None, "--range": None,
            "--aligned": False, "--bare": False, "--full": False}
    it = iter(argv[1:])
    for a in it:
        if a == "--aligned":
            opts["--aligned"] = True
        elif a == "--bare":
            opts["--bare"] = True
        elif a == "--full":
            opts["--full"] = True
        elif a in opts:
            opts[a] = next(it, None)
        else:
            print("ERROR: unknown flag %s (--help for usage)" % a)
            return 2
    # bare default when grepping (T3.2), --full wins back the citation
    bare = opts["--bare"] or (opts["--grep"] and not opts["--full"])
    offsets = {}
    aligned_note = "no"
    if opts["--aligned"]:
        dpath = os.path.splitext(db)[0] + ".drift.json"
        if os.path.exists(dpath):
            with open(dpath) as fh:
                dj = json.load(fh)
            for s in dj["sources"]:
                if s.get("offset_ms") is not None:
                    offsets[s["source"]] = s["offset_ms"]
            aligned_note = "yes"
        else:
            print("LOUD: --aligned requested but NO drift file at %s" % dpath)
            print("      run merge_timeline.py over the same logs to build it;")
            print("      proceeding UNALIGNED - t is native per source, so any")
            print("      CROSS-MACHINE range/order in this output is WRONG until then.")
            aligned_note = "NO (drift missing)"
    q = "SELECT source, file, line, t_ms, ev, stage, kv, raw FROM events WHERE 1=1"
    params = []
    if opts["--ev"]:
        q += " AND ev=?"; params.append(opts["--ev"])
    if opts["--stage"]:
        q += " AND stage=?"; params.append(opts["--stage"])
    if opts["--fn"]:
        q += " AND kv LIKE ?"; params.append('%%"fn": "%s"%%' % opts["--fn"])
    if opts["--source"]:
        q += " AND source=?"; params.append(opts["--source"])
    if opts["--grep"]:
        q += " AND raw LIKE ?"; params.append("%" + opts["--grep"] + "%")
    if opts["--range"]:
        lo, hi = opts["--range"].split(",") if "," in opts["--range"] \
            else (opts["--range"], None)
        if opts["--aligned"] and offsets:
            con0 = sqlite3.connect(db)
            srcs = [r[0] for r in con0.execute("SELECT DISTINCT source FROM events")]
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
    q += " ORDER BY t_ms"
    con = sqlite3.connect(db)
    rows = list(con.execute(q, params))
    con.close()
    total = len(rows)
    if opts["--aligned"] and offsets:
        rows = sorted(rows, key=lambda r: r[3] - offsets.get(r[0], 0))
    if opts["--tail"]:
        rows = rows[-int(opts["--tail"]):]
    for source, file, line, t, ev, stage, kv, raw in rows:
        uni = t - offsets.get(source, 0) if offsets else t
        if bare:
            print("t=%d %s" % (uni, raw.rstrip("\n")))
        else:
            # the index stores source AND file as the same full path; printing
            # both was the ~200-char prefix that broke every cut (T3.2)
            print("%s t=%d %s:%d | %s" % (source, uni, os.path.basename(file),
                                          line, raw.rstrip("\n")))
    if opts["--tail"] and total > len(rows):
        print("TRUNCATED: showing %d of %d (a conclusion from this view is "
              "standing on a truncated view - re-run without --tail to "
              "confirm; empty-mask #9)" % (len(rows), total))
    print("-- %d hit(s)%s | filters: ev=%s stage=%s fn=%s grep=%s source=%s aligned=%s"
          % (len(rows),
             " (of %d)" % total if opts["--tail"] and total > len(rows) else "",
             opts["--ev"], opts["--stage"], opts["--fn"], opts["--grep"],
             opts["--source"], aligned_note))
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
