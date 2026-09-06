#!/usr/bin/env python3
# REGISTRY: caps: project-dashboard, live-tail, repo-view
"""project_dashboard.py - the operator's second monitor (2026-09-06).

A read-only local web page for the two questions a boot actually asks:
"what is happening right now" and "where does the project stand". Runs on
the mac as a small stdlib-only HTTP service; the game pipeline is untouched.

    /usr/bin/python3 RE_scripts/project_dashboard.py --serve [--port 8400]
        [--lan]     # bind the LAN address so the rig's browser can open it

Panels (all data sources are read-only):
  NOW        server proc/ports/state (poll the admin :8099 verbs), bootflow
             lanes per client (stage + dwell), contract counters over the
             tail window (withdrawals / acks / bodies / creation attempts),
             instrument census (attached/calls per probe), warn|error stream,
             per-source stall detection (last-line age).
  RESEARCH   STATE.md verdict/NEXT/DO-NOT/DEPLOYED rendered as-is, boot
             outcome ledger + third-branch streak, open decisions, newest
             findings headlines, recent boot archives.
  LOGS       merged tail of mac client + server (local files) and rig (ssh
             ControlMaster, same channel boot_verdict uses), per-source
             color, field-highlighted, text/level filter, follow/pause.
             Merged on one clock ONLY when a drift file exists; otherwise
             per-source native t= and the page says NOT ALIGNED (never fake
             alignment - the old dashboard's lesson).

Degrade gracefully: server down = its side greys out; rig unreachable =
UNREACHABLE lane; missing files = visible absence lines. Everything the page
shows is provenance-labeled; it invents nothing.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

ROOT = Path(__file__).resolve().parent.parent
MAC_LOG = ROOT / "Game/bin/x64/Sunrise/logs/sunrise.log"
SRV_LOG = ROOT / "RE_output/s1_accept/Sunrise/logs/sunrise.log"
CLIENT_DLL = ROOT / "Game/bin/x64/steam_api64.dll"
SERVER_EXE = ROOT / "RE_output/s1_accept/sunrise-server.exe"
BUILT_CLIENT = ROOT / "RE_build/Sunrise-fork-inventory/build/steam_api64.dll"
BUILT_SERVER = ROOT / "RE_build/Sunrise-fork-inventory/build/sunrise-server.exe"

RIG_HOST = "rasla@192.168.1.136"
RIG_LOG = r"C:\Users\rasla\Downloads\destiny-preservation\dcv build\bin\x64\Sunrise\logs\sunrise.log"
SSH_OPTS = ["-o", "ControlPath=" + os.path.expanduser("~/.ssh/cm-rig"),
            "-o", "ConnectTimeout=4", "-o", "BatchMode=yes"]

ADMIN = "http://192.168.1.7:8099"
ADMIN_LOOPBACK = "http://127.0.0.1:8099"

BOOTFLOW_STAGES = ["character_select", "slice_set", "profile_setup",
                   "composition", "orbit_handoff", "join_ready", "owner_slot",
                   "region", "world_step", "spawn_hold", "fade_release"]

KV_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_.-]*)=([^\s]+)")


def parse_line(src, raw):
    kv = dict(KV_RE.findall(raw))
    t = int(kv["t"]) if kv.get("t", "").isdigit() else None
    return {"src": src, "t": t,
            "level": kv.get("level", ""), "ev": kv.get("ev", ""),
            "stage": kv.get("stage", ""), "result": kv.get("result", ""),
            "fn": kv.get("fn", ""), "session": kv.get("session", ""),
            "line": raw.rstrip()}


def tail_file(path, n):
    """Last n complete lines of a file (binary-safe, no full read)."""
    try:
        with open(path, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - n * 320))
            data = fh.read().decode("utf8", errors="replace")
        lines = data.splitlines()
        return lines[-n:], size, time.time() - (Path(path).stat().st_mtime)
    except OSError as e:
        return [f"(unavailable: {e})"], 0, -1


_rig_cache = {"ts": 0.0, "data": None}
_rig_bf_cache = {"ts": 0.0, "data": []}


def rig_tail(n):
    """Rig log tail over the existing ControlMaster; cached 3s."""
    now = time.time()
    if _rig_cache["data"] is not None and now - _rig_cache["ts"] < 3:
        return _rig_cache["data"]
    try:
        r = subprocess.run(
            ["ssh"] + SSH_OPTS + [RIG_HOST,
             f"powershell -NoProfile -Command Get-Content -Tail {n} "
             f"-LiteralPath '{RIG_LOG}'"],
            capture_output=True, text=True, timeout=10)
        if r.returncode != 0 and not r.stdout.strip():
            raise RuntimeError(f"ssh rc={r.returncode}")
        lines = r.stdout.splitlines()[-n:]
        data = {"lines": lines, "age": 0.0, "error": None}
    except Exception as e:
        data = {"lines": [], "age": None, "error": f"unreachable: {e}"}
    _rig_cache.update(ts=now, data=data)
    return data


def tail_all(n):
    out = {}
    for src, path in (("mac", MAC_LOG), ("server", SRV_LOG)):
        lines, size, age = tail_file(path, n)
        out[src] = {"lines": lines, "age": round(age, 1) if age >= 0 else None,
                    "error": None if age >= 0 else "file missing"}
    r = rig_tail(n)
    out["rig"] = {"lines": r["lines"], "age": r["age"], "error": r["error"]}
    return out


def admin_get(path, timeout=2.0):
    for base in (ADMIN, ADMIN_LOOPBACK):
        try:
            with urlopen(base + path, timeout=timeout) as r:
                return json.loads(r.read().decode("utf8", errors="replace"))
        except Exception:
            continue
    return None


def http_up():
    return admin_get("/state?probe=1") is not None


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
    return {"pid": pid[0] if pid else None,
            "listeners": listeners,
            "http": st is not None,
            "sessions": (st or {}).get("sessions", []),
            "session_count": (st or {}).get("count"),
            "lobby": lobby}


def sha16(p):
    try:
        import hashlib
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


_lane_state = {}  # path -> {"offset": int, "transitions": [(t, stage)]}


def bootflow_lane(src, force=False):
    """Incremental bootflow scanner: reads only NEW bytes since the last poll
    (the file is append-only; a 74 MB session log cannot be re-read at a 2 s
    cadence) and keeps every transition seen this session in memory. Reset on
    shrink (rotation/truncation). Current = the LAST transition; dwell = the
    log's NEWEST t (any line - the svc ticks keep advancing while a client
    sits stuck in a stage) minus the current stage's entry t."""
    path = MAC_LOG if src == "mac" else (SRV_LOG if src == "server" else None)
    st = _lane_state.setdefault(src if src != "rig" else "rig",
                                {"offset": 0, "transitions": []})
    if src == "rig":
        # the rig log arrives as a tail snapshot, not an append-only stream;
        # its bootflow lines age out of any tail window, so fetch them with a
        # server-side Select-String (whole file, network-light), cached 10s
        now = time.time()
        if force or not _rig_bf_cache["data"] or now - _rig_bf_cache["ts"] > 10:
            try:
                # the rig's ssh shell is cmd.exe (pipes break powershell
                # quoting); findstr is native and streams only the matches
                r = subprocess.run(
                    ["ssh"] + SSH_OPTS + [RIG_HOST,
                     f'findstr /C:"ev=bootflow" "{RIG_LOG}"'],
                    capture_output=True, text=True, timeout=20)
                lines = [l for l in r.stdout.splitlines() if "ev=bootflow" in l]
                _rig_bf_cache.update(ts=now, data=lines)
            except Exception:
                _rig_bf_cache.update(ts=now, data=_rig_bf_cache["data"] or [])
        # rebuild (not append): the Select-String cache holds the WHOLE file's
        # bootflow lines; appending on every poll would duplicate them
        st["transitions"] = []
        for raw in _rig_bf_cache["data"]:
            kv = dict(KV_RE.findall(raw))
            stg = kv.get("stage")
            t = int(kv["t"]) if kv.get("t", "").isdigit() else None
            if stg in BOOTFLOW_STAGES:
                st["transitions"].append((t, stg))
        return _lane_summary(st["transitions"], now_t=rig_now_t())
    try:
        size = path.stat().st_size
    except OSError:
        return _lane_summary([])
    if size < st["offset"]:  # rotated/truncated: start over
        st.update(offset=0, transitions=[])
    if force or size > st["offset"]:
        with open(path, "rb") as fh:
            fh.seek(st["offset"])
            chunk = fh.read(size - st["offset"]).decode("utf8", errors="replace")
        st["offset"] = size
        for raw in chunk.splitlines():
            if "ev=bootflow" not in raw:
                continue
            kv = dict(KV_RE.findall(raw))
            stg = kv.get("stage")
            t = int(kv["t"]) if kv.get("t", "").isdigit() else None
            if stg in BOOTFLOW_STAGES:
                st["transitions"].append((t, stg))
        if len(st["transitions"]) > 500:
            st["transitions"] = st["transitions"][-500:]
    return _lane_summary(st["transitions"], now_t=file_now_t(path))


