#!/usr/bin/env python3
# REGISTRY: caps: project-dashboard, live-tail, boot-segments
"""project_dashboard.py - the operator's second monitor (2026-09-07 v3).

Read-only local web page answering "what is happening during THIS boot" and
"is the deployed stack healthy". Lifetime-safe by construction:

  - front-specific numbers come from a DECLARED config
    (RE_output/map/dashboard_contract.json) that the working session updates
    when the front moves; the dashboard renders whatever is declared and NAGS
    when the declaration looks stale (mtime older than STATE.md's);
  - everything else is generic: boot segments, stage transitions, wire-type
    census, instrument census, warn stream, live logs.

v3 (2026-09-07) - three structural fixes to what v2 shipped:

  1. NOTHING SLOW RUNS ON THE REQUEST PATH. v2 served every route from a
     single-threaded HTTPServer while /api/now.json made two blocking ssh
     calls to the rig (15 s + 10 s timeouts), SHA-256'd 128 MB of binaries,
     ran lsof, and hit the admin HTTP twice - and /api/health.json ran four
     subprocesses at 120 s timeouts IN THE HANDLER. Any one stall froze the
     whole page; that is what "the live logs do not keep up" actually was.
     Now background COLLECTOR / STATUS / RIG / HEALTH threads own all I/O,
     every handler is a read of cached state, and the server is threaded.
     Binary hashes cache on (size, mtime_ns).

  2. ONE INGEST PATH, ONE EPOCH. Each source's current boot is mirrored into
     RE_output/dashboard/segments/<src>.log and that snapshot is the ONLY
     thing the census and the log pane read. mac/server ingest by byte delta
     from the live file; the rig ingests by byte delta over ssh. v2 instead
     tailed 400 rig lines per poll and rebuilt the rig census from that
     window, so rig counters were a sliding window while mac/server were
     cumulative - the 4->7->3 bug v2's own docstring claims to have killed.
     Reads now carry a PARTIAL-LINE BUFFER: v2 split byte chunks straight
     off a live writer, so every poll could tear the boundary line and feed
     half an event to the census.

  3. ALIGNMENT MUST EARN THE WORD. v2 read offset_ms out of the drift
     report, ignored robust_spread_ms, and painted a green "clocks: ALIGNED"
     chip over offsets whose own anchor pairs disagreed by +/-31 s (mac) and
     +/-20 s (rig). Because the merged view was then served from the tail of
     a 217 MB merge.jsonl rewritten only every ~53 s, it was also up to a
     minute stale and dominated by whichever source carried the largest
     offset. Now the pane always tails the live snapshots (2 s), an offset is
     used only when its robust spread is inside ALIGN_SPREAD_MAX_MS, and a
     source that fails the gate says WHY on the page instead of going green.

BOOT EPOCHS: a client process log spans MANY boot cycles. Every restart
signal - a new client pid, character_select re-entered after a later stage,
a log rotation, a server pid change - bumps ONE per-source counter. The log
pane clears exactly that source when its epoch moves and prints a divider;
the census resets with it; a cached clock offset is invalidated by it. v2
spread that decision over four mechanisms that could disagree.

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

# Background cadences (seconds). The page polls every 2 s and only ever
# reads what these threads have already produced - no handler blocks on I/O.
COLLECT_EVERY = 1.0        # mac/server ingest + scan of all three snapshots
STATUS_EVERY = 2.0         # pgrep / lsof / admin-http / deployed-hash check
RIG_INGEST_EVERY = 2.0     # ssh byte-delta pull of the rig log
RIG_PID_EVERY = 5.0        # ssh tasklist
RIG_HOST_EVERY = 600.0     # ssh hostname
HEALTH_EVERY = 120.0       # the four tooling subprocesses

ALIGN_EVERY = 120.0        # the clock-alignment merge; it only feeds the
                           # drift report, so it does not need a 45 s cadence
SCAN_CHUNK = 4 * 1024 * 1024        # max bytes one scan pass holds the lock for
STARTUP_TAIL = 4 * 1024 * 1024      # local log history taken on startup
RIG_FIRST_PULL = 20 * 1024 * 1024   # bytes of history on first sight/rotation
RIG_MAX_DELTA = 4 * 1024 * 1024     # cap one cycle's pull so it cannot stall

# An offset whose own anchor pairs disagree by more than this is not an
# alignment - it is a guess with a 30-second error bar, and interleaving on
# it puts lines in the wrong order while the UI calls itself ALIGNED.
# Override in dashboard_contract.json: {"align": {"max_spread_ms": N}}.
ALIGN_SPREAD_MAX_MS = 2000

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
    """Incremental line processor for ONE source's CURRENT boot segment.
    Maintains, for that segment only: bootflow transitions, wire-type census,
    contract-pattern counts, instrument census, warns.

    It does not own the boot epoch - SourceState does. When the stream itself
    says a new boot cycle began (character_select re-entered after a later
    stage) the scanner clears its counters and calls on_reset, so the one
    counter that means "which boot are these lines from" moves in lockstep
    with the snapshot truncation and the clock-offset invalidation."""

    def __init__(self, name):
        self.name = name
        self.on_reset = None        # SourceState hook (bumps the boot epoch)
        self.segment_seq = 0        # bumped on every segment reset
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
        if self.on_reset is not None:
            self.on_reset(reason)

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
            self.reset("character_select re-entered")
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
        # `live` = this boot has a stage to point at; `producing` = the log
        # is still being written. Collapsing the two made a running client
        # with no ev=bootflow line yet read as "no live boot".
        return {"lane": lane, "current": current if live else None,
                "dwell_ms": dwell, "live": live, "producing": bool(fresh),
                "bootflow_last_t": self.last_t, "stale": source_age}


# ------------------------------------------------------------ source state

_segments_dir = ROOT / "RE_output/dashboard/segments"
_SNAPSHOT_CAP = 25 * 1024 * 1024      # keep segment snapshots bounded
_PANE_CATCHUP_CAP = 2 * 1024 * 1024   # a cursor further behind jumps to the tail
_PANE_FIRST_TAIL = 256 * 1024         # bytes handed to a pane with no cursor


def snapshot_path(src):
    return _segments_dir / f"{src}.log"


class SourceState:
    """One log source, and the single authority on its BOOT EPOCH.

    Data flows one way: INGEST appends new bytes to the current epoch's
    snapshot (mac/server copy them from the live file, the rig pulls them
    over ssh), SCAN feeds the snapshot's new bytes to the scanner, and the
    log pane reads the same snapshot by cursor. Because there is exactly one
    ingest path, the census and the pane can never disagree about what this
    boot contains - in v2 the rig's census came from a 400-line ssh tail and
    the pane from a separate one.

    Offsets handed out are ABSOLUTE: bytes since this epoch began. trim_base
    records how many of them have been dropped off the front, so trimming an
    over-long snapshot is a visible gap to a reader rather than a silent skip
    under its byte cursor (v2 trimmed with live cursors pointing into it)."""

    def __init__(self, name, live_path=None):
        self.name = name
        self.live_path = live_path      # None for the rig (ssh-fed)
        self.lock = threading.RLock()
        self.scanner = SegmentScanner(name)
        self.scanner.on_reset = self._note_epoch
        self.ingest_offset = 0          # byte cursor into live_path
        self.scan_offset = 0            # absolute cursor into the stream
        self.trim_base = 0              # absolute bytes dropped off the front
        self.pending = b""              # partial trailing line, not yet fed
        self.epoch = 0
        self.epoch_reason = "startup"
        self.epoch_wall = time.time()
        self.pid = None
        self.last_growth = None         # wall time the snapshot last grew

    # -- epoch ------------------------------------------------------------

    def _note_epoch(self, reason):
        """The scanner found an in-log restart and has already cleared its
        counters; record the new epoch. Snapshot surgery is the caller's."""
        self.epoch += 1
        self.epoch_reason = reason
        self.epoch_wall = time.time()

    def bump_epoch(self, reason):
        """An EXTERNAL restart signal (new pid, rotation, first sight).
        Resets everything scoped to a boot, the snapshot included."""
        with self.lock:
            self.scanner.reset(reason)   # -> _note_epoch
            self.truncate_snapshot()

    def truncate_snapshot(self):
        _segments_dir.mkdir(parents=True, exist_ok=True)
        with self.lock:
            try:
                with open(snapshot_path(self.name), "wb"):
                    pass
            except OSError:
                pass
            self.scan_offset = 0
            self.trim_base = 0
            self.pending = b""

    def note_pid(self, pid):
        """A NEW pid is a new clock epoch. A pid of None (process closed)
        leaves everything in place: the lane goes dark via the live flag and
        the frozen log stays inspectable.

        Callers MUST run this before ingest in the same cycle - bump_epoch
        truncates the snapshot but never rewinds ingest_offset, so bytes
        ingested first and truncated after are gone (v2's empty-census bug,
        in its new shape)."""
        prev = self.pid
        if pid == prev:
            return
        self.pid = pid
        if pid is not None and prev is not None:
            self.bump_epoch(f"new {self.name} pid {pid}")

    # -- ingest -----------------------------------------------------------

    def ingest_file(self):
        """Copy the new bytes of an append-only live log into the snapshot.
        A shrinking live file is a rotation, which is a restart signal."""
        if self.live_path is None:
            return
        try:
            size = self.live_path.stat().st_size
        except OSError:
            return
        with self.lock:
            if size < self.ingest_offset:
                self.bump_epoch("log rotated")
                self.ingest_offset = 0
            if size <= self.ingest_offset:
                return
            try:
                with open(self.live_path, "rb") as fh:
                    fh.seek(self.ingest_offset)
                    chunk = fh.read(size - self.ingest_offset)
            except OSError:
                return
            self.ingest_offset = size
        self.append_snapshot(chunk)

    def seed_from_tail(self, want=STARTUP_TAIL):
        """Start ingest near the live log's tail instead of replaying it from
        byte 0. The dashboard's subject is the CURRENT boot; a client log
        spans many of them (and reaches tens of MB during one), and the in-log
        character_select rule trims whatever of this seed belongs to an
        earlier boot."""
        if self.live_path is None:
            return
        try:
            size = self.live_path.stat().st_size
        except OSError:
            return
        start = max(0, size - want)
        if start:
            try:
                with open(self.live_path, "rb") as fh:
                    fh.seek(start)
                    nl = fh.read(1 << 16).find(b"\n")
                start += nl + 1 if nl >= 0 else 0   # begin on a line boundary
            except OSError:
                pass
        with self.lock:
            self.ingest_offset = start

    def append_snapshot(self, data):
        if not data:
            return
        _segments_dir.mkdir(parents=True, exist_ok=True)
        p = snapshot_path(self.name)
        with self.lock:
            try:
                with open(p, "ab") as fh:
                    fh.write(data)
                size = p.stat().st_size
                if size > _SNAPSHOT_CAP:
                    with open(p, "rb") as fh:
                        fh.seek(size - _SNAPSHOT_CAP // 2)
                        keep = fh.read()
                    cut = keep.find(b"\n")       # start the file on a line
                    keep = keep[cut + 1:] if cut >= 0 else keep
                    with open(p, "wb") as fh:
                        fh.write(keep)
                    self.trim_base += size - len(keep)
            except OSError:
                return
            self.last_growth = time.time()

    # -- scan -------------------------------------------------------------

    def scan(self):
        """Feed the snapshot's new bytes to the scanner.

        Lines are cut on newlines through a PARTIAL-LINE BUFFER. The ingest
        chunk boundary lands wherever the writer happened to be, so the last
        line of a chunk is routinely half an event; v2 fed both halves to the
        census as if they were records (the current snapshot on disk starts
        with the fragment "_get call=274301 ..."). Buffering bytes rather
        than text also keeps a split UTF-8 sequence from decoding to U+FFFD."""
        p = snapshot_path(self.name)
        with self.lock:
            try:
                fsize = p.stat().st_size
            except OSError:
                return
            end = self.trim_base + fsize
            if self.scan_offset < self.trim_base:   # trimmed out from under us
                self.scan_offset = self.trim_base
                self.pending = b""
            if self.scan_offset >= end:
                return
            # bounded pass: the collector loops every second, so a backlog
            # (the rig's 20 MB first pull) drains over a few cycles instead of
            # holding this source's lock against every reader for all of it
            end = min(end, self.scan_offset + SCAN_CHUNK)
            try:
                with open(p, "rb") as fh:
                    fh.seek(self.scan_offset - self.trim_base)
                    raw = fh.read(end - self.scan_offset)
            except OSError:
                return
            self.scan_offset = end
            data = self.pending + raw
            parts = data.split(b"\n")
            self.pending = parts.pop()          # incomplete line: hold it back
            lines = [b.decode("utf8", "replace").rstrip("\r") for b in parts]
            restart_at = None
            for i, line in enumerate(lines):
                seq = self.scanner.segment_seq
                self.scanner.feed_line(line)
                if self.scanner.segment_seq != seq:
                    restart_at = i              # this line opened a new boot
            if restart_at is not None:
                self._rewrite_from(lines, restart_at)

    def _rewrite_from(self, lines, idx):
        """An in-log restart landed mid-chunk: the snapshot must hold the new
        boot only, beginning at the line that opened it. The scanner already
        re-fed itself from there, and _note_epoch already moved the epoch, so
        the pane will clear this source on its next poll.

        Bytes this pass never reached (SCAN_CHUNK stopped it short) are carried
        over verbatim - dropping them would silently lose the newest lines of
        the very boot we just switched to."""
        p = snapshot_path(self.name)
        try:
            with open(p, "rb") as fh:
                fh.seek(self.scan_offset - self.trim_base)
                unscanned = fh.read()
        except OSError:
            unscanned = b""
        body = ("\n".join(lines[idx:]) + "\n").encode("utf8") + self.pending
        try:
            with open(p, "wb") as fh:
                fh.write(body + unscanned)
        except OSError:
            return
        self.trim_base = 0
        self.scan_offset = len(body)   # pending sits at the tail of the file

    # -- serve ------------------------------------------------------------

    def read_window(self, cursor, tail_bytes=_PANE_FIRST_TAIL):
        """@return (lines, new_cursor, gap). `cursor` is an absolute stream
        offset; None means "give me the tail". gap=True when the reader had
        fallen behind far enough that bytes were skipped - the pane says so
        rather than pretending the stream was continuous."""
        p = snapshot_path(self.name)
        with self.lock:
            try:
                fsize = p.stat().st_size
            except OSError:
                return [], self.trim_base, False
            end = self.trim_base + fsize
            gap = False
            start = end - tail_bytes if cursor is None else cursor
            if start < self.trim_base:
                start = self.trim_base
                gap = cursor is not None
            if end - start > _PANE_CATCHUP_CAP:
                start = end - _PANE_CATCHUP_CAP
                gap = True
            if start >= end:
                return [], end, False
            # a cursor handed back by a previous call always sits on a line
            # boundary; only a seek (no cursor, or a skip) can land mid-line
            seeked = (cursor is None or gap) and start > self.trim_base
            try:
                with open(p, "rb") as fh:
                    fh.seek(start - self.trim_base)
                    raw = fh.read(end - start)
            except OSError:
                return [], end, False
        parts = raw.split(b"\n")
        partial = parts.pop()                  # not terminated yet: not ours
        new_cursor = end - len(partial)
        if seeked and parts:
            parts = parts[1:]                  # drop the head fragment
        lines = [b.decode("utf8", "replace").rstrip("\r") for b in parts]
        return lines, new_cursor, gap

    def stream_end(self):
        with self.lock:
            try:
                return self.trim_base + snapshot_path(self.name).stat().st_size
            except OSError:
                return self.trim_base


SOURCES = {"mac": SourceState("mac", MAC_LOG),
           "server": SourceState("server", SRV_LOG),
           "rig": SourceState("rig", None)}
CLIENT_SOURCES = ("mac", "rig")
ALL_SOURCES = ("mac", "rig", "server")


# ---------------------------------------------------------------- probes

def mac_client_pid():
    """The mac client = wine64 running destiny2.exe (its cmdline matches;
    pgrep -f 'destiny2.exe' - the dot matches the literal dot, close enough
    for a process-name check)."""
    try:
        r = subprocess.run(["pgrep", "-f", "destiny2.exe"],
                           capture_output=True, text=True, timeout=5)
        pids = r.stdout.split()
        return int(pids[0]) if pids else None
    except Exception:
        return None


def server_process_pid():
    try:
        r = subprocess.run(["pgrep", "-f", "wine64-preloader .*sunrise-server"],
                           capture_output=True, text=True, timeout=5)
        pids = r.stdout.split()
        return int(pids[0]) if pids else None
    except Exception:
        return None


_rig = {"pid": None, "hostname": None, "reachable": None, "error": None,
        "last_ok": None, "remote_offset": None, "syncing": False}


def _ssh(cmd, timeout):
    return subprocess.run(["ssh"] + SSH_OPTS + [RIG_HOST, cmd],
                          capture_output=True, text=True, timeout=timeout)


def rig_client_pid_probe():
    """The rig client via tasklist (cmd.exe native). RIG THREAD ONLY - this
    is an ssh round trip and must never sit on a request path."""
    try:
        r = _ssh('tasklist /FI "IMAGENAME eq destiny2.exe" /FO CSV /NH', 15)
        for line in r.stdout.splitlines():
            if line.strip().lower().startswith('"destiny2.exe"'):
                parts = [p.strip('"') for p in line.split('","')]
                if len(parts) > 1 and parts[1].strip().isdigit():
                    return int(parts[1])
                break
    except Exception:
        pass
    return None


def rig_hostname_probe():
    try:
        r = _ssh("echo %COMPUTERNAME%", 8)
        name = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else None
        if name:
            _rig["hostname"] = name
    except Exception:
        pass
    return _rig["hostname"]


def rig_remote_size():
    try:
        r = _ssh(f'powershell -NoProfile -Command "(Get-Item -LiteralPath'
                 f" '{RIG_LOG}').Length\"", 15)
        m = re.search(r"(\d+)\s*$", r.stdout.strip())
        if m:
            _rig.update(reachable=True, error=None, last_ok=time.time())
            return int(m.group(1))
        _rig.update(reachable=False,
                    error=(r.stderr.strip().splitlines() or ["no size"])[-1][:120])
    except Exception as e:
        _rig.update(reachable=False, error=f"{type(e).__name__}: {e}"[:120])
    return None


def rig_read_range(start, end):
    """Read [start, end) bytes of the rig log (byte-offset delta fetch; a
    live client's log appends, so each cycle pulls only the new tail)."""
    n = end - start
    cmd = (f"$fs=[IO.File]::Open('{RIG_LOG}','Open','Read','ReadWrite');"
           f"$fs.Seek({start},'Begin')|Out-Null;"
           f"$b=New-Object byte[] {n};"
           f"$null=$fs.Read($b,0,{n});"
           f"[Text.Encoding]::UTF8.GetString($b);$fs.Close()")
    try:
        r = _ssh('powershell -NoProfile -Command "' + cmd + '"', 90)
        return r.stdout if r.returncode == 0 or r.stdout else None
    except Exception as e:
        _rig.update(reachable=False, error=f"{type(e).__name__}: {e}"[:120])
        return None


def rig_ingest():
    """Byte-delta pull of the rig log into its snapshot. First sight (or a
    remote rotation) takes the log's last RIG_FIRST_PULL bytes and is one
    epoch bump; afterwards each cycle appends only what is new, so a live
    boot's constant appends never invalidate the clock alignment."""
    size = rig_remote_size()
    if size is None:
        return
    st = SOURCES["rig"]
    prev = _rig["remote_offset"]
    if prev is None or size < prev:
        _rig["syncing"] = True
        try:
            st.bump_epoch("rig log first seen" if prev is None
                          else "rig log rotated")
            start = max(0, size - RIG_FIRST_PULL)
            body = rig_read_range(start, size)
            if body is None:
                return
            st.append_snapshot(body.encode("utf8", "replace"))
            _rig["remote_offset"] = size
        finally:
            _rig["syncing"] = False
        return
    if size > prev:
        end = min(size, prev + RIG_MAX_DELTA)   # one cycle cannot stall
        body = rig_read_range(prev, end)
        if body is None:
            return
        st.append_snapshot(body.encode("utf8", "replace"))
        _rig["remote_offset"] = end


# ------------------------------------------------------------- freshness

SHUTDOWN_RE = re.compile(r"ev=shutdown\b")


def snapshot_last_lines(name, k=3):
    lines, _c, _g = SOURCES[name].read_window(None, tail_bytes=16384)
    return lines[-k:]


def source_age(name):
    """Seconds since this source last produced. mac/server read the LIVE
    file's mtime; the rig has no visible mtime from here, so it reads when
    its snapshot last grew."""
    st = SOURCES[name]
    if st.live_path is not None:
        try:
            return round(time.time() - st.live_path.stat().st_mtime, 1)
        except OSError:
            return None
    return round(time.time() - st.last_growth, 1) if st.last_growth else None


def source_live(name):
    """Producing right now = the log is still being written, the process is
    up, and it did not end in ev=shutdown. A clean quit is a FACT from the
    log, not a timing guess - no 2-minute lingering 'live' after quitting."""
    st = SOURCES[name]
    age = source_age(name)
    if age is None or age >= 120 or st.pid is None:
        return False
    return not any(SHUTDOWN_RE.search(l) for l in snapshot_last_lines(name, 3))


# ------------------------------------------------------------ collectors

def _collector_loop():
    while True:
        try:
            # pids FIRST: bump_epoch truncates the snapshot without rewinding
            # ingest_offset, so anything ingested before a bump is lost
            SOURCES["mac"].note_pid(mac_client_pid())
            SOURCES["server"].note_pid(server_process_pid())
            SOURCES["mac"].ingest_file()
            SOURCES["server"].ingest_file()
            for name in ALL_SOURCES:
                SOURCES[name].scan()
            type_seen_save()
        except Exception:
            pass
        time.sleep(COLLECT_EVERY)


def _rig_loop():
    last_pid = last_host = 0.0
    while True:
        try:
            now = time.time()
            if now - last_pid >= RIG_PID_EVERY:
                last_pid = now
                SOURCES["rig"].note_pid(rig_client_pid_probe())   # before ingest
            if now - last_host >= RIG_HOST_EVERY:
                last_host = now
                rig_hostname_probe()
            rig_ingest()
        except Exception:
            pass
        time.sleep(RIG_INGEST_EVERY)


def _status_loop():
    while True:
        try:
            refresh_server_status()
            refresh_identity()
        except Exception:
            pass
        time.sleep(STATUS_EVERY)


def _health_loop():
    while True:
        try:
            refresh_health()
        except Exception:
            pass
        time.sleep(HEALTH_EVERY)


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
    global _bootflow_order, ALIGN_SPREAD_MAX_MS
    cfg = load_contract()
    if not cfg:
        return None
    order = (cfg.get("bootflow") or {}).get("order")
    if isinstance(order, list) and len(order) >= 2:
        _bootflow_order = order
    spread = (cfg.get("align") or {}).get("max_spread_ms")
    if isinstance(spread, (int, float)) and spread > 0:
        ALIGN_SPREAD_MAX_MS = int(spread)
    pats = {src: [] for src in ALL_SOURCES}
    for c in cfg.get("counters", []):
        src = c.get("source", "server")
        pats.setdefault(src, []).append((c.get("name", "?"), c.get("match", "")))
    for name in ALL_SOURCES:
        sc = SOURCES[name].scanner
        want = pats.get(name, [])
        if want != sc.contract_patterns:
            # the declaration changed under us: old tallies were counting a
            # different question. v2 cleared these on EVERY bind, and bind ran
            # once per 2 s poll - so "front vitals" were a 2-second window
            # wearing a boot-total label.
            sc.contract_patterns = want
            sc.contract_counts = {}
    return cfg


# ------------------------------------------------------------- live data

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


def admin_get(path, timeout=2.0):
    for base in (ADMIN, ADMIN_LOOPBACK):
        try:
            with urlopen(base + path, timeout=timeout) as r:
                return json.loads(r.read().decode("utf8", errors="replace"))
        except Exception:
            continue
    return None


_hash_cache = {}   # path -> ((size, mtime_ns), digest)


def sha16(p):
    """Cached on (size, mtime_ns). v2 re-hashed all four binaries on every
    2-second poll - 128 MB of SHA-256 per tick, on the request thread."""
    try:
        st = Path(p).stat()
    except OSError:
        return None
    key = (st.st_size, st.st_mtime_ns)
    hit = _hash_cache.get(str(p))
    if hit is not None and hit[0] == key:
        return hit[1]
    try:
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
    except OSError:
        return None
    digest = h.hexdigest()[:16]
    _hash_cache[str(p)] = (key, digest)
    return digest


_identity = {"data": {"mac_client": {}, "server": {}}}


def refresh_identity():
    mac, srv = sha16(CLIENT_DLL), sha16(SERVER_EXE)
    bm, bs = sha16(BUILT_CLIENT), sha16(BUILT_SERVER)
    _identity["data"] = {
        "mac_client": {"deployed": mac, "built": bm,
                       "match": mac == bm if mac and bm else None},
        "server": {"deployed": srv, "built": bs,
                   "match": srv == bs if srv and bs else None}}


def identity():
    return _identity["data"]


_status = {"data": {"pid": None, "listeners": {}, "http": False,
                    "sessions": [], "session_count": None, "lobby": None},
           "ts": None}


def refresh_server_status():
    """STATUS THREAD ONLY. lsof plus two admin HTTP calls (2 s timeout each,
    tried against two bases) is up to ~4.5 s of blocking - v2 ran all of it
    inside /api/now.json on a single-threaded server, every 2 seconds."""
    pid = SOURCES["server"].pid
    listeners = {}
    try:
        r = subprocess.run(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"],
                           capture_output=True, text=True, timeout=10)
        for port in ("8443", "30975", "8099"):
            listeners[port] = any(f":{port}\t" in l or f":{port} " in l
                                  for l in r.stdout.splitlines())
    except Exception:
        listeners = {}
    st = admin_get("/state")
    lobby = admin_get("/lobby")
    _status["data"] = {"pid": pid, "listeners": listeners,
                       "http": st is not None,
                       "sessions": (st or {}).get("sessions", []),
                       "session_count": (st or {}).get("count"),
                       "lobby": lobby}
    _status["ts"] = time.time()


def server_status():
    d = dict(_status["data"])
    d["pid"] = SOURCES["server"].pid          # the freshest fact we have
    d["age_s"] = round(time.time() - _status["ts"], 1) if _status["ts"] else None
    return d


def api_now():
    """A pure read of what the background threads have already collected."""
    cfg = bind_contract()
    st = server_status()
    lanes, census, instruments, warns, ages, pids, epochs = {}, {}, {}, {}, {}, {}, {}
    for name in ALL_SOURCES:
        s = SOURCES[name]
        sc = s.scanner
        ages[name] = source_age(name)
        pids[name] = s.pid
        epochs[name] = {"epoch": s.epoch, "reason": s.epoch_reason,
                        "age_s": round(time.time() - s.epoch_wall, 1),
                        "bytes_scanned": s.scan_offset - s.trim_base}
        census[name] = {
            "types": sorted(({"type": k, "count": v,
                              "known": KNOWN_TYPES.get(k)}
                             for k, v in sc.type_counts.items()),
                            key=lambda x: -x["count"]),
            "novel": sorted(sc.novel_types), "lines": None}
        warns[name] = list(sc.warns)[-40:]
    for name in CLIENT_SOURCES:
        s = SOURCES[name]
        lanes[name] = s.scanner.summary(s.scanner.last_t, ages[name],
                                        order=_bootflow_order,
                                        fresh=source_live(name))
        instruments[name] = sorted(s.scanner.instruments.values(),
                                   key=lambda r: r["fn"])
    lanes["segment"] = {n: len(SOURCES[n].scanner.stages) for n in CLIENT_SOURCES}
    counters = []
    if cfg:
        for c in cfg.get("counters", []):
            src = c.get("source", "server")
            nm = c.get("name", "?")
            counters.append({"name": nm, "why": c.get("why", ""), "source": src,
                             "value": SOURCES[src].scanner.contract_counts.get(nm, 0)
                             if src in SOURCES else 0})
    dead = [f"{r['fn']} ({src})" for src in CLIENT_SOURCES
            for r in instruments[src] if r.get("attached") == "0"]
    return {
        "server": st, "identity": identity(),
        "lanes": lanes,
        "contract": {"declared": bool(cfg), "front": (cfg or {}).get("front"),
                     "updated": (cfg or {}).get("updated"),
                     "stale": contract_stale(cfg) if cfg else None,
                     "counters": counters},
        "census": census, "instruments": instruments, "dead_probes": dead,
        "warns": warns,
        "hostnames": {"mac": os.uname().nodename, "rig": _rig["hostname"]},
        "client_pids": {n: pids[n] for n in CLIENT_SOURCES},
        "epochs": epochs,
        "rig": {"reachable": _rig["reachable"], "error": _rig["error"],
                "syncing": _rig["syncing"],
                "last_ok_s": round(time.time() - _rig["last_ok"], 1)
                if _rig["last_ok"] else None},
        "tail_age": ages,
        "ts": datetime.now().isoformat(timespec="seconds")}


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


# per-source clock offsets, cached across merges: an offset is a property of
# the CLIENT PROCESS CLOCK (boot), not of traffic - once anchored for the
# current boot it stays valid until that boot ends, even when fresh anchors
# stop flowing (idle Tower, client quit). Keyed by the source's BOOT EPOCH.
# Each entry carries the evidence alignment_view() gates on, not just the
# number: {"offset": int, "spread": int|None, "pairs": int, "epoch": int}.
# v2 stored the offset alone, so nothing downstream could tell a 2 ms
# alignment from a 31 s guess.
_clock_offsets = {"mac": None, "server": None, "rig": None}
WINDOW_MS = 10 * 60 * 1000  # merge windows cover the last 10 wall-minutes


def write_merge_window(src, cutoff_t):
    """The merge window: snapshot lines with t >= cutoff_t (a bounded recent
    window - the constant-k matcher cannot lock over full history)."""
    p = snapshot_path(src)
    out = snapshot_path(src).with_suffix(".window")
    try:
        lines = []
        # under the source lock: _rewrite_from can replace this file whole,
        # and a torn read of it becomes garbage anchors in the drift report
        with SOURCES[src].lock, open(p, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - 32 * 1024 * 1024))
            for raw in fh.read().decode("utf8", errors="replace").splitlines():
                m = re.search(r"\bt=(\d+)", raw)
                if m and int(m.group(1)) >= cutoff_t:
                    lines.append(raw)
        out.write_text("\n".join(lines) + "\n", encoding="utf8")
        return out.exists() and out.stat().st_size > 0
    except OSError:
        return False


