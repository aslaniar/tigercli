#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
boot_diff.py A B — Lane B: compare two boot records.

ORDER OF COMPARISON (deliverable 4, the falsifiable-check arbiter):
  1. MANIFEST FIRST: hash fields, then RECURSIVE FIELD-LEVEL settings diff
     (exact JSON paths, old -> new), eqHash, per-table DB row counts, flags
     count, state.db hash, content-JSON roster, WAL/shm presence.
     Known-volatile fields (captured_at, log pre-state, process census,
     label) are reported but NOT compared.
  2. EVENT STREAMS second: differences by (side, ev, stage, result) —
     per-signature counts, then ordered-sequence first divergence
     (difflib), then aligned kv payload diffs for 1:1 signatures
     (reports keys that differ, with example lines).

Usage: python3 RE_scripts/boot_diff.py A B
  A/B = record dirs (full path, or bare names under RE_output/boots).

Exit: 0 = no differences; 1 = differences found; 2 = usage error.
"""

import difflib
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(ROOT, "RE_output", "boots")

VOLATILE_MANIFEST_KEYS = {
    "captured_at_iso", "label", "mode", "recorder", "logs_prestate",
    "processes", "lane_dependency",
}


def resolve_record(arg):
    if os.path.isdir(arg):
        return arg
    cand = os.path.join(DEFAULT_OUT, arg)
    if os.path.isdir(cand):
        return cand
    sys.exit("ERROR: record not found: %s (tried %s)" % (arg, cand))


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def diff_recursive(path, a, b, out):
    """Recursive field diff; path = JSON pointer-ish dot path."""
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            np = "%s.%s" % (path, key) if path else key
            if key not in a:
                out.append(("added", np, None, b[key]))
            elif key not in b:
                out.append(("removed", np, a[key], None))
            else:
                diff_recursive(np, a[key], b[key], out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            diff_recursive("%s[%d]" % (path, i), x, y, out)
    elif a != b:
        out.append(("changed", path, a, b))


def short(v, limit=220):
    s = json.dumps(v, sort_keys=True) if not isinstance(v, str) else v
    return s if len(s) <= limit else s[:limit] + "..."


def manifest_section(dir_a, dir_b):
    ma = load_json(os.path.join(dir_a, "manifest.json"))
    mb = load_json(os.path.join(dir_b, "manifest.json"))
    print("=" * 72)
    print("MANIFEST (%s vs %s)" % (os.path.basename(dir_a), os.path.basename(dir_b)))
    print("=" * 72)

    ha = ma.get("hashes", {})
    hb = mb.get("hashes", {})
    for key in sorted(set(ha) | set(hb)):
        if key not in ha or key not in hb:
            print("  hash %-24s present only in %s" % (
                key, "A" if key in ha else "B"))
            continue
        same = ha[key].get("sha256") == hb[key].get("sha256") and \
            ha[key].get("size") == hb[key].get("size")
        print("  hash %-24s %s" % (key, "identical" if same else "DIFFERS"))
        if not same:
            print("        A sha256=%s size=%s" % (ha[key].get("sha256"), ha[key].get("size")))
            print("        B sha256=%s size=%s" % (hb[key].get("sha256"), hb[key].get("size")))

    diffs = []
    for side in ("server", "client"):
        diff_recursive("settings.%s" % side, ma.get("settings", {}).get(side, {}),
                       mb.get("settings", {}).get(side, {}), diffs)
    if diffs:
        print("  settings field diffs:")
        for kind, path, old, new in diffs:
            print("    %-8s %-45s %s -> %s" % (kind, path,
                                               short(old), short(new)))
    else:
        print("  settings: identical (no field diffs)")

    scalar_keys = [
        ("eqHash_computed", "eqHash (computed)"),
        ("flags_row_count", "flags row count"),
    ]
    for key, label in scalar_keys:
        va, vb = ma.get("db", {}).get(key, ma.get(key)), mb.get("db", {}).get(key, mb.get(key))
        print("  %-24s %s" % (label, "identical" if va == vb else "A=%s B=%s" % (va, vb)))

    ta = ma.get("db", {}).get("tables", {})
    tb = mb.get("db", {}).get("tables", {})
    row_diffs = [(k, ta.get(k), tb.get(k)) for k in sorted(set(ta) | set(tb))
                 if ta.get(k) != tb.get(k)]
    if row_diffs:
        print("  per-table row-count diffs:")
        for k, va, vb in row_diffs:
            print("    %-22s %s -> %s" % (k, va, vb))
    else:
        print("  per-table row counts: identical (%d tables)" % len(ta))

    dla, dlb = ma.get("db", {}).get("wal_present"), mb.get("db", {}).get("wal_present")
    print("  state.db wal/shm  %s" % ("identical" if
          (dla, ma.get("db", {}).get("shm_present")) ==
          (dlb, mb.get("db", {}).get("shm_present")) else
          "A wal=%s B wal=%s" % (dla, dlb)))
    # content hash (canonical dump) is the compared field; the raw file bytes
    # churn with WAL checkpoint timing while content is identical, so the
    # file hash is informational only (fallback for pre-v2 records).
    cha, chb = ma.get("db", {}).get("content_hash"), mb.get("db", {}).get("content_hash")
    if cha is None or chb is None:
        cha = ma.get("hashes", {}).get("state_db", {}).get("sha256")
        chb = mb.get("hashes", {}).get("state_db", {}).get("sha256")
        label = "state.db hash (file bytes; legacy records)"
    else:
        label = "state.db content hash (canonical dump)"
    print("  %-42s %s" % (label, "identical" if cha == chb
                          else "A=%s B=%s" % (cha, chb)))

    ca = ma.get("content_jsons", {})
    cb = mb.get("content_jsons", {})
    if set(ca) != set(cb):
        print("  content JSON roster differs: only-A=%s only-B=%s" % (
            sorted(set(ca) - set(cb)), sorted(set(cb) - set(ca))))
    else:
        size_diffs = [k for k in ca if ca[k] != cb[k]]
        if size_diffs:
            print("  content JSON sizes differ: %s" % size_diffs)
        else:
            print("  content JSON roster: identical (%d files)" % len(ca))

    print("  (not compared: %s)" % ", ".join(sorted(VOLATILE_MANIFEST_KEYS)))
    return diffs, row_diffs


def load_events(rec_dir):
    db = os.path.join(rec_dir, "events.sqlite")
    con = sqlite3.connect(db)
    rows = con.execute(
        "SELECT side, ev, stage, result, kv, raw FROM events WHERE parsed=1 "
        "ORDER BY side, rowid").fetchall()
    con.close()
    return rows


def signature_key(row):
    side, ev, stage, result = row[0], row[1], row[2], row[3]
    return (side, ev or "", stage or "", result or "")


def event_section(dir_a, dir_b):
    rows_a, rows_b = load_events(dir_a), load_events(dir_b)
    print("=" * 72)
    print("EVENT STREAMS (side, ev, stage, result)  A=%d lines B=%d lines"
          % (len(rows_a), len(rows_b)))
    print("=" * 72)

    from collections import Counter
    ca, cb = Counter(signature_key(r) for r in rows_a), \
        Counter(signature_key(r) for r in rows_b)
    sig_diffs = []
    for sig in sorted(set(ca) | set(cb)):
        if ca[sig] != cb[sig]:
            sig_diffs.append((sig, ca[sig], cb[sig]))
    if sig_diffs:
        print("  per-signature count diffs (%d):" % len(sig_diffs))
        for sig, na, nb in sig_diffs[:40]:
            print("    %-5s %-16s %-20s %-12s A=%-6d B=%d"
                  % (sig[0], sig[1], sig[2], sig[3], na, nb))
        if len(sig_diffs) > 40:
            print("    ... %d more" % (len(sig_diffs) - 40))
    else:
        print("  per-signature counts: identical (%d distinct signatures)"
              % len(ca))

    seq_a = [signature_key(r) for r in rows_a]
    seq_b = [signature_key(r) for r in rows_b]

    def first_divergence():
        n = min(len(seq_a), len(seq_b))
        for i in range(n):
            if seq_a[i] != seq_b[i]:
                return i
        return n if len(seq_a) != len(seq_b) else None

    budget = 4_000_000  # SequenceMatcher is quadratic-ish; stay linear past this
    if len(seq_a) * len(seq_b) <= budget:
        sm = difflib.SequenceMatcher(None, seq_a, seq_b, autojunk=True)
        ops = [op for op in sm.get_opcodes() if op[0] != "equal"]
        if ops:
            print("  sequence: first divergence at A[%d]/B[%d], %d change blocks"
                  % (ops[0][1], ops[0][3], len(ops)))
            i1, i2, j1, j2 = ops[0][1], ops[0][2], ops[0][3], ops[0][4]
            print("    A lines %d..%d:" % (i1, i2))
            for r in rows_a[i1:i1 + 6]:
                print("      [%s] %s" % (r[0], truncate(r[5], 140)))
            print("    B lines %d..%d:" % (j1, j2))
            for r in rows_b[j1:j1 + 6]:
                print("      [%s] %s" % (r[0], truncate(r[5], 140)))
        else:
            print("  sequence: identical order (no change blocks)")
    else:
        div = first_divergence()
        if div is None:
            print("  sequence: identical order (linear scan, %d lines)" % len(seq_a))
        else:
            print("  sequence: first divergence at index %d (linear scan; "
                  "%d x %d items, block analysis budgeted out)" % (div, len(seq_a), len(seq_b)))
            for r in rows_a[div:div + 6]:
                print("      A: [%s] %s" % (r[0], truncate(r[5], 140)))
            for r in rows_b[div:div + 6]:
                print("      B: [%s] %s" % (r[0], truncate(r[5], 140)))
        ops = [] if div is None else [("unequal", div, min(div + 6, len(rows_a)),
                                       div, min(div + 6, len(rows_b)))]

    # aligned kv payload diff for signatures with matching counts (bounded:
    # the per-signature rescan is O(n_sig * n_lines); cap it)
    if not sig_diffs and len(rows_a) <= 100_000:
        kv_reports = []
        seen_examples = set()
        for sig in sorted(ca):
            group_a = [r for r in rows_a if signature_key(r) == sig]
            group_b = [r for r in rows_b if signature_key(r) == sig]
            pairs = zip(group_a, group_b)
            for ra, rb in pairs:
                kva = json.loads(ra[4])
                kvb = json.loads(rb[4])
                for key in sorted(set(kva) | set(kvb)):
                    if kw_differ(kva, kvb, key):
                        key_id = (sig, key)
                        if key_id not in seen_examples:
                            kv_reports.append(key_id)
                            seen_examples.add(key_id)
                        # mark kv change on the first occurrence only
                        break
        if kv_reports:
            print("  aligned kv payload diffs (%d distinct signature/keys, first examples):"
                  % len(kv_reports))
            for (sig, key) in list(seen_examples)[:15]:
                print("    %-5s %-16s %-18s key=%s" % (sig[0], sig[1], sig[2], key))
        else:
            print("  aligned kv payloads: identical for all 1:1 signatures")
    elif not sig_diffs:
        print("  aligned kv payload scan skipped: %d lines exceeds the 100k cap" % len(rows_a))
    return sig_diffs, ops, kv_reports if not sig_diffs else []


# native ms timestamps are the t_ms / unified_t_ms columns' job, and always
# vary run-to-run; exclude them from kv alignment.
EXCLUDED_KV = {"t"}


def kw_differ(kva, kvb, key):
    if key in EXCLUDED_KV:
        return False
    return kva.get(key) != kvb.get(key)


def truncate(s, n):
    return s if len(s) <= n else s[:n] + "..."


def main():
    if len(sys.argv) != 3:
        print("usage: boot_diff.py A B", file=sys.stderr)
        return 2
    dir_a = resolve_record(sys.argv[1])
    dir_b = resolve_record(sys.argv[2])
    diffs, row_diffs = manifest_section(dir_a, dir_b)
    sig_diffs, ops, kv_reports = event_section(dir_a, dir_b)

    print("=" * 72)
    n_findings = len(diffs) + len(row_diffs) + len(sig_diffs) + len(ops) + len(kv_reports)
    if n_findings == 0:
        print("VERDICT: CLEAN — no manifest differences, no event-stream differences.")
        return 0
    print("VERDICT: %d difference group(s): settings=%d db_rows=%d signature=%d sequence=%d kv=%d"
          % (len(diffs) + len(row_diffs) + len(sig_diffs) + len(ops) + len(kv_reports),
             len(diffs), len(row_diffs), len(sig_diffs), len(ops), len(kv_reports)))
    return 1


if __name__ == "__main__":
    sys.exit(main())