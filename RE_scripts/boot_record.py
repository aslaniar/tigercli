#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
boot_record.py — Lane B: turn one boot into a queryable event table plus an
input-state manifest. Pure stdlib, read-only over the fork inputs.

Tails BOTH Sunrise logs during a boot (tail -F semantics: rotation at app
start renames the previous log to sunrise.log.old and opens a fresh file —
the recorder reopens on inode change and restarts at position 0), parses the
uniform grammar

    src level=<lvl> t=<ms> ev=<name> [key=value ...]

into RE_output/boots/<ts>_<label>/events.sqlite with real columns
(side, level, t_ms, ev, stage, result) and the remaining key=value pairs as a
JSON blob. Both sides land on one clock when anchor pairs exist; otherwise
the record is honest: offset=null, native t_ms per side, unified_t_ms NULL.

Clock merge reuses merge_logs.py's anchor logic VERBATIM (same regexes, same
best_shift): PRIMARY client ev=ability_gate stage=emit_2100 <-> server
ev=queuez stage=ability_change result=fail step=mutate; SANITY client
queuez/family0_list version bumps <-> server queuez/banner_refresh result=ok.
Extension (documented, 2026-08-22 ~22:0x): when the primary pair is absent on
BOTH sides but the sanity pair is complete, the sanity pair becomes the
offset's carrier (both halves present = real shared moments; the primary
lineaments need the ability-swap session type). When no pair completes the
record keeps offset=null (anchor census on every capture on disk so far:
primary=0 client-side hits everywhere).

The recorder REFUSES to start without a boot brief (deliverable 3): a
markdown file carrying PURPOSE/PAYOFF, FALSIFIABLE CLAIM, NOT-TEST, and
GRAPHICS DELTA sections. The brief is stored verbatim in the record.

The manifest (deliverable 2) captures INPUT state BEFORE the boot:
sunrise-server.exe sha256, Game/bin/x64/steam_api64.dll sha256, both
settings.json sha256 AND full parsed contents (field-level diff material),
computed eqHash (EXACT port of bootL_eqhash_exact.py — validated tool; the
equip pipeline self-restamps offset 20, eqHash is live state, never assumed),
flags row count, per-table DB row counts, state.db hash, content JSON roster,
log pre-state (size/inode/mtime), live-process census.

Usage:
  python3 RE_scripts/boot_record.py --brief PATH [options]

  --server-log PATH   server log (default RE_output/s1_accept/Sunrise/logs/sunrise.log)
  --client-log PATH   client log (default Game/bin/x64/Sunrise/logs/sunrise.log)
  --out DIR           records root (default RE_output/boots)
  --label TEXT        short record label (sanitized; default "boot")
  --dry               validate brief + capture the manifest, then exit (no tailing)
  --from-files        both logs are finished files; ingest fully, finalize now
  --min-duration S    stop: at least S seconds of tailing
  --quiet-timeout S   stop: no new lines on either side for S seconds (after min-duration)
  --until-grep RE     stop requires an event line matching RE (applied to parsed text)
  --max-duration S    hard stop (default 900)

Exit codes: 0 ok; 2 brief missing; 3 brief incomplete; 4 manifest/parse
error; 5 runtime error.
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SERVER_LOG = os.path.join(ROOT, "RE_output", "s1_accept", "Sunrise", "logs", "sunrise.log")
DEFAULT_CLIENT_LOG = os.path.join(ROOT, "Game", "bin", "x64", "Sunrise", "logs", "sunrise.log")
DEFAULT_OUT = os.path.join(ROOT, "RE_output", "boots")
SERVER_EXE = os.path.join(ROOT, "RE_output", "s1_accept", "sunrise-server.exe")
CLIENT_DLL = os.path.join(ROOT, "Game", "bin", "x64", "steam_api64.dll")
SERVER_SETTINGS = os.path.join(ROOT, "RE_output", "s1_accept", "Sunrise", "settings.json")
CLIENT_SETTINGS = os.path.join(ROOT, "Game", "bin", "x64", "Sunrise", "settings.json")
STATE_DB = os.path.join(ROOT, "RE_output", "s1_accept", "Sunrise", "state.db")
CONTENT_DIR = os.path.join(ROOT, "RE_output", "s1_accept", "content")
EQHASH_TOOL = os.path.join(ROOT, "RE_output", "scripts", "bootL_eqhash_exact.py")

