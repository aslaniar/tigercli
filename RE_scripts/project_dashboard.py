#!/usr/bin/env python3
# REGISTRY: caps: project-dashboard, live-tail, boot-segments
"""project_dashboard.py - the operator's second monitor (2026-09-06 v2).

Read-only local web page answering "what is happening during THIS boot" and
"is the deployed stack healthy". Lifetime-safe by construction:

  - front-specific numbers come from a DECLARED config
    (RE_output/map/dashboard_contract.json) that the working session updates
    when the front moves; the dashboard renders whatever is declared and NAGS
    when the declaration looks stale (mtime older than STATE.md's);
  - everything else is generic: boot segments, stage transitions, wire-type
    census, instrument census, warn stream, merged logs.

Boot segmentation (the v2 fix): a client process log spans MANY boot cycles
(re-entering character_select after landing starts a new one). The scanners
below split the stream into segments and report only the CURRENT boot:
  client (mac):  a new segment starts when character_select is re-entered
                 after a strictly later stage was already seen;
  server:        a new segment starts when the server PID changes or the log
                 rotates/shrinks;
  rig:           the fetched snapshot is split by the same client rule and
                 the LAST segment wins.
All counters are monotonic WITHIN the current segment (no more sliding-window
values that go 4 -> 7 -> 3 while you watch).

Log pane: the three sources run on DIFFERENT t= epochs. Until a drift anchor
exists the pane renders PER-SOURCE BLOCKS - never a fake merged timeline
(the old dashboard's lesson). Merged view returns when alignment exists.

    /usr/bin/python3 RE_scripts/project_dashboard.py --serve [--port 8400] [--lan]

Degrade gracefully: server down = its side greys out; rig unreachable =
UNREACHABLE lane; missing files = visible absence lines. Everything shown is
provenance-labeled; the page invents nothing.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
MAC_LOG = ROOT / "Game/bin/x64/Sunrise/logs/sunrise.log"
SRV_LOG = ROOT / "RE_output/s1_accept/Sunrise/logs/sunrise.log"
CLIENT_DLL = ROOT / "Game/bin/x64/steam_api64.dll"
SERVER_EXE = ROOT / "RE_output/s1_accept/sunrise-server.exe"
BUILT_CLIENT = ROOT / "RE_build/Sunrise-fork-inventory/build/steam_api64.dll"
BUILT_SERVER = ROOT / "RE_build/Sunrise-fork-inventory/build/sunrise-server.exe"
CONTRACT_FILE = Path(os.environ.get(
    "RE_DASHBOARD_CONTRACT", str(ROOT / "RE_output/map/dashboard_contract.json")))

RIG_HOST = "rasla@192.168.1.136"
RIG_LOG = r"C:\Users\rasla\Downloads\destiny-preservation\dcv build\bin\x64\Sunrise\logs\sunrise.log"
SSH_OPTS = ["-o", "ControlPath=" + os.path.expanduser("~/.ssh/cm-rig"),
            "-o", "ConnectTimeout=4", "-o", "BatchMode=yes"]

ADMIN = "http://192.168.1.7:8099"
ADMIN_LOOPBACK = "http://127.0.0.1:8099"

# boot-cycle stages in the order the client first walks them (corpus-derived,
# p2-175..179 archives); the LANE renders this pinned pipeline for every boot
# (all stages visible: reached / current / not-yet), and the session can
# correct the order in dashboard_contract.json ("bootflow.order") without
# touching code. Stages outside this list append dynamically so nothing hides.
DEFAULT_BOOTFLOW_ORDER = ["character_select", "slice_set", "profile_setup",
                          "composition", "orbit_handoff", "join_ready",
                          "owner_slot", "region", "world_step", "spawn_hold",
                          "fade_release"]
RESTART_STAGE = "character_select"
_bootflow_order = list(DEFAULT_BOOTFLOW_ORDER)  # rebound by the contract file
LATE_STAGES = {"orbit_handoff", "join_ready", "owner_slot", "region",
               "world_step", "spawn_hold", "fade_release"}

# the game's wire anatomy (stable across fronts). Known meaning per activity
# type; anything not listed renders as "type N" and is flagged NOVEL when it
# appears in a segment that had not shown it before.
KNOWN_TYPES = {
    "0": "grant (reaches pool_recv)",
    "7": "sobject record",
    "12": "membership replication (the peer row)",
    "17": "excluded carrier (ring-only)",
    "20": "routing lookup input",
    "21": "grant (idx21 chain)",
    "22": "receive-tick gate",
    "30": "pool assignment",
    "45": "pool body (the chase)",
    "52": "epoch",
}

KV_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_.-]*)=([^\s]+)")
TYPE_RE = re.compile(r"[^\w]type=(\d+)")
TYPE_SEEN_FILE = ROOT / "RE_output/map/wire_types_seen.json"
_type_seen = None  # learned registry: {"<type>": "first-seen date"} (durable)


def type_seen():
    global _type_seen
    if _type_seen is None:
        try:
            _type_seen = json.loads(TYPE_SEEN_FILE.read_text(encoding="utf8"))
        except Exception:
            _type_seen = {}
    return _type_seen


_type_seen_dirty = False


def type_seen_note_new(ty):
    """A type neither KNOWN nor in the learned registry is a genuine first
    sighting: record it durably so it is only ever NOVEL once."""
    global _type_seen_dirty
    seen = type_seen()
    if ty not in seen:
        seen[ty] = datetime.now().strftime("%Y-%m-%d")
        _type_seen_dirty = True
        return True
    return False


def type_seen_save():
    global _type_seen_dirty
    if _type_seen_dirty:
        TYPE_SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TYPE_SEEN_FILE.write_text(json.dumps(_type_seen, indent=1, sort_keys=True),
                                  encoding="utf8")
        _type_seen_dirty = False


# ---------------------------------------------------------------- scanners

class SegmentScanner:
    """Incremental, segment-aware line processor for one append-only log.
    Maintains, for the CURRENT boot segment only: bootflow transitions,
    wire-type census, contract-pattern counts, instrument census, warns."""

    def __init__(self, name):
        self.name = name
        self.offset = 0
        self.segment_seq = 0  # bumped on every segment reset (snapshot sync)
        self.stages = []            # (t, stage) for the current segment
        self.segment_stages = set()  # distinct stages seen this segment
        self.type_counts = {}
        self.novel_types = set()
        self.contract_counts = {}
        self.instruments = {}
        self.warns = deque(maxlen=80)
        self.last_t = None
        self.contract_patterns = []  # [(name, pattern)] per source

    def reset(self, reason):
        self.segment_seq += 1
        self.stages = []
        self.segment_stages = set()
        self.type_counts = {}
        self.novel_types = set()
        self.contract_counts = {}
        self.instruments = {}
        self.warns.clear()
        self.last_t = None
        self._reset_reason = reason

    def feed(self, new_text):
        for raw in new_text.splitlines():
            self.feed_line(raw)

    def feed_line(self, raw):
        kv = dict(KV_RE.findall(raw))
        t = int(kv["t"]) if kv.get("t", "").isdigit() else None
        if t is not None:
            self.last_t = t
        # wire census
        for m in TYPE_RE.finditer(raw):
            ty = m.group(1)
            self.type_counts[ty] = self.type_counts.get(ty, 0) + 1
            if ty not in KNOWN_TYPES and ty not in self.novel_types \
                    and type_seen_note_new(ty):
                self.novel_types.add(ty)
        # contract patterns (declared)
        for name, pat in self.contract_patterns:
            if pat in raw:
                self.contract_counts[name] = self.contract_counts.get(name, 0) + 1
        # instruments: latest census line per fn
        if "ev=mtrace" in raw and "stage=census" in raw:
            fn = kv.get("fn")
            if fn:
                self.instruments[fn] = {
                    "fn": fn, "attached": kv.get("attached"),
                    "calls": kv.get("calls"), "rva": kv.get("rva"),
                    "why": kv.get("why"), "t": t}
        # warns
        if "level=warn" in raw or "level=error" in raw:
            self.warns.append(raw.rstrip())
        # bootflow + segment rule (clients only)
        if "ev=bootflow" in raw:
            stg = kv.get("stage")
            if stg:
                self._on_stage(t, stg)

    def _on_stage(self, t, stg):
        if (stg == RESTART_STAGE and self.segment_stages
                and self.segment_stages & LATE_STAGES):
            # a new boot cycle began inside the same process: start a segment
            self.reset("new boot cycle")
        self.stages.append((t, stg))
        self.segment_stages.add(stg)

    def summary(self, now_t=None, source_age=None, order=None, fresh=None):
        """Progress-bar semantics over the PINNED pipeline: stages up to the
        client's current stage are PASSED (the client is logically past them
        even when a Tower return skips their re-emission), stages after are
        UPCOMING, the current is highlighted. When the source is not live
        (client closed), NOTHING is lit."""
        order = order or DEFAULT_BOOTFLOW_ORDER
        idx = {s: i for i, s in enumerate(order)}
        first_seen = {}
        for t, s in self.stages:
            if s not in first_seen:
                first_seen[s] = t
        current = self.stages[-1][1] if self.stages else None
        cur_t = first_seen.get(current)
        live = bool(fresh) and current is not None
        dwell = None
        if live and cur_t is not None and now_t is not None:
            dwell = now_t - cur_t
        cur_i = idx.get(current)
        lane = []
        for s in order:
            if not live:
                state = "upcoming"
            elif s == current:
                state = "current"
            elif s in idx and cur_i is not None and idx[s] < cur_i:
                state = "passed"
            else:
                state = "upcoming"
            lane.append({"stage": s, "t": first_seen.get(s), "state": state})
        for s in first_seen:  # stages outside the pinned list append
            if s not in idx:
                lane.append({"stage": s, "t": first_seen[s], "state": "passed"})
        return {"lane": lane, "current": current if live else None,
                "dwell_ms": dwell, "live": live,
                "bootflow_last_t": self.last_t, "stale": source_age}


_file_scanners = {name: SegmentScanner(name) for name in ("mac", "server")}
_rig_scanner = SegmentScanner("rig")
_rigbf_cache = {"ts": 0.0, "lines": []}
_rig_tail_cache = {"ts": 0.0, "data": None}
_rig_hostname = {"ts": 0.0, "name": None}
_scanner_pid = {"server": None}
_segments_dir = ROOT / "RE_output/dashboard/segments"
_SNAPSHOT_CAP = 25 * 1024 * 1024  # keep segment snapshots bounded


def snapshot_path(src):
    return _segments_dir / f"{src}.log"


def append_snapshot(src, text, reset_seq=None):
    """Append freshly-read lines to the source's CURRENT-SEGMENT snapshot
    (the file merge_timeline re-anchors over). A segment reset truncates the
    snapshot: the new cycle starts clean. The reset lands mid-chunk, so the
    boundary chunk is dropped (seconds of lines) - anchors re-form quickly
    and the alternative is re-parsing the chunk byte-offset, not worth it."""
    try:
        _segments_dir.mkdir(parents=True, exist_ok=True)
        p = snapshot_path(src)
        if reset_seq is not None:
            st = _snapshot_seq.setdefault(src, 0)
            if reset_seq != st:
                with open(p, "w", encoding="utf8") as fh:
                    fh.write(text)
                _snapshot_seq[src] = reset_seq
                _snapshot_gen[src] = _snapshot_gen.get(src, 0) + 1
                return
        if p.exists() and p.stat().st_size > _SNAPSHOT_CAP:
            with open(p, "rb") as fh:
                fh.seek(-_SNAPSHOT_CAP // 2, 2)
                keep = fh.read().decode("utf8", errors="replace")
            with open(p, "w", encoding="utf8") as fh:
                fh.write(keep)
        with open(p, "a", encoding="utf8") as fh:
            fh.write(text)
    except OSError:
        pass


_snapshot_seq = {}
_snapshot_gen = {}  # bumped on truncation/rewrite; drift validity keys on this


def snapshot_gens():
    return tuple(_snapshot_gen.get(s, 0) for s in ("mac", "server", "rig"))


def file_now_t(path):
    """Newest t= in the log's last 8 KB (heartbeats advance while stuck)."""
    try:
        with open(path, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - 8192))
            tail = fh.read().decode("utf8", errors="replace")
        ts = [int(m.group(1)) for m in re.finditer(r"\bt=(\d+)", tail)]
        return max(ts) if ts else None
    except OSError:
        return None


