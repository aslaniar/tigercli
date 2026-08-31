#!/usr/bin/env python3
# REGISTRY: caps: log-indexing
"""logindex.py - universal index over sunrise.log-shaped logs (2026-08-27).

Turns the project's standard ev=/stage=/key=value grammar into a queryable
SQLite index so agents stop re-deriving grep+sed chains per question. The
grammar is generic: ANY log using "prefix t=<ms> ev=X stage=Y k=v ..." ingests
without per-family code.

Usage:
  /usr/bin/python3 RE_scripts/logindex.py [--out NAME] [LABEL=]PATH ...

  LABEL optional (default: file basename minus extension). Side inferred:
  label/path containing "server" -> server, else client.

Live-file policy (universal ingestion hygiene, not capture-specific): a file
modified within the last 5 minutes is copied to a snapshot first so an
in-flight append can never tear a read; the snapshot path is recorded in the
index header. Frozen captures index in place.

Output: RE_output/logindex/<NAME>.db with table events(source, file, line,
t_ms, ev, stage, kv, raw) + indexes. Prints per-source liveness counts;
--selftest runs a synthetic fixture and asserts extraction.

Exit: 0 indexed, 2 usage/environment error.
"""
import json
import os
import re
import shutil
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import merge_timeline as mt  # reuses parse_log_file + boot_record grammar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUTDIR = os.path.join(ROOT, "RE_output", "logindex")
KV_RE = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)=([^\s]+)")
LIVE_WINDOW_S = 300


def looks_live(path):
    try:
        return (time.time() - os.path.getmtime(path)) < LIVE_WINDOW_S
    except OSError:
        return False


def index_source(con, label, path, outdir):
    side = "server" if "server" in label.lower() or "server" in path.lower() \
        else "client"
    used = path
    snap = None
    if looks_live(path):
        snap = os.path.join(outdir, "snapshots",
                            "%s_%s.log" % (label, time.strftime("%Y%m%d_%H%M%S")))
        os.makedirs(os.path.dirname(snap), exist_ok=True)
        shutil.copyfile(path, snap)
        used = snap
    src = mt.parse_log_file(side, label, used)
    n = 0
    for line_no, (t, text) in enumerate(src.entries, 1):
        ev_m = re.search(r"\bev=([^\s]+)", text)
        st_m = re.search(r"\bstage=([^\s]+)", text)
        kvs = {k: v for k, v in KV_RE.findall(text)
               if k not in ("ev", "stage")}
        con.execute(
            "INSERT INTO events(source, file, line, t_ms, ev, stage, kv, raw) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (label, used, line_no, t,
             ev_m.group(1) if ev_m else None,
             st_m.group(1) if st_m else None,
             json.dumps(kvs, sort_keys=True), text))
        n += 1
    con.execute("INSERT INTO sources(source, side, file, snapshot, n_events) "
                "VALUES (?,?,?,?,?)", (label, side, path, snap, n))
    return n, side, snap


def selftest():
    import tempfile
    d = tempfile.mkdtemp(prefix="logq_fix_")
    p = os.path.join(d, "test_server.log")
    with open(p, "w") as fh:
        fh.write("server level=debug t=1000 ev=activity stage=push result=ok "
                 "type=1 body=189 len=234\n")
        fh.write("client level=info t=54350 ev=handle_message stage=push "
                 "tape=1 svc=9 size=206\x00with_nul\n")
        fh.write("garbage line without grammar\n")
    db = os.path.join(d, "test.db")
    n, side, snap = None, None, None
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE events(source TEXT, file TEXT, line INT, "
                "t_ms INT, ev TEXT, stage TEXT, kv TEXT, raw TEXT)")
    con.execute("CREATE TABLE sources(source TEXT, side TEXT, file TEXT, "
                "snapshot TEXT, n_events INT)")
    n, side, snap = index_source(con, "test_server", p, d)
    rows = list(con.execute("SELECT t_ms, ev, stage, kv, raw FROM events "
                            "ORDER BY line"))
    ok = True
    def check(name, cond, detail=""):
        nonlocal ok
        print("%s %-46s %s" % ("PASS" if cond else "FAIL", name, detail))
        ok = ok and cond
    check("row count == grammar lines (2 of 3, garbage preserved? no)",
          n == 2, "n=%d" % n)
    check("ev/stage extracted", rows[0][1] == "activity" and
          rows[0][2] == "push", str(rows[0][:3]))
    check("kv extracted", json.loads(rows[0][3]).get("type") == "1",
          rows[0][3][:60])
    check("NUL-bearing line indexed, content preserved (parser sanitizes "
          "NUL->space)",
          len(rows) > 1 and "with_nul" in rows[1][4] and "\x00" not in rows[1][4],
          rows[1][4][-40:])
    con.close()
    print("LOGINDEX SELFTEST %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    outdir = DEFAULT_OUTDIR
    if "--out" in argv:
        i = argv.index("--out")
        val = argv[i + 1]
        if os.path.dirname(val):
            outdir = os.path.dirname(os.path.abspath(val))
            name = os.path.basename(val)
        else:
            name = val  # bare name -> default logindex dir
        del argv[i:i + 2]
    else:
        name = "index_%s" % time.strftime("%Y%m%d_%H%M%S")
    inputs = [a for a in argv if not a.startswith("--")]
    if not inputs:
        print(__doc__)
        return 2
    os.makedirs(outdir, exist_ok=True)
    db_path = os.path.join(outdir, name if name.endswith(".db") else name + ".db")
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE IF NOT EXISTS events(source TEXT, file TEXT, "
                "line INT, t_ms INT, ev TEXT, stage TEXT, kv TEXT, raw TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS sources(source TEXT, side TEXT, "
                "file TEXT, snapshot TEXT, n_events INT)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_events_ev ON events(ev)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_events_stage ON events(stage)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_events_source ON events(source)")
    total = 0
    for spec in inputs:
        label, _, path = spec.rpartition("=") if "=" in spec else (spec, "", spec)
        if not os.path.exists(path):
            print("WARN missing: %s" % path)
            continue
        n, side, snap = index_source(con, label, path, outdir)
        total += n
        print("indexed %-14s side=%-6s events=%-6d %s%s" %
              (label, side, n, path, " (snapshot: %s)" % snap if snap else ""))
    con.commit()
    con.close()
    print("LIVENESS: total_events=%d db=%s" % (total, db_path))
    if total == 0:
        print("DEGENERATE: zero events indexed - check paths/grammar.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