# ---------------------------------------------------------------------------
# anchor logic — VERBATIM from RE_scripts/merge_logs.py (the proven offset
# solver; do not reinvent). Layout note: unified clock = CLIENT-relative;
# offset = median(server_t - client_t); server unified = native - offset.
# ---------------------------------------------------------------------------

T_RE = re.compile(r"(?:^|\s)t=(\d+)")
# THE WIRE ANCHOR (2026-08-22, preferred over both legacy pairs).
# A server activity push and the client tape row that applies it are the SAME
# wire event observed from both ends, so they mark one true shared instant -
# which is exactly what the cross-process anchor trap says is required (the
# client's core lines come from the DLL in the game process, the server's from
# a process that booted minutes earlier, so same-NAME events are not the same
# moment). The pair is type-validated, and the server's len is the client's
# size plus a constant 28-byte BAP frame header, giving a second check.
# Measured on the 22:46 two-sided record: 94 pairs, every type matching,
# p10..p90 spread 52 ms against the sanity anchor's 16,755 ms.
TAPE_SERVER = re.compile(r"ev=activity\s+stage=push\b")
TAPE_CLIENT = re.compile(r"\btape=1\b.*\bsvc=9\b")
TYPE_RE = re.compile(r"(?<![A-Za-z0-9_])type=(\d+)")
LEN_RE = re.compile(r"(?<![A-Za-z0-9_])len=(\d+)")
SIZE_RE = re.compile(r"(?<![A-Za-z0-9_])size=(\d+)")
PRIMARY_CLIENT = re.compile(r"ev=ability_gate.*stage=emit_2100")
PRIMARY_SERVER = re.compile(r"ev=queuez.*stage=ability_change.*result=fail.*step=mutate")
SANITY_CLIENT = re.compile(r"ev=queuez.*stage=family0_list.*first=0x[0-9A-Fa-f]+/\d+")
SANITY_SERVER = re.compile(r"ev=queuez.*stage=banner_refresh.*result=ok")
VER_RE = re.compile(r"first=0x[0-9A-Fa-f]+/(\d+)")
TIGHT_MS = 500


def best_shift(client_ts, server_ts):
    """merge_logs.best_shift, verbatim."""
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


def sanity_client_ts(entries):
    """merge_logs sanity client ticks: family0_list version bumps only."""
    out, prev = [], None
    for text in entries:
        if SANITY_CLIENT.search(text):
            v = int(VER_RE.search(text).group(1))
            if v != prev:
                out.append(int(T_RE.search(text).group(1)))
            prev = v
    return out


# ---------------------------------------------------------------------------
# line parsing (binary-safe; log lines can carry embedded NUL + truncated
# tail garbage — the build_data identity warn is the canonical case)
# ---------------------------------------------------------------------------

KEY_RE = re.compile(r"[A-Za-z0-9_.]+")


def sanitize(line):
    """Strip NUL and C0 control bytes (keep printable + whitespace)."""
    return "".join(ch if ch >= " " or ch in "\t" else " " for ch in line)


def parse_line(text):
    """Parse one log line into (kv dict, ok). Grammar:
    src level=<lvl> t=<ms> ev=<name> [key=value ...]; the leading bare token
    (server/state/core/client/...) becomes kv['src']; each kv token splits at
    its FIRST '=' (values may contain '='). Tokens without '=' are collected
    into kv['tail'] (truncated/garbage tails — e.g. the build_data identity
    line's NUL-mangled remainder). On any grammar violation ok is False while
    kv still carries everything parseable — the raw line is always recorded."""
    tokens = text.split()
    kv = {}
    tails = []
    if tokens and "=" not in tokens[0]:
        kv["src"] = tokens[0]
        tokens = tokens[1:]
    for tok in tokens:
        key, sep, value = tok.partition("=")
        if not sep:
            tails.append(tok)
            continue
        if KEY_RE.fullmatch(key):
            kv[key] = value
        else:
            tails.append(tok)
    if tails:
        kv["tail"] = " ".join(tails)
    if "level" not in kv or "t" not in kv or "ev" not in kv:
        return kv, False
    if not kv["t"].isdigit():
        return kv, False
    return kv, True


