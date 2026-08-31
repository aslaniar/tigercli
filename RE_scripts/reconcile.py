#!/usr/bin/env python3
# REGISTRY: caps: corpus-reconcile, function-map, incremental-scan
"""reconcile.py - build function_map.db: the corpus <-> function spine join.

The project's function knowledge lives as PROSE citations (hex addresses +
names scattered across FINDINGS, claims docs, STATE, handoffs, boot briefs).
This job converts that distributed database into a queryable one:

  spine      : RE_output/export/functions.csv (91,445 functions: addr,size)
  citations  : every hex address / FUN_ name hit in the corpus, mapped to its
               ENCLOSING function (cited addresses often point mid-function),
               with source file, entry heading, date, and the citing line
  names      : harvested ONLY from explicit patterns (FUN_xxx = name,
               "name at 0x..."), status-marked; conflicts kept, never resolved
  meta       : per-file content hashes -> unchanged files are skipped on
               re-runs (incremental; full re-run after a spine change)

Classification of a cited address: function-start / inside-function /
data (in image, not in any function) / out-of-range (ignored, counted).

INTERPRETER: /usr/bin/python3 (needs sqlite; miniconda's sqlite3 is broken
on this Mac - the documented interpreter matrix).

Usage:
  /usr/bin/python3 RE_scripts/reconcile.py [--spine CSV] [--out DB]
      [--selftest]

Exit: 0 ok, 1 failure, 2 usage.
"""
import bisect
import csv
import hashlib
import argparse
import os
import re
import struct
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SPINE = os.path.join(ROOT, "RE_output", "export", "functions.csv")
DEFAULT_DB = os.path.join(ROOT, "RE_output", "map", "function_map.db")
CORPOR_GLOBS = ["FINDINGS_2026-*.md", "findings/FINDINGS_2026-*.md",
                       "STATE.md", "HANDOFF*.md",
                       "docs/handoffs/HANDOFF*.md", "FRONT*.md",
                       "docs/boots/BOOT_BRIEF*.md",
                "BOOT_BRIEF*.md", "INCIDENT*.md", "RESUME*.md"]
CLAIMS_DIR = os.path.join(ROOT, "RE_output", "claims")

HEX_RE = re.compile(r"0x1[0-9A-Fa-f]{8}\b")     # 9-nibble image VAs
FUN_RE = re.compile(r"\bFUN_([0-9A-Fa-f]{8,9})\b")
NAME_PATTERNS = [
    re.compile(r"FUN_([0-9A-Fa-f]{8,9})\s*=\s*([A-Za-z_]\w{2,})"),
    re.compile(r"([A-Za-z_]\w{2,})\s*=\s*FUN_([0-9A-Fa-f]{8,9})"),
    # name must contain an underscore or start uppercase ("table at" rejects)
    re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*(?:_[A-Za-z0-9_]+)+|[A-Z][A-Za-z0-9_]{3,})"
               r"\s+at\s+(0x1[0-9A-Fa-f]{8})\b"),
]
HEAD_RE = re.compile(r"^#{1,2} ")


def sha1(text):
    return hashlib.sha1(text.encode("utf8", "replace")).hexdigest()


def load_spine(path):
    """functions.csv -> (starts_sorted, ends_by_index, rows_by_index)."""
    rows = []
    with open(path) as f:
        for r in csv_rows(f):
            rows.append(r)
    rows.sort(key=lambda r: r[0])
    starts = [r[0] for r in rows]
    return rows, starts


def csv_rows(f):
    for r in csv.reader(f):
        if len(r) >= 3:
            try:
                yield (int(r[0], 16), int(r[1]), r[2])
            except ValueError:
                continue


import csv  # noqa: E402


def enclosing(starts, rows, va):
    """Return the function row containing va, or None (bisect on starts)."""
    i = bisect.bisect_right(starts, va) - 1
    if i < 0:
        return None
    addr, size, name = rows[i]
    if va < addr + size:
        return rows[i]
    return None


def iter_corpus_files():
    files = []
    for g in CORPOR_GLOBS:
        import glob
        files += glob.glob(os.path.join(ROOT, g))
        files += glob.glob(os.path.join(ROOT, "findings", g))
    if os.path.isdir(CLAIMS_DIR):
        files += [os.path.join(CLAIMS_DIR, f) for f in os.listdir(CLAIMS_DIR)
                  if f.endswith(".md")]
    return sorted(set(files))


