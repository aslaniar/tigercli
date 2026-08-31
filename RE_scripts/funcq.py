#!/usr/bin/env python3
# REGISTRY: caps: function-query, coverage-report
"""funcq.py - query the function map (built by reconcile.py).

One command replaces the "grep FINDINGS for the address, open Ghidra,
re-derive context" dig. Answers "what does the project know about function X"
with names (status-marked), dated citations grouped by source, and the
function's neighbors in the spine.

INTERPRETER: /usr/bin/python3 (sqlite; miniconda's sqlite3 is broken here).

Usage:
  /usr/bin/python3 RE_scripts/funcq.py 0x1416E1620
  /usr/bin/python3 RE_scripts/funcq.py --coverage
  /usr/bin/python3 RE_scripts/funcq.py --corpus "reason_name"
  /usr/bin/python3 RE_scripts/funcq.py ADDR [--db PATH]

Exit: 0 hits, 1 no hits, 2 usage.
"""
import argparse
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.path.join(ROOT, "RE_output", "map", "function_map.db")


def tier(size):
    if size >= 4096:
        return "big"
    if size >= 256:
        return "mid"
    return "small"


def show_function(con, addr):
    row = con.execute("SELECT addr, size, auto_name FROM functions "
                      "WHERE addr=?", (addr,)).fetchone()
    if not row:
        # maybe an address INSIDE a function
        cand = con.execute(
            "SELECT addr, size, auto_name FROM functions "
            "WHERE addr<=? AND addr+size>? ORDER BY addr DESC LIMIT 1",
            (addr, addr)).fetchone()
        if cand:
            print("address 0x%x is INSIDE function 0x%x (offset +%d)" %
                  (addr, cand[0], addr - cand[0]))
            addr = cand[0]
            row = cand
        else:
            print("0x%x: not in spine" % addr)
            return 1
    print("== function 0x%x (size %d, %s tier) auto=%s" %
          (row[0], row[1], tier(row[1]), row[2]))
    names = con.execute("SELECT name, file, status FROM names "
                        "WHERE func=? ORDER BY rowid", (addr,)).fetchall()
    if names:
        print("names:")
        for n, f, st in names:
            print("  - %s [%s] (%s)" % (n, st, os.path.basename(f)))
    cites = con.execute(
        "SELECT kind, file, entry, quote FROM citations "
        "WHERE func=? ORDER BY rowid DESC", (addr,)).fetchall()
    print("citations: %d" % len(cites))
    by_file = {}
    for kind, f, entry, quote in cites:
        by_file.setdefault(os.path.basename(f), []).append((entry, quote))
    for f, items in sorted(by_file.items(), key=lambda kv: -len(kv[1])):
        print("  %s (%d):" % (f, len(items)))
        for entry, quote in items[:4]:
            print("    [%s] %s" % (entry[:60], quote[:150]))
        if len(items) > 4:
            print("    ... +%d more" % (len(items) - 4))
    prev = con.execute("SELECT addr FROM functions WHERE addr<? "
                       "ORDER BY addr DESC LIMIT 1", (addr,)).fetchone()
    nxt = con.execute("SELECT addr FROM functions WHERE addr>? "
                      "ORDER BY addr LIMIT 1", (addr,)).fetchone()
    print("neighbors: prev=0x%x next=0x%s" %
          (prev[0] if prev else 0,
           "%x" % nxt[0] if nxt else "none"))
    return 0


def coverage(con):
    total, = con.execute("SELECT COUNT(*) FROM functions").fetchone()
    cited, = con.execute("SELECT COUNT(DISTINCT func) FROM citations "
                         "WHERE func IS NOT NULL").fetchone()
    named, = con.execute("SELECT COUNT(DISTINCT func) FROM names "
                         "WHERE func IS NOT NULL").fetchone()
    print("== coverage ==")
    print("functions in spine : %d" % total)
    print("cited by corpus    : %d (%.2f%%)" % (cited, 100.0 * cited / max(1, total)))
    print("named via corpus   : %d (%.2f%%)" % (named, 100.0 * named / max(1, total)))
    print("by tier (cited/total):")
    for t, lo, hi in (("big", 4096, 10 ** 9), ("mid", 256, 4096),
                      ("small", 0, 256)):
        tot, = con.execute("SELECT COUNT(*) FROM functions WHERE size>=? "
                           "AND size<?", (lo, hi)).fetchone()
        c, = con.execute("SELECT COUNT(DISTINCT f.func) FROM citations f "
                         "JOIN functions fu ON fu.addr=f.func "
                         "WHERE fu.size>=? AND fu.size<?", (lo, hi)).fetchone()
        print("  %-5s %6d / %6d (%.2f%%)" % (t, c, tot,
                                             100.0 * c / max(1, tot)))
    return 0


def corpus_search(con, term):
    rows = con.execute(
        "SELECT func, va, kind, file, entry, quote FROM citations "
        "WHERE quote LIKE ? ORDER BY rowid DESC LIMIT 40",
        ("%" + term + "%",)).fetchall()
    for func, va, kind, f, entry, quote in rows:
        print("%s %s [%s] %s | %s" % (va, kind, entry[:40],
                                      os.path.basename(f), quote[:140]))
    print("-- %d hit(s)" % len(rows))
    return 0 if rows else 1


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("target", nargs="?", help="hex address (0x...) or name")
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--coverage", action="store_true")
    ap.add_argument("--corpus", metavar="TERM")
    args = ap.parse_args(argv)
    if not os.path.exists(args.db):
        print("ERROR: no map at %s (run reconcile.py first)" % args.db)
        return 2
    con = sqlite3.connect("file:%s?mode=ro" % args.db, uri=True)
    try:
        if args.coverage:
            return coverage(con)
        if args.corpus:
            return corpus_search(con, args.corpus)
        if not args.target:
            ap.print_help()
            return 2
        try:
            addr = int(args.target, 0)
        except ValueError:
            names = con.execute(
                "SELECT func FROM names WHERE name=? AND func IS NOT NULL "
                "ORDER BY rowid DESC LIMIT 1", (args.target,)).fetchall()
            if not names:
                print("no name/symbol match for %r" % args.target)
                return 1
            addr = names[0][0]
        return show_function(con, addr)
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
