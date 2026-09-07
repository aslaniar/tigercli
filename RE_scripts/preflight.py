#!/usr/bin/env python3
# REGISTRY: caps: preflight, env-gate, instrument-manifest
"""preflight.py - the WORLD gate, separate from the document gate
(enforcement-layer plan point 2; TOOLING_AUDIT 08-30 C5/A2/A4c, 09-05 addendum).

gate_boot checks the BRIEF; preflight checks the MACHINE. "ready" is defined:
gate PASS + preflight PASS. Nothing else. (08-30 A2: a 225-line brief passed
while no settings were edited, no backups existed, and no server ran - a
passing document gate was read as a ready environment.)

Usage:
  preflight.py [--brief <brief.md>] [--record] [--skip-rig] [--skip-server]
               [--no-traps]
               [--client P] [--built-client P] [--server P] [--built-server P]
               [--settings P] [--ports N,N]

Checks (each prints ok / WARN / FAIL and a line even when clean - L13):
  1. deployed client DLL hash == built client DLL hash (08-30 A6 class)
  2. deployed server exe hash == built server exe hash
  3. client DLL EXPORT COUNT == manifest (08-30 C5: the fastest load-time
     failure check; a broken export table kills the game at load)
  4. settings.json exists + at least one .bak backup (A2)
  5. server process alive + listeners bound on the expected ports (A2)
  6. hook INSTALL TABLE arithmetic (T1.4: declared size == initializer
     count, no null/rva-0 entries - the RVA-0 login-crash class, shared
     parser with verify_hook_rvas)
  7. detour FOOTPRINT: every table target's .pdata function is big enough
     to hold a detour + relocated prologue (08-30 C2: 36/37-byte targets)
  8. --brief: every INSTRUMENTS literal present in the DEPLOYED binary
     (A4c: the instrument must be in what will actually run)
  9. rig deployed DLL hash == built (best-effort ssh; WARN when the rig is
     unreachable - the boot can still be solo)

--record: (re)write RE_output/map/instruments.json from the CURRENT machine
state (hashes, sizes, export counts). Run it after every intentional deploy;
check mode FAILS with "manifest stale" when the deployed binary is newer
than the manifest, and FAILS on any hash/export drift.

Exit: 0 GO; 1 NO-GO (reasons listed); 2 usage/environment error.
"""
import argparse
import hashlib
import json
import os
import struct
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path(os.environ.get(
    "RE_INSTRUMENTS_MANIFEST",
    str(ROOT / "RE_output/map/instruments.json")))

DEFAULTS = {
    "client": ROOT / "Game/bin/x64/steam_api64.dll",
    "built_client": ROOT / "RE_build/Sunrise-fork-inventory/build/steam_api64.dll",
    "server": ROOT / "RE_output/s1_accept/sunrise-server.exe",
    "built_server": ROOT / "RE_build/Sunrise-fork-inventory/build/sunrise-server.exe",
    "settings": ROOT / "Game/bin/x64/Sunrise/settings.json",
    "rig": "rasla@192.168.1.136:C:\\Users\\rasla\\Downloads\\destiny-preservation\\dcv build\\bin\\x64\\steam_api64.dll",
}
DETOUR_MIN_BYTES = 16  # 08-30 C2: 36/37-byte targets could not hold a detour


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pe_export_count(path):
    """Minimal PE export-directory parse -> NumberOfFunctions (the count the
    C5 check wants: a rebuilt shim with a broken .edata kills the game at
    load). Returns int or None when the file has no export directory."""
    data = Path(path).read_bytes()
    if data[:2] != b"MZ":
        return None
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    if data[e_lfanew:e_lfanew + 4] != b"PE\x00\x00":
        return None
    opt_off = e_lfanew + 24
    magic = struct.unpack_from("<H", data, opt_off)[0]
    dd_off = opt_off + (112 if magic == 0x20B else 96)  # data dir 0 (export)
    rva = struct.unpack_from("<I", data, dd_off)[0]
    if rva == 0:
        return 0
    nsec = struct.unpack_from("<H", data, e_lfanew + 6)[0]
    opt_size = struct.unpack_from("<H", data, e_lfanew + 20)[0]
    sec_off = opt_off + opt_size
    for i in range(nsec):
        s = sec_off + i * 40
        vsize = struct.unpack_from("<I", data, s + 8)[0]
        va = struct.unpack_from("<I", data, s + 12)[0]
        raw = struct.unpack_from("<I", data, s + 20)[0]
        if va <= rva < va + max(vsize, 1):
            off = raw + (rva - va)
            # ExportDirectory: Characteristics, TimeDateStamp, Major, Minor,
            # Name, Base, NumberOfFunctions, NumberOfNames ...
            nfuncs = struct.unpack_from("<I", data, off + 20)[0]
            return nfuncs
    return None