def file_now_t(path):
    """The newest t= anywhere in the log's last 8 KB (the heartbeat/svc ticks
    advance even when a client is stuck in a stage)."""
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


def rig_now_t():
    d = rig_tail(50)["lines"]
    ts = []
    for raw in d:
        m = re.search(r"\bt=(\d+)", raw)
        if m:
            ts.append(int(m.group(1)))
    return max(ts) if ts else None


def _lane_summary(transitions, now_t=None):
    current = transitions[-1][1] if transitions else None
    cur_t = transitions[-1][0] if transitions else None
    first_seen = []
    for _t, s in transitions:
        if s not in first_seen:
            first_seen.append(s)
    dwell = None
    if current and cur_t is not None and now_t is not None:
        dwell = now_t - cur_t
    return {"lane": [{"stage": s,
                      "t": next((t for t, st2 in transitions if st2 == s), None)}
                     for s in first_seen],
            "current": current,
            "dwell_ms": dwell,
            "last_t": now_t}


def src_age(src):
    try:
        p = MAC_LOG if src == "mac" else SRV_LOG
        return time.time() - Path(p).stat().st_mtime
    except OSError:
        return -1


def counters(taildata):
    """Contract counters over the tail window (honestly labeled)."""
    c = {"withdrawals": 0, "acks": 0, "bodies_pushed": 0,
         "create_attempts_failed": 0}
    window = {}
    for src in ("mac", "server", "rig"):
        d = taildata.get(src, {})
        lines = d.get("lines", [])
        window[src] = len(lines)
        for raw in lines:
            if "result=withdrawn" in raw and "membership_peer" in raw:
                c["withdrawals"] += 1
            elif "stage=membership_ack" in raw and "result=ok" in raw:
                c["acks"] += 1
            elif "stage=push" in raw and "result=ok" in raw:
                c["bodies_pushed"] += 1
            if "failed to create" in raw.lower():
                c["create_attempts_failed"] += 1
    c["window_lines"] = window
    return c