def merge_cutoffs():
    """Per-source cutoff t = now_t - WINDOW_MS in each source's own clock.
    The SERVER's window must cover the CLIENTS' period, not just its own
    last 10 minutes: when the clients have closed, their windows freeze at
    the boot period while the server's clock keeps advancing - a server
    window of 'its own last 10 min' would hold zero client-era pushes and
    the anchors would never pair. So the server reaches back to the
    earliest client-log mtime (its last write) minus the window."""
    cut = {"mac": None, "server": None, "rig": None}
    for src, path in (("mac", MAC_LOG), ("server", SRV_LOG)):
        nt = file_now_t(path)
        if nt is not None:
            cut[src] = max(0, nt - WINDOW_MS)
    try:
        nt = file_now_t(snapshot_path("rig"))
        if nt is not None:
            cut["rig"] = max(0, nt - WINDOW_MS)
    except OSError:
        pass
    # the server reaches back to its clients' period (see docstring)
    try:
        client_mt = min(p.stat().st_mtime for p in
                        (MAC_LOG, snapshot_path("rig")) if p.exists())
        srv_now_t = cut["server"]
        srv_now_wall = SRV_LOG.stat().st_mtime
        span_wall = max(0.0, srv_now_wall - (client_mt - 600))
        if srv_now_t is not None:
            cut["server"] = max(0, srv_now_t - int(span_wall * 1000) - 60000)
    except OSError:
        pass
    return cut