def source_age(path):
    try:
        return time.time() - Path(path).stat().st_mtime
    except OSError:
        return None


def scan_file_source(name, path):
    """Feed only the NEW bytes of an append-only log to its scanner, and
    mirror them into the current-segment snapshot file."""
    sc = _file_scanners[name]
    try:
        size = path.stat().st_size
    except OSError:
        return sc
    if size < sc.offset:  # rotated/truncated -> new everything
        sc.reset("log rotated")
        sc.offset = 0
    if size > sc.offset:
        with open(path, "rb") as fh:
            fh.seek(sc.offset)
            chunk = fh.read(size - sc.offset).decode("utf8", errors="replace")
        seq_before = sc.segment_seq
        sc.offset = size
        sc.feed(chunk)
        append_snapshot(name, chunk,
                        reset_seq=sc.segment_seq if sc.segment_seq != seq_before else None)
    return sc


def rig_tail(n=400):
    now = time.time()
    if _rig_tail_cache["data"] is not None and now - _rig_tail_cache["ts"] < 3:
        return _rig_tail_cache["data"]
    try:
        r = subprocess.run(
            ["ssh"] + SSH_OPTS + [RIG_HOST,
             f"powershell -NoProfile -Command Get-Content -Tail {n} "
             f"-LiteralPath '{RIG_LOG}'"],
            capture_output=True, text=True, timeout=10)
        if r.returncode != 0 and not r.stdout.strip():
            raise RuntimeError(f"ssh rc={r.returncode}")
        data = {"lines": r.stdout.splitlines()[-n:], "error": None}
    except Exception as e:
        data = {"lines": [], "error": f"unreachable: {e}"}
    _rig_tail_cache.update(ts=now, data=data)
    return data


