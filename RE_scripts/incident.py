#!/usr/bin/env python3
"""Incident digest generator (2026-08-15, contract step 2).

Snapshots: v4 pro session events + game/client logs + server logs + processes/
listeners + acceptance-stack hashes into RE_output/incidents/INCIDENT_<ts>.md,
so any model (or a restarted session) catches up from ONE file instead of
re-deriving context from raw sources.

Usage:
    python -X utf8 RE_scripts\\incident.py [--session <id>] [--events N]
Default session = the v4 pro main session. Read-only DB access (mode=ro).
"""
import hashlib
import json
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = Path(r"C:\Users\rasla\.local\share\opencode\opencode.db")
GAME_LOG = ROOT / "Game" / "bin" / "x64" / "Sunrise" / "logs" / "sunrise.log"
# PC-era path kept as a fallback (the dcv build tree when running on Windows).
GAME_LOG_PC = ROOT / "dcv build" / "bin" / "x64" / "Sunrise" / "logs" / "sunrise.log"
if not GAME_LOG.exists() and GAME_LOG_PC.exists():
    GAME_LOG = GAME_LOG_PC
S0_LOG = ROOT / "RE_output" / "s0_accept" / "Sunrise" / "logs" / "sunrise.log"
S1_LOG = ROOT / "RE_output" / "s1_accept" / "Sunrise" / "logs" / "sunrise.log"

HASH_TARGETS = [
    ROOT / "dcv build" / "bin" / "x64" / "steam_api64.dll",
    ROOT / "dcv build" / "bin" / "x64" / "Sunrise" / "settings.json",
    ROOT / "dcv build" / "bin" / "x64" / "Sunrise" / "cache" / "build_data.bin",
    ROOT / "dcv build" / "bin" / "x64" / "Sunrise" / "cache" / "content_manifest.bin",
    ROOT / "RE_output" / "s0_accept" / "sunrise-server.exe",
    ROOT / "RE_output" / "s0_accept" / "settings.json",
    ROOT / "RE_output" / "s0_accept" / "Sunrise" / "settings.json",
    ROOT / "RE_output" / "s0_accept" / "Sunrise" / "cache" / "build_data.bin",
    ROOT / "RE_output" / "s0_accept" / "Sunrise" / "cache" / "content_manifest.bin",
    ROOT / "RE_output" / "s1_accept" / "sunrise-server.exe",
    ROOT / "RE_output" / "s1_accept" / "Sunrise" / "settings.json",
    ROOT / "RE_output" / "s1_accept" / "Sunrise" / "cache" / "build_data.bin",
    ROOT / "RE_output" / "s1_accept" / "Sunrise" / "cache" / "content_manifest.bin",
    ROOT / "RE_output" / "s1_accept" / "Sunrise" / "state.db",
]

DEFAULT_SESSION = "ses_ffcd9b73dffeYQZAVdEzX8TkKI"


def sha16(path: Path) -> str:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except Exception as exc:  # noqa: BLE001
        return f"ERR:{exc.__class__.__name__}"


def section_events(session_id: str, count: int) -> list[str]:
    out = [f"## v4 pro session events (last {count})"]
    try:
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        rows = list(
            con.execute(
                "SELECT seq, type, data FROM session_message "
                "WHERE session_id=? ORDER BY seq DESC LIMIT ?",
                (session_id, count),
            )
        )
        lines: list[str] = []
        for row in reversed(rows):
            data = json.loads(row["data"]) if row["data"] else {}
            t = data.get("time", {}).get("created") or 0
            ts = datetime.fromtimestamp(t / 1000).strftime("%m-%d %H:%M:%S") if t else "??:??:??"
            if row["type"] == "user":
                text = (data.get("text") or "").replace("\n", " ")[:200]
                lines.append(f"{ts} USER: {text}")
            elif row["type"] == "assistant":
                for part in data.get("content") or []:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text = (part.get("text") or "").replace("\n", " ")[:300]
                        lines.append(f"{ts} ASST: {text}")
        out.extend(lines or ["(no events)"])
    except Exception as exc:  # noqa: BLE001
        out.append(f"(events unavailable: {exc})")
    return out


def read_lines(path: Path, limit: int) -> list[str]:
    try:
        with open(path, "r", encoding="utf8", errors="replace") as f:
            return f.read().splitlines()[-limit:]
    except Exception as exc:  # noqa: BLE001
        return [f"(log unavailable: {exc.__class__.__name__})"]


def section_log(name: str, path: Path, grep=None, tailn: int = 20) -> list[str]:
    if path.exists():
        mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%m-%d %H:%M:%S")
        head = f"## {name} ({path.name} mtime {mtime})"
    else:
        head = f"## {name} (MISSING)"
    out = [head]
    lines = read_lines(path, 4000 if grep else tailn)
    if grep:
        hits = [l for l in lines if any(g.lower() in l.lower() for g in grep)][:50]
        out.extend(f"  {l[:200]}" for l in hits)
        out.append(f"  -- grep hits: {len(hits)} (raw tail below) --")
    out.extend(f"  {l[:200]}" for l in lines[-tailn:])
    return out


def section_procs() -> list[str]:
    out = ["## processes / listeners"]
    try:
        for image in ("destiny2.exe", "sunrise-server.exe"):
            r = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {image}", "/FO", "CSV"],
                capture_output=True, text=True, timeout=15,
            )
            out.extend(f"  {l}" for l in r.stdout.splitlines() if l.strip() and "INFO:" not in l)
        r = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=15)
        out.extend(
            f"  {l.strip()}"
            for l in r.stdout.splitlines()
            if "LISTENING" in l and (":443 " in l or ":30974" in l or ":30975" in l)
        )
    except Exception as exc:  # noqa: BLE001
        out.append(f"  (unavailable: {exc})")
    return out


def section_hashes() -> list[str]:
    out = ["## acceptance stack hashes (sha256[:16], size, mtime)"]
    for path in HASH_TARGETS:
        rel = str(path.relative_to(ROOT))
        if path.exists():
            out.append(f"  {sha16(path):>18}  {path.stat().st_size:>9}  "
                       f"{datetime.fromtimestamp(path.stat().st_mtime).strftime('%m-%d %H:%M')}  {rel}")
        else:
            out.append(f"  {'MISSING':>18}  {'-':>9}  {'-':>5}  {rel}")
    return out


def main() -> None:
    session = DEFAULT_SESSION
    count = 25
    args = sys.argv[1:]
    if "--session" in args:
        session = args[args.index("--session") + 1]
    if "--events" in args:
        count = int(args[args.index("--events") + 1])
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = ROOT / "RE_output" / "incidents"
    outdir.mkdir(parents=True, exist_ok=True)
    parts = [
        f"# INCIDENT {stamp}",
        f"generated {datetime.now().isoformat(timespec='seconds')} by RE_scripts/incident.py",
        "",
    ]
    parts += section_events(session, count) + [""]
    parts += section_log(
        "game-side client log",
        GAME_LOG,
        grep=["assert", "error", "package_registration", "bootflow", "queuez",
              "shello", "suspend", "endpoint traffic", "content_check"],
    ) + [""]
    parts += section_log("s0_accept server log", S0_LOG) + [""]
    parts += section_log("s1_accept server log", S1_LOG) + [""]
    parts += section_procs() + [""]
    parts += section_hashes()
    dest = outdir / f"INCIDENT_{stamp}.md"
    dest.write_text("\n".join(parts), encoding="utf8")
    print(f"wrote {dest} ({dest.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