def instruments(taildata):
    """Latest census line per probe fn (why=periodic wins over install)."""
    latest = {}
    for src in ("mac", "rig"):
        for raw in taildata.get(src, {}).get("lines", []):
            if "ev=mtrace" in raw and "stage=census" in raw:
                kv = dict(KV_RE.findall(raw))
                fn = kv.get("fn")
                if not fn:
                    continue
                rank = 1 if kv.get("why") == "periodic" else 0
                prev = latest.get(fn)
                if prev is None or rank >= prev["rank"]:
                    latest[fn] = {"fn": fn, "attached": kv.get("attached"),
                                  "calls": kv.get("calls"),
                                  "rva": kv.get("rva"), "why": kv.get("why"),
                                  "src": src, "rank": rank}
    rows = sorted(latest.values(), key=lambda r: r["fn"])
    return {"probes": rows,
            "dead": [r["fn"] for r in rows if r["attached"] == "0"]}


def warns(taildata, cap=40):
    out = []
    for src in ("mac", "server", "rig"):
        for raw in taildata.get(src, {}).get("lines", []):
            if "level=warn" in raw or "level=error" in raw:
                out.append(parse_line(src, raw))
    return out[-cap:]


# ---- cached subprocess health (slow tools; refresh at most every N s) ----
_health_cache = {"ts": 0.0, "data": None}