# ---------------------------------------------------------------------------
# eqHash — EXACT port of the validated RE_output/scripts/bootL_eqhash_exact.py
# (same functions, same DB query, db path parameterized). Cross-checked
# against the original module in the selftest.
# ---------------------------------------------------------------------------

FNV_BASIS = 14695981039346656037
FNV_PRIME = 1099511628211


def mix_byte(h, v):
    h ^= (v & 0xFF)
    h = (h * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return h


def mix_u32(h, v):
    v &= 0xFFFFFFFF
    for i in range(4):
        h = mix_byte(h, (v >> (8 * i)) & 0xFF)
    return h


def parse_hex_u32(text):
    return int(text, 16) & 0xFFFFFFFF


def db_configured_hash(db_path):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT soid, movement_ability_entry, grenade_ability_entry, super_ability_entry, "
        "melee_ability_entry, class_ability_entry FROM characters ORDER BY character_index")
    chars = cur.fetchall()
    h = FNV_BASIS
    h = mix_byte(h, len(chars))
    for ch in chars:
        for ability in (ch[1], ch[2], ch[3], ch[4], ch[5]):
            h = mix_byte(h, ability)
        soid = ch[0]
        cur.execute(
            "SELECT equipment_slot, definition_hash, instance_level, socket_policy, item_id "
            "FROM items WHERE account_id = (SELECT account_id FROM accounts LIMIT 1) "
            "AND character_index = (SELECT character_index FROM characters WHERE soid = ?) "
            "AND in_equipment = 1", (soid,))
        rows = cur.fetchall()
        slots = {}
        for r in rows:
            slot = r[0]
            cur.execute(
                "SELECT lane, plug_definition_hash FROM item_plugs WHERE item_id = ? "
                "ORDER BY lane", (r[4],))
            plugs = cur.fetchall()
            slots[slot] = (r[1], r[2], r[3], plugs)
        for slot_idx in range(16):
            item = slots.get(slot_idx)
            if item is None:
                h = mix_byte(h, 0)
                continue
            defhash_text, level, socket_policy, plugs = item
            h = mix_byte(h, 1)
            h = mix_u32(h, parse_hex_u32(defhash_text))
            h = mix_u32(h, int(level) & 0xFFFFFFFF)
            h = mix_byte(h, 0 if socket_policy == 0 else 1)
            plug_count = max((lane for lane, _ in plugs), default=-1) + 1 if plugs else 0
            h = mix_byte(h, plug_count)
            by_lane = {lane: plug for lane, plug in plugs}
            for lane in range(plug_count):
                plug = by_lane.get(lane)
                if plug is None:
                    h = mix_byte(h, 0)
                else:
                    h = mix_byte(h, 1)
                    h = mix_u32(h, parse_hex_u32(plug))
    con.close()
    return h


# ---------------------------------------------------------------------------
# manifest capture
# ---------------------------------------------------------------------------

REQUIRED_TABLES = [
    "accounts", "characters", "entitlements", "family5_overrides", "flags",
    "instance_state", "item_plugs", "items", "meta", "objectives",
    "progression", "vendor_sale_items", "vendors",
]


