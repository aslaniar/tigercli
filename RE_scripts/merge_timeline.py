#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_timeline.py -- N-sided timeline merger for multi-source boot captures.

Merges two or more log sources (server log, client1 log, optional client2
log) and/or existing boot-record event stores into ONE anchor-corrected,
source-tagged chronology, plus a per-source clock-drift report.

THE ANCHOR RULE (the documented cross-process trap): same-NAME core events on
client vs server sides are NOT the same real moment (client core lines come
from the in-process DLL; the server is a standalone process booted minutes
earlier; ~5.3 s disagreement observed). Only WIRE events are true shared
moments usable as merge anchors:

  family "wire_tape_push"  (verified, measured: 94 pairs on the 22:46 record)
      server side : ev=activity stage=push ... type=<T> ... len=<L>
      client side : tape=1 ... svc=9 ... size=<S> ... type=<T>
      checks      : per-pair type equality REQUIRED; len = size + 28 reported.
  family "wire_tape_peer"  (inferred; see lanes/capture_rig_claims.md 1.1)
      client <-> client tape rows for the same underlying push;
      checks: per-pair type equality + size equality.

Transport accept lines are carried as marker rows but never used to pair
(no verifiable both-end shape on disk yet).

OFFSET SIGN CONVENTION (generalized from boot_record.py): for source S vs
reference R, offset_S = median over anchor pairs of (t_S - t_R);
unified_S(t) = t - offset_S; the reference keeps offset 0. With R = a client
and S = the server this is exactly boot_record's client-relative clock.
No anchor pair => offset stays None and the source stays native (honest null).

Usage:
  /usr/bin/python3 RE_scripts/merge_timeline.py [inputs] [options]

Inputs (repeatable):
  --server-log [LABEL=]PATH    raw server-side log file
  --client-log [LABEL=]PATH    raw client-side log file
  --record     [LABEL=]DIR     existing boot-record dir (events.sqlite); each
                               side inside becomes its own source LABEL:side

Options:
  --reference LABEL            pivot timeline label (default: the SERVER when
                               present, else first client; 2026-08-27 change -
                               see the grammar-drift note near typed_tapes)
  --out PREFIX                 write PREFIX.tsv, PREFIX.jsonl, PREFIX.drift.json
                               (default: print summary only)
  --tolerance-ms N             fixture verification tolerance (default 500)

Fixture / validation modes:
  --make-fixtures DIR          generate synthetic 3-source logs + ground truth
  --verify-fixtures DIR        merge DIR fixtures in-process, assert against
                               ground truth, exit 0/1
  --selftest                   make fixtures in a scratch dir, merge, verify,
                               plus record-store integration + no-anchor
                               honesty checks; exit 0/1