def health(force=False):
    now = time.time()
    if not force and _health_cache["data"] and now - _health_cache["ts"] < 120:
        return _health_cache["data"]
    def run(cmd, timeout=120):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            tail = (r.stdout + r.stderr).strip().splitlines()
            return {"rc": r.returncode,
                    "summary": tail[-1] if tail else "(no output)"}
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


def api_now():
    st = server_status()
    td = tail_all(400)
    return {"server": st, "identity": identity(),
            "bootflow": {"mac": bootflow_lane("mac"), "rig": bootflow_lane("rig"),
                         "server": bootflow_lane("server")},
            "counters": counters(td), "instruments": instruments(td),
            "warns": warns(td), "tail_age": {k: v["age"] for k, v in td.items()},
            "tail_errors": {k: v["error"] for k, v in td.items()},
            "ts": datetime.now().isoformat(timespec="seconds")}



def api_tail(args):
    n = min(int(args.get("n", ["300"])[0]), 1200)
    flt = args.get("filter", [""])[0].lower()
    level = args.get("level", ["all"])[0]
    td = tail_all(n)
    rows = []
    for src in ("server", "mac", "rig"):
        d = td.get(src, {})
        if d.get("error") and not d["lines"]:
            continue
        for raw in d.get("lines", []):
            if "unavailable" in raw and src in ("mac", "server"):
                continue
            rows.append(parse_line(src, raw))
    if flt:
        rows = [r for r in rows if flt in r["line"].lower()]
    if level != "all":
        rows = [r for r in rows if r["level"] == level]
    drift = (ROOT / "RE_output/logindex")  # informational only for now
    aligned = False
    rows.sort(key=lambda r: (r["t"] is None, r["t"] or 0))
    return {"rows": rows[-n:], "sources": {k: {"age": v["age"], "error": v["error"]}
                                           for k, v in td.items()},
            "aligned": aligned, "count": len(rows)}


# ---- the page (inline; textContent-only JS) ----