def rig_hostname():
    now = time.time()
    if _rig_hostname["name"] and now - _rig_hostname["ts"] < 600:
        return _rig_hostname["name"]
    try:
        r = subprocess.run(["ssh"] + SSH_OPTS + [RIG_HOST, "echo %COMPUTERNAME%"],
                           capture_output=True, text=True, timeout=8)
        name = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else None
        if name:
            _rig_hostname.update(ts=now, name=name)
    except Exception:
        pass
    return _rig_hostname["name"]


def rig_scanner():
    """Split the fetched bootflow stream into segments, keep the LAST one;
    feed the type/instrument/warn census from the tail snapshot."""
    now = time.time()
    lines = rig_tail(400)["lines"]
    bf = _rigbf_cache
    if now - bf["ts"] > 10:
        try:
            r = subprocess.run(
                ["ssh"] + SSH_OPTS + [RIG_HOST,
                 f'findstr /C:"ev=bootflow" "{RIG_LOG}"'],
                capture_output=True, text=True, timeout=20)
            bf.update(ts=now,
                      lines=[l for l in r.stdout.splitlines()
                             if "ev=bootflow" in l])
        except Exception:
            pass
    sc = _rig_scanner
    sc.reset("rescan")
    # split the whole bootflow stream into boot cycles; keep the last segment
    stages = []
    for raw in bf["lines"]:
        kv = dict(KV_RE.findall(raw))
        t = int(kv["t"]) if kv.get("t", "").isdigit() else None
        stg = kv.get("stage")
        if stg == RESTART_STAGE and any(s in LATE_STAGES for _t, s in stages):
            stages = []
        if stg:
            stages.append((t, stg))
    sc.stages = stages
    sc.segment_stages = {s for _t, s in stages}
    for raw in lines:
        sc.feed_line(raw)
    sc.last_t = None
    for raw in lines:
        m = re.search(r"\bt=(\d+)", raw)
        if m:
            sc.last_t = max(sc.last_t or 0, int(m.group(1)))
    return sc


_rig_fresh = {"last_t": None, "changed_ts": None}

SHUTDOWN_RE = re.compile(r"ev=shutdown\b")


def last_lines_shutdown(lines):
    """A clean client quit writes ev=shutdown as (one of) its last line(s) -
    closure is then a FACT from the log, not a timing guess."""
    return any(SHUTDOWN_RE.search(l) for l in lines[-3:])


def read_last_lines(path, k=3):
    try:
        with open(path, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - 16384))
            return fh.read().decode("utf8", errors="replace").splitlines()[-k:]
    except OSError:
        return []


def rig_fresh(last_t, lines=None):
    """The rig log's mtime is not visible from here; freshness = the tail's
    newest t= has CHANGED within the last 120 s (a live client keeps ticking),
    AND the session has not cleanly shut down (ev=shutdown closes it
    immediately - no 2-minute lingering 'live' after quitting)."""
    if lines is not None and last_lines_shutdown(lines):
        _rig_fresh.update(last_t=last_t)
        return False
    now = time.time()
    if last_t is None:
        return False
    if last_t != _rig_fresh["last_t"]:
        _rig_fresh["last_t"] = last_t
        _rig_fresh["changed_ts"] = now
    return (_rig_fresh["changed_ts"] is not None
            and now - _rig_fresh["changed_ts"] < 120)


# ------------------------------------------------------------- contract

def load_contract():
    try:
        cfg = json.loads(CONTRACT_FILE.read_text(encoding="utf8"))
    except Exception:
        return None
    if not isinstance(cfg, dict) or not isinstance(cfg.get("counters"), list):
        return None
    return cfg


def contract_stale(cfg):
    """The declaration is stale when STATE.md moved after it was written."""
    try:
        cfg_t = CONTRACT_FILE.stat().st_mtime
        state_t = (ROOT / "STATE.md").stat().st_mtime
        return state_t > cfg_t + 3600  # >1h newer verdicts
    except OSError:
        return False


def bind_contract():
    global _bootflow_order
    cfg = load_contract()
    if not cfg:
        return None
    order = (cfg.get("bootflow") or {}).get("order")
    if isinstance(order, list) and len(order) >= 2:
        _bootflow_order = order
    pats = {src: [] for src in ("mac", "server", "rig")}
    for c in cfg.get("counters", []):
        src = c.get("source", "server")
        pats.setdefault(src, []).append((c.get("name", "?"), c.get("match", "")))
    for name, sc in list(_file_scanners.items()) + [("rig", _rig_scanner)]:
        sc.contract_patterns = pats.get(name, [])
        if name in _file_scanners:
            sc.contract_counts = {}
    return cfg


# ------------------------------------------------------------- live data

def tail_file(path, n):
    try:
        with open(path, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - n * 320))
            data = fh.read().decode("utf8", errors="replace")
        lines = data.splitlines()
        return lines[-n:], round(time.time() - Path(path).stat().st_mtime, 1), None
    except OSError as e:
        return [], None, f"unavailable: {e}"


def admin_get(path, timeout=2.0):
    for base in (ADMIN, ADMIN_LOOPBACK):
        try:
            with urlopen(base + path, timeout=timeout) as r:
                return json.loads(r.read().decode("utf8", errors="replace"))
        except Exception:
            continue
    return None


def sha16(p):
    try:
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except OSError:
        return None


def identity():
    mac, srv = sha16(CLIENT_DLL), sha16(SERVER_EXE)
    bm, bs = sha16(BUILT_CLIENT), sha16(BUILT_SERVER)
    return {"mac_client": {"deployed": mac, "built": bm,
                           "match": mac == bm if mac and bm else None},
            "server": {"deployed": srv, "built": bs,
                       "match": srv == bs if srv and bs else None}}


def server_status():
    pid = subprocess.run(["pgrep", "-f", "wine64-preloader .*sunrise-server"],
                         capture_output=True, text=True).stdout.split()
    listeners = {}
    r = subprocess.run(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"],
                       capture_output=True, text=True)
    for port in ("8443", "30975", "8099"):
        listeners[port] = any(f":{port}\t" in l or f":{port} " in l
                              for l in r.stdout.splitlines())
    st = admin_get("/state")
    lobby = admin_get("/lobby")
    # a server restart is a segment boundary for the server log scanner
    new_pid = pid[0] if pid else None
    if new_pid != _scanner_pid["server"]:
        _file_scanners["server"].reset(f"server pid {new_pid}")
        _scanner_pid["server"] = new_pid
    return {"pid": new_pid, "listeners": listeners,
            "http": st is not None, "sessions": (st or {}).get("sessions", []),
            "session_count": (st or {}).get("count"), "lobby": lobby}