Exit codes: 0 ok/selftest pass; 1 selftest or verification failure;
2 usage error. Stdlib only; /usr/bin/python3 (broken _sqlite3 elsewhere).
"""

import argparse
import json
import os
import random
import re
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boot_record as br  # line grammar + wire-anchor regexes, VERBATIM

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SCRATCH = os.path.join(ROOT, "RE_output", "scratch", "timeline_fixtures")

# 2026-08-27: measured envelope delta len(server)=size(client)+28 on the
# p2-58 capture (234=206+28, 601=573+28). Era-specific; override via
# --size-delta if the envelope changes again.
SIZE_DELTA = 28

# peer-family tape extraction (same line shapes as TAPE_CLIENT; used when BOTH
# ends of a candidate pair are clients)
TAPE_ANY = re.compile(r"\btape=1\b.*\bsvc=9\b")


# ---------------------------------------------------------------------------
# sources
# ---------------------------------------------------------------------------

class Source(object):
    """One timeline: a labeled stream of parsed entries from one process."""

    def __init__(self, label, side, entries, unparsed=None, origin=""):
        self.label = label
        self.side = side              # 'server' | 'client' | other-native
        self.entries = entries        # [(t_ms, raw_text)] parsed only, ascending
        self.unparsed = unparsed or []  # raw text of grammar-violating lines
        self.origin = origin          # where it came from (path or record dir)
        self.offset_ms = None         # native -> unified: unified = t - offset
        self.anchor = None            # drift-report dict

    def ident(self):
        return "%s/%s" % (self.label, self.side)


def split_label(spec, default_prefix):
    """'LABEL=path' -> (label, path); bare 'path' -> (default_prefix, path)."""
    if "=" in spec:
        label, path = spec.split("=", 1)
        return label, path
    return default_prefix, spec


def parse_log_file(side, label, path):
    """Parse a raw sunrise-grammar log into a Source (boot_record.parse_line)."""
    entries, unparsed = [], []
    with open(path, "rb") as fh:
        for raw in fh:
            text = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            clean = br.sanitize(text)
            kv, ok = br.parse_line(clean)
            # parse_line already guarantees kv["t"] is digits when ok
            if ok:
                entries.append((int(kv["t"]), clean))
            else:
                unparsed.append(clean)
    return Source(label, side, entries, unparsed, origin=path)


def load_record_store(label, rec_dir):
    """Load one boot-record events.sqlite into per-side Sources."""
    db_path = os.path.join(rec_dir, "events.sqlite")
    if not os.path.exists(db_path):
        raise SystemExit("ERROR: no events.sqlite in record dir: %s" % rec_dir)
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT side, t_ms, ev, stage, result, kv, raw, parsed FROM events "
        "ORDER BY rowid").fetchall()
    con.close()
    buckets, unparsed = {}, {}
    for side, t_ms, ev, stage, result, kv, raw, parsed in rows:
        side = side or "unknown"
        if not parsed or t_ms is None:
            unparsed.setdefault(side, []).append(raw)
            continue
        # rebuild the canonical raw text exactly as ingested (kv blob holds the
        # parsed fields; raw is the sanitized line the recorder stored)
        try:
            kvd = json.loads(kv)
        except ValueError:
            kvd = {}
        text = rebuild_raw(kvd, raw)
        buckets.setdefault(side, []).append((int(t_ms), text))
    out = []
    for side in sorted(buckets):
        # stable t-sort ONLY: preserves ingestion (rowid) order within equal
        # timestamps. Sorting by the full tuple would reorder same-t events
        # alphabetically and scramble the wire-type sequence the anchor
        # alignment depends on.
        src = Source(label, side, sorted(buckets[side], key=lambda e: e[0]),
                     unparsed.get(side, []), origin=rec_dir)
        out.append(src)
    if not out:
        raise SystemExit("ERROR: no parsed events in %s" % db_path)
    return out


def rebuild_raw(kvd, raw_fallback):
    """Records store raw already-sanitized; prefer it (it is the captured
    bytes). kv blob is kept for structured output."""
    return raw_fallback


# ---------------------------------------------------------------------------
# typed wire events + alignment (port of boot_record.tape_anchor, generalized)
# ---------------------------------------------------------------------------

def typed_pushes(entries):
    """Server-side push rows: (t, type, len)."""
    return br._typed_events(entries, br.TAPE_SERVER, br.LEN_RE)


def _typed_events_opt(entries, line_re, size_re):
    """(t, type_or_None, size) for lines matching line_re; type OPTIONAL.
    2026-08-27 grammar drift: p2-5x-era client tape lines no longer carry
    type= (0 of 143 svc=9 rows on the p2-58 capture). Pairing degrades to the
    len-size relation instead of dying silently."""
    out = []
    for t, text in entries:
        if not line_re.search(text):
            continue
        m = br.TYPE_RE.search(text)
        n = size_re.search(text)
        out.append((t, int(m.group(1)) if m else None,
                    int(n.group(1)) if n else None))
    return out


def typed_tapes(entries):
    """Client-side svc=9 tape rows: (t, type, size); type optional since
    2026-08-27 (None when the line omits it)."""
    return _typed_events_opt(entries, br.TAPE_CLIENT, br.SIZE_RE)


def pair_size_window(pushes, tapes, size_delta=28, slack_ms=400,
                     min_pairs=5, min_distinct_sizes=5):
    """
    New-era pairing (client lines lack type=; server outnumbers client ~12:1
    because it logs pushes for every session/client). Monotone subsequence
    match: each client tape row (in time order) pairs the NEXT server push
    (in time order) whose len == size + size_delta, accepting a candidate only
    if its time delta clusters with the running median. Guards against silent
    wrong locks: the matched set must cover >= min_distinct_sizes DISTINCT
    sizes (a periodic-keepalive mislock matches mostly one size) and the final
    spread must be tight. Returns (deltas, med, spread, robust) or None.
    NOT a port of the old positional path; used only when type pairing fails.
    """
    if not pushes or not tapes:
        return None
    deltas = []
    used_sizes = set()
    j = 0
    n_p = len(pushes)
    running = None
    for t_c, _ty, s in tapes:
        if s is None:
            continue
        target = s + size_delta
        while j < n_p and pushes[j][0] < t_c:
            j += 1
        k = j
        while k < n_p:
            t_s, _ty2, ln = pushes[k]
            if ln != target:
                k += 1
                continue
            d = t_s - t_c
            if running is None or abs(d - running) <= slack_ms:
                deltas.append(d)
                used_sizes.add(s)
                running = sorted(deltas)[len(deltas) // 2]
                j = k + 1
            break
    if len(deltas) < min_pairs or len(used_sizes) < min_distinct_sizes:
        return None
    deltas.sort()
    med = deltas[len(deltas) // 2]
    if deltas[-1] - deltas[0] > 10 * slack_ms:
        return None
    robust = deltas[(9 * len(deltas)) // 10] - deltas[len(deltas) // 10]
    return deltas, med, deltas[-1] - deltas[0], robust


def align_newest_first(seq_a, seq_b, max_k=16, min_pairs=3):
    """
    Align two typed sequences newest-first (capture windows rarely start
    together), scanning tail shifts k in 0..max_k. Rows are (t, ty, n) triples.
    Pair rule per pair:
      - both types present  -> types must be equal (strict, unchanged);
      - any type missing    -> size relation: |a_n - b_n - med_delta| <= 1,
        where med_delta = median (a_n - b_n) over this k's candidate pairs
        (2026-08-27: 28 measured stable on the p2-58 capture);
      - either n missing    -> alignment fails at this k (honest null).
    Scored by robust spread (p10..p90), then smaller k, then more pairs.
    Returns (k, n_pairs, med, spread, robust, type_mode) or None, where
    type_mode is "type" or "size-only".
    """
    n_a, n_b = len(seq_a), len(seq_b)
    if n_a == 0 or n_b == 0:
        return None
    best = None
    span = min(n_a, n_b)
    for k in range(0, min(max_k + 1, span)):
        pairs = []
        deltas = []
        ok = True
        for i in range(span - k):
            a = seq_a[-(i + 1)]
            b = seq_b[-(i + 1 + k)]
            a_ty, b_ty, a_n, b_n = a[1], b[1], a[2], b[2]
            if a_n is None or b_n is None:
                ok = False
                break
            deltas.append(a_n - b_n)
            if a_ty is not None and b_ty is not None and a_ty != b_ty:
                ok = False
                break
            pairs.append(a[0] - b[0])
        if not ok or len(pairs) < min_pairs:
            continue
        deltas.sort()
        med_d = deltas[len(deltas) // 2]
        if any(abs(d - med_d) > 1 for d in deltas):
            continue  # size relation must be consistent, not roughly so
        pairs.sort()
        med = pairs[len(pairs) // 2]
        spread = pairs[-1] - pairs[0]
        robust = pairs[(9 * len(pairs)) // 10] - pairs[len(pairs) // 10]
        type_mode = ("type" if all(a[1] is not None and b[1] is not None
                                   for a, b in zip(
                                       [seq_a[-(i + 1)] for i in range(span - k)],
                                       [seq_b[-(i + 1 + k)] for i in range(span - k)]))
                     else "size-only")
        cand = (robust, k, -len(pairs), med, spread, pairs, type_mode)
        if best is None or cand[:3] < best[:3]:
            best = cand
    if best is None:
        return None
    robust, k, neg_n, med, spread, pairs, type_mode = best
    return k, -neg_n, med, spread, robust, type_mode


def size_check(pushes_by_type, tapes_by_type):
    """Secondary len=size+28 check: count matches/mismatches across aligned
    multiset intersection (per type, sorted lengths zipped). Best-effort
    reporting only; pairing validity comes from type agreement."""
    total = mismatch = 0
    for ty in sorted(set(pushes_by_type) & set(tapes_by_type)):
        lens = sorted(l for _, l in pushes_by_type[ty])
        sizes = sorted(s for _, s in tapes_by_type[ty])
        for lv, sv in zip(lens, sizes):
            total += 1
            if lv - sv != 28:
                mismatch += 1
    return total, mismatch


def _group_by_type(rows):
    out = {}
    for t, ty, n in rows:
        if n is not None:
            out.setdefault(ty, []).append((t, n))
    return out


def solve_offset(src, ref):
    """
    Estimate src's clock offset vs ref using WIRE anchors only.
    Returns (offset_ms_or_None, drift_dict). Cross-side pairs use the verified
    push<->tape family (type-equality when client lines carry type=, else the
    len=size+delta relation, delta derived per alignment); client<->client uses
    the peer tape family (weak-marked when both sides are typeless).
    """
    drift = {"source": src.ident(), "side": src.side, "n_events": len(src.entries),
             "family": None, "anchor_pairs": 0, "offset_ms": None,
             "spread_ms": None, "robust_spread_ms": None,
             "len_size_checks": None, "type_check": None,
             "status": "native_null"}
    a_rows, b_rows, family, extra = None, None, None, {}
    if src.side != ref.side:
        push_side, tape_side = (src, ref) if src.side == "server" else (ref, src)
        pushes = typed_pushes(push_side.entries)
        tapes = typed_tapes(tape_side.entries)
        if not pushes or not tapes:
            return None, drift
        family = "wire_tape_push"
        # orient rows as (non-ref minus ref); triples (t, ty, n)
        if src.side == "server":
            a_rows, b_rows = list(pushes), list(tapes)
        else:
            a_rows, b_rows = list(tapes), list(pushes)
        typeless = any(r[1] is None for r in tapes)
        extra["type_check"] = "size-only" if typeless else "type"
    elif src.side == "client" and ref.side == "client":
        ta = typed_tapes(src.entries)
        tb = typed_tapes(ref.entries)
        if not ta or not tb:
            return None, drift
        family = "wire_tape_peer"
        a_rows, b_rows = list(ta), list(tb)
        if all(r[1] is None for r in ta) and all(r[1] is None for r in tb):
            extra["type_check"] = "size-only-WEAK"
        else:
            extra["type_check"] = "type"
    else:
        return None, drift  # no verified family for this combination
    got = align_newest_first(a_rows, b_rows)
    offset = None
    if got is not None:
        k, n, med, spread, robust, type_mode = got
        drift.update({"family": family, "anchor_k_tail_skip": k,
                      "anchor_pairs": n, "offset_ms": med,
                      "spread_ms": spread, "robust_spread_ms": robust})
        offset = med
    elif family == "wire_tape_push":
        # new-era grammar: typeless client rows, ~12:1 server/client volume ->
        # positional pairing cannot apply; use the monotone size-window match.
        sw = pair_size_window(list(pushes), list(tapes),
                              size_delta=SIZE_DELTA)
        if sw is not None:
            deltas, med, spread, robust = sw
            drift.update({"family": "wire_tape_push_sizewin",
                          "anchor_pairs": len(deltas), "offset_ms": med,
                          "spread_ms": spread, "robust_spread_ms": robust,
                          "distinct_sizes": len(set(s for _, _, s in tapes
                                                    if s is not None))})
            offset = med
    if offset is None:
        drift["family"] = family
        drift.update(extra)
        return None, drift
    if drift.get("type_check") == "size-only-WEAK":
        drift["status"] = "anchored-weak"
    else:
        drift["status"] = "anchored"
    drift["type_check"] = extra.get("type_check") or (
        "size-window" if drift["family"] == "wire_tape_push_sizewin" else None)
    return offset, drift


# ---------------------------------------------------------------------------
# merge
# ---------------------------------------------------------------------------

def merge(sources, tolerance_ms=500, verbose=True, ref_ident=None):
    """Pick reference, solve every offset, emit the merged chronology."""
    if len(sources) < 2:
        raise SystemExit("ERROR: need >= 2 sources to merge (got %d)" % len(sources))
    labels = [s.ident() for s in sources]
    if len(set(labels)) != len(labels):
        raise SystemExit("ERROR: duplicate source labels: %s" % labels)
    ref = None
    if ref_ident:
        for s in sources:
            if s.ident() == ref_ident or s.label == ref_ident:
                ref = s
                break
        if ref is None:
            raise SystemExit("ERROR: reference not found: %s (have %s)"
                             % (ref_ident, labels))
    else:
        # 2026-08-27: prefer the SERVER as pivot when present. Every client
        # then anchors cross-side (push<->tape); with typeless client lines a
        # client<->client pivot would rely on weak size-only peer pairing.
        for s in sources:
            if s.side == "server":
                ref = s
                break
        if ref is None:
            for s in sources:
                if s.side == "client":
                    ref = s
                    break
        if ref is None:
            ref = sources[0]
    drifts = [{"source": ref.ident(), "side": ref.side, "n_events": len(ref.entries),
               "family": "reference", "anchor_pairs": 0, "offset_ms": 0,
               "spread_ms": None, "robust_spread_ms": None,
               "len_size_checks": None, "status": "reference"}]
    for s in sources:
        if s is ref:
            continue
        off, drift = solve_offset(s, ref)
        s.offset_ms = off
        s.anchor = drift
        drifts.append(drift)
        if verbose:
            print("drift   : %-24s %-8s offset=%s pairs=%s family=%s status=%s"
                  % (drift["source"], drift["side"],
                     off if off is not None else "none",
                     drift["anchor_pairs"], drift["family"], drift["status"]))
    rows = []
    for idx, s in enumerate(sources):
        off = s.offset_ms or 0
        for j, (t, raw) in enumerate(s.entries):
            kv, ok = br.parse_line(raw)
            rows.append({
                "unified_t_ms": t - off,
                "source": s.label,
                "side": s.side,
                "ev": kv.get("ev"),
                "stage": kv.get("stage"),
                "result": kv.get("result"),
                "t_native": t,
                "seq": j,
                "kv": {k: v for k, v in kv.items() if k not in ("src",)},
                "raw": raw,
                "_idx": idx,
            })
    rows.sort(key=lambda r: (r["unified_t_ms"], r["_idx"], r["seq"]))
    unparsed = [{"source": s.ident(), "raw": r}
                for s in sources for r in s.unparsed]
    return {"reference": ref.ident(), "rows": rows, "drift": drifts,
            "unparsed": unparsed, "tolerance_ms": tolerance_ms}


def write_outputs(merged, prefix):
    tsv = prefix + ".tsv"
    jsonl = prefix + ".jsonl"
    driftj = prefix + ".drift.json"
    with open(tsv, "w", encoding="utf-8") as fh:
        fh.write("unified_t_ms\tsource\tside\tev\tstage\tresult\tt_native\traw\n")
        for r in merged["rows"]:
            raw = r["raw"].replace("\t", " ").replace("\n", " ")
            fh.write("%d\t%s\t%s\t%s\t%s\t%s\t%d\t%s\n" % (
                r["unified_t_ms"], r["source"], r["side"] or "",
                r["ev"] or "", r["stage"] or "", r["result"] or "",
                r["t_native"], raw))
    with open(jsonl, "w", encoding="utf-8") as fh:
        for r in merged["rows"]:
            out = dict(r)
            out.pop("_idx", None)
            out.pop("seq", None)
            fh.write(json.dumps(out, sort_keys=True) + "\n")
    with open(driftj, "w", encoding="utf-8") as fh:
        json.dump({"generated_iso": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                   "reference": merged["reference"],
                   "tolerance_ms": merged["tolerance_ms"],
                   "sources": merged["drift"],
                   "rows_merged": len(merged["rows"]),
                   "rows_unparsed_kept": len(merged["unparsed"])},
                  fh, indent=2, sort_keys=True)
    return tsv, jsonl, driftj


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

BRIEF_FIXTURE = """# BOOT BRIEF (merge_timeline selftest fixture)