def maybe_realign(force=False):
    """Re-run merge_timeline over bounded recent windows of the snapshots
    when any of them changed (background thread; the API only reads results).
    Per-source outcomes: anchored -> cache the offset for that segment gen;
    native_null -> KEEP the cached offset (the clock did not change just
    because traffic got quiet).
    Cross-process lockfile: a manual run and the service thread must never
    merge concurrently - a window rewrite during another run's read produces
    empty parses (the 0-anchors race)."""
    lock = ROOT / "RE_output/dashboard/align.lock"
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
    except FileExistsError:
        # stale-lock recovery: a SIGKILLed holder (restart mid-align) leaves
        # the lock behind; steal it when the recorded pid no longer exists
        try:
            holder = int(lock.read_text().strip() or "0")
            os.kill(holder, 0)
            return  # a live process really is aligning
        except (ValueError, ProcessLookupError, PermissionError):
            pass  # pid gone (or unparsable) -> orphaned lock, steal it
        except OSError as e:
            if e.errno == 3:  # ESRCH: no such process
                pass
            else:
                return
        try:
            os.unlink(str(lock))
        except OSError:
            return
        return maybe_realign(force=force)
    try:
        _maybe_realign_locked(force=force)
    finally:
        try:
            os.unlink(str(lock))
        except OSError:
            pass