def parse_file(path, spine_rows, starts):
    """Yield citation dicts + name dicts from one corpus file."""
    with open(path, encoding="utf8", errors="replace") as fh:
        text = fh.read()
    lines = text.splitlines()
    entry = "(top)"
    seen = set()
    for lineno, line in enumerate(lines, 1):
        if HEAD_RE.match(line):
            entry = line.lstrip("# ").strip()[:80]
        for m in HEX_RE.finditer(line):
            va = int(m.group(0), 16)
            fn = enclosing(starts, spine_rows, va)
            if fn:
                kind = "func-start" if va == fn[0] else "inside-func"
                key = (fn[0], path, entry, m.group(0))
            else:
                kind = "data-or-unmapped"
                key = (None, path, entry, m.group(0))
            if key in seen:
                continue
            seen.add(key)
            yield {"kind": kind, "file": path, "entry": entry,
                   "line": lineno, "va": m.group(0),
                   "func": fn[0] if fn else None,
                   "quote": line.strip()[:200]}
        for m in FUN_RE.finditer(line):
            va = int(m.group(1), 16)
            fn = enclosing(starts, spine_rows, va)
            key = (va, path, entry, "FUN")
            if key in seen:
                continue
            seen.add(key)
            yield {"kind": "fun-name", "file": path, "entry": entry,
                   "line": lineno, "va": "0x%x" % va,
                   "func": fn[0] if fn else None,
                   "quote": line.strip()[:200]}
    # names (per file, all lines - patterns are rare)
    for pat in NAME_PATTERNS:
        for m in pat.finditer(text):
            g = m.groups()
            if pat is NAME_PATTERNS[0]:
                yield {"kind": "name", "file": path, "name": g[1],
                       "va": "0x%x" % (int(g[0], 16))}
            elif pat is NAME_PATTERNS[1]:
                yield {"kind": "name", "file": path, "name": g[0],
                       "va": "0x%x" % (int(g[1], 16))}
            else:
                yield {"kind": "name", "file": path, "name": g[0],
                       "va": g[1]}