class Report:
    def __init__(self):
        self.fails, self.warns, self.oks = [], [], []

    def ok(self, msg):
        self.oks.append(msg)
        print(f"  ok      {msg}")

    def warn(self, msg):
        self.warns.append(msg)
        print(f"  WARN    {msg}")

    def fail(self, msg):
        self.fails.append(msg)
        print(f"  FAIL    {msg}")

    def finish(self):
        print(f"PREFLIGHT {'PASS' if not self.fails else 'NO-GO'} "
              f"(ok={len(self.oks)} warn={len(self.warns)} fail={len(self.fails)})")
        if self.fails:
            print("NO-GO - do not boot until all of these hold:")
            for f in self.fails:
                print(f"  - {f}")
            return 1
        return 0


def read_manifest():
    if not MANIFEST.exists():
        return None
    try:
        return json.loads(MANIFEST.read_text(encoding="utf8"))
    except json.JSONDecodeError:
        return None


def record(args, rep):
    """Capture the current machine state into the manifest (run after a
    deploy; the manifest is the 'last known good' the next check compares
    against)."""
    entry = {"recorded": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "deployed": {}}
    for key in ("client", "built_client", "server", "built_server"):
        p = Path(args.__dict__[key])
        e = {"path": str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)}
        if p.exists():
            e.update(sha256=sha256(p), size=p.stat().st_size,
                     mtime=p.stat().st_mtime)
            if key in ("client", "built_client"):
                ec = pe_export_count(p)
                e["exports"] = ec
                if ec is None:
                    e["exports_error"] = "no MZ/PE/export dir found"
        else:
            e["missing"] = True
        entry["deployed"][key] = e
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf8")
    print(f"manifest recorded -> {MANIFEST}")
    for k, e in entry["deployed"].items():
        print(f"  {k:13} " + ("MISSING" if e.get("missing") else
              f"sha={e['sha256'][:16]} size={e['size']}"
              + (f" exports={e['exports']}" if "exports" in e else "")))
    return 0


def check_deployed(rep, key, live_path, built_path, manifest, skip_built=False):
    live, built = Path(live_path), Path(built_path)
    tag = key.replace("_", " ")
    if not live.exists():
        rep.fail(f"{tag} MISSING: {live}")
        return
    lh = sha256(live)
    if built.exists() and not skip_built:
        bh = sha256(built)
        if lh == bh:
            rep.ok(f"{tag} deployed == built ({lh[:16]}, {live.stat().st_size} B)")
        else:
            rep.fail(f"{tag} deployed != built ({lh[:16]} vs {bh[:16]}) - "
                     "deploy again (deploy_client_dll.sh / deploy_p2d6_gameplay.sh)")
    else:
        rep.warn(f"{tag} built artifact missing ({built}) - identity not assertable")
    if manifest:
        m = manifest.get("deployed", {}).get(key)
        if m and not m.get("missing"):
            if m.get("mtime") and live.stat().st_mtime > m["mtime"] + 1:
                rep.fail(f"{tag} NEWER than the manifest ({m['path']} recorded "
                         f"{datetime.fromtimestamp(m['mtime'], tz=timezone.utc).isoformat()}) "
                         "- intentional? re-run preflight.py --record; otherwise "
                         "something changed the binary outside the deploy pipeline")
            elif m.get("sha256") != lh:
                rep.fail(f"{tag} hash drift vs manifest")
            elif m.get("exports") is not None:
                ec = pe_export_count(live)
                if ec != m["exports"]:
                    rep.fail(f"{tag} export count {ec} != manifest {m['exports']} "
                             "(C5: a broken export table kills the game at load)")
                else:
                    rep.ok(f"{tag} exports == manifest ({ec})")
            else:
                rep.ok(f"{tag} == manifest")
        elif m is None:
            rep.warn(f"{tag} not in manifest - run preflight.py --record")