## Purpose/Payoff
Produce a real recorder-shaped events store from synthetic logs so the
merger's --record input path consumes genuine records unchanged.

## Falsifiable Claim
Recorder exit 0; store parses; merger recovers planted offsets from it.

## Does NOT test
Live tailing, rotation, real wine/game processes.

## GRAPHICS DELTA
None (synthetic logs, no renderer).
"""


def make_fixtures(out_dir, seed=20260823, notype=False):
    """
    Generate fake server log + two fake client logs with KNOWN planted skews
    (server +5300 ms, client2 -2000 ms relative to client1) and ~12 shared
    wire moments (activity push <-> tape svc9), plus same-name decoy events at
    DIFFERENT true instants (the cross-process trap) and per-client gaps.
    Ground truth JSON lands next to the logs.
    """
    rng = random.Random(seed)
    os.makedirs(out_dir, exist_ok=True)
    srv_skew, c1_skew, c2_skew = 5300, 0, -2000
    skews = {"srv": srv_skew, "cli1": c1_skew, "cli2": c2_skew}

    def stamp(true_t, skew, jitter_max=25):
        return true_t + skew + rng.randint(-jitter_max, jitter_max)

    lines = {"srv": [], "cli1": [], "cli2": []}
    truth = []  # {id, source_key, true_t, native_t, kind}

    def add(src_key, true_t, body, kind="solo", eid=None):
        """body = everything AFTER 'src level=<lvl> t='."""
        t_native = stamp(true_t, skews[src_key])
        text = "%s level=info t=%d %s" % (SRC_TAG[src_key], t_native, body)
        lines[src_key].append(text)
        if eid:
            truth.append({"id": eid, "source": src_key, "true_t": true_t,
                          "native_t": t_native, "kind": kind})
        return t_native

    SRC_TAG = {"srv": "server", "cli1": "client", "cli2": "client"}
    LVL = {"srv": "info", "cli1": "info", "cli2": "info"}

    # --- independent boots at different TRUE moments (the trap material) ----
    add("srv", 0, "ev=persistence stage=initialize result=ok", eid="S_boot")
    add("srv", 40, "ev=https stage=listen result=ok port=8443", eid="S_https")
    add("srv", 80, "ev=transport stage=listen result=ok port=30975",
        eid="S_listen")
    add("srv", 120, "ev=initialize result=ok", eid="S_init")   # decoy name
    add("cli1", 30000, "core ev=initialize result=ok", eid="C1_init")
    add("cli1", 30350, "ev=graphics stage=probe result=ok driver=warp level=0xB000",
        eid="C1_gfx")
    add("cli2", 61000, "core ev=initialize result=ok", eid="C2_init")
    add("cli2", 61400, "ev=steam_init result=ok", eid="C2_steam")

    # transport accepts: one per client, distinct conn ids (marker rows, NOT
    # anchors -- no verified client counterpart exists)
    add("srv", 32000, "ev=transport stage=accept result=ok conn=1", eid="S_acc1")
    add("srv", 62500, "ev=transport stage=accept result=ok conn=2", eid="S_acc2")

    # --- shared wire moments: activity push <-> tape svc=9 ------------------
    types = [1, 4, 0, 1, 4, 1, 0, 4, 1, 4, 0, 1]  # repeats exercise ambiguity
    t_true = 40000
    last = len(types) - 1
    for i, ty in enumerate(types):
        t_true += rng.randint(900, 2600)
        size = rng.randrange(120, 1400)
        eid = "W%02d" % i
        add("srv", t_true,
            "ev=activity stage=push result=ok type=%d soid=0x9EAA300100200001 "
            "body=%d len=%d" % (ty, size - 45, size + 28), kind="wire", eid=eid)
        ty_txt = "" if notype else " type=%d" % ty
        add("cli1", t_true + 12,  # small wire latency, inside jitter budget
            "ev=handle_message stage=push tape=1 dir=down svc=9 "
            "service=activity_message session=1 size=%d result=ok accepted=1 "
            "elapsed=0%s msg=fxt_%s" % (size, ty_txt, eid),
            kind="wire", eid=eid + ".c1")
        if 2 <= i < last:  # joins late; capture also ends one push early
            add("cli2", t_true + 18,
                "ev=handle_message stage=push tape=1 dir=down svc=9 "
                "service=activity_message session=1 size=%d result=ok accepted=1 "
                "elapsed=0%s msg=fxt_%s" % (size, ty_txt, eid),
                kind="wire", eid=eid + ".c2")

    # --- same-name core decoys AFTER the wires (order stress) ---------------
    add("srv", t_true + 5000, "ev=queuez stage=banner_refresh result=ok",
        eid="S_banner")
    add("cli1", t_true + 5100,
        "ev=queuez stage=family0_list first=0xCAFE/7", eid="C1_fam")
    add("cli2", t_true + 5200,
        "ev=queuez stage=family0_list first=0xCAFE/7", eid="C2_fam")

    # one grammar-violating line each (must be preserved as unparsed)
    lines["srv"].append("server level=info ev=no_t_line garbage\x00tail")
    lines["cli1"].append("core level=info ev=no_t_smoke phase=fixture")

    paths = {}
    for key, name in (("srv", "server.log"), ("cli1", "client1.log"),
                      ("cli2", "client2.log")):
        p = os.path.join(out_dir, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines[key]) + "\n")
        paths[key] = p
    ground = {
        "seed": seed,
        "skews_ms": skews,           # native = true + skew (+ jitter <=25 ms)
        "jitter_max_ms": 25,
        "paths": paths,
        "events": truth,
    }
    gpath = os.path.join(out_dir, "ground_truth.json")
    with open(gpath, "w", encoding="utf-8") as fh:
        json.dump(ground, fh, indent=2, sort_keys=True)
    return paths, gpath


# ---------------------------------------------------------------------------
# fixture verification
# ---------------------------------------------------------------------------

def verify_fixture(out_dir, tol_order=500, tol_off=100, verbose=True,
                   ref_ident=None):
    """
    Merge the fixture logs in-process and ASSERT against ground truth:
      1. recovered offsets within tol_off of planted skews;
      2. each shared wire moment unifies across all copies within tol_off;
      3. global ordering: ground-truth pairs >= tol_order apart never invert;
      4. unparsed fixture lines preserved.
    Returns (n_failures, summary_dict).
    """
    fails = []

    def check(name, cond, detail=""):
        if verbose:
            print("%s %-52s %s" % ("PASS" if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    with open(os.path.join(out_dir, "ground_truth.json")) as fh:
        gt = json.load(fh)
    paths = gt["paths"]
    sources = [
        parse_log_file("server", "srv", paths["srv"]),
        parse_log_file("client", "cli1", paths["cli1"]),
        parse_log_file("client", "cli2", paths["cli2"]),
    ]
    m = merge(sources, verbose=False, ref_ident=ref_ident)
    drift = {d["source"]: d for d in m["drift"]}  # keys are ident(): label/side

    # ---- 1. offsets --------------------------------------------------------
    for key, ident in (("srv", "srv/server"), ("cli2", "cli2/client")):
        d = drift.get(ident)
        want = gt["skews_ms"][key]
        got = d.get("offset_ms") if d else None
        check("offset %s ~= planted %+d ms" % (key, want),
              got is not None and abs(got - want) <= tol_off,
              "got=%s (want %+d +/- %d)" % (got, want, tol_off))
    check("reference cli1 offset == 0",
          drift.get("cli1/client", {}).get("offset_ms") == 0, "")
    check("server anchored via wire_tape_push",
          drift.get("srv/server", {}).get("family") == "wire_tape_push" and
          drift.get("srv/server", {}).get("status") == "anchored",
          str(drift.get("srv/server", {}).get("family")))
    check("client2 anchored via wire_tape_peer (late joiner, k>0)",
          drift.get("cli2/client", {}).get("family") == "wire_tape_peer" and
          drift.get("cli2/client", {}).get("anchor_k_tail_skip", 0) >= 1,
          "k=%s" % drift.get("cli2/client", {}).get("anchor_k_tail_skip"))

    # ---- 2. wire-moment unification (via actual merged rows) ---------------
    by_id = {}
    for e in gt["events"]:
        if e["kind"] == "wire":
            by_id.setdefault(e["id"].split(".")[0], {})[e["source"]] = e
    uni = {}
    for r in m["rows"]:
        uni[(r["source"], r["t_native"])] = r["unified_t_ms"]
    worst = 0
    missing = 0
    for wid in sorted(by_id):
        unified = []
        for key, e in by_id[wid].items():
            u = uni.get((key, e["native_t"]))
            if u is None:
                missing += 1
                continue
            unified.append(u)
        if len(unified) >= 2:
            span = max(unified) - min(unified)
            worst = max(worst, span)
    check("all wire copies present in merged rows", missing == 0,
          "missing=%d" % missing)
    check("every shared wire moment unifies within 100 ms", worst <= 100,
          "worst span=%d ms" % worst)

    # ---- 3. global ordering -------------------------------------------------
    gt_sorted = sorted(gt["events"], key=lambda e: e["true_t"])
    inversions = 0
    compared = 0
    for i in range(len(gt_sorted)):
        for j in range(i + 1, len(gt_sorted)):
            ea, eb = gt_sorted[i], gt_sorted[j]
            gap = eb["true_t"] - ea["true_t"]
            if gap < tol_order:
                continue
            ta = uni.get((ea["source"], ea["native_t"]))
            tb = uni.get((eb["source"], eb["native_t"]))
            if ta is None or tb is None:
                continue
            compared += 1
            if ta > tb:
                inversions += 1
    check("global ordering: 0 inversions (%d far-apart pairs compared)"
          % compared, inversions == 0, "inversions=%d" % inversions)

    # ---- 4. unparsed preserved ---------------------------------------------
    n_unparsed = sum(len(s.unparsed) for s in sources)
    check("grammar-violating fixture lines preserved", n_unparsed == 2,
          "found=%d" % n_unparsed)
    return len(fails), {
        "failures": fails, "drift": m["drift"],
        "rows_merged": len(m["rows"]), "ordering_compared": compared,
        "worst_wire_span_ms": worst,
    }


# ---------------------------------------------------------------------------
# selftest (fixture round trip + record-store integration + honesty control)
# ---------------------------------------------------------------------------

def run_recorder(server_log, client_log, out_root, label):
    import subprocess
    brief = os.path.join(out_root, "brief_selftest.md")
    with open(brief, "w") as fh:
        fh.write(BRIEF_FIXTURE)
    cmd = ["/usr/bin/python3",
           os.path.join(ROOT, "RE_scripts", "boot_record.py"),
           "--brief", brief, "--out", out_root, "--label", label,
           "--server-log", server_log, "--client-log", client_log,
           "--from-files"]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    dirs = [d for d in os.listdir(out_root) if label in d and
            os.path.isdir(os.path.join(out_root, d))]
    return p.returncode, (p.stdout + p.stderr)[-400:], dirs


def selftest():
    fails = []

    def check(name, cond, detail=""):
        print("%s %-52s %s" % ("PASS" if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    scratch = DEFAULT_SCRATCH
    print("== fixtures under %s ==" % scratch)
    paths, gpath = make_fixtures(scratch)
    print("fixtures: %s (+ %s)" % (sorted(paths.values()), gpath))

    # ---- A. in-process fixture verification --------------------------------
    print("== A. merge fixture logs, assert vs ground truth ==")
    n, summary = verify_fixture(scratch, ref_ident="cli1")
    fails.extend(summary["failures"])

    # ---- B. record-store integration (real boot_record output consumed) ----
    print("== B. consume a REAL recorder store (--record path) ==")
    rec_root = os.path.join(scratch, "records")
    os.makedirs(rec_root, exist_ok=True)
    rc, tail, dirs = run_recorder(paths["srv"], paths["cli1"], rec_root,
                                  "mt_int")
    check("recorder accepted fixture logs (exit 0)", rc == 0, tail.strip())
    if dirs:
        rec_dir = os.path.join(rec_root, sorted(dirs)[0])
        srcs = load_record_store("recA", rec_dir)
        check("record store yields server+client sources",
              sorted(s.side for s in srcs) == ["client", "server"],
              str([(s.label, s.side, len(s.entries)) for s in srcs]))
        cli2_src = parse_log_file("client", "cli2x", paths["cli2"])
        m = merge(list(srcs) + [cli2_src], verbose=False)
        dm = {d["source"]: d for d in m["drift"]}
        got_srv = dm.get("recA/server", {}).get("offset_ms")
        got_c2 = dm.get("cli2x/client", {}).get("offset_ms")
        check("record-sourced server is the pivot (offset 0)",
              got_srv is not None and got_srv == 0 and
              dm.get("recA/server", {}).get("status") == "reference",
              "got=%s" % got_srv)
        # server pivot: cli2 offset = skew(cli2) - skew(srv) = -7300-ish
        check("mixed record+log client2 offset ~= -7300",
              got_c2 is not None and abs(got_c2 + 7300) <= 100,
              "got=%s" % got_c2)
    else:
        check("recorder produced a record dir", False, tail.strip())

    # ---- C. honesty control: strip all wire anchors -> native_null ---------
    print("== C. no-anchor honesty control ==")
    stripped_dir = os.path.join(scratch, "stripped")
    os.makedirs(stripped_dir, exist_ok=True)
    stripped = {}
    for key, name in (("srv", "server.log"), ("cli1", "client1.log"),
                      ("cli2", "client2.log")):
        with open(paths[key]) as fh:
            txt = "".join(l for l in fh if not (br.TAPE_SERVER.search(l) or
                                                br.TAPE_CLIENT.search(l)))
        p = os.path.join(stripped_dir, name)
        with open(p, "w") as fh:
            fh.write(txt)
        stripped[key] = p
    s_sources = [parse_log_file("server", "srv", stripped["srv"]),
                 parse_log_file("client", "cli1", stripped["cli1"]),
                 parse_log_file("client", "cli2", stripped["cli2"])]
    ms = merge(s_sources, verbose=False)
    ds = {d["source"]: d for d in ms["drift"]}
    # 2026-08-27: with the server pivot, srv/server is the REFERENCE (offset 0
    # by definition, not a guess); the honesty property is that cli2 - which
    # cannot anchor - stays native_null with NO guessed offset.
    check("no anchors -> pivot=reference, cli2=native_null (no guessed offset)",
          ds["srv/server"]["status"] == "reference" and
          ds["cli2/client"]["status"] == "native_null" and
          ds["cli2/client"]["offset_ms"] is None,
          str({k: (ds[k]["status"], ds[k]["offset_ms"])
               for k in ("srv/server", "cli2/client")}))

    # ---- D. output writers smoke -------------------------------------------
    print("== D. output files ==")
    sources = [parse_log_file("server", "srv", paths["srv"]),
               parse_log_file("client", "cli1", paths["cli1"]),
               parse_log_file("client", "cli2", paths["cli2"])]
    m = merge(sources, verbose=False, ref_ident="cli1")
    tsv, jsonl, driftj = write_outputs(
        m, os.path.join(scratch, "merged_timeline"))
    n_tsv = sum(1 for _ in open(tsv)) - 1
    n_jsonl = sum(1 for _ in open(jsonl))
    with open(driftj) as fh:
        dj = json.load(fh)
    check("tsv rowcount == jsonl rowcount == merged rows",
          n_tsv == n_jsonl == len(m["rows"]),
          "tsv=%d jsonl=%d rows=%d" % (n_tsv, n_jsonl, len(m["rows"])))
    check("drift.json carries 3 sources + reference",
          len(dj["sources"]) == 3 and dj["reference"] == "cli1/client",
          dj["reference"])

    # ---- E. 2026-08-27: typeless client lines + server pivot ---------------
    # p2-5x-era client tape lines omit type=; pairing must degrade to the
    # len=size+delta relation and the pivot defaults to the server, so every
    # client anchors cross-side (no weak client<->client size-only pairing).
    tol_off = 100
    print("== E. typeless-client fixtures (server pivot) ==")
    scratch_nt = scratch + "_notype"
    paths_nt, gpath_nt = make_fixtures(scratch_nt, notype=True)
    with open(gpath_nt) as fh:
        gt_nt = json.load(fh)
    skews = gt_nt["skews_ms"]
    sources_nt = [
        parse_log_file("server", "srv", paths_nt["srv"]),
        parse_log_file("client", "cli1", paths_nt["cli1"]),
        parse_log_file("client", "cli2", paths_nt["cli2"]),
    ]
    m_nt = merge(sources_nt, verbose=False)  # default pivot = server now
    d_nt = {d["source"]: d for d in m_nt["drift"]}
    check("server is the reference pivot",
          m_nt["reference"] == "srv/server", m_nt["reference"])
    check("cli1 offset ~= skew(cli1)-skew(srv)",
          d_nt["cli1/client"]["offset_ms"] is not None and
          abs(d_nt["cli1/client"]["offset_ms"] -
              (skews["cli1"] - skews["srv"])) <= tol_off,
          "got=%s want=%+d" % (d_nt["cli1/client"]["offset_ms"],
                               skews["cli1"] - skews["srv"]))
    check("cli2 offset ~= skew(cli2)-skew(srv)",
          d_nt["cli2/client"]["offset_ms"] is not None and
          abs(d_nt["cli2/client"]["offset_ms"] -
              (skews["cli2"] - skews["srv"])) <= tol_off,
          "got=%s want=%+d" % (d_nt["cli2/client"]["offset_ms"],
                               skews["cli2"] - skews["srv"]))
    check("cross-side pairing flagged size-only (not weak)",
          d_nt["cli1/client"].get("type_check") == "size-only" and
          d_nt["cli1/client"]["status"] == "anchored",
          "%s/%s" % (d_nt["cli1/client"].get("type_check"),
                     d_nt["cli1/client"]["status"]))

    print("-" * 72)
    if fails:
        print("SELFTEST FAILURES: %d" % len(fails))
        for f in fails:
            print("  - %s" % f)
        return 1
    print("SELFTEST PASS (%s)" % time.strftime("%Y-%m-%d %H:%M:%S"))
    return 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="N-sided anchor-corrected timeline merger.")
    ap.add_argument("--server-log", action="append", default=[],
                    metavar="[LABEL=]PATH")
    ap.add_argument("--client-log", action="append", default=[],
                    metavar="[LABEL=]PATH")
    ap.add_argument("--record", action="append", default=[],
                    metavar="[LABEL=]DIR")
    ap.add_argument("--reference", default=None)
    ap.add_argument("--size-delta", type=int, default=28,
                    help="len(server)-size(client) envelope delta "
                         "(measured 28 on p2-58; override if grammar drifts)")
    ap.add_argument("--out", default=None, help="output file prefix")
    ap.add_argument("--tolerance-ms", type=int, default=500)
    ap.add_argument("--make-fixtures", metavar="DIR")
    ap.add_argument("--verify-fixtures", metavar="DIR")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    global SIZE_DELTA
    SIZE_DELTA = args.size_delta

    if args.make_fixtures:
        paths, gpath = make_fixtures(args.make_fixtures)
        print("fixtures written:")
        for k in sorted(paths):
            print("  %-5s %s" % (k, paths[k]))
        print("  truth %s" % gpath)
        print("next: --verify-fixtures %s" % args.make_fixtures)
        return 0

    if args.verify_fixtures:
        n, summary = verify_fixture(args.verify_fixtures)
        print("VERDICT: %s (%d failure(s), %d rows merged, %d order pairs)"
              % ("PASS" if n == 0 else "FAIL", n, summary["rows_merged"],
                 summary["ordering_compared"]))
        return 0 if n == 0 else 1

    if args.selftest:
        return selftest()

    sources = []
    for i, spec in enumerate(args.server_log):
        label, path = split_label(spec, "server%d" % (i + 1))
        sources.append(parse_log_file("server", label, path))
    for i, spec in enumerate(args.client_log):
        label, path = split_label(spec, "client%d" % (i + 1))
        sources.append(parse_log_file("client", label, path))
    for i, spec in enumerate(args.record):
        label, path = split_label(spec, "rec%d" % (i + 1))
        sources.extend(load_record_store(label, path))
    if len(sources) < 2:
        ap.error("need >= 2 sources: --server-log/--client-log/--record")
    if args.reference:
        merged = merge(sources, ref_ident=args.reference)
    else:
        merged = merge(sources)
    print("merged  : %d rows from %d sources; reference=%s"
          % (len(merged["rows"]), len(sources), merged["reference"]))
    if args.out:
        tsv, jsonl, driftj = write_outputs(merged, args.out)
        print("wrote   : %s" % tsv)
        print("          %s" % jsonl)
        print("          %s" % driftj)
    else:
        print("(pass --out PREFIX to write .tsv/.jsonl/.drift.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