def api_now():
    # the pid check MUST run before the feeds: a server restart is a segment
    # boundary, and resetting after the feed would wipe the segment forever
    # (the offset never rewinds) - the empty-census bug
    st = server_status()
    bind_contract()
    sc_mac = scan_file_source("mac", MAC_LOG)
    sc_srv = scan_file_source("server", SRV_LOG)
    sc_rig = rig_scanner()
    now_t = {"mac": file_now_t(MAC_LOG), "server": file_now_t(SRV_LOG)}
    now_t["rig"] = sc_rig.last_t
    age = {"mac": source_age(MAC_LOG), "server": source_age(SRV_LOG),
           "rig": None if _rig_tail_cache["data"] is None or
                  _rig_tail_cache["data"]["error"] is None else None}
    mac_shutdown = last_lines_shutdown(read_last_lines(MAC_LOG))
    rig_shutdown = last_lines_shutdown(rig_tail(20)["lines"])
    cfg = load_contract()
    counters = []
    if cfg:
        vals = {"mac": sc_mac.contract_counts, "server": sc_srv.contract_counts,
                "rig": sc_rig.contract_counts}
        for c in cfg.get("counters", []):
            src = c.get("source", "server")
            counters.append({"name": c.get("name", "?"), "why": c.get("why", ""),
                             "source": src, "value": vals[src].get(c.get("name", "?"), 0)})
    census = {}
    for src, sc in (("mac", sc_mac), ("server", sc_srv), ("rig", sc_rig)):
        census[src] = {
            "types": sorted(({"type": k, "count": v,
                              "known": KNOWN_TYPES.get(k)}
                             for k, v in sc.type_counts.items()),
                            key=lambda x: -x["count"]),
            "novel": sorted(sc.novel_types),
            "lines": None}
    instruments = {}
    for src, sc in (("mac", sc_mac), ("rig", sc_rig)):
        instruments[src] = sorted(sc.instruments.values(), key=lambda r: r["fn"])
    dead = [r["fn"] for src in ("mac", "rig") for r in instruments[src]
            if r.get("attached") == "0"]
    out = {
        "server": st, "identity": identity(),
        "lanes": {"mac": sc_mac.summary(now_t["mac"], age["mac"],
                                        order=_bootflow_order,
                                        fresh=age["mac"] is not None
                                        and age["mac"] < 120
                                        and not mac_shutdown),
                  "rig": sc_rig.summary(now_t["rig"],
                                        order=_bootflow_order,
                                        fresh=rig_fresh(sc_rig.last_t)
                                        and not rig_shutdown),
                  "segment": {"mac": len(sc_mac.stages),
                              "rig": len(sc_rig.stages)}},
        "contract": {"declared": bool(cfg), "front": (cfg or {}).get("front"),
                     "updated": (cfg or {}).get("updated"),
                     "stale": contract_stale(cfg) if cfg else None,
                     "counters": counters},
        "census": census, "instruments": instruments, "dead_probes": dead,
        "warns": {src: list(sc.warns)[-40:]
                  for src, sc in (("mac", sc_mac), ("server", sc_srv),
                                  ("rig", sc_rig))},
        "hostnames": {"mac": os.uname().nodename, "rig": rig_hostname()},
        "tail_age": age,
        "ts": datetime.now().isoformat(timespec="seconds")}
    type_seen_save()
    return out
# ----------------------------------------------------- live wire alignment

_align_state = {"ts": 0.0, "sig": None, "running": False}


def _snapshot_sig():
    sig = []
    for src in ("mac", "server", "rig"):
        p = snapshot_path(src)
        try:
            st = p.stat()
            sig.append((src, st.st_size, int(st.st_mtime)))
        except OSError:
            sig.append((src, -1, -1))
    return tuple(sig)


def refresh_rig_snapshot():
    """The rig snapshot is a fetch (not append-only): rewrite it wholesale.
    Gen bump only when the CONTENT actually changed (a static rig log must
    not invalidate the drift every cycle)."""
    d = rig_tail(4000)
    if d["error"] and not d["lines"]:
        return
    try:
        _segments_dir.mkdir(parents=True, exist_ok=True)
        body = "\n".join(d["lines"]) + "\n"
        p = snapshot_path("rig")
        old = p.read_text(encoding="utf8") if p.exists() else ""
        if old != body:
            with open(p, "w", encoding="utf8") as fh:
                fh.write(body)
            _snapshot_gen["rig"] = _snapshot_gen.get("rig", 0) + 1
    except OSError:
        pass


def maybe_realign(force=False):
    """Re-run merge_timeline over the three current-segment snapshots when
    any of them changed (background thread; the API only reads results)."""
    now = time.time()
    if _align_state["running"]:
        return
    if not force and now - _align_state["ts"] < 45:
        return
    refresh_rig_snapshot()
    sig = _snapshot_sig()
    if not force and sig == _align_state["sig"]:
        _align_state["ts"] = now  # nothing changed; skip quietly
        return
    _align_state["running"] = True
    try:
        subprocess.run(
            ["/usr/bin/python3", str(ROOT / "RE_scripts/merge_timeline.py"),
             f"--server-log=server={SRV_LOG}",
             f"--client-log=mac={snapshot_path('mac')}",
             f"--client-log=rig={snapshot_path('rig')}",
             "--out", str(ROOT / "RE_output/dashboard/merge")],
            capture_output=True, text=True, timeout=420)
        # record the segment generations this merge was computed over; the
        # view is valid only while the generations still match (a reset or a
        # NEW appends do NOT invalidate - clocks do not shift on appends)
        meta = {"gens": list(snapshot_gens()), "computed": time.time()}
        (ROOT / "RE_output/dashboard/merge.meta.json").write_text(
            json.dumps(meta), encoding="utf8")
        _align_state["sig"] = sig
        _align_state["ts"] = time.time()
    except Exception:
        _align_state["ts"] = time.time()  # retry after the cadence
    finally:
        _align_state["running"] = False


