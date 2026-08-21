# -*- coding: utf-8 -*-
"""DEPLOY BOOT Q — the census-intent boot (the upstream-exact 403, FINDINGS 13.3).

Sequence (each step logged + verified before the next):
  G0  destiny2.exe must NOT be running (the DLL swap gate — abort otherwise).
  S1  Stop the live server (PID from the listeners, port 443).
  S2  Backups: the exe -> .bak_bootP; the server cache -> .bak_bootP; the
      deployed DLL -> .bak_bootL_deployed (6ef4ea030638cbda).
  S3  Copy the lane-X build outputs (verified by SHA-256):
        server exe  1ca70c623627d6476037ba0d470604c1f3f0e72d5eaafdf108c0533175ab451b
        client dll  3da28dfd62c594f965ba162e57b44c1198b5bc4760b07192af0660553b497401
      (the DLL copy falls back to the rename trick if a zombie holds it.)
  S4  The cache pre-stamp: the new exe's ts/size + the LIVE DB's configured
      hash (the bootL_eqhash_exact.py C++ port, read-only) into the cache
      header at offset 12 (<IIQ; magic "SUNRISEB" checked).
  S5  Start the server from RE_output\s1_accept (the boot-P launch shape).
  S6  ONE settle wait (10 s), then print the boot-verification lines from the
      fresh server log (the six domains + build_data cache ok + initialize ok).
The incident re-hash + the acceptance-stack verification = the NEXT step,
run separately before the game boots (incident.py).
"""
import hashlib
import os
import shutil
import struct
import sqlite3
import subprocess
import sys
import time

ROOT = r"C:\Users\rasla\Downloads\destiny-preservation"
S1 = os.path.join(ROOT, "RE_output", "s1_accept")
EXE_LIVE = os.path.join(S1, "sunrise-server.exe")
CACHE_LIVE = os.path.join(S1, "Sunrise", "cache", "build_data.bin")
DB_LIVE = os.path.join(S1, "Sunrise", "state.db")
SRV_LOG = os.path.join(S1, "Sunrise", "logs", "sunrise.log")
BUILD = os.path.join(ROOT, "RE_build", "Sunrise-fork-inventory", "build")
EXE_NEW = os.path.join(BUILD, "server", "x64", "Release", "sunrise-server.exe")
DLL_NEW = os.path.join(BUILD, "x64", "Release", "steam_api64.dll")
DLL_LIVE = os.path.join(ROOT, "dcv build", "bin", "x64", "steam_api64.dll")

EXE_SHA = "4329d95e3a69b78e0878e0f42047f33443ef1e7c0196c1cf300eb0a7572b2dc6"
DLL_SHA = "a17db6dd2d138cfd6bf863554d3f7aaf75a0721357b60647cc0739843c129fa5"

FNV_BASIS = 14695981039346656037
FNV_PRIME = 1099511628211


def log(msg):
    print(f"[deploy] {msg}", flush=True)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pe_identity(path):
    with open(path, "rb") as f:
        data = f.read(0x400)
    e = struct.unpack_from("<I", data, 0x3C)[0]
    ts = struct.unpack_from("<I", data, e + 8)[0]
    size = struct.unpack_from("<I", data, e + 24 + 56)[0]
    return ts, size


def mix_byte(h, v):
    h ^= (v & 0xFF)
    return (h * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF


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


def server_pid():
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-NetTCPConnection -State Listen | "
         "Where-Object {$_.LocalPort -eq 443}).OwningProcess"],
        capture_output=True, text=True, timeout=30)
    for line in out.stdout.splitlines():
        line = line.strip()
        if line.isdigit():
            return int(line)
    return None