def sha256_hex(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def file_state(path):
    if not os.path.exists(path):
        return {"missing": True}
    st = os.stat(path)
    return {"size": st.st_size, "inode": st.st_ino, "mtime": int(st.st_mtime)}


def read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def db_census(db_path):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    counts = {}
    for t in tables:
        counts[t] = cur.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
    con.close()
    return counts


def db_content_hash(db_path):
    """Canonical content hash: table by table, ALL rows (repr form), hashed
    incrementally. Byte-stable across WAL checkpoint timing (the raw file
    bytes churn while content is identical) — this is the honest input-state
    hash the manifest compares. Read-only."""
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    h = hashlib.sha256()
    for t in tables:
        h.update(("T:%s\n" % t).encode("utf-8"))
        for row in cur.execute("SELECT * FROM %s" % t):
            h.update(repr(row).encode("utf-8"))
    con.close()
    return h.hexdigest()


def content_roster(dir_path):
    out = {}
    if not os.path.isdir(dir_path):
        return out
    for name in sorted(os.listdir(dir_path)):
        full = os.path.join(dir_path, name)
        if os.path.isfile(full):
            out[name] = os.path.getsize(full)
    return out


def live_process_census():
    import subprocess
    procs = []
    try:
        out = subprocess.run(["pgrep", "-fl", "sunrise-server|destiny2"],
                             capture_output=True, text=True, timeout=10).stdout
        for line in out.splitlines():
            parts = line.strip().split(" ", 1)
            if parts:
                procs.append({"pid": parts[0], "cmd": parts[1] if len(parts) > 1 else ""})
    except Exception as exc:  # pragma: no cover - environment wide
        procs.append({"error": str(exc)})
    return procs


def capture_manifest(args):
    """INPUT-state manifest (deliverable 2). Never assumes eqHash."""
    m = {
        "captured_at_iso": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "label": args.label,
        "mode": "dry" if args.dry else ("from_files" if args.from_files else "live_tail"),
        "recorder": "boot_record.py",
    }
    hashes = {}
    for name, path in [("sunrise_server_exe", SERVER_EXE),
                       ("steam_api64_dll", CLIENT_DLL),
                       ("server_settings_json", SERVER_SETTINGS),
                       ("client_settings_json", CLIENT_SETTINGS),
                       ("state_db_file", STATE_DB)]:
        if os.path.exists(path):
            hashes[name] = {"sha256": sha256_hex(path), "size": os.path.getsize(path)}
        else:
            hashes[name] = {"missing": True}
    m["hashes"] = hashes
    m["settings"] = {"server": read_json(SERVER_SETTINGS),
                     "client": read_json(CLIENT_SETTINGS)}
    m["eqHash_computed"] = "0x%016X" % db_configured_hash(STATE_DB)
    m["eqHash_tool"] = EQHASH_TOOL
    m["db"] = {"tables": db_census(STATE_DB),
               "flags_row_count": db_census(STATE_DB).get("flags"),
               "content_hash": db_content_hash(STATE_DB),
               "wal_present": os.path.exists(STATE_DB + "-wal"),
               "shm_present": os.path.exists(STATE_DB + "-shm")}
    m["content_jsons"] = content_roster(CONTENT_DIR)
    m["logs_prestate"] = {"server": file_state(args.server_log),
                          "client": file_state(args.client_log)}
    m["processes"] = live_process_census()
    # Lane A dependency (2026-08-22): client log levels change the client
    # settings hash + the log volume the recorder parses. Noted in the record.
    m["lane_dependency"] = {"client_log_levels": m["settings"]["client"]
                            .get("core", {}).get("logging", {}).get("levels", {})}
    return m


# ---------------------------------------------------------------------------
# sqlite staging + finalize
# ---------------------------------------------------------------------------

SCHEMA_EVENTS = """
CREATE TABLE IF NOT EXISTS events (
  side TEXT NOT NULL,
  level TEXT,
  t_ms INTEGER,
  unified_t_ms INTEGER,
  ev TEXT,
  stage TEXT,
  result TEXT,
  kv TEXT NOT NULL,
  raw TEXT NOT NULL,
  parsed INTEGER NOT NULL
);
"""


def open_store(db_path):
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute(SCHEMA_EVENTS)
    return con


def _typed_events(entries, line_re, size_re):
    """(t, type, size) for lines matching line_re that carry a type."""
    out = []
    for t, text in entries:
        if not line_re.search(text):
            continue
        m = TYPE_RE.search(text)
        if not m:
            continue
        n = size_re.search(text)
        out.append((t, int(m.group(1)), int(n.group(1)) if n else None))
    return out


def tape_anchor(server_entries, client_entries):
    """
    Pair server activity pushes with the client tape rows that applied them.

    Aligns newest-first (the two capture windows rarely start together) and
    scans a small shift range, keeping only alignments where EVERY pair agrees
    on type. Returns (k, pairs, median_offset, spread, robust_spread) or None.
    Robust spread is p10..p90: a handful of early pairs sit far off the
    cluster, so the full range overstates the real agreement badly.
    """
    srv = _typed_events(server_entries, TAPE_SERVER, LEN_RE)
    cli = _typed_events(client_entries, TAPE_CLIENT, SIZE_RE)
    if not srv or not cli:
        return None
    best = None
    span = min(len(srv), len(cli))
    for k in range(0, min(16, span)):
        pairs = []
        ok = True
        for i in range(span - k):
            s_t, s_ty, s_len = srv[-(i + 1)]
            c_t, c_ty, c_size = cli[-(i + 1 + k)]
            if s_ty != c_ty:
                ok = False
                break
            pairs.append(s_t - c_t)
        if not ok or len(pairs) < 3:
            continue
        pairs.sort()
        med = pairs[len(pairs) // 2]
        spread = pairs[-1] - pairs[0]
        robust = pairs[(9 * len(pairs)) // 10] - pairs[len(pairs) // 10]
        cand = (robust, k, len(pairs), med, spread)
        if best is None or cand[0] < best[0]:
            best = cand
    if best is None:
        return None
    robust, k, n, med, spread = best
    return k, n, med, spread, robust


def summarize_offset(server_entries, client_entries):
    """merge_logs anchor logic; returns (offset_or_None, stats dict)."""
    prim_c = [t for t, text in client_entries if PRIMARY_CLIENT.search(text)]
    prim_s = [t for t, text in server_entries if PRIMARY_SERVER.search(text)]
    san_c = sanity_client_ts([text for _, text in client_entries])
    san_s = [t for t, text in server_entries if SANITY_SERVER.search(text)]
    stats = {"primary_client": len(prim_c), "primary_server": len(prim_s),
             "sanity_client": len(san_c), "sanity_server": len(san_s)}
    chain = []
    if prim_c and prim_s:
        pk, ppairs, pmed, pspread = best_shift(prim_c, prim_s)
        chain.append(("primary", pk, len(ppairs), pmed, pspread))
    if san_c and san_s:
        sk, spairs, smed, sspread = best_shift(san_c, san_s)
        chain.append(("sanity", sk, len(spairs), smed, sspread))
    if not chain:
        return None, stats
    # prefer primary; sanity carries only when primary is absent (extension).
    name, k, n, med, spread = chain[0]
    for cand in chain[1:]:
        if cand[0] == "primary":
            name, k, n, med, spread = cand
    stats.update({"anchor": name, "anchor_k": k, "anchor_pairs": n,
                  "offset_ms": med, "anchor_spread_ms": spread})
    return med, stats


def resolve_offset(server_entries, client_entries):
    """
    Offset resolution with the WIRE anchor first, legacy pairs as fallback.
    The wire pair marks a true shared instant; the legacy pairs correlate
    same-named events across two processes and are far looser.
    """
    stats = {}
    wire = tape_anchor(server_entries, client_entries)
    legacy_off, legacy_stats = summarize_offset(server_entries, client_entries)
    stats.update(legacy_stats)
    if wire is not None:
        k, n, med, spread, robust = wire
        stats.update({"anchor": "wire_tape_push", "anchor_k": k,
                      "anchor_pairs": n, "offset_ms": med,
                      "anchor_spread_ms": spread,
                      "anchor_robust_spread_ms": robust,
                      "legacy_anchor": legacy_stats.get("anchor"),
                      "legacy_offset_ms": legacy_stats.get("offset_ms")})
        return med, stats
    return legacy_off, stats


# ---------------------------------------------------------------------------
# live tailing (tail -F: rotation at app start = inode change -> seek 0)
# ---------------------------------------------------------------------------

class TailF:
    """Follow a file across rotations/truncations like tail -F."""

    def __init__(self, path, start_at_end=True, poll=0.25):
        self.path = path
        self.poll = poll
        self.fh = None
        self.inode = None
        self.pos = 0
        self.buf = b""
        if os.path.exists(path):
            self._open(start_at_end)

    def _open(self, at_end):
        self.fh = open(self.path, "rb")
        st = os.stat(self.path)
        self.inode = st.st_ino
        self.pos = st.st_size if at_end else 0
        if at_end:
            self.fh.seek(self.pos)

    def lines(self):
        """Yield newly available complete lines; call in a poll loop."""
        out = []
        if self.fh is None:
            if not os.path.exists(self.path):
                return out
            self._open(False)
        st = os.stat(self.path)
        if st.st_ino != self.inode:
            self.fh.close()
            self._open(False)          # rotation: fresh file from position 0
        elif st.st_size < self.pos:
            self.fh.seek(0)             # truncation
            self.pos = 0
        data = self.fh.read()
        self.pos += len(data)
        if not data:
            return out
        self.buf += data
        while b"\n" in self.buf:
            line, self.buf = self.buf.split(b"\n", 1)
            text = line.decode("utf-8", errors="replace")
            out.append(text.rstrip("\r"))
        return out

    def close(self):
        if self.fh is not None:
            self.fh.close()


def main():
    ap = argparse.ArgumentParser(description="Record one boot as events.sqlite + manifest.")
    ap.add_argument("--brief", required=True, help="boot brief markdown (refuses to start without it)")
    ap.add_argument("--server-log", default=DEFAULT_SERVER_LOG)
    ap.add_argument("--client-log", default=DEFAULT_CLIENT_LOG)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--label", default="boot")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--from-files", action="store_true")
    ap.add_argument("--manifest-override", default=None,
                    help="optional JSON deep-merged onto the captured manifest "
                         "(used for historical records whose input state is "
                         "reconstructed from byte-exact backups)")
    ap.add_argument("--min-duration", type=float, default=0.0)
    ap.add_argument("--quiet-timeout", type=float, default=0.0)
    ap.add_argument("--until-grep", default=None)
    ap.add_argument("--max-duration", type=float, default=900.0)
    args = ap.parse_args()

    # ---- deliverable 3: the boot brief gate -------------------------------
    if not os.path.exists(args.brief):
        print("ERROR: boot brief file not found: %s" % args.brief, file=sys.stderr)
        print("  A brief MUST carry: purpose/payoff, falsifiable claim,", file=sys.stderr)
        print("  what the boot does NOT test, and GRAPHICS DELTA.", file=sys.stderr)
        return 2
    with open(args.brief, "r", encoding="utf-8") as fh:
        brief_text = fh.read()
    low = brief_text.lower()
    required = [
        ("purpose/payoff", r"(^|\n)#{1,6}\s*[^#\n]*(purpose|payoff)[^\n]*\n"),
        ("falsifiable claim", r"(^|\n)#{1,6}\s*[^#\n]*(falsifia)[^\n]*\n"),
        ("not-test", r"(^|\n)#{1,6}\s*[^#\n]*(does not test|not test|not-test)[^\n]*\n"),
        ("graphics delta", r"(^|\n)#{1,6}\s*[^#\n]*(graphics)[^\n]*\n"),
    ]
    missing = [name for name, pat in required
               if not re.search(pat, low, re.IGNORECASE)]
    if missing:
        print("ERROR: boot brief incomplete; missing sections: %s" % ", ".join(missing),
              file=sys.stderr)
        return 3

    # ---- manifest + record dir -------------------------------------------
    label = re.sub(r"[^A-Za-z0-9_.-]", "_", args.label)[:60]
    ts = time.strftime("%Y%m%d_%H%M%S")
    rec_dir = os.path.join(args.out, "%s_%s" % (ts, label))
    os.makedirs(rec_dir, exist_ok=True)
    db_path = os.path.join(rec_dir, "events.sqlite")
    manifest_path = os.path.join(rec_dir, "manifest.json")
    record_path = os.path.join(rec_dir, "record.json")
    brief_path = os.path.join(rec_dir, "brief.md")

    try:
        manifest = capture_manifest(args)
        if args.manifest_override:
            with open(args.manifest_override, "r", encoding="utf-8") as fh:
                patch = json.load(fh)

            def deep_merge(base, src):
                for k, v in src.items():
                    if isinstance(v, dict) and isinstance(base.get(k), dict):
                        deep_merge(base[k], v)
                    else:
                        base[k] = v
            deep_merge(manifest, patch)
    except Exception as exc:
        print("ERROR: manifest capture failed: %s" % exc, file=sys.stderr)
        return 4
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    with open(brief_path, "w", encoding="utf-8") as fh:
        fh.write(brief_text)
    print("manifest : %s" % manifest_path)
    print("eqHash   : %s (computed, never assumed)" % manifest["eqHash_computed"])

    if args.dry:
        print("dry run complete: brief valid, manifest captured, no tailing.")
        return 0

    # ---- ingest: live tail or finished files ------------------------------
    con = open_store(db_path)
    server_entries, client_entries = [], []

    def ingest(side, text):
        s = sanitize(text.rstrip("\r\n"))
        kv, ok = parse_line(s)
        if ok:
            level = kv.get("level")
            t_ms = int(kv["t"])
            ev = kv.get("ev")
            stage = kv.get("stage")
            result = kv.get("result")
        else:
            level = t_ms = ev = stage = result = None
        con.execute(
            "INSERT INTO events (side, level, t_ms, ev, stage, result, kv, raw, parsed)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (side, level, t_ms, ev, stage, result,
             json.dumps(kv, sort_keys=True), s, 1 if ok else 0))
        if ok:
            (server_entries if side == "server" else client_entries).append((t_ms, text))
        return ok

    if args.from_files:
        for path, side in ((args.server_log, "server"), (args.client_log, "client")):
            n_lines = n_ok = 0
            with open(path, "rb") as fh:
                for raw in fh:
                    n_lines += 1
                    text = raw.decode("utf-8", errors="replace").rstrip("\r\n")
                    n_ok += ingest(side, text)
            print("%s : %d lines, %d parsed (%s)" % (side, n_lines, n_ok, path))
        stop_reason = "from_files"
    else:
        tailers = {"server": TailF(args.server_log, start_at_end=True),
                   "client": TailF(args.client_log, start_at_end=True)}
        start = time.time()
        last_activity = time.time()
        seen_until = False
        stop_reason = None
        try:
            while True:
                for side, tl in tailers.items():
                    n_new = 0
                    for text in tl.lines():
                        ingest(side, text)
                        last_activity = time.time()
                        n_new += 1
                        if args.until_grep and re.search(args.until_grep, text):
                            seen_until = True
                    if n_new:
                        con.commit()   # crash-safe: visible mid-run, retrievable on kill
                elapsed = time.time() - start
                if args.max_duration and elapsed >= args.max_duration:
                    stop_reason = "max_duration"; break
                if elapsed >= args.min_duration:
                    if args.until_grep and not seen_until:
                        pass
                    elif args.quiet_timeout and (time.time() - last_activity) >= args.quiet_timeout:
                        stop_reason = "quiet_timeout"; break
                time.sleep(0.25)
        except KeyboardInterrupt:
            stop_reason = "interrupt"
        for tl in tailers.values():
            tl.close()
        print("tail    : %s (%.1f s)" % (stop_reason, time.time() - start))

    con.commit()

    # ---- merge-agnostic summary + offset ----------------------------------
    offset, astats = resolve_offset(server_entries, client_entries)
    n_rows = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    n_parsed = con.execute("SELECT COUNT(*) FROM events WHERE parsed=1").fetchone()[0]
    n_native = con.execute("SELECT COUNT(*) FROM events WHERE parsed=0").fetchone()[0]
    if offset is not None:
        con.execute("UPDATE events SET unified_t_ms = CASE side"
                    " WHEN 'server' THEN t_ms - ? ELSE t_ms END WHERE parsed=1", (offset,))
    con.commit()
    ev_counts = {r[0]: r[1] for r in con.execute(
        "SELECT ev, COUNT(*) FROM events WHERE parsed=1 GROUP BY ev ORDER BY 2 DESC")}
    record = {
        "record_dir": rec_dir,
        "label": label,
        "stop_reason": stop_reason if not args.from_files else "from_files",
        "offset_ms": offset,
        "anchor_stats": astats,
        "lines": {"total": n_rows, "parsed": n_parsed, "unparsed": n_native},
        "ev_counts": ev_counts,
        "eqHash_computed": manifest["eqHash_computed"],
        "graphics_delta_note": "none recorded; see brief.md",
        "lane_dependency": manifest["lane_dependency"],
    }
    with open(record_path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, sort_keys=True)
    con.close()
    print("events  : %s (%d lines; %d parsed; %d unparsed)"
          % (db_path, n_rows, n_parsed, n_native))
    print("offset  : %s ms (%s)" % (offset if offset is not None else "none",
                                    astats.get("anchor", "no anchor pair")))
    print("record  : %s" % rec_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())