def _maybe_realign_locked(force=False):
    now = time.time()
    if _align_state["running"]:
        return
    if not force and now - _align_state["ts"] < ALIGN_EVERY:
        return
    sig = _snapshot_sig()   # the rig thread owns rig ingest (one ingest path)
    if not force and sig == _align_state["sig"]:
        _align_state["ts"] = now  # nothing changed; skip quietly
        return
    # bounded merge windows (the matcher cannot lock over full history)
    cut = merge_cutoffs()
    inputs = {}
    for src in ("mac", "server", "rig"):
        if write_merge_window(src, cut[src]):
            inputs[src] = snapshot_path(src).with_suffix(".window")
    if "server" not in inputs:
        _align_state["ts"] = now
        return  # nothing to anchor against
    _align_state["running"] = True
    try:
        cmd = ["/usr/bin/python3", str(ROOT / "RE_scripts/merge_timeline.py"),
               f"--server-log=server={inputs['server']}"]
        for src in ("mac", "rig"):
            if src in inputs:
                cmd.append(f"--client-log={src}={inputs[src]}")
        cmd.append("--out")
        cmd.append(str(ROOT / "RE_output/dashboard/merge"))
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        # the merge must never fail silently (U13): every run logs its rc and
        # the stderr tail - the stale drift went unnoticed for 25 minutes
        # because the refresher swallowed its own failures
        try:
            with open(ROOT / "RE_output/dashboard/align.log", "a",
                      encoding="utf8") as fh:
                fh.write(f"[{datetime.now().isoformat(timespec='seconds')}] "
                         f"rc={r.returncode} "
                         + (r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "-")
                         + " | stderr_tail="
                         + ((r.stderr.strip().splitlines()[-1][:200]) if r.stderr.strip() else "-")
                         + "\n")
        except OSError:
            pass
        if r.returncode == 0:
            # cache per-source offsets for the CURRENT boot epoch, WITH the
            # spread that says whether the offset means anything
            try:
                drift = json.loads((ROOT / "RE_output/dashboard/merge.drift.json")
                                   .read_text(encoding="utf8"))
                for s in drift.get("sources", []):
                    label = (s.get("source") or "?").split("/")[0]
                    if label in _clock_offsets and s.get("offset_ms") is not None:
                        spread = s.get("robust_spread_ms")
                        if spread is None:
                            spread = s.get("spread_ms")
                        _clock_offsets[label] = {
                            "offset": s["offset_ms"],
                            "spread": spread,
                            "pairs": s.get("anchor_pairs") or 0,
                            "epoch": SOURCES[label].epoch}
                        # native_null: keep the cached offset (clock unchanged)
            except Exception:
                pass
        meta = {"epochs": {n: SOURCES[n].epoch for n in ALL_SOURCES},
                "computed": time.time()}
        (ROOT / "RE_output/dashboard/merge.meta.json").write_text(
            json.dumps(meta), encoding="utf8")
        _align_state["sig"] = sig
        _align_state["ts"] = time.time()
    except Exception:
        _align_state["ts"] = time.time()  # retry after the cadence
    finally:
        _align_state["running"] = False