def alignment_view():
    """@return (aligned, meta): the merged chronology is USABLE while the
    segment generations are unchanged since the merge (appends are fine -
    clock offsets only break on a segment RESET)."""
    prefix = ROOT / "RE_output/dashboard/merge"
    meta_p = Path(str(prefix) + ".meta.json")
    jsonl = Path(str(prefix) + ".jsonl")
    if not meta_p.exists() or not jsonl.exists():
        return False, None
    try:
        m = json.loads(meta_p.read_text(encoding="utf8"))
        if list(m.get("gens", [])) != list(snapshot_gens()):
            return False, None
        drift = json.loads(Path(str(prefix) + ".drift.json").read_text(encoding="utf8"))
        offsets = {}
        for s in drift.get("sources", []):
            label = (s.get("source") or "?").split("/")[0]
            offsets[label] = s.get("offset_ms")
        if any(v is None for v in offsets.values()):
            return False, None  # honest: a source with no anchor stays native
        meta = {"reference": drift.get("reference"),
                "generated": drift.get("generated_iso"),
                "offsets": offsets,
                "age_s": round(time.time() - m.get("computed", time.time()), 1)}
        return True, meta
    except Exception:
        return False, None


def read_merged_tail(n, flt, level):
    """Last rows of the merged chronology (jsonl is unified-t sorted, so the
    file tail IS the newest window)."""
    p = ROOT / "RE_output/dashboard/merge.jsonl"
    rows = []
    try:
        with open(p, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - n * 700))
            for line in fh.read().decode("utf8", errors="replace").splitlines():
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                raw = r.get("raw", "")
                if flt and flt not in raw.lower():
                    continue
                if level != "all" and f"level={level}" not in raw:
                    continue
                rows.append({"src": (r.get("source", "?") or "?").split("/")[0],
                             "tu": r.get("unified_t_ms"),
                             "t": r.get("t_native"), "line": raw.rstrip()})
        rows = rows[-n:]
    except OSError:
        pass
    return rows


def api_tail(args):
    n = min(int(args.get("n", ["300"])[0]), 1200)
    flt = (args.get("filter", [""])[0] or "").lower()
    level = args.get("level", ["all"])[0]
    want = (args.get("sources", ["mac,rig,server"])[0] or "mac,rig,server").split(",")
    aligned, meta = alignment_view()
    if aligned:
        rows = read_merged_tail(max(n * 4, 1200), flt, level)
        rows = [r for r in rows if r["src"] in want][-n:]
        return {"aligned": True, "rows": rows, "drift": meta,
                "sources": {}, "ts": datetime.now().isoformat(timespec="seconds")}
    out = {}
    for src, path in (("mac", MAC_LOG), ("server", SRV_LOG)):
        if src not in want:
            continue
        lines, age, err = tail_file(path, n)
        rows = [l for l in lines if "unavailable" not in l]
        out[src] = {"lines": rows, "age": age, "error": err}
    if "rig" in want:
        r = rig_tail(n)
        out["rig"] = {"lines": r["lines"], "age": 0.0 if r["lines"] else None,
                      "error": r["error"]}
    for src in out:
        if flt:
            out[src]["lines"] = [l for l in out[src]["lines"]
                                 if flt in l.lower()]
        if level != "all":
            out[src]["lines"] = [l for l in out[src]["lines"]
                                 if f"level={level}" in l]
        out[src]["count"] = len(out[src]["lines"])
    return {"sources": out, "aligned": False, "drift": meta,
            "ts": datetime.now().isoformat(timespec="seconds")}


def warn_shape(raw):
    return re.sub(r"t=\d+", "t=N", re.sub(r"\d{6,}", "N", raw))[:120]


# ------------------------------------------------------------- the page