def check_settings(rep, path):
    p = Path(path)
    if not p.exists():
        rep.fail(f"settings missing: {p} (A2: the boot would run on defaults)")
        return
    rep.ok(f"settings present: {p.name}")
    baks = sorted(p.parent.glob(p.name + ".bak*"))
    if baks:
        rep.ok(f"{len(baks)} settings backup(s) (newest: {baks[-1].name})")
    else:
        rep.fail(f"no settings backups next to {p} - edit protocol requires a "
                 ".bak copy before every settings change (A2)")
    try:
        raw = p.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            rep.warn("settings carry a UTF-8 BOM (the 09-05 TRAP 18b shape) - "
                     "confirm the shim's parser tolerates it before trusting "
                     "this file")
            raw = raw[3:]
        json.loads(raw.decode("utf8"))
        rep.ok("settings parse as JSON")
    except Exception as e:
        rep.fail(f"settings do not parse as JSON: {e}")


def check_server(rep, ports, skip):
    if skip:
        rep.warn("server-state check skipped (--skip-server)")
        return
    out = subprocess.run(["pgrep", "-f", "wine64-preloader .*sunrise-server"],
                         capture_output=True, text=True)
    if not out.stdout.strip():
        rep.fail("server process NOT running - start it from the REPO ROOT "
                 "(mac-port/launch-server-macos.sh)")
        return
    rep.ok(f"server process alive (pid {out.stdout.split()[0]})")
    for port in ports:
        r = subprocess.run(["lsof", "-nP", "-i", f":{port}"],
                           capture_output=True, text=True)
        lines = [l for l in r.stdout.splitlines()[1:] if l.strip()]
        if lines:
            first = lines[0].split()
            rep.ok(f"port {port} bound ({first[0]} pid {first[1]})")
        else:
            rep.fail(f"port {port} NOT bound (server up but the listener is "
                     "missing - restart the server between runs)")
    # reset the server between runs is a STATE hard rule; preflight cannot
    # know whether a reset happened - the brief's checklist owns that.


def check_hooks(rep, no_traps):
    sys.path.insert(0, str(ROOT / "RE_scripts"))
    try:
        from hook_targets import parse_tables, strip_comments  # noqa: F401
    except ImportError:
        rep.warn("hook_targets unavailable - table arithmetic not checked")
        return
    hooks = ROOT / "RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks"
    if not hooks.is_dir():
        rep.warn(f"hook tree missing: {hooks}")
        return
    tables = parse_tables(hooks)
    problems = [p for t in tables for p in t.problems()]
    from hook_targets import duplicate_rva_problems, raw_lines_around
    problems.extend(duplicate_rva_problems(
        tables, raw_reader=lambda path, ln: raw_lines_around(path, ln)))
    n = sum(len(t.entries) for t in tables)
    if problems:
        for p in problems:
            rep.fail(f"hook table: {p}")
    else:
        rep.ok(f"hook install table arithmetic clean ({n} entries, "
               "declared size == initializer count, no null/rva-0 entries)")
    if no_traps:
        rep.warn("detour-footprint trap check skipped (--no-traps)")
        return
    # footprint: each table target's .pdata function must exceed the detour
    exe = ROOT / "RE_output/destiny2_unpacked_full.exe"
    if not exe.exists():
        rep.warn(f"no PE at {exe} - footprint not checkable")
        return
    import subprocess as sp
    small = []
    seen = set()
    for t in tables:
        for e in t.entries:
            if not e.rva or not e.name:
                continue
            va = 0x140000000 + e.rva
            if va in seen:
                continue
            seen.add(va)
            r = sp.run(["/usr/bin/python3", str(ROOT / "RE_scripts/pdata_bounds.py"), hex(va)],
                       capture_output=True, text=True, timeout=60)
            import re as _re
            m = _re.search(r"entry (0x[0-9a-fA-F]+)\.\.(0x[0-9a-fA-F]+)", r.stdout)
            if not m:
                small.append((e.name, va, "no .pdata (leaf/gap)"))
                continue
            size = int(m.group(2), 16) - int(m.group(1), 16)
            if size < DETOUR_MIN_BYTES:
                small.append((e.name, va, f"fn is {size} B"))
    if small:
        for name, va, why in small:
            rep.fail(f"detour FOOTPRINT: {name} va={va:#x} {why} - too small "
                     f"for a detour + relocated prologue (min {DETOUR_MIN_BYTES} B; "
                     "08-30 C2)")
    else:
        rep.ok(f"detour footprint ok ({len(seen)} targets >= {DETOUR_MIN_BYTES} B)")


