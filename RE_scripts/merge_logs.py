#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_logs.py — offline merge of the Sunrise server+client logs onto ONE
client-relative clock.

Both logs carry t=<ms since process start>; the server starts first, so the
same real moment differs by one constant offset (both clocks derive from the
same system tick).  Offset = median(server_t - client_t) over anchor pairs
matched in order — PRIMARY: client ev=ability_gate stage=emit_2100 hash=0x...
<-> server ev=queuez stage=ability_change result=fail step=mutate; SANITY:
client stage=family0_list first=0x.../N version bumps <-> server
stage=banner_refresh result=ok.  The server log can span several client
sessions, so the Nth client anchor may pair with the (N+k)th server anchor:
k is chosen so the per-pair deltas cluster most tightly (min spread).

Unified clock = CLIENT-relative: client lines keep their t; server lines get
t - offset.  Earlier-session server lines therefore carry NEGATIVE unified
times (pre-client history) and appear first.  Output:
RE_output\\content\\merged\\merged_<YYYYmmdd_HHMMSS>.log as
"[SERVER] t=<unified> (t=<native>) <original line VERBATIM>".  Two-way merge
of the internally-sorted streams (no full sort).  Pure stdlib; read-only
inputs.  Usage: python -X utf8 RE_scripts\\merge_logs.py [--server PATH]
[--client PATH]
"""

import argparse
import datetime
import os
import re
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SERVER = os.path.join(ROOT, "RE_output", "s1_accept", "Sunrise", "logs", "sunrise.log")
DEFAULT_CLIENT = os.path.join(ROOT, "dcv build", "bin", "x64", "Sunrise", "logs", "sunrise.log")
OUT_DIR = os.path.join(ROOT, "RE_output", "content", "merged")

T_RE = re.compile(r"(?:^|\s)t=(\d+)")                    # t= is field 3 in every log line
PRIMARY_CLIENT = re.compile(r"ev=ability_gate.*stage=emit_2100")
PRIMARY_SERVER = re.compile(r"ev=queuez.*stage=ability_change.*result=fail.*step=mutate")
SANITY_CLIENT = re.compile(r"ev=queuez.*stage=family0_list.*first=0x[0-9A-Fa-f]+/\d+")
SANITY_SERVER = re.compile(r"ev=queuez.*stage=banner_refresh.*result=ok")
VER_RE = re.compile(r"first=0x[0-9A-Fa-f]+/(\d+)")

TIGHT_MS = 500   # a pairing is "tight" when its per-pair deltas span <= this


def read_log(path, label):
    """Read one log into [(t, original_text), ...] in file order.  Lines
    without a parseable t= are counted and skipped; a missing or unreadable
    (locked) file exits with a clear message."""
    if not os.path.exists(path):
        sys.exit("ERROR: %s log not found: %s" % (label, path))
    entries, n_no_t = [], 0
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as fh:
            for line in fh:
                text = line.rstrip("\r\n")          # content verbatim; terminator re-added on write
                m = T_RE.search(text)
                if not m:
                    n_no_t += 1
                    continue
                entries.append((int(m.group(1)), text))
    except OSError as exc:
        sys.exit("ERROR: cannot read %s log %s: %s (locked by a live process?)" % (label, path, exc))
    if not entries:
        sys.exit("ERROR: %s log %s is empty or has no t= lines" % (label, path))
    return entries, n_no_t


def best_shift(client_ts, server_ts):
    """Pair client anchor i with server anchor i+k; return
    (k, pairs, median_delta, spread) for the tightest-delta k (min spread,
    then max pairs, then min k).  Degenerate (<2 pairable anchors): the k=0
    pairing with spread 0 — the caller warns."""
    n, m = len(client_ts), len(server_ts)
    best = None
    for k in range(-(n - 1), m):
        pairs = [(client_ts[i], server_ts[i + k], server_ts[i + k] - client_ts[i])
                 for i in range(n) if 0 <= i + k < m]
        if len(pairs) < 2:
            continue
        deltas = [p[2] for p in pairs]
        cand = (max(deltas) - min(deltas), -len(pairs), k, pairs)
        if best is None or cand[:3] < best[:3]:
            best = cand
    if best is None:
        k = 0
        pairs = [(client_ts[i], server_ts[i], server_ts[i] - client_ts[i])
                 for i in range(min(n, m))]
        if not pairs:
            return None
        return k, pairs, pairs[0][2], 0
    spread, _, k, pairs = best
    med = statistics.median(p[2] for p in pairs)
    return k, pairs, med, spread


def two_way_merge(server_entries, client_entries, shift):
    """Two-way merge of the internally-sorted streams on the unified clock
    (server unified = native + shift; client = native).  Ties go server-first
    (deterministic).  Returns (out_lines, n_inversions); per-stream disorder
    shows up as local inversions, never a re-sort."""
    out, si, ci, last_u, n_inv = [], 0, 0, None, 0
    while si < len(server_entries) or ci < len(client_entries):
        if ci >= len(client_entries):
            take_server = True
        elif si >= len(server_entries):
            take_server = False
        else:
            take_server = (server_entries[si][0] + shift) <= client_entries[ci][0]
        if take_server:
            native, text = server_entries[si]
            side, unified, si = "SERVER", native + shift, si + 1
        else:
            native, text = client_entries[ci]
            side, unified, ci = "CLIENT", native, ci + 1
        out.append("[%s] t=%d (t=%d) %s" % (side, unified, native, text))
        if last_u is not None and unified < last_u:
            n_inv += 1
        last_u = unified
    return out, n_inv


def main():
    ap = argparse.ArgumentParser(
        description="Merge the Sunrise server+client logs onto one client-relative clock.")
    ap.add_argument("--server", default=DEFAULT_SERVER, help="server log path")
    ap.add_argument("--client", default=DEFAULT_CLIENT, help="client log path")
    args = ap.parse_args()

    server, s_no_t = read_log(args.server, "server")
    client, c_no_t = read_log(args.client, "client")

    # ---- primary anchor: emit_2100 <-> ability_change ----
    prim_c = [t for t, text in client if PRIMARY_CLIENT.search(text)]
    prim_s = [t for t, text in server if PRIMARY_SERVER.search(text)]
    if not prim_c or not prim_s:
        sys.exit("ERROR: no primary anchor lines found "
                 "(client emit_2100=%d, server ability_change=%d) — cannot compute the offset"
                 % (len(prim_c), len(prim_s)))
    pk, ppairs, pmed, pspread = best_shift(prim_c, prim_s)
    offset = pmed  # median(server_t - client_t); positive: server started first
    shift = -offset

    # ---- sanity anchor: family0_list version bumps <-> banner_refresh ----
    san_c, prev_ver = [], None
    for t, text in client:
        if SANITY_CLIENT.search(text):
            v = int(VER_RE.search(text).group(1))
            if v != prev_ver:          # a version bump (dedupe repeats)
                san_c.append(t)
            prev_ver = v
    san_s = [t for t, text in server if SANITY_SERVER.search(text)]
    if san_c and san_s:
        sk, spairs, smed, sspread = best_shift(san_c, san_s)
    else:
        sk, spairs, smed, sspread = None, [], None, None

    # ---- merge + write ----
    merged, n_inv = two_way_merge(server, client, shift)
    n_pre = sum(1 for t, _ in server if t + shift < 0)   # pre-client server history
    out_path = os.path.abspath(os.path.join(
        OUT_DIR, "merged_%s.log" % datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(merged) + "\n")

    # ---- summary ----
    print("server log : %s" % args.server)
    print("client log : %s" % args.client)
    print("lines      : server %d (%d without t=)  client %d (%d without t=)"
          % (len(server), s_no_t, len(client), c_no_t))
    print("PRIMARY anchor (emit_2100 <-> ability_change): client=%d server=%d"
          " shift k=%d pairs=%d median(server_t-client_t)=%d ms spread=%d ms"
          % (len(prim_c), len(prim_s), pk, len(ppairs), pmed, pspread))
    if len(ppairs) < 2:
        print("  WARNING: single anchor pair — offset from one pair only")
    elif pspread > TIGHT_MS:
        print("  WARNING: anchor deltas span %d ms (>%d) — offset is approximate" % (pspread, TIGHT_MS))
    if spairs:
        print("SANITY anchor (family0_list bumps <-> banner_refresh): client=%d server=%d"
              " shift k=%s pairs=%d median=%s ms spread=%s ms"
              % (len(san_c), len(san_s), sk, len(spairs), smed, sspread))
        if len(spairs) >= 2 and sspread <= TIGHT_MS and abs(smed - offset) <= TIGHT_MS:
            print("  -> confirms the primary offset")
        else:
            print("  -> NOT 1:1/tight in this capture; the primary anchor carries the offset")
    else:
        print("SANITY anchor : no family0_list/banner_refresh lines found; primary carries the offset")
    print("offset     : median(server_t - client_t) = %d ms; server unified = t - %d" % (offset, offset))
    print("merged     : %s" % out_path)
    print("  %d lines (%d server + %d client); %d server lines at unified t<0 = pre-client history;"
          " %d local out-of-order inversions tolerated" % (len(merged), len(server), len(client), n_pre, n_inv))


if __name__ == "__main__":
    main()
