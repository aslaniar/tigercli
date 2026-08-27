#!/usr/bin/env python3
"""incident.py - incident digest generator (2026-08-26 PORT; originally 08-15).

Snapshots: session events (opencode DB) + game/client logs + server logs +
processes/listeners + acceptance-stack hashes into RE_output/incidents/
INCIDENT_<ts>.md, so any model or restarted session catches up from ONE file
instead of re-deriving context from raw sources.

Usage:
    python3 RE_scripts/incident.py [--session <id>] [--events N] [--root <dir>]

Default session = the MOST RECENTLY UPDATED non-subagent session for this
project directory (no hardcoded id). Read-only DB access.

PORT NOTES (2026-08-26) - what changed and why:
  - Cross-platform: resolves opencode DB per-OS; process/port probe via ps/lsof
    on macOS, tasklist/netstat on Windows.
  - Schema-current (verified 2026-08-26): sessions live in session_v2, messages
    in session_message. The message/part tables hold only pre-migration data.
    Earlier diagnosis ("session_message is legacy") was itself a stale join
    against the old session table - recorded so nobody re-diagnoses it.
  - Liveness: always prints section counts; exits NONZERO if the digest found
    nothing anywhere (a fully-empty report is an error state, not a quiet pass).
  - Roots: uses THIS checkout by default; --root <dir> to digest another tree.

Exit codes: 0 wrote a non-degenerate digest, 1 digest degenerate/empty,
2 environment error.
"""
import json
import platform
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parent.parent


def db_path():
    home = Path.home()
    for cand in (
        home / ".local" / "share" / "opencode" / "opencode.db",   # linux/mac
        home / "AppData" / "Local" / "opencode" / "opencode.db",  # windows
    ):
        if cand.exists():
            return cand
    return None


def resolve_session(con, project_hint):
    """Newest-updated top-level session whose directory matches the hint;
    falls back to newest overall. Returns (id, directory, title)."""
    rows = list(con.execute(
        "SELECT id, directory, title, time_updated FROM session_v2 "
        "ORDER BY time_updated DESC LIMIT 200"))
    if not rows:
        return None
    hint = str(project_hint)
    for sid, directory, title, _ in rows:
        if directory and hint in str(directory):
            return sid, directory, title
    sid, directory, title, _ = rows[0]
    return sid, directory, f"(no dir match; newest overall) {title}"


def event_lines(con, session_id, count):
    """Reconstruct turn-level events from session_message (the table current
    opencode actually writes; message/part hold only pre-migration data)."""
    rows = list(con.execute(
        "SELECT type, time_created, data FROM session_message WHERE session_id=? "
        "ORDER BY time_created LIMIT 4000", (session_id,)))
    lines = []
    for typ, t, raw in rows:
        try:
            d = json.loads(raw)
        except (TypeError, ValueError):
            continue
        if typ == "user":
            body = (d.get("text") or "")[:200].replace("\n", " ")
        elif typ == "assistant":
            texts = [p.get("text") or "" for p in d.get("content") or []
                     if isinstance(p, dict) and p.get("type") == "text"]
            body = " ".join(x for x in texts if x)[:300].replace("\n", " ")
        else:
            continue
        if not body:
            continue
        ts = datetime.fromtimestamp(t / 1000).strftime("%m-%d %H:%M:%S") if t else "??:??:??"
        lines.append(f"{ts} {'USER' if typ == 'user' else 'ASST'}: {body}")
    return lines[-count:]


def section_events(root, count):
    out = ["## session events"]
    db = db_path()
    if not db:
        out.append("(opencode DB not found on this machine)")
        return out, 0
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        out.append(f"(DB open failed: {exc})")
        return out, 0
    pick = resolve_session(con, root)
    if not pick:
        out.append("(no sessions in DB)")
        return out, 0
    sid, _directory, title = pick
    lines = event_lines(con, sid, count)
    out.append(f"session {sid} | {title[:80]}")
    out.extend(lines or ["(no readable events - check schema/version)"])
    con.close()
    return out, len(lines)


def read_tail(path, limit):
    try:
        with open(path, "r", encoding="utf8", errors="replace") as f:
            return f.read().splitlines()[-limit:]
    except OSError:
        return None


def find_log(root, *rel_cands):
    for rel in rel_cands:
        p = root / rel
        if p.exists():
            return p
    return None


def section_log(name, path, grep=None, tailn=20):
    if path and path.exists():
        mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%m-%d %H:%M:%S")
        head = [f"## {name} ({path.name} mtime {mtime})"]
        lines = read_tail(path, 4000 if grep else tailn) or []
    else:
        head = [f"## {name} (MISSING: expected {' / '.join(str(x) for x in []) or 'n/a'})"]
        lines = []
        path = None
    hits = []
    if lines and grep:
        hits = [l for l in lines if any(g.lower() in l.lower() for g in grep)][:50]
        head.append("  ".join([])) if False else None
        head += [f"  {l[:200]}" for l in hits] + [f"  -- grep hits: {len(hits)} --"]
    head += [f"  {l[:200]}" for l in lines[-tailn:]]
    n = len(hits) if grep else len(lines)
    return head, n


def sha16(path):
    import hashlib
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except OSError as exc:
        return f"ERR:{exc.__class__.__name__}"