def alignment_view():
    """@return (ok, meta): which sources may share one timeline, and WHY the
    others may not.

    An offset is used only when (a) it was computed for that source's CURRENT
    boot epoch and (b) its own anchor pairs agree to within
    ALIGN_SPREAD_MAX_MS. v2 checked neither. It took offset_ms straight out
    of the drift report and painted a green "clocks: ALIGNED" chip over a mac
    offset whose robust spread was 31 s and a rig offset whose spread was
    20 s, then sorted the merged view on them - which is how the pane came to
    be dominated by whichever source carried the largest offset. A failing
    source now renders in its own column with the reason printed on it."""
    offsets, why, detail = {}, {}, {}
    for src in ALL_SOURCES:
        st = SOURCES[src]
        c = _clock_offsets.get(src)
        detail[src] = c
        if c is None:
            why[src] = "no anchors yet"
        elif c.get("epoch") != st.epoch:
            why[src] = "new boot - re-anchoring"
        elif c.get("spread") is not None and c["spread"] > ALIGN_SPREAD_MAX_MS:
            why[src] = ("anchors disagree by +/-%.1fs over %d pairs (need +/-%.1fs)"
                        % (c["spread"] / 1000.0, c.get("pairs") or 0,
                           ALIGN_SPREAD_MAX_MS / 1000.0))
        else:
            offsets[src] = c["offset"]
    ok = "server" in offsets and len(offsets) >= 2
    if not ok:   # a one-source "merge" is not a merge
        for src in list(offsets):
            why[src] = "waiting on the server plus one client to anchor"
        offsets = {}
    return ok, {"reference": "server", "offsets": offsets, "unaligned": why,
                "max_spread_ms": ALIGN_SPREAD_MAX_MS, "detail": detail}