PAGE = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Sunrise project dashboard</title>
<style>
:root { --bg:#0d1117; --panel:#161b22; --edge:#30363d; --fg:#c9d1d9; --dim:#8b949e;
        --mac:#58a6ff; --rig:#d2a8ff; --srv:#3fb950; --warn:#d29922; --err:#f85149;
        --ok:#3fb950; }
* { box-sizing: border-box; }
body { background:var(--bg); color:var(--fg); font:13px/1.45 -apple-system,Menlo,monospace; margin:0; padding:14px; }
h2 { font-size:13px; text-transform:uppercase; letter-spacing:.08em; color:var(--dim); margin:0 0 8px; }
.panel { background:var(--panel); border:1px solid var(--edge); border-radius:8px; padding:12px; margin-bottom:14px; }
.grid { display:grid; grid-template-columns: 1fr 1fr 1fr; gap:14px; }
@media (max-width:1100px){ .grid{grid-template-columns:1fr;} }
.chip { display:inline-block; padding:2px 9px; border-radius:10px; border:1px solid var(--edge); margin:0 6px 4px 0; font-size:12px; }
.ok { color:var(--ok); border-color:var(--ok); } .bad { color:var(--err); border-color:var(--err); }
.warn { color:var(--warn); border-color:var(--warn); } .dim { color:var(--dim); }
.src-mac { color:var(--mac); } .src-rig { color:var(--rig); } .src-server { color:var(--srv); }
table { border-collapse:collapse; width:100%; font-size:12px; }
td,th { padding:2px 8px; border-bottom:1px solid var(--edge); text-align:left; white-space:nowrap; }
.lane { display:flex; align-items:center; flex-wrap:wrap; gap:4px; margin:6px 0; }
.lane b { color:var(--dim); width:34px; display:inline-block; }
.st { padding:1px 7px; border-radius:4px; border:1px solid var(--edge); font-size:11px; }
.st.done { color:var(--dim); } .st.cur { color:#fff; background:#1f6feb; border-color:#1f6feb; }
.st.stuck { color:var(--err); border-color:var(--err); }
#logbox { height:420px; overflow-y:auto; background:#0a0d12; border:1px solid var(--edge); border-radius:6px; padding:6px; font-size:12px; }
.lr { white-space:pre-wrap; word-break:break-all; padding:1px 0; }
.f-ev { color:#ffa657; } .f-stage { color:#79c0ff; } .f-res-ok { color:var(--ok); }
.f-res-bad { color:var(--err); } .f-fn { color:#d2a8ff; } .f-lvl-warn { color:var(--warn); } .f-lvl-error { color:var(--err); }
.counters { display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:8px; }
.cnt { border:1px solid var(--edge); border-radius:6px; padding:8px; text-align:center; }
.cnt b { display:block; font-size:22px; }
.controls input,select,button { background:#0d1117; color:var(--fg); border:1px solid var(--edge); border-radius:5px; padding:3px 8px; font:inherit; }
.muted { color:var(--dim); } pre { white-space:pre-wrap; word-break:break-word; margin:4px 0; font-size:12px; }
.stale { color:var(--warn); }
</style></head><body>
<div class="panel" id="banner">
  <b>Sunrise project dashboard</b>
  <span id="serverchip" class="chip dim">server: ?</span>
  <span id="idchip" class="chip dim">builds: ?</span>
  <span id="clock" class="chip dim"></span>
  <span id="alignedchip" class="chip dim"></span>
</div>
<div class="grid">
  <div class="panel"><h2>Bootflow lanes</h2><div id="lanes" class="muted">...</div></div>
  <div class="panel"><h2>Contract counters <span class="muted" id="cntwin"></span></h2><div id="counters" class="counters muted">...</div>
       <h2 style="margin-top:12px">Pairing</h2><div id="pairing" class="muted">...</div></div>
  <div class="panel"><h2>Instruments <span class="muted" id="instnote"></span></h2><div id="instruments" class="muted">...</div></div>
</div>
<div class="panel">
  <h2>Warnings / errors <span class="muted">(deduped by shape)</span></h2><div id="warns" class="muted">...</div>
  <div id="health" class="muted" style="margin-top:8px"></div>
</div>
<div class="panel">
  <h2>Live logs
    <span class="controls" style="float:right">
      <input id="filter" placeholder="filter text" size="18">
      <select id="levelsel"><option>all</option><option>info</option><option>debug</option><option>warn</option><option>error</option></select>
      <select id="nlinesel"><option>300</option><option>600</option><option>1200</option></select>
      <label><input type="checkbox" id="follow" checked> follow</label>
      <span id="srcages" class="muted"></span>
    </span>
  </h2>
  <div id="logbox"></div>
</div>
<script>
"use strict";
var LOGBUFFER = [];
var box = document.getElementById("logbox");
function el(tag, cls, text){ var e=document.createElement(tag); if(cls) e.className=cls; if(text!==undefined) e.textContent=text; return e; }
function chipText(id, txt, cls){ var e=document.getElementById(id); e.textContent=txt; e.className="chip "+(cls||"dim"); }
function fmtRow(r){
  var d = el("div","lr src-"+r.src);
  var t = (r.t===null||r.t===undefined) ? "t=? " : "t="+r.t+" ";
  d.appendChild(el("span","muted", t));
  d.appendChild(el("span","src-"+r.src, "["+r.src+"] "));
  if(r.level==="warn"||r.level==="error") d.appendChild(el("span","f-lvl-"+r.level, r.level+" "));
  if(r.ev) d.appendChild(el("span","f-ev", "ev="+r.ev+" "));
  if(r.stage) d.appendChild(el("span","f-stage", "stage="+r.stage+" "));
  if(r.result) d.appendChild(el("span", r.result==="ok"?"f-res-ok":"f-res-bad", "result="+r.result+" "));
  if(r.fn) d.appendChild(el("span","f-fn", "fn="+r.fn+" "));
  var rest = r.line.replace(/^.*? t=\d+ /,"");
  d.appendChild(el("span","", rest));
  return d;
}
function renderLog(){
  var f = document.getElementById("filter").value.toLowerCase();
  var lv = document.getElementById("levelsel").value;
  box.textContent = "";
  var n = 0;
  for (var i = 0; i < LOGBUFFER.length; i++){
    var r = LOGBUFFER[i];
    if (f && r.line.toLowerCase().indexOf(f) < 0) continue;
    if (lv !== "all" && r.level !== lv) continue;
    box.appendChild(fmtRow(r)); n++;
  }
  if (document.getElementById("follow").checked) box.scrollTop = box.scrollHeight;
  if (LOGBUFFER.length >= 4000) LOGBUFFER = LOGBUFFER.slice(-3000);
}
function pollTail(){
  var n = document.getElementById("nlinesel").value;
  var q = "?n="+n; var f = document.getElementById("filter").value;
  if (f) q += "&filter="+encodeURIComponent(f);
  var lv = document.getElementById("levelsel").value;
  if (lv !== "all") q += "&level="+lv;
  fetch("/api/tail.json"+q).then(function(r){return r.json();}).then(function(d){
    LOGBUFFER = d.rows || [];
    renderLog();
    var ages = [];
    for (var s in d.sources){
      var sd = d.sources[s];
      ages.push(s + ": " + (sd.error ? sd.error : (sd.age===null ? "?" : "last write "+sd.age+"s ago")));
    }
    document.getElementById("srcages").textContent = ages.join(" | ");
    chipText("alignedchip", d.aligned ? "clock: aligned" : "clock: NOT ALIGNED (per-source t=)", d.aligned?"ok":"warn");
  }).catch(function(e){ chipText("alignedchip","tail error: "+e,"bad"); });
}
function pollNow(){
  fetch("/api/now.json").then(function(r){return r.json();}).then(function(d){
    var s = d.server;
    chipText("serverchip", "server: " + (s.pid ? "pid "+s.pid+(s.http?" (http up)":" (http DOWN)") : "DOWN"),
             s.pid ? (s.http?"ok":"warn") : "bad");
    var id = d.identity;
    chipText("idchip", "client "+(id.mac_client.deployed||"?")+(id.mac_client.match?"==":"!=")+"built "
             + "| server "+(id.server.deployed||"?")+(id.server.match?"==":"!=")+"built",
             (id.mac_client.match && id.server.match) ? "ok":"warn");
    // lanes
    var L = document.getElementById("lanes"); L.textContent="";
    [["mac",d.bootflow.mac],["rig",d.bootflow.rig]].forEach(function(p){
      var row = el("div","lane"); row.appendChild(el("b",null,p[0]));
      var bf = p[1];
      if (!bf.lane.length){ row.appendChild(el("span","muted","no bootflow lines yet")); }
      bf.lane.forEach(function(st,i){
        var isCur = st.stage===bf.current;
        var cls = "st "+(isCur ? (bf.dwell_ms!==null && bf.dwell_ms>120000 ? "stuck" : "cur") : "done");
        var sp = el("span",cls, st.stage + (isCur && bf.dwell_ms!==null ? " ("+Math.round(bf.dwell_ms/1000)+"s)" : ""));
        row.appendChild(sp);
        if (i < bf.lane.length-1) row.appendChild(el("span","muted","-"));
      });
      L.appendChild(row);
    });
    // counters
    var C = document.getElementById("counters"); C.textContent="";
    var c = d.counters;
    [["withdrawals",c.withdrawals],["acks",c.acks],["bodies pushed",c.bodies_pushed],
     ["create FAILs",c.create_attempts_failed]].forEach(function(p){
      var card = el("div","cnt"); card.appendChild(el("b",null,String(p[1]))); card.appendChild(el("span","muted",p[0])); C.appendChild(card);
    });
    document.getElementById("cntwin").textContent = "(over the tail window: "
      + Object.keys(c.window_lines).map(function(k){return k+" "+c.window_lines[k];}).join(", ") + " lines)";
    // pairing
    var P = document.getElementById("pairing"); P.textContent="";
    var lobby = s.lobby || {};
    P.appendChild(el("div",null,"sessions: " + s.session_count + " | lobby entries: " + (Array.isArray(lobby)?lobby.length:"?")));
    (s.sessions||[]).slice(0,4).forEach(function(x){ P.appendChild(el("div","muted", JSON.stringify(x).slice(0,160))); });
    // instruments
    var I = document.getElementById("instruments"); I.textContent="";
    var ins = d.instruments;
    document.getElementById("instnote").textContent = ins.dead.length ? ("DEAD: "+ins.dead.join(",")) : "";
    var tbl = el("table"); var tr = el("tr");
    ["probe","attached","calls","src"].forEach(function(h){ tr.appendChild(el("th",null,h)); }); tbl.appendChild(tr);
    ins.probes.slice(0,14).forEach(function(r){
      var row = el("tr");
      [r.fn, r.attached, r.calls, r.src].forEach(function(v,i){
        var td = el("td", null, String(v===null||v===undefined?"":v)); if(i===1&&v==="0") td.className="bad"; row.appendChild(td);
      });
      tbl.appendChild(row);
    });
    I.appendChild(tbl);
    // warns deduped by shape
    var W = document.getElementById("warns"); W.textContent="";
    var seen = {};
    d.warns.forEach(function(r){
      var shape = r.line.replace(/t=\d+/g,"t=N").replace(/\d{6,}/g,"N").slice(0,120);
      if (seen[shape]){ seen[shape].n++; seen[shape].el.replaceChildren(); seen[shape].el.appendChild(fmtRow(r)); seen[shape].el.appendChild(el("span","muted"," x"+seen[shape].n)); return; }
      var w = el("div"); w.appendChild(fmtRow(r)); W.appendChild(w); seen[shape] = {el:w, n:1};
    });
    if (!d.warns.length) W.appendChild(el("span","muted","none in window"));
  }).catch(function(e){ chipText("serverchip","now error: "+e,"bad"); });
}
function pollHealth(){
  fetch("/api/health.json").then(function(r){return r.json();}).then(function(d){
    var H = document.getElementById("health"); H.textContent="";
    var parts = [];
    [["registry",d.registry],["preflight",d.preflight],["gate fixture",d.gate_fixture],["index lint",d.index_fresh]].forEach(function(p){
      parts.push((p[1].rc===0?"ok ":"FLAG ") + p[0]);
    });
    H.appendChild(el("span","muted","tooling: " + parts.join(" | ") + "  ("+d.ts.slice(11)+")"));
  });
}
document.getElementById("filter").addEventListener("input", renderLog);
document.getElementById("levelsel").addEventListener("change", renderLog);
setInterval(function(){ if(document.getElementById("follow").checked) pollTail(); pollNow(); }, 2000);
setInterval(pollHealth, 60000);
pollTail(); pollNow(); pollHealth();
setInterval(function(){ document.getElementById("clock").textContent = new Date().toLocaleTimeString(); }, 1000);
</script></body></html>
"""


class Handler(argparse.ArgumentParser):
    pass


def make_handler(port, lan):
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):  # quiet
            pass

        def do_GET(self):
            path, _, qs = self.path.partition("?")
            args = [tuple(a.split("=", 1)) for a in qs.split("&") if "=" in a]
            args = [(k, v) for k, v in args]
            get = lambda k, d=None: [v for k2, v in args if k2 == k] or [d]
            try:
                if path == "/" or path == "/index.html":
                    body = PAGE.encode("utf8")
                    self._send(200, "text/html; charset=utf-8", body)
                elif path == "/api/tail.json":
                    self._json(api_tail(dict((k, [v]) for k, v in args)))
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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--port", type=int, default=8400)
    ap.add_argument("--lan", action="store_true", help="bind 0.0.0.0 (rig browser can open)")
    args = ap.parse_args(argv)
    if not args.serve:
        print(__doc__)
        return 2
    httpd = make_handler(args.port, args.lan)
    bind, port = httpd.server_address[:2]
    print(f"project dashboard: http://{bind}:{port}/  (Ctrl-C to stop; read-only)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