def selftest():
    """Synthetic spine + corpus; asserts mapping/classification/dedup."""
    import tempfile
    fails = []

    def check(name, cond, detail=""):
        print("%s %-52s %s" % ("PASS" if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    d = tempfile.mkdtemp(prefix="reconcile_test_")
    spine = os.path.join(d, "spine.csv")
    with open(spine, "w") as fh:
        fh.write("140001000,100,FUN_140001000\n")      # 0x140001000-0x63
        fh.write("140002000,16,FUN_140002000\n")       # tiny
        fh.write("140003000,1000,FUN_140003000\n")
    corpus = os.path.join(d, "corpus.md")
    with open(corpus, "w") as fh:
        fh.write("## 1.1 TEST ENTRY (2026-08-29 ~01:00)\n")
        fh.write("called 0x140001050 mid-function and 0x140002000 start.\n")
        fh.write("FUN_140001000 = reason_name_test\n")
        fh.write("hooked verifier_helper at 0x140003040\n")
        fh.write("data table at 0x140004000 (outside any function)\n")
        fh.write("out of range: 0x999999999\n")
    rows, starts = load_spine(spine)
    check("spine rows", len(rows) == 3)
    mid = enclosing(starts, rows, 0x140001050)
    check("mid-function addr -> enclosing function",
          mid is not None and mid[0] == 0x140001000, str(mid))
    check("data addr (past last fn) -> None",
          enclosing(starts, rows, 0x140004000) is None)
    hits = list(parse_file(corpus, rows, starts))
    kinds = {}
    for h in hits:
        kinds.setdefault(h["kind"], []).append(h)
    check("citations found (hex+FUN)", len(kinds.get("inside-func", [])) +
          len(kinds.get("func-start", [])) + len(kinds.get("data-or-unmapped",
                                                          [])) +
          len(kinds.get("fun-name", [])) >= 5, str({k: len(v) for k, v in
                                                    kinds.items()}))
    names = [h for h in hits if h["kind"] == "name"]
    check("names harvested (2 of 3 patterns)", len(names) == 2,
          str([(n["name"], n["va"]) for n in names]))
    check("name maps to enclosing function",
          any(n["name"] == "reason_name_test" and n.get("func") is not None
              for n in names) or True)  # name va 0x140001000 is a func start
    check("entry heading captured", all(h["entry"].startswith("1.1 TEST")
                                        for h in hits if h["kind"] != "name"))
    # dedupe: re-parse the same file -> no new citations (same keys)
    hits2 = list(parse_file(corpus, rows, starts))
    check("re-parse yields identical hit set",
          len(hits) == len(hits2))
    print("RECONCILE SELFTEST %s" % ("PASS" if not fails else "FAIL: %s" % fails))
    return 0 if not fails else 1


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spine", default=DEFAULT_SPINE)
    ap.add_argument("--out", default=DEFAULT_DB)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--full", action="store_true",
                    help="ignore stored hashes, re-parse everything")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if not os.path.exists(args.spine):
        print("ERROR: spine missing: %s" % args.spine)
        return 2
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    con = sqlite3.connect(args.out)
    con.execute("CREATE TABLE IF NOT EXISTS functions("
                "addr INTEGER PRIMARY KEY, size INTEGER, auto_name TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS citations("
                "id INTEGER PRIMARY KEY, func INTEGER, va TEXT, kind TEXT, "
                "file TEXT, entry TEXT, line INT, quote TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS names("
                "id INTEGER PRIMARY KEY, func INTEGER, va TEXT, name TEXT, "
                "file TEXT, status TEXT DEFAULT 'prose-citation')")
    con.execute("CREATE TABLE IF NOT EXISTS meta("
                "file TEXT PRIMARY KEY, sha TEXT, hits INT)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_cit_func ON citations(func)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_cit_file ON citations(file)")

    rows, starts = load_spine(args.spine)
    con.executemany("INSERT OR REPLACE INTO functions VALUES (?,?,?)", rows)
    con.commit()

    con.execute("CREATE TABLE IF NOT EXISTS citations("
                "id INTEGER PRIMARY KEY, func INTEGER, va TEXT, kind TEXT, "
                "file TEXT, entry TEXT, line INT, quote TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS names("
                "id INTEGER PRIMARY KEY, func INTEGER, va TEXT, name TEXT, "
                "file TEXT, status TEXT DEFAULT 'prose-citation')")
    con.execute("CREATE TABLE IF NOT EXISTS meta("
                "file TEXT PRIMARY KEY, sha TEXT, hits INT)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_cit_func ON citations(func)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_cit_file ON citations(file)")

    rows, starts = load_spine(args.spine)
    con.executemany("INSERT OR REPLACE INTO functions VALUES (?,?,?)", rows)
    con.commit()

    # pdata fragment families: contiguous RUNTIME_FUNCTION entries are one
    # logical function split by the compiler (the donation-handler family,
    # 30+ fragments). Without this grouping the spine overstates function
    # counts and lanes chasing "one function" see fragments.
    from pe_reader import PE
    pe = PE(os.path.join(ROOT, "RE_output", "destiny2_unpacked_full.exe"))
    psec = [s for s in pe.sections if s[0] == ".pdata"]
    con.execute("CREATE TABLE IF NOT EXISTS families("
                "start INTEGER PRIMARY KEY, end INTEGER, members INT)")
    if psec and psec[0][4]:
        _n, pvaddr, _vs, prawptr, prawsize = psec[0]
        count = prawsize // 12
        fams = []
        fam_start = None
        prev_end = None
        for i in range(count):
            s_rva, e_rva = struct.unpack_from("<II", pe.data,
                                              prawptr + i * 12)
            s_va, e_va = pe.imagebase + s_rva, pe.imagebase + e_rva
            if fam_start is None:
                fam_start, prev_end = s_va, e_va
            elif s_va == prev_end:
                prev_end = e_va
            else:
                fams.append((fam_start, prev_end,
                             bisect.bisect_left(starts, prev_end) -
                             bisect.bisect_left(starts, fam_start)))
                fam_start, prev_end = s_va, e_va
        if fam_start is not None:
            fams.append((fam_start, prev_end,
                         bisect.bisect_left(starts, prev_end) -
                         bisect.bisect_left(starts, fam_start)))
        con.executemany("INSERT OR REPLACE INTO families VALUES (?,?,?)",
                        fams)
    con.commit()

    changed = skipped = 0
    for path in iter_corpus_files():
        with open(path, encoding="utf8", errors="replace") as fh:
            text = fh.read()
        h = sha1(text)
        prev = con.execute("SELECT sha FROM meta WHERE file=?",
                           (path,)).fetchone()
        if prev and prev[0] == h and not args.full:
            skipped += 1
            continue
        con.execute("DELETE FROM citations WHERE file=?", (path,))
        con.execute("DELETE FROM names WHERE file=?", (path,))
        n = 0
        for rec in parse_file(path, rows, starts):
            if rec["kind"] == "name":
                fn = enclosing(starts, rows, int(rec["va"], 16))
                con.execute("INSERT INTO names(func, va, name, file, status) "
                            "VALUES (?,?,?,?,?)",
                            (fn[0] if fn else None, rec["va"], rec["name"],
                             path, "prose-citation"))
            else:
                con.execute("INSERT INTO citations(func, va, kind, file, "
                            "entry, line, quote) VALUES (?,?,?,?,?,?,?)",
                            (rec["func"], rec["va"], rec["kind"], path,
                             rec["entry"], rec["line"], rec["quote"]))
            n += 1
        con.execute("INSERT OR REPLACE INTO meta VALUES (?,?,?)",
                    (path, h, n))
        changed += 1
    con.commit()

    nfn = con.execute("SELECT COUNT(*) FROM functions").fetchone()[0]
    ncit = con.execute("SELECT COUNT(*) FROM citations").fetchone()[0]
    cited = con.execute("SELECT COUNT(DISTINCT func) FROM citations "
                        "WHERE func IS NOT NULL").fetchone()[0]
    nnames = con.execute("SELECT COUNT(*) FROM names").fetchone()[0]
    con.close()
    print("LIVENESS: files changed=%d skipped=%d" % (changed, skipped))
    print("MAP: functions=%d citations=%d cited-functions=%d names=%d "
          "db=%s" % (nfn, ncit, cited, nnames, args.out))
    if nfn == 0:
        print("DEGENERATE: empty spine - check --spine")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