_T_RE = re.compile(r"\bt=(\d+)")
_PANE_BATCH_CAP = 2000   # lines one source may return in one poll


def _row(raw, offset):
    m = _T_RE.search(raw)
    t = int(m.group(1)) if m else None
    return {"t": t, "tu": (t - offset) if (t is not None and offset is not None)
            else None, "line": raw.rstrip()}


def api_tail(args):
    """Incremental, epoch-aware, straight off the live snapshots.

    The pane holds a byte CURSOR and an EPOCH per source and gets back only
    what is new, so it appends instead of re-rendering and a poll costs the
    last 2 seconds rather than the last 300 lines. When a source's epoch has
    moved, that source alone is reset: the pane drops its rows, prints a
    divider, and takes a fresh tail - the other sources keep streaming.

    v2 served this from the tail of a 217 MB merge.jsonl that the aligner
    rewrote about every 53 s, so a 2-second poll re-read a file that changed
    once a minute; and a single client restart dropped the whole pane from
    merged mode to per-source blocks while merge.jsonl still held the
    previous boot's rows."""
    def one(k, d=None):
        v = args.get(k)
        return v[0] if v else d

    try:
        n = min(max(int(one("n", "300") or 300), 50), 1200)
    except ValueError:
        n = 300
    flt = (one("filter", "") or "").lower()
    level = one("level", "all") or "all"
    # an ABSENT param defaults to all; an explicitly EMPTY list means none
    # (the all-off bug: "" is falsy, so `or` used to substitute the default)
    if "sources" in args:
        want = [s for s in (args["sources"][0] or "").split(",") if s in SOURCES]
    else:
        want = list(ALL_SOURCES)
    aligned, meta = alignment_view()
    out = {}
    for src in want:
        st = SOURCES[src]
        epoch = st.epoch
        try:
            client_epoch = int(one("ep_" + src, ""))
        except (TypeError, ValueError):
            client_epoch = None
        try:
            cursor = int(one("cur_" + src, ""))
        except (TypeError, ValueError):
            cursor = None
        reset = client_epoch != epoch      # a first poll resets too
        if reset:
            cursor = None
        # a filtered reset needs more history to find matches in
        tail = _PANE_CATCHUP_CAP if (flt or level != "all") \
            else min(_PANE_CATCHUP_CAP, max(n * 400, _PANE_FIRST_TAIL))
        lines, new_cursor, gap = st.read_window(cursor, tail_bytes=tail)
        shown, hidden = [], 0
        off = meta["offsets"].get(src)
        for raw in lines:
            if flt and flt not in raw.lower():
                hidden += 1
                continue
            if level != "all" and ("level=" + level) not in raw:
                hidden += 1
                continue
            shown.append(_row(raw, off))
        if reset:
            shown = shown[-n:]
        elif len(shown) > _PANE_BATCH_CAP:
            shown = shown[-_PANE_BATCH_CAP:]
            gap = True
        out[src] = {"epoch": epoch, "epoch_reason": st.epoch_reason,
                    "reset": reset, "gap": gap, "cursor": new_cursor,
                    "rows": shown, "hidden": hidden, "pid": st.pid,
                    "age": source_age(src), "live": source_live(src),
                    "aligned": off is not None,
                    "unaligned_why": meta["unaligned"].get(src),
                    "error": (_rig["error"] if src == "rig"
                              and _rig["reachable"] is False else None),
                    "syncing": _rig["syncing"] if src == "rig" else False}
    return {"aligned": aligned, "drift": meta, "sources": out,
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
.chip { display:inline-block; margin-left:8px; padding:1px 8px; border:1px solid var(--edge); border-radius:10px; font-size:11px; vertical-align:middle; }
#logbox { display:flex; gap:8px; height:460px; overflow:hidden; background:transparent; border:none; padding:0; }
.logcol { flex:1 1 0; min-width:0; display:flex; flex-direction:column; background:#0a0d12; border:1px solid var(--edge); border-radius:6px; }
.colhead { padding:4px 8px; border-bottom:1px solid var(--edge); font-size:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; flex:0 0 auto; }
.colbody { flex:1 1 auto; overflow-y:auto; padding:6px; min-height:0; }
.divider { border-top:1px dashed var(--warn); color:var(--warn); margin:8px 0 4px; padding-top:4px; font-size:11px; font-weight:bold; }
.gapmark { color:var(--warn); font-size:11px; padding:2px 0; }
.why { color:var(--warn); }
.hidden-note { color:var(--dim); font-size:11px; padding-top:4px; }
.dot { display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:5px; vertical-align:middle; }
.dot.on { background:var(--ok); } .dot.off { background:#3a424d; } .dot.err { background:var(--err); }
</style></head><body>
<div class="panel" id="banner">
  <b>Sunrise project dashboard</b>
  <span id="serverchip" class="chip dim">server: ?</span>
  <span id="idchip" class="chip dim">builds: ?</span>
  <span id="alignedchip" class="chip dim">clocks: ?</span>
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
      <div class="sub">contract counters <span style="text-transform:none">(totals for the current boot)</span></div>
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

var PROMOTED = {level:1, ev:1, stage:1, result:1, fn:1, type:1, t:1};
function fmtRow(src, raw, tu, showSrc){
  var d = el("div","lr");
  d.setAttribute("data-src", src);
  if (showSrc) d.appendChild(el("span","src-"+src, "["+src+"] "));
  // tokenise ONCE into k=v pairs plus the free text between them, so a field
  // promoted into the header is not also emitted in the body. v2 rendered
  // the header chips and then re-rendered the whole line from after t=,
  // deduping only the server's exact "ev stage " prefix - so every client
  // line printed its ev/stage/fn twice ("fn=ent_make ev=mtrace stage=census
  // why=periodic fn=ent_make ...").
  var toks = [], kv = {}, re = /([A-Za-z_][A-Za-z0-9_.-]*)=(\S*)/g, m, last = 0;
  while ((m = re.exec(raw)) !== null){
    if (m.index > last) toks.push({text: raw.slice(last, m.index)});
    toks.push({k: m[1], v: m[2]});
    if (!(m[1] in kv)) kv[m[1]] = m[2];
    last = m.index + m[0].length;
  }
  if (last < raw.length) toks.push({text: raw.slice(last)});
  var tm = (tu !== undefined && tu !== null) ? String(tu) : kv.t;
  if (tm) d.appendChild(el("span","muted","t="+tm+" "));
  if (kv.level==="warn"||kv.level==="error") d.appendChild(el("span","f-lvl-"+kv.level, kv.level+" "));
  if (kv.ev) d.appendChild(el("span","f-ev","ev="+kv.ev+" "));
  if (kv.stage) d.appendChild(el("span","f-stage","stage="+kv.stage+" "));
  if (kv.result) d.appendChild(el("span", kv.result==="ok"?"f-res-ok":"f-res-bad","result="+kv.result+" "));
  if (kv.fn) d.appendChild(el("span","f-fn","fn="+kv.fn+" "));
  if (kv.type) d.appendChild(el("span","f-stage","type="+kv.type+" "));
  var sawKv = false;
  toks.forEach(function(tk){
    if (tk.k !== undefined){
      sawKv = true;
      if (PROMOTED[tk.k]) return;            // already in the header
      d.appendChild(el("span","muted", tk.k+"="));
      d.appendChild(el("span","", tk.v+" "));
    } else if (sawKv && tk.text.trim()){
      d.appendChild(el("span","", tk.text.trim()+" "));   // free-text message
    }
    // leading free text before the first k=v is the log's own "client"/
    // "server" word - the column header already says which source this is
  });
  return d;
}
function warnShape(raw){ return raw.replace(/t=\d+/g,"t=N").replace(/\d{6,}/g,"N").slice(0,120); }

function renderLane(name, bf, ep){
  var wrap = el("div","lane");
  var who = el("div");
  who.appendChild(el("span","who src-"+name, name));
  if (!bf.live && bf.producing){
    who.appendChild(el("span","warn","  producing, but no ev=bootflow stage in this boot yet"));
  } else if (!bf.live){
    who.appendChild(el("span","muted","  no live boot"
      + (bf.stale!==null && bf.stale!==undefined ? " (last write "+Math.round(bf.stale)+"s ago)" : "")));
  } else if (bf.current){
    who.appendChild(el("span","muted","  now: "+bf.current
      + (bf.dwell_ms!==null ? " ("+Math.round(bf.dwell_ms/1000)+"s)" : "")));
  }
  // the boot epoch is the answer to "am I looking at this run or the last
  // one" - the single question a restart used to make unanswerable
  if (ep) who.appendChild(el("span","muted","  · boot #"+ep.epoch+" ("+ep.reason+", "+Math.round(ep.age_s)+"s ago)"));
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
      var rigTxt = "rig="+(d.hostnames.rig||"?");
      if (d.rig && d.rig.reachable === false) rigTxt += " UNREACHABLE ("+(d.rig.error||"?")+")";
      else if (d.rig && d.rig.syncing) rigTxt += " (syncing log...)";
      H.textContent = "mac="+d.hostnames.mac+"  "+rigTxt;
      swapIfChanged("lanes", function(L){
        [["mac",d.lanes.mac],["rig",d.lanes.rig]].forEach(function(p){
          L.appendChild(renderLane(p[0], p[1], d.epochs[p[0]]));
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
          var w = el("div"); w.appendChild(fmtRow(src, raw, null, true)); w.appendChild(el("span","muted"," x1"));
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

// --------------------------------------------------------------- log pane
// The pane keeps a byte CURSOR and an EPOCH per source and APPENDS what
// comes back. Two consequences worth stating: scrolling up no longer stops
// the stream (v2 only polled while `follow` was checked - reading history
// froze the log), and a client restart clears exactly that client's column
// instead of flipping the whole pane into another rendering mode.
var SRC = {mac: true, rig: true, server: true};
var CUR = {}, EPOCH = {}, RATE = {}, LASTPOLL = null;
var LAYOUT = "";
var MAXROWS = 4000;

function toggleSrc(name, btn){
  SRC[name] = !SRC[name];
  btn.classList.toggle("active", SRC[name]);
  resetPane();
}
function resetPane(){
  CUR = {}; EPOCH = {}; RATE = {}; LASTPOLL = null; LAYOUT = "";
  box.textContent = "";
  pollTail();
}
function activeSources(){ return ["mac","rig","server"].filter(function(s){ return SRC[s]; }); }

function ensureLayout(cols){
  var sig = cols.join(",");
  if (LAYOUT === sig) return;
  LAYOUT = sig;
  box.textContent = "";
  cols.forEach(function(c){
    var col = el("div","logcol"); col.id = "col-"+c;
    col.appendChild(el("div","colhead")).id = "colhead-"+c;
    var body = el("div","colbody"); body.id = "colbody-"+c;
    body.addEventListener("scroll", onColScroll);
    col.appendChild(body);
    box.appendChild(col);
  });
}
var SUPPRESS_SCROLL = 0;
function onColScroll(ev){
  // scrolling up = the user wants history: drop out of follow (and re-engage
  // at the bottom). The suppress counter keeps our own scroll writes from
  // reading as user intent.
  if (SUPPRESS_SCROLL > 0){ SUPPRESS_SCROLL--; return; }
  var b = ev.target;
  var atBottom = b.scrollHeight - b.scrollTop - b.clientHeight < 40;
  var follow = document.getElementById("follow");
  if (!atBottom && follow.checked) follow.checked = false;
  else if (atBottom && !follow.checked) follow.checked = true;
}
function appendRows(bodyId, nodes){
  var body = document.getElementById(bodyId);
  if (!body || !nodes.length) return;
  var frag = document.createDocumentFragment();
  nodes.forEach(function(nd){ frag.appendChild(nd); });
  body.appendChild(frag);
  // trim only while pinned to the bottom; trimming under a reader who has
  // scrolled up would yank the text out from under them
  if (document.getElementById("follow").checked){
    while (body.childNodes.length > MAXROWS) body.removeChild(body.firstChild);
  }
}
function followAll(){
  if (!document.getElementById("follow").checked) return;
  Array.prototype.forEach.call(box.querySelectorAll(".colbody"), function(b){
    if (b.scrollHeight - b.scrollTop - b.clientHeight > 2){ SUPPRESS_SCROLL++; b.scrollTop = b.scrollHeight; }
  });
}
function head(src, sd, extra){
  var h = document.getElementById("colhead-"+src);
  if (!h) return;
  h.textContent = "";
  var live = sd.live, cls = sd.error ? "err" : (live ? "on" : "off");
  h.appendChild(el("span","dot "+cls));
  h.appendChild(el("span","src-"+src, src));
  var bits = [];
  if (sd.pid) bits.push("pid "+sd.pid);
  if (sd.age !== null && sd.age !== undefined) bits.push(sd.age+"s");
  if (RATE[src] !== undefined) bits.push(RATE[src].toFixed(0)+"/s");
  bits.push("boot #"+sd.epoch);
  if (sd.hidden) bits.push(sd.hidden+" filtered");
  h.appendChild(el("span","muted"," "+bits.join(" · ")));
  if (sd.error) h.appendChild(el("span","why"," "+sd.error));
  else if (sd.syncing) h.appendChild(el("span","muted"," syncing..."));
  else if (extra) h.appendChild(el("span","why"," "+extra));
}

function pollTail(){
  once("tail", function(){
    var srcs = activeSources();
    if (!srcs.length){
      box.textContent = ""; LAYOUT = "";
      box.appendChild(el("div","muted","all sources hidden - toggle one back on above"));
      return Promise.resolve();
    }
    var q = "?n="+document.getElementById("nlinesel").value;
    var f = document.getElementById("filter").value;
    if (f) q += "&filter="+encodeURIComponent(f);
    var lv = document.getElementById("levelsel").value;
    if (lv !== "all") q += "&level="+lv;
    q += "&sources=" + srcs.join(",");   // sent ALWAYS - an empty list must
    // mean "show nothing", not "default to everything" (the all-off bug)
    srcs.forEach(function(s){
      if (CUR[s] !== undefined) q += "&cur_"+s+"="+CUR[s];
      if (EPOCH[s] !== undefined) q += "&ep_"+s+"="+EPOCH[s];
    });
    return fetch("/api/tail.json"+q).then(function(r){return r.json();}).then(function(d){
      var now = Date.now();
      var dt = LASTPOLL ? (now - LASTPOLL)/1000 : null;
      LASTPOLL = now;
      var merged = d.aligned;
      ensureLayout(merged ? ["timeline"] : srcs);
      if (merged){
        var h = document.getElementById("colhead-timeline");
        h.textContent = "merged timeline (reference: server, offsets applied)";
      }
      var pool = [];
      srcs.forEach(function(s){
        var sd = d.sources[s]; if (!sd) return;
        if (dt) RATE[s] = (sd.rows.length + sd.hidden) / dt;
        var target = merged ? "colbody-timeline" : "colbody-"+s;
        if (sd.reset){
          // this source alone restarted: drop its rows, mark the boundary
          if (merged){
            Array.prototype.forEach.call(box.querySelectorAll('[data-src="'+s+'"]'),
              function(nd){ nd.remove(); });
          } else {
            var b = document.getElementById(target); if (b) b.textContent = "";
          }
          var div = el("div","divider", "— new boot · "+s+(sd.pid?" · pid "+sd.pid:"")+" · "+sd.epoch_reason+" —");
          div.setAttribute("data-src", s);
          appendRows(target, [div]);
        }
        if (sd.gap){
          var g = el("div","gapmark","⋯ fell behind; older lines skipped ⋯");
          g.setAttribute("data-src", s);
          appendRows(target, [g]);
        }
        CUR[s] = sd.cursor; EPOCH[s] = sd.epoch;
        if (merged){ sd.rows.forEach(function(r){ pool.push({s:s, r:r}); }); }
        else { appendRows(target, sd.rows.map(function(r){ return fmtRow(s, r.line, r.tu, false); })); }
        if (!merged) head(s, sd, sd.aligned ? null : sd.unaligned_why);
      });
      if (merged && pool.length){
        pool.sort(function(a,b){ return (a.r.tu||0) - (b.r.tu||0); });
        appendRows("colbody-timeline", pool.map(function(p){ return fmtRow(p.s, p.r.line, p.r.tu, true); }));
      }
      followAll();
      // the alignment chip states the CLAIM and, when it fails, the reason -
      // v2 said ALIGNED over offsets whose own anchors disagreed by 31s
      var dr = d.drift || {};
      var una = dr.unaligned || {};
      if (d.aligned){
        chipText("alignedchip", "clocks: ALIGNED ("+Object.keys(dr.offsets||{}).join("+")+")", "ok");
      } else {
        var reasons = Object.keys(una).map(function(k){ return k+": "+una[k]; });
        chipText("alignedchip", "clocks: NOT aligned — "+(reasons[0]||"no anchors"), "warn");
        document.getElementById("alignedchip").title = reasons.join("\n");
      }
    });
  });
}

function pollHealth(){
  once("health", function(){
    return fetch("/api/health.json").then(function(r){return r.json();}).then(function(d){
      if (d.pending){ document.getElementById("health").textContent = "tooling: first check running..."; return; }
      var parts = [];
      [["registry",d.registry],["preflight",d.preflight],["gate fixture",d.gate_fixture],["index lint",d.index_fresh]].forEach(function(p){
        if (p[1]) parts.push((p[1].rc===0?"ok ":"FLAG ")+p[0]);
      });
      document.getElementById("health").textContent = "tooling: "+parts.join(" | ")+" ("+String(d.ts).slice(11)+")";
    });
  });
}
// a filter/level/size change changes what the cursors mean: start clean
document.getElementById("filter").addEventListener("input", resetPane);
document.getElementById("levelsel").addEventListener("change", resetPane);
document.getElementById("nlinesel").addEventListener("change", resetPane);
document.getElementById("follow").addEventListener("change", followAll);
// ALWAYS poll: `follow` controls auto-scroll, not whether the log updates
setInterval(function(){ pollTail(); pollNow(); }, 2000);
setInterval(pollHealth, 60000);
pollTail(); pollNow(); pollHealth();
setInterval(function(){ document.getElementById("clock").textContent = new Date().toLocaleTimeString(); }, 1000);
</script></body></html>
"""


_health = {"data": None, "ts": None}


def refresh_health():
    """HEALTH THREAD ONLY. Four subprocesses at 120 s timeouts each - v2 ran
    all of them inside /api/health.json's handler on a single-threaded
    server, so one cache miss could freeze the whole page for minutes."""
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
    _health.update(data=data, ts=time.time())
    return data


def health():
    if _health["data"] is None:
        return {"pending": True, "ts": datetime.now().isoformat(timespec="seconds")}
    d = dict(_health["data"])
    d["age_s"] = round(time.time() - _health["ts"], 1)
    return d


def make_handler(port, lan):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

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
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

    bind = "0.0.0.0" if lan else "127.0.0.1"
    # THREADED: v2 used HTTPServer, so a slow /api/now.json (two ssh calls to
    # the rig at 15 s and 10 s timeouts) queued every other request behind it
    return ThreadingHTTPServer((bind, port), H)


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
    ap.add_argument("--no-rig", action="store_true",
                    help="skip the rig thread entirely (rig powered down)")
    ap.add_argument("--no-align", action="store_true",
                    help="skip the clock-alignment merge (it is expensive)")
    args = ap.parse_args(argv)
    if not args.serve:
        print(__doc__)
        return 2
    # every source starts on a clean segment: a snapshot left behind by a
    # previous run belongs to a boot this process never saw
    for name in ALL_SOURCES:
        SOURCES[name].bump_epoch("dashboard started")
        SOURCES[name].seed_from_tail()
    bind_contract()
    httpd = make_handler(args.port, args.lan)
    bind, port = httpd.server_address[:2]
    print(f"project dashboard: http://{bind}:{port}/  (Ctrl-C to stop; read-only)")
    threads = [("collector", _collector_loop), ("status", _status_loop),
               ("health", _health_loop)]
    if not args.no_rig:
        threads.append(("rig", _rig_loop))
    if not args.no_align:
        threads.append(("align", _align_loop))
    for name, fn in threads:
        threading.Thread(target=fn, name=name, daemon=True).start()
    print("background threads: " + ", ".join(n for n, _ in threads))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