def hash_targets(root):
    dll = root / "Game" / "bin" / "x64" / "steam_api64.dll"
    exe_names = ["destiny2.exe"]
    targets = []
    if dll.exists():
        targets.append(dll)
    gamedir = root / "Game" / "bin" / "x64"
    for name in exe_names:
        p = gamedir / name
        if p.exists():
            targets.append(p)
    for sub in ("s0_accept", "s1_accept"):
        base = root / "RE_output" / sub
        for rel in ("sunrise-server.exe", "Sunrise/settings.json",
                    "Sunrise/cache/build_data.bin",
                    "Sunrise/cache/content_manifest.bin", "state.db"):
            p = base / rel
            if p.exists():
                targets.append(p)
    settings = root / "Game" / "bin" / "x64" / "Sunrise" / "settings.json"
    if settings.exists():
        targets.append(settings)
    return targets


def section_hashes(root):
    out = ["## stack hashes (sha256[:16], size, mtime)"]
    targets = hash_targets(root)
    if not targets:
        out.append("  (no known artifacts present under this root)")
    for path in targets:
        rel = path.relative_to(root)
        mt = datetime.fromtimestamp(path.stat().st_mtime).strftime("%m-%d %H:%M")
        out.append(f"  {sha16(path):>18}  {path.stat().st_size:>10}  {mt}  {rel}")
    return out, len(targets)


def section_procs():
    out = ["## processes / listeners"]
    n = 0
    system = platform.system()
    try:
        if system == "Darwin":
            r = subprocess.run(["ps", "axo", "comm"], capture_output=True,
                               text=True, timeout=15)
            procs = [l.strip() for l in r.stdout.splitlines()
                     if "destiny2" in l.lower() or "sunrise" in l.lower()]
            out += [f"  proc: {p}" for p in procs or ["(none matching destiny2/sunrise)"]]
            n += len(procs)
            r = subprocess.run(["lsof", "-iTCP", "-sTCP:LISTEN", "-P", "-n"],
                               capture_output=True, text=True, timeout=20)
            ports = [l.strip() for l in r.stdout.splitlines()
                     if ":443 " in l or ":30974" in l or ":30975" in l]
            out += [f"  listen: {p}" for p in ports[:10]]
            n += len(ports)
        else:  # Windows-era behavior preserved for the rig
            for image in ("destiny2.exe", "sunrise-server.exe"):
                r = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {image}",
                                    "/FO", "CSV"], capture_output=True,
                                   text=True, timeout=15)
                got = [l for l in r.stdout.splitlines()
                       if l.strip() and "INFO:" not in l]
                out += [f"  {l}" for l in got]
                n += len(got)
            r = subprocess.run(["netstat", "-ano"], capture_output=True,
                               text=True, timeout=15)
            listens = [l.strip() for l in r.stdout.splitlines()
                       if "LISTENING" in l and
                       (":443 " in l or ":30974" in l or ":30975" in l)]
            out += [f"  {l}" for l in listens]
            n += len(listens)
    except Exception as exc:  # noqa: BLE001
        out.append(f"  (unavailable: {exc.__class__.__name__})")
    return out, n


def main(argv):
    root = SCRIPT_ROOT
    count = 25
    session = None
    it = iter(argv)
    for a in it:
        if a == "--session":
            session = next(it, None)
        elif a == "--events":
            count = int(next(it, "25"))
        elif a == "--root":
            root = Path(next(it)).resolve()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = root / "RE_output" / "incidents"
    outdir.mkdir(parents=True, exist_ok=True)

    parts = [
        f"# INCIDENT {stamp}",
        f"generated {datetime.now().isoformat(timespec='seconds')} by "
        f"RE_scripts/incident.py (2026 port)",
        f"root: {root}",
        "",
    ]
    tallies = {}
    if session:
        db = db_path()
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True) if db else None
        if con:
            parts += ["## session events (explicit --session)", f"{session}"] + \
                (event_lines(con, session, count) or ["(none)"])
            tallies["events"] = 0
            con.close()
    else:
        ev_block, ev_n = section_events(root, count)
        parts += ev_block + [""]
        tallies["events"] = ev_n

    client_log = find_log(
        root, "Game/bin/x64/Sunrise/logs/sunrise.log",
        "dcv build/bin/x64/Sunrise/logs/sunrise.log")
    cblock, c_n = section_log(
        "game-side client log", client_log,
        grep=["assert", "error", "package_registration", "bootflow", "queuez",
              "shello", "suspend", "endpoint traffic", "content_check"])
    parts += cblock + [""]
    tallies["client_log"] = c_n

    for label, sub in (("s0_accept", "s0_accept"), ("s1_accept", "s1_accept")):
        lp = find_log(root, f"RE_output/{sub}/Sunrise/logs/sunrise.log")
        sblock, s_n = section_log(f"{label} server log", lp)
        parts += sblock + [""]
        tallies[label] = s_n

    pblock, p_n = section_procs()
    parts += pblock + [""]
    tallies["procs"] = p_n

    hblock, h_n = section_hashes(root)
    parts += hblock
    tallies["hashes"] = h_n

    dest = outdir / f"INCIDENT_{stamp}.md"
    dest.write_text("\n".join(parts), encoding="utf8")

    print(f"wrote {dest} ({dest.stat().st_size} bytes)")
    print("LIVENESS:", ", ".join(f"{k}={v}" for k, v in tallies.items()))
    # Degeneracy judged ONLY on root-bound sections; events/procs follow the
    # DB/machine, not the tree, and would mask an empty --root.
    rootbound = ["client_log", "s0_accept", "s1_accept", "hashes"]
    nonempty = sum(1 for k in rootbound if tallies.get(k, 0) > 0)
    if nonempty == 0:
        print("DEGENERATE DIGEST: no logs or hashes found under this root - "
              "verify --root points at the checkout holding the runtime before "
              "trusting this as 'all quiet'.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