PAGE = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Sunrise project dashboard</title>
<style>
:root { --bg:#0d1117; --panel:#161b22; --edge:#30363d; --fg:#c9d1d9; --dim:#8b949e;
        --mac:#58a6ff; --rig:#d2a8ff; --srv:#3fb950; --warn:#d29922; --err:#f85149;
        --ok:#3fb950; }
* { box-sizing: border-box; }
body { background:var(--bg); color:var(--fg); font:13px/1.45 -apple-system,Menlo,monospace; margin:0; padding:14px; }
h2 { font-size:12px; text-transform:uppercase; letter-spacing:.1em; color:var(--fg); font-weight:600; margin:0 0 10px; border-left:3px solid #1f6feb; padding-left:8px; }
.panel { background:var(--panel); border:1px solid var(--edge); border-radius:8px; padding:10px 14px; margin-bottom:14px; }
.bs, .fv, .dg { display:grid; gap:16px; grid-template-columns: 1.2fr 1fr; align-items:start; }
.bs > *, .fv > *, .dg > * { min-width:0; }
.sub { font-size:10px; text-transform:uppercase; letter-spacing:.12em; color:var(--dim); margin-bottom:6px; }
.vsep { border-left:1px solid var(--edge); padding-left:16px; }
@media (max-width:1100px){ .bs,.fv,.dg{grid-template-columns:1fr;} .vsep{border-left:none;border-top:1px solid var(--edge);padding-left:0;padding-top:10px;} }
.scrollbox { max-height:230px; overflow:auto; }
table { border-collapse:collapse; width:100%; font-size:12px; }
td,th { padding:2px 8px; border-bottom:1px solid var(--edge); text-align:left; white-space:nowrap; }
.wrap { word-break:break-all; }
.censuswrap { max-height:250px; overflow:auto; }
.ok { color:var(--ok); border-color:var(--ok); } .bad { color:var(--err); border-color:var(--err); }
.warn { color:var(--warn); border-color:var(--warn); } .dim { color:var(--dim); }
.src-mac { color:var(--mac); } .src-rig { color:var(--rig); } .src-server { color:var(--srv); }
table { border-collapse:collapse; width:100%; font-size:12px; }
td,th { padding:2px 8px; border-bottom:1px solid var(--edge); text-align:left; white-space:nowrap; }
.lane { margin:8px 0; }
.lane .who { font-weight:bold; }
.lane .stages { display:flex; align-items:center; flex-wrap:wrap; gap:4px; margin-top:3px; }
.st { padding:1px 7px; border-radius:4px; border:1px solid var(--edge); font-size:11px; }
.st.done { color:var(--fg); background:#1c2430; border-color:#39414d; }
.st.off { color:#555f6e; border-color:#232a33; background:transparent; opacity:.75; }
.st.cur { color:#fff; background:#1f6feb; border-color:#1f6feb; }
.st.stuck { color:var(--err); border-color:var(--err); }
.counters { display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:8px; }
.cnt { border:1px solid var(--edge); border-radius:6px; padding:8px; text-align:center; }
.cnt b { display:block; font-size:22px; }
#logbox { height:460px; overflow-y:auto; background:#0a0d12; border:1px solid var(--edge); border-radius:6px; padding:6px; font-size:12px; }
.lr { white-space:pre-wrap; padding:1px 0; }
.lr, .lr span { overflow-wrap:anywhere; word-break:break-all; min-width:0; }
.blkhead { font-weight:bold; border-top:1px solid var(--edge); margin-top:6px; padding-top:4px; }
.f-ev { color:#ffa657; } .f-stage { color:#79c0ff; } .f-res-ok { color:var(--ok); }
.f-res-bad { color:var(--err); } .f-fn { color:#d2a8ff; } .f-lvl-warn { color:var(--warn); }
.f-lvl-error { color:var(--err); }
.controls input,select,button { background:#0d1117; color:var(--fg); border:1px solid var(--edge); border-radius:5px; padding:3px 8px; font:inherit; }
.tgl { cursor:pointer; }
.tgl.active.mac { color:var(--mac); border-color:var(--mac); font-weight:bold; }
.tgl.active.rig { color:var(--rig); border-color:var(--rig); font-weight:bold; }
.tgl.active.server { color:var(--srv); border-color:var(--srv); font-weight:bold; }
.muted { color:var(--dim); }
.novel { color:var(--warn); }
.censustable td.num { text-align:right; }
</style></head><body>
<div class="panel" id="banner">
  <b>Sunrise project dashboard</b>
  <span id="serverchip" class="chip dim">server: ?</span>
  <span id="idchip" class="chip dim">builds: ?</span>
  <span id="alignedchip" class="chip dim">clocks: per-source (not aligned)</span>
  <span id="clock" class="chip dim"></span>
</div>
<div class="panel">
  <h2>Live logs
    <span class="controls" style="float:right">
      <button id="tgl-mac"  class="tgl mac active" onclick="toggleSrc('mac',this)">mac</button>
      <button id="tgl-rig"  class="tgl rig active" onclick="toggleSrc('rig',this)">rig</button>
      <button id="tgl-server" class="tgl server active" onclick="toggleSrc('server',this)">server</button>
      <input id="filter" placeholder="filter text" size="18">
      <select id="levelsel"><option>all</option><option>info</option><option>debug</option><option>warn</option><option>error</option></select>
      <select id="nlinesel"><option>300</option><option>600</option><option>1200</option></select>
      <label><input type="checkbox" id="follow" checked> follow</label>
      <span id="srcages" class="muted"></span>
    </span>
  </h2>
  <div id="logbox"></div>
</div>
<div class="panel">
  <h2>Boot state</h2>
  <div class="bs">
    <div>
      <div class="sub">bootflow lanes</div>
      <div id="lanehost" class="muted" style="font-size:11px"></div>
      <div id="lanes" class="muted">...</div>
    </div>
    <div class="vsep">
      <div class="sub">pairing</div>
      <div id="pairing" class="muted">...</div>
    </div>
  </div>
</div>
<div class="panel">
  <h2>Front vitals <span class="muted" id="contractmeta"></span></h2>
  <div id="contractfront" class="muted" style="margin-bottom:8px"></div>
  <div class="fv">
    <div>
      <div class="sub">contract counters</div>
      <div id="contract" class="counters muted">...</div>
    </div>
    <div class="vsep">
      <div class="sub">wire census <span style="text-transform:none">(type= counts, this boot)</span></div>
      <div id="census" class="muted">...</div>
    </div>
  </div>
</div>
<div class="panel">
  <h2>Diagnostics</h2>
  <div class="dg">
    <div>
      <div class="sub">instruments</div>
      <div id="instruments" class="muted">...</div>
    </div>
    <div class="vsep">
      <div class="sub">warnings <span style="text-transform:none">(deduped by shape)</span></div>
      <div id="warns" class="muted">...</div>
      <div id="health" class="muted" style="margin-top:8px"></div>
    </div>
  </div>
</div>
<script>
"use strict";
var box = document.getElementById("logbox");
function el(tag, cls, text){ var e=document.createElement(tag); if(cls) e.className=cls; if(text!==undefined) e.textContent=text; return e; }
function chipText(id, txt, cls){ var e=document.getElementById(id); e.textContent=txt; e.className="chip "+(cls||"dim"); }
var BUSY = {};
function once(key, fn){ if (BUSY[key]) return; BUSY[key] = true; fn().finally(function(){ BUSY[key] = false; }); }
// flicker guard: build into a detached node; swap the host's children only
// when the content actually changed (full clears every 2s read as blinking)
function swapIfChanged(id, build){
  var tmp = el("div"); build(tmp);
  var sig = tmp.innerHTML;
  var host = document.getElementById(id);
  if (host.__sig !== sig){ host.__sig = sig; host.textContent = ""; while (tmp.firstChild) host.appendChild(tmp.firstChild); }
}

function fmtRow(src, raw, tu){
  var kv = {}, m, re=/\b([A-Za-z_][A-Za-z0-9_.-]*)=([^\s]+)/g;
  while ((m = re.exec(raw)) !== null) kv[m[1]] = m[2];
  var d = el("div","lr");
  d.appendChild(el("span","src-"+src, "["+src+"] "));
  var tm = tu !== undefined && tu !== null ? String(tu) : (raw.match(/\bt=(\d+)/) || [])[1];
  d.appendChild(el("span","muted", (tm ? "t="+tm+" " : "")));
  if(kv.level==="warn"||kv.level==="error") d.appendChild(el("span","f-lvl-"+kv.level, kv.level+" "));
  if(kv.ev) d.appendChild(el("span","f-ev","ev="+kv.ev+" "));
  if(kv.stage) d.appendChild(el("span","f-stage","stage="+kv.stage+" "));
  if(kv.result) d.appendChild(el("span", kv.result==="ok"?"f-res-ok":"f-res-bad","result="+kv.result+" "));
  if(kv.fn) d.appendChild(el("span","f-fn","fn="+kv.fn+" "));
  if(kv.type) d.appendChild(el("span","f-stage","type="+kv.type+" "));
  // the message body: highlight the remaining k=v KEYS (dim) so the free
  // text is what carries the eye - the old render was one monochrome block
  var rest = raw.replace(/^.*?\bt=\d+\s*/, "");
  // the server's own line format repeats the header ev/stage inside the
  // message; drop the leading duplicate so it does not render twice
  if (kv.ev && kv.stage && rest.indexOf(kv.ev + " " + kv.stage + " ") === 0){
    rest = rest.slice(kv.ev.length + kv.stage.length + 2);
  }
  var last = 0, kvre = /([a-zA-Z_][a-zA-Z0-9_.-]*)=(\S*)/g, mm;
  while ((mm = kvre.exec(rest)) !== null){
    if (mm.index > last) d.appendChild(el("span","", rest.slice(last, mm.index)));
    d.appendChild(el("span","muted", mm[1]+"="));
    d.appendChild(el("span","", mm[2]+" "));
    last = mm.index + mm[0].length + 1;
  }
  if (last <= rest.length) d.appendChild(el("span","", rest.slice(last)));
  return d;
}
function warnShape(raw){ return raw.replace(/t=\d+/g,"t=N").replace(/\d{6,}/g,"N").slice(0,120); }

function renderLane(name, bf, fresh){
  var wrap = el("div","lane");
  var who = el("div");
  if (!bf.live){
    who.appendChild(el("span","who src-"+name, name));
    who.appendChild(el("span","muted","  no live boot"
      + (bf.stale!==null && bf.stale!==undefined ? " (last write "+Math.round(bf.stale)+"s ago)" : "")));
  } else {
    who.appendChild(el("span","who src-"+name, name));
    if (bf.current){
      who.appendChild(el("span","muted","  now: "+bf.current
        + (bf.dwell_ms!==null ? " ("+Math.round(bf.dwell_ms/1000)+"s)" : "")));
    }
  }
  wrap.appendChild(who);
  var row = el("div","stages");
  // PINNED pipeline, progress-bar semantics: stages up to the client's
  // current stage are PASSED, after it UPCOMING; nothing lit when the
  // client is closed
  bf.lane.forEach(function(st){
    var cls = "st " + (st.state==="current" ? (bf.dwell_ms!==null && bf.dwell_ms>120000 ? "stuck" : "cur")
             : st.state==="passed" ? "done" : "off");
    var txt = st.stage + (st.state==="current" && bf.dwell_ms!==null ? " ("+Math.round(bf.dwell_ms/1000)+"s)" : "");
    var sp = el("span",cls,txt);
    if (st.t !== null && st.t !== undefined) sp.title = "entered t="+st.t;
    row.appendChild(sp);
  });
  wrap.appendChild(row);
  return wrap;
}

function pollNow(){
  once("now", function(){
    return fetch("/api/now.json").then(function(r){return r.json();}).then(function(d){
      var s = d.server;
      chipText("serverchip","server: "+(s.pid?"pid "+s.pid+(s.http?" (http up)":" (http DOWN)"):"DOWN"),
               s.pid?(s.http?"ok":"warn"):"bad");
      var id=d.identity;
      chipText("idchip","client "+(id.mac_client.deployed||"?")+(id.mac_client.match?"==":"!=")+"built | server "
               +(id.server.deployed||"?")+(id.server.match?"==":"!=")+"built",
               (id.mac_client.match&&id.server.match)?"ok":"warn");
      var H = document.getElementById("lanehost");
      H.textContent = "mac="+d.hostnames.mac+"  rig="+(d.hostnames.rig||"?");
      swapIfChanged("lanes", function(L){
        [["mac",d.lanes.mac],["rig",d.lanes.rig]].forEach(function(p){
          L.appendChild(renderLane(p[0], p[1]));
        });
      });
      // contract (declared)
      var CM = document.getElementById("contractmeta");
      if (!d.contract.declared){ CM.textContent="(nothing declared)"; }
      else {
        CM.textContent = "declared " + d.contract.updated
          + (d.contract.stale ? "  - STALE? (STATE.md has newer verdicts)" : "");
        CM.className = "chip " + (d.contract.stale ? "warn" : "dim");
      }
      document.getElementById("contractfront").textContent = d.contract.front || "";
      swapIfChanged("contract", function(C){
        if (!d.contract.counters.length) C.appendChild(el("span","muted","no counters declared"));
        d.contract.counters.forEach(function(c){
          var card = el("div","cnt"); card.title = c.why;
          card.appendChild(el("b",null,String(c.value)));
          card.appendChild(el("span","muted", c.name + " ("+c.source+")"));
          C.appendChild(card);
        });
      });
      // census (one merged table: source | type | count | meaning)
      swapIfChanged("census", function(Z){
        var rows = [], novel = {};
        ["server","mac","rig"].forEach(function(src){
          var cz = d.census[src] || {types:[], novel:[]};
          cz.types.forEach(function(t){ rows.push({src:src, type:t.type, count:t.count, known:t.known}); });
          (cz.novel||[]).forEach(function(t){ novel[src+"|"+t] = true; });
        });
        if (!rows.length){ Z.appendChild(el("span","muted","no wire traffic this boot")); return; }
        rows.sort(function(a,b){ return b.count - a.count; });
        var tbl = el("table","censustable");
        var tr = el("tr");
        ["source","type","count","meaning"].forEach(function(h){ tr.appendChild(el("th",null,h)); });
        tbl.appendChild(tr);
        rows.forEach(function(r){
          var tr = el("tr");
          tr.appendChild(el("td","src-"+r.src, r.src));
          tr.appendChild(el("td",null,"type "+r.type));
          tr.appendChild(el("td","num",String(r.count)));
          var meaning = r.known || (novel[r.src+"|"+r.type] ? "NEW (first sighting)" : "");
          tr.appendChild(el("td","muted", meaning));
          tbl.appendChild(tr);
        });
        var wrap = el("div","censuswrap"); wrap.appendChild(tbl); Z.appendChild(wrap);
      });
      // instruments
      swapIfChanged("instruments", function(I){
      if (d.dead_probes.length) I.appendChild(el("div","bad","DEAD: "+d.dead_probes.join(", ")));
      var tbl = el("table"); var tr = el("tr");
      ["probe","att","calls","src"].forEach(function(h){ tr.appendChild(el("th",null,h)); }); tbl.appendChild(tr);
      ["mac","rig"].forEach(function(src){
        (d.instruments[src]||[]).forEach(function(r){
          var row = el("tr");
          var c1 = el("td","src-"+src, r.fn); row.appendChild(c1);
          var c2 = el("td", r.attached==="0"?"bad":"", String(r.attached===null||r.attached===undefined?"":r.attached)); row.appendChild(c2);
          row.appendChild(el("td",null,String(r.calls===null||r.calls===undefined?"":r.calls)));
          row.appendChild(el("td","muted",src));
          tbl.appendChild(row);
        });
      });
      var wrap = el("div","scrollbox"); wrap.appendChild(tbl); I.appendChild(wrap);
      });
      // pairing
      swapIfChanged("pairing", function(P){
        P.appendChild(el("div",null,"sessions: "+s.session_count+" | lobby entries: "+(Array.isArray(s.lobby)?s.lobby.length:"?")));
        (s.sessions||[]).slice(0,6).forEach(function(x){
          var txt = JSON.stringify(x);
          var row = el("div","wrap muted", txt.length > 220 ? txt.slice(0,220)+"..." : txt);
          P.appendChild(row);
        });
      });
      // warns (per source, deduped by shape)
      swapIfChanged("warns", function(W){
      var seen = {};
      var any = false;
      ["mac","server","rig"].forEach(function(src){
        (d.warns[src]||[]).forEach(function(raw){
          any = true;
          var shape = warnShape(raw);
          if (seen[shape]){ seen[shape].n++; seen[shape].el.lastChild.textContent = " x"+seen[shape].n; return; }
          var w = el("div"); w.appendChild(fmtRow(src, raw)); w.appendChild(el("span","muted"," x1"));
          W.appendChild(w); seen[shape] = {el:w, n:1};
        });
      });
      if (!any) W.appendChild(el("span","muted","none this boot"));
      var wrap = el("div","scrollbox"); wrap.style.maxHeight = "200px";
      while (W.firstChild) wrap.appendChild(W.firstChild);
      W.appendChild(wrap);
      });
    });
  });
}

var SRC = {mac: true, rig: true, server: true};
function toggleSrc(name, btn){
  SRC[name] = !SRC[name];
  btn.classList.toggle("active", SRC[name]);
  pollTail();
}
function pollTail(){
  once("tail", function(){
    var n = document.getElementById("nlinesel").value;
    var q = "?n="+n, f = document.getElementById("filter").value;
    if (f) q += "&filter="+encodeURIComponent(f);
    var lv = document.getElementById("levelsel").value;
    if (lv !== "all") q += "&level="+lv;
    var srcs = ["mac","rig","server"].filter(function(s){ return SRC[s]; });
    if (srcs.length && srcs.length < 3) q += "&sources="+srcs.join(",");
    return fetch("/api/tail.json"+q).then(function(r){return r.json();}).then(function(d){
      var kids = [];
      if (d.aligned){
        d.rows.forEach(function(r){ kids.push(fmtRow(r.src, r.line, r.tu)); });
        if (!d.rows.length) kids.push(el("div","muted","  (no lines match)"));
        var dr = d.drift || {};
        chipText("alignedchip", "clocks: ALIGNED (ref="+dr.reference+", computed "+dr.age_s+"s ago)", "ok");
      } else {
        ["mac","rig","server"].forEach(function(src){
          var sd = d.sources[src];
          if (!sd) return;
          var head = el("div","blkhead src-"+src, src + (sd.error ? " - "+sd.error : " ("+sd.count+" lines)")
            + (sd.age!==null && sd.age!==undefined ? "  last write "+sd.age+"s ago" : ""));
          kids.push(head);
          sd.lines.forEach(function(raw){ kids.push(fmtRow(src, raw)); });
          if (!sd.lines.length && !sd.error) kids.push(el("div","muted","  (no lines match)"));
        });
        chipText("alignedchip", "clocks: per-source blocks (not aligned)", "warn");
      }
      box.replaceChildren.apply(box, kids);   // one atomic swap - no blink
      if (document.getElementById("follow").checked){
        SUPPRESS_SCROLL = true;
        box.scrollTop = box.scrollHeight;
      }
      var ages = [];
      for (var s in d.sources){ var sd=d.sources[s]; ages.push(s+": "+(sd.error?"ERR":(sd.age===null?"?":sd.age+"s"))); }
      if (ages.length) document.getElementById("srcages").textContent = ages.join(" | ");
      else document.getElementById("srcages").textContent = "merged timeline";
    });
  });
}

function pollHealth(){
  once("health", function(){
    return fetch("/api/health.json").then(function(r){return r.json();}).then(function(d){
      var parts = [];
      [["registry",d.registry],["preflight",d.preflight],["gate fixture",d.gate_fixture],["index lint",d.index_fresh]].forEach(function(p){
        parts.push((p[1].rc===0?"ok ":"FLAG ")+p[0]);
      });
      document.getElementById("health").textContent = "tooling: "+parts.join(" | ")+" ("+d.ts.slice(11)+")";
    });
  });
}
document.getElementById("filter").addEventListener("input", pollTail);
document.getElementById("levelsel").addEventListener("change", pollTail);
document.getElementById("nlinesel").addEventListener("change", pollTail);
// scrolling up = the user wants history: drop out of follow automatically
// (and re-engage when they return to the bottom). The suppress flag keeps
// the programmatic follow-scroll from being read as a user scroll.
var SUPPRESS_SCROLL = false;
box.addEventListener("scroll", function(){
  if (SUPPRESS_SCROLL){ SUPPRESS_SCROLL = false; return; }
  var atBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 40;
  var follow = document.getElementById("follow");
  if (!atBottom && follow.checked) follow.checked = false;
  else if (atBottom && !follow.checked) follow.checked = true;
});
setInterval(function(){ if(document.getElementById("follow").checked) pollTail(); pollNow(); }, 2000);
setInterval(pollHealth, 60000);
pollTail(); pollNow(); pollHealth();
setInterval(function(){ document.getElementById("clock").textContent = new Date().toLocaleTimeString(); }, 1000);
</script></body></html>
"""


_health_cache = {"ts": 0.0, "data": None}


def health(force=False):
    now = time.time()
    if not force and _health_cache["data"] and now - _health_cache["ts"] < 120:
        return _health_cache["data"]

    def run(cmd, timeout=120):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            tail = (r.stdout + r.stderr).strip().splitlines()
            return {"rc": r.returncode, "summary": tail[-1] if tail else "(no output)"}
        except Exception as e:
            return {"rc": -1, "summary": f"error: {e}"}
    data = {
        "registry": run(["/usr/bin/python3", str(ROOT / "RE_scripts/registry_audit.py")]),
        "preflight": run(["/usr/bin/python3", str(ROOT / "RE_scripts/preflight.py"),
                          "--skip-rig", "--skip-server", "--no-traps"]),
        "gate_fixture": run(["/usr/bin/python3", str(ROOT / "RE_scripts/gate_boot.py"),
                             str(ROOT / "RE_output/map/boot_brief_v3_selftest.md")]),
        "index_fresh": run(["/usr/bin/python3", str(ROOT / "RE_scripts/build_index.py"), "--lint"]),
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
    _health_cache.update(ts=now, data=data)
    return data


class _Handler:
    pass


def make_handler(port, lan):
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            path, _, qs = self.path.partition("?")
            args = {}
            for a in qs.split("&"):
                if "=" in a:
                    k, v = a.split("=", 1)
                    args.setdefault(k, []).append(v)
            try:
                if path == "/" or path == "/index.html":
                    self._send(200, "text/html; charset=utf-8", PAGE.encode("utf8"))
                elif path == "/api/tail.json":
                    self._json(api_tail(args))
                elif path == "/api/now.json":
                    self._json(api_now())
                elif path == "/api/health.json":
                    self._json(health())
                else:
                    self._send(404, "text/plain", b"no such route")
            except Exception as e:
                try:
                    self._json({"error": repr(e)})
                except Exception:
                    pass

        def _json(self, obj):
            self._send(200, "application/json",
                       json.dumps(obj, default=str).encode("utf8"))

        def _send(self, code, ctype, body):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    bind = "0.0.0.0" if lan else "127.0.0.1"
    return HTTPServer((bind, port), H)


def _align_loop():
    while True:
        try:
            maybe_realign()
        except Exception:
            pass
        time.sleep(15)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--port", type=int, default=8400)
    ap.add_argument("--lan", action="store_true")
    args = ap.parse_args(argv)
    if not args.serve:
        print(__doc__)
        return 2
    httpd = make_handler(args.port, args.lan)
    bind, port = httpd.server_address[:2]
    print(f"project dashboard: http://{bind}:{port}/  (Ctrl-C to stop; read-only)")
    threading.Thread(target=_align_loop, daemon=True).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