def main():
    # G0: the game must be closed (the DLL swap gate).
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-Process -Name destiny2 -ErrorAction SilentlyContinue).Id"],
        capture_output=True, text=True, timeout=30)
    alive = [l.strip() for l in out.stdout.splitlines() if l.strip().isdigit()]
    if alive:
        log(f"ABORT: destiny2.exe still running (PID {','.join(alive)}) — "
            "close the game first; the DLL swap needs it gone.")
        return 1

    # S1: stop the live server.
    pid = server_pid()
    if pid is None:
        log("no server on 443 — proceeding (already stopped?)")
    else:
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"Stop-Process -Id {pid} -Force"], timeout=30)
        time.sleep(2)
        if server_pid() is not None:
            log("ABORT: the server on 443 did not stop.")
            return 1
        log(f"stopped the live server (PID {pid})")

    # S2: backups.
    for src, bak in ((EXE_LIVE, EXE_LIVE + ".bak_bootQ"),
                     (CACHE_LIVE, CACHE_LIVE + ".bak_bootQ"),
                     (DLL_LIVE, DLL_LIVE + ".bak_bootQ_deployed")):
        if os.path.exists(bak):
            log(f"note: backup {os.path.basename(bak)} already exists — keeping it")
        else:
            shutil.copy2(src, bak)
            log(f"backed up {os.path.basename(src)} -> {os.path.basename(bak)} "
                f"({os.path.getsize(bak)} B)")

    # S3: copy + verify the build outputs.
    for src, dst, want in ((EXE_NEW, EXE_LIVE, EXE_SHA),
                           (DLL_NEW, DLL_LIVE, DLL_SHA)):
        got = sha(src)
        if got != want:
            log(f"ABORT: build output {os.path.basename(src)} hash mismatch "
                f"{got[:16]} != {want[:16]}")
            return 1
        try:
            shutil.copy2(src, dst)
        except PermissionError:
            # THE LOCKED-DLL TRICK: a zombie holds the old name; rename it away.
            log(f"copy blocked on {os.path.basename(dst)} — applying the rename trick")
            os.rename(dst, dst + ".broken")
            shutil.copy2(src, dst)
        if sha(dst) != want:
            log(f"ABORT: the deployed copy {os.path.basename(dst)} does not verify.")
            return 1
        log(f"deployed {os.path.basename(dst)} ({os.path.getsize(dst)} B, "
            f"{got[:16]}... verified)")

    # S4: the cache pre-stamp (ts/size of the new exe + the LIVE DB hash).
    ts, size = pe_identity(EXE_LIVE)
    eq = db_configured_hash(DB_LIVE)
    log(f"new exe identity: ts=0x{ts:08X} size=0x{size:X}")
    log(f"live DB configured_hash = 0x{eq:016X}")
    with open(CACHE_LIVE, "r+b") as f:
        head = f.read(96)
        if head[:8] != b"SUNRISEB":
            log("ABORT: cache magic mismatch — refusing to stamp.")
            return 1
        old_ts, old_size, old_eq = struct.unpack_from("<IIQ", head, 12)
        log(f"cache old identity: ts=0x{old_ts:08X} size=0x{old_size:X} eq=0x{old_eq:016X}")
        f.seek(12)
        f.write(struct.pack("<IIQ", ts, size, eq))
        f.flush()
    with open(CACHE_LIVE, "rb") as f:
        head = f.read(96)
    nts, nsz, neq = struct.unpack_from("<IIQ", head, 12)
    assert (nts, nsz, neq) == (ts, size, eq), "stamp mismatch"
    log("CACHE STAMP OK (ts/size/eqHash set; the checksum untouched)")

    # S5: start the server (the boot-P launch shape). DETACHED: the server must
    # not inherit this script's stdio handles, or the harness that runs the
    # script waits on the server's open pipes forever (the observed
    # "script keeps running after the deploy is done" bug — the script exits,
    # the wrapper hangs on the child's inherited handles).
    subprocess.Popen(
        [EXE_LIVE],
        cwd=S1,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        creationflags=subprocess.DETACHED_PROCESS
        | subprocess.CREATE_NEW_PROCESS_GROUP)
    log("server started (detached) — settling...")

    # S6: one settle wait, then the boot-verification lines.
    time.sleep(10)
    try:
        with open(SRV_LOG, "r", encoding="utf-8", errors="replace") as f:
            tail = f.readlines()[-40:]
    except FileNotFoundError:
        log(f"server log not found at {SRV_LOG}")
        return 0
    keys = ("domain", "build_data", "initialize", "listening", "listen",
            "error", "fail")
    for line in tail:
        low = line.lower()
        if any(k in low for k in keys):
            print("   " + line.rstrip())
    log("deploy script done — run incident.py next (the acceptance re-hash), "
        "then the boot verification vs the full log.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