def check_brief(rep, brief_path):
    text = Path(brief_path).read_text(encoding="utf8", errors="replace")
    import re
    instr = []
    m = re.search(r"instruments?\s*:\s*([^\n]+)", text, re.I)
    if m:
        instr += [s.strip().strip("\"'") for s in m.group(1).split(",") if s.strip()]
    targets = {k: Path(v) for k, v in
               (("client", DEFAULTS["client"]), ("server", DEFAULTS["server"]))}
    if not instr:
        rep.warn("brief declares no INSTRUMENTS - nothing to reconcile (ok if "
                 "this boot ships no new instrument)")
        return
    for lit in set(instr):
        found = []
        for tag, p in targets.items():
            if p.exists() and lit.encode() in p.read_bytes():
                found.append(tag)
        if found:
            rep.ok(f"literal {lit!r} present in deployed {', '.join(found)}")
        else:
            rep.fail(f"literal {lit!r} NOT in any deployed binary - the "
                     "instrument is not in what will run (A4c)")


def check_rig(rep, skip):
    if skip:
        rep.warn("rig check skipped (--skip-rig)")
        return
    host, path = DEFAULTS["rig"].split(":", 1)
    opts = ["-o", "ControlPath=" + os.path.expanduser("~/.ssh/cm-rig"),
            "-o", "ConnectTimeout=6"]
    r = subprocess.run(["ssh"] + opts + [host, "certutil", "-hashfile",
                                         f'"{path}"', "SHA256"],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0 or not r.stdout.strip():
        rep.warn(f"rig unreachable - rig identity NOT asserted this run "
                 "(solo-safe; a paired boot on a stale rig DLL is the 08-25 "
                 "class: assert it before pairing)")
        return
    # certutil prints the hash as a bare hex line; parse it
    import re as _re
    m = _re.search(r"([0-9a-fA-F]{64})", r.stdout)
    if not m:
        rep.warn(f"rig reachable but hash unparsable: {r.stdout[:120]!r}")
        return
    rhash = m.group(1).lower()
    built = Path(DEFAULTS["built_client"])
    lhash = sha256(built) if built.exists() else "?"
    if rhash == lhash:
        rep.ok(f"rig deployed DLL == built ({rhash[:16]})")
    else:
        rep.fail(f"rig deployed DLL {rhash[:16]} != built {lhash[:16]} - "
                 "the machines would run DIFFERENT clients")


def main(argv=None):
    ap = argparse.ArgumentParser(description="the world gate (see docstring)")
    ap.add_argument("--brief")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--skip-rig", action="store_true")
    ap.add_argument("--skip-server", action="store_true")
    ap.add_argument("--no-traps", action="store_true")
    for k in ("client", "built_client", "server", "built_server", "settings"):
        ap.add_argument(f"--{k.replace('_', '-')}", default=str(DEFAULTS[k]))
    ap.add_argument("--ports", default="30975,30976")
    args = ap.parse_args(argv)

    print(f"======== PREFLIGHT  {datetime.now().isoformat(timespec='seconds')} ========")
    rep = Report()
    if args.record:
        return record(args, rep)
    manifest = read_manifest()
    if manifest is None:
        rep.warn(f"no manifest at {MANIFEST} - run preflight.py --record once "
                 "after the current deploy; until then export/staleness checks "
                 "are inert")
    check_deployed(rep, "client", args.client, args.built_client, manifest)
    check_deployed(rep, "server", args.server, args.built_server, manifest)
    check_settings(rep, args.settings)
    check_server(rep, [p.strip() for p in args.ports.split(",") if p.strip()],
                 args.skip_server)
    check_hooks(rep, args.no_traps)
    if args.brief:
        check_brief(rep, args.brief)
    check_rig(rep, args.skip_rig)
    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
