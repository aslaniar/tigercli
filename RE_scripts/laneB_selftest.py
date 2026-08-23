#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
laneB_selftest.py — smoke/selftest for boot_record.py + boot_diff.py
(NO-SYNTAX-TAX: every deliverable script is parse-checked and smoke-run
before its real run; this is that smoke pass, re-runnable).

Covered:
  1. brief gate: no brief -> exit 2; incomplete brief -> exit 3.
  2. dry manifest: exit 0; manifest.json fields present; eqHash CROSS-CHECK
     against the validated tool (RE_output/scripts/bootL_eqhash_exact.py,
     imported with its DB constant patched to the Mac path).
  3. synthetic two-sided fixture at a KNOWN offset (5000 ms) with primary +
     sanity anchor pairs, NUL-garbage, truncated pairs, embedded '=' in a
     value, and a no-t line: recorder must recover offset 5000, unify both
     sides, keep every raw line.
  4. boot_diff on two fixtures differing in exactly one settings value:
     manifest names the exact JSON path; event streams clean.

Usage: /usr/bin/python3 RE_scripts/laneB_selftest.py
Exit: 0 all green; 1 any failure.
"""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORDER = os.path.join(ROOT, "RE_scripts", "boot_record.py")
DIFF = os.path.join(ROOT, "RE_scripts", "boot_diff.py")
SYS_PY = "/usr/bin/python3"

SCRATCH = tempfile.mkdtemp(prefix="laneB_selftest_")
OUT = os.path.join(SCRATCH, "boots")
os.makedirs(OUT, exist_ok=True)

BRIEF_OK = """# BOOT BRIEF (selftest synthetic)

## Purpose/Payoff
Exercise the recorder pipeline end to end on synthetic logs: brief gate,
manifest, parse robustness, anchor offset, queryable schema.

## Falsifiable Claim
offset computed == 5000 ms; every raw line preserved; unparsed rows counted.

## What it does NOT test
Real wine/game boot, live tailing, rotation re-open (covered by tail -F
construction; live boots exercise it).

## GRAPHICS DELTA
None (synthetic logs, no renderer).
"""

BRIEF_BAD = "# BOOT BRIEF\n## Purpose\nmissing everything else\n"

fails = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print("%s %-46s %s" % (tag, name, detail))
    if not cond:
        fails.append(name)


def run_recorder(args):
    cmd = [SYS_PY, RECORDER] + args
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return p.returncode, p.stdout, p.stderr


def make_fixture(brief_path, server_log, client_log, carrier):
    """Synthetic two-sided logs at a KNOWN client-relative offset of 5000 ms
    (server clock ahead by 5000 ms). Caller bakes native t into each line."""
    with open(brief_path, "w") as fh:
        fh.write(BRIEF_OK)

    def sline(t_real, rest):
        return rest % (t_real + 5000)

    # server boot sequence (mirrors the real grammar, incl. the truncated
    # build_data identity warn with embedded NUL)
    s = []
    s.append(sline(100, "server level=debug t=%d ev=build_data stage=identity result=mismatch "
                       "cached_eq=0xE8683B305DA99CD7 expected_eq=0xAF63BD4C8601B\x00\x00\x00 tail 0xDEADBEEF"))
    s.append(sline(110, "server level=info t=%d ev=account stage=identity primary=0x9EAA300100100100 characters=0"))
    s.append(sline(120, "server level=info t=%d ev=persistence stage=initialize result=ok"))
    s.append(sline(121, "server level=info t=%d ev=transport stage=listen result=ok port=30975"))
    s.append(sline(122, "server level=info t=%d ev=https stage=listen result=ok port=8443"))
    s.append(sline(123, "server level=warn t=%d ev=config depth=1 url=https://127.0.0.1:8443/config/ token=abc=def"))
    s.append(sline(130, "server level=info t=%d ev=initialize result=ok"))
    c = []
    # primary anchor pairs (client emit_2100 / server ability_change) at
    # shared real moments t=1000 and t=2000
    c.append("client level=debug t=1000 ev=ability_gate stage=emit_2100 hash=0x00000000AAAAAAAA")
    s.append("server level=debug t=%d ev=queuez stage=ability_change result=fail step=mutate why=carrier_%d"
             % (1000 + 5000, carrier))
    c.append("client level=debug t=2000 ev=ability_gate stage=emit_2100 hash=0x00000000BBBBBBBB")
    s.append("server level=debug t=%d ev=queuez stage=ability_change result=fail step=mutate why=carrier_%d"
             % (2000 + 5000, carrier))
    # sanity anchor pairs (version bumps / banner_refresh) at t=3000,3100
    c.append("client level=debug t=3000 ev=queuez stage=family0_list first=0xCAFE/1")
    c.append("client level=debug t=3100 ev=queuez stage=family0_list first=0xCAFE/2")
    s.append(sline(3000, "server level=debug t=%d ev=queuez stage=banner_refresh result=ok"))
    s.append(sline(3100, "server level=debug t=%d ev=queuez stage=banner_refresh result=ok"))
    # a no-t line (grammar violation, must be preserved as unparsed)
    c.append("core level=info ev=initialize phase=no_t_smoke")
    # session tail
    s.append(sline(4000, "server level=debug t=%d ev=activity stage=keepalive result=ok bytes=835"))
    c.append("client level=debug t=4001 ev=egress stage=resolve target=redirect action=allow name=stun101.signon.deadorbit.net result=ok")
    with open(server_log, "w") as fh:
        fh.write("\n".join(s) + "\n")
    with open(client_log, "w") as fh:
        fh.write("\n".join(c) + "\n")


def run():
    # ---- 1. brief gate ----------------------------------------------------
    rc, out, err = run_recorder(["--out", OUT, "--label", "gate_missing"])
    check("brief gate: missing brief -> exit 2", rc == 2, "rc=%d err=%s" % (rc, err.strip()))
    bad_brief = os.path.join(SCRATCH, "brief_bad.md")
    with open(bad_brief, "w") as fh:
        fh.write(BRIEF_BAD)
    rc, out, err = run_recorder(["--brief", bad_brief, "--out", OUT, "--label", "gate_bad", "--dry"])
    check("brief gate: incomplete brief -> exit 3", rc == 3, "rc=%d err=%s" % (rc, err.strip()))

    # ---- 2. dry manifest + eqHash cross-check ------------------------------
    good_brief = os.path.join(SCRATCH, "brief_ok.md")
    with open(good_brief, "w") as fh:
        fh.write(BRIEF_OK)
    rc, out, err = run_recorder(["--brief", good_brief, "--out", OUT, "--label", "dry_manifest", "--dry"])
    check("dry manifest: exit 0", rc == 0, "rc=%d err=%s" % (rc, err.strip()))
    dry_dir = os.path.join(OUT, [d for d in os.listdir(OUT) if "dry_manifest" in d][0])
    with open(os.path.join(dry_dir, "manifest.json")) as fh:
        m = json.load(fh)
    check("dry manifest: hashes present",
          all(k in m["hashes"] for k in ("sunrise_server_exe", "steam_api64_dll",
                                         "server_settings_json", "client_settings_json",
                                         "state_db_file")))
    check("dry manifest: settings embedded",
          "server" in m["settings"] and "client" in m["settings"])
    db_c = m["db"]["tables"]
    check("dry manifest: 13 tables counted", len(db_c) == 13, str(len(db_c)))
    check("dry manifest: flags==5255 (baseline)", db_c.get("flags") == 5255,
          str(db_c.get("flags")))
    # eqHash cross-check vs the validated tool
    sys.path.insert(0, os.path.join(ROOT, "RE_output", "scripts"))
    import bootL_eqhash_exact as oracle
    import boot_record as rec
    oracle.DB = os.path.join(ROOT, "RE_output", "s1_accept", "Sunrise", "state.db")
    h_oracle = oracle.db_configured_hash(oracle.DB)
    h_rec = rec.db_configured_hash(rec.STATE_DB)
    check("eqHash: port == validated tool", h_oracle == h_rec,
          "oracle=0x%016X rec=0x%016X" % (h_oracle, h_rec))
    check("eqHash: manifest matches", m["eqHash_computed"] == "0x%016X" % h_rec,
          m["eqHash_computed"])

    # ---- 3. synthetic fixture A (known offset 5000) -------------------------
    fa = os.path.join(SCRATCH, "fxA")
    os.makedirs(fa, exist_ok=True)
    brief_a = os.path.join(fa, "brief.md")
    make_fixture(brief_a, os.path.join(fa, "sunrise.log"), os.path.join(fa, "client.log"), carrier=7)
    rc, out, err = run_recorder(["--brief", brief_a, "--out", OUT,
                                 "--label", "selftest_A_carrier7",
                                 "--server-log", os.path.join(fa, "sunrise.log"),
                                 "--client-log", os.path.join(fa, "client.log"),
                                 "--from-files"])
    check("fixture A: exit 0", rc == 0, "rc=%d err=%s" % (rc, err.strip()))
    rec_a = os.path.join(OUT, [d for d in os.listdir(OUT) if "selftest_A" in d][0])
    with open(os.path.join(rec_a, "record.json")) as fh:
        rj_a = json.load(fh)
    check("fixture A: offset==5000", rj_a.get("offset_ms") == 5000,
          "offset=%s" % rj_a.get("offset_ms"))
    check("fixture A: anchor==primary", rj_a.get("anchor_stats", {}).get("anchor") == "primary",
          str(rj_a.get("anchor_stats")))
    con = sqlite3.connect(os.path.join(rec_a, "events.sqlite"))
    n_all = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    n_parsed = con.execute("SELECT COUNT(*) FROM events WHERE parsed=1").fetchone()[0]
    n_unparsed = con.execute("SELECT COUNT(*) FROM events WHERE parsed=0").fetchone()[0]
    check("fixture A: all lines preserved", n_all == 18, "n=%d" % n_all)
    check("fixture A: unparsed no-t line counted", n_unparsed == 1, "n=%d" % n_unparsed)
    row_uni = con.execute("SELECT unified_t_ms FROM events WHERE side='server' AND ev='activity'").fetchone()[0]
    row_native = con.execute("SELECT t_ms FROM events WHERE side='server' AND ev='activity'").fetchone()[0]
    check("fixture A: unified math (9000-5000=4000)", row_uni == 4000 and row_native == 9000,
          "native=%s unified=%s" % (row_native, row_uni))
    row_c = con.execute("SELECT unified_t_ms FROM events WHERE side='client' AND ev='egress'").fetchone()[0]
    check("fixture A: client unified == native", row_c == 4001, str(row_c))
    blob = con.execute("SELECT kv FROM events WHERE ev='config'").fetchone()[0]
    kv = json.loads(blob)
    check("fixture A: '=' inside value split at first '='", kv.get("token") == "abc=def", blob)
    con.close()

    # ---- 4. fixture B: same logs, carrier=8 settings value -----------------
    fb = os.path.join(SCRATCH, "fxB")
    os.makedirs(fb, exist_ok=True)
    brief_b = os.path.join(fb, "brief.md")
    make_fixture(brief_b, os.path.join(fb, "sunrise.log"), os.path.join(fb, "client.log"), carrier=8)
    # patch the two settings copies the manifest reads: use tiny per-fixture
    # settings files (copy of the real ones with carrier flipped) — the
    # recorder reads fixed project paths, so for the selftest we verify the
    # diff on the settings DOCUMENT only via a small driver: run the settings
    # diff logic directly.
    rc, out, err = run_recorder(["--brief", brief_b, "--out", OUT,
                                 "--label", "selftest_B_carrier8",
                                 "--server-log", os.path.join(fb, "sunrise.log"),
                                 "--client-log", os.path.join(fb, "client.log"),
                                 "--from-files"])
    check("fixture B: exit 0", rc == 0, "rc=%d err=%s" % (rc, err.strip()))
    rec_b = os.path.join(OUT, [d for d in os.listdir(OUT) if "selftest_B" in d][0])
    with open(os.path.join(rec_b, "record.json")) as fh:
        rj_b = json.load(fh)
    check("fixture B: offset==5000", rj_b.get("offset_ms") == 5000, str(rj_b.get("offset_ms")))
    # event diff between A and B fixtures: identical except the why=carrier_N
    # payloads — signatures are (ev,stage,result) so the streams must be CLEAN.
    p = subprocess.run([SYS_PY, DIFF, rec_a, rec_b], capture_output=True, text=True, timeout=120)
    check("selftest diff: exit 1 (kv diffs expected)", p.returncode == 1, "rc=%d" % p.returncode)
    check("selftest diff: completed (VERDICT present, no crash)",
          "VERDICT:" in p.stdout, p.stdout[-400:])
    check("selftest diff: names queuez ability_change kv key",
          "key=why" in p.stdout, "")
    check("selftest diff: no signature/sequence diffs",
          "per-signature counts: identical" in p.stdout and
          "sequence: identical order" in p.stdout, "")
    sys.path.insert(0, os.path.join(ROOT, "RE_scripts"))
    import boot_diff as bd
    diffs = []
    bd.diff_recursive("server",
                      {"world_population_carrier": 7, "world_population": False},
                      {"world_population_carrier": 8, "world_population": False}, diffs)
    check("settings field diff names exact path",
          diffs == [("changed", "server.world_population_carrier", 7, 8)],
          str(diffs))

    # ---- 4b. t-shift case: identical events with all t= nudged +7 ms ------
    # must diff as CLEAN (kv['t'] excluded from alignment; it is the
    # t_ms/unified columns' job).
    fc = os.path.join(SCRATCH, "fxC")
    os.makedirs(fc, exist_ok=True)
    import re as _re
    for name in ("sunrise.log", "client.log"):
        src = os.path.join(fa, name)
        dst = os.path.join(fc, name)
        with open(src) as fh:
            text = fh.read()
        # shift ONLY standalone t= tokens (word-boundary guard: 'port=',
        # 'first=' etc. also end in 't=' and must not be touched)
        text = _re.sub(r"(?<![A-Za-z0-9_])t=(\d+)",
                       lambda m: "t=%d" % (int(m.group(1)) + 7), text)
        with open(dst, "w") as fh:
            fh.write(text)
    brief_c = os.path.join(fc, "brief.md")
    with open(brief_c, "w") as fh:
        fh.write(BRIEF_OK)
    rc, out, err = run_recorder(["--brief", brief_c, "--out", OUT,
                                 "--label", "selftest_C_tshift",
                                 "--server-log", os.path.join(fc, "sunrise.log"),
                                 "--client-log", os.path.join(fc, "client.log"),
                                 "--from-files"])
    check("t-shift fixture: exit 0", rc == 0, "rc=%d err=%s" % (rc, err.strip()))
    rec_c = os.path.join(OUT, [d for d in os.listdir(OUT) if "selftest_C" in d][0])
    p = subprocess.run([SYS_PY, DIFF, rec_a, rec_c], capture_output=True, text=True, timeout=120)
    check("t-shift diff: CLEAN (exit 0)", p.returncode == 0,
          "rc=%d out=%s" % (p.returncode, p.stdout[-500:]))
    check("t-shift diff: VERDICT CLEAN", "VERDICT: CLEAN" in p.stdout, p.stdout[-300:])

    # ---- 4c. db content hash determinism (real state.db, read-only) -------
    import boot_record as rec2
    h1 = rec2.db_content_hash(rec2.STATE_DB)
    h2 = rec2.db_content_hash(rec2.STATE_DB)
    check("db content hash: deterministic across opens", h1 == h2,
          "%s vs %s" % (h1[:16], h2[:16]))

    # ---- 5. LIVE TAIL + ROTATION smoke -------------------------------------
    # The 22:11 crash class: live tailing was never smoke-covered (selftest
    # used --from-files only), and TailF.buf was uninitialized. This case
    # sequences: start-at-end -> append in place -> inode rotation -> append
    # to the fresh file -> quiet stop finalize.
    def wait_for(pred, timeout=20):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if pred():
                return True
            time.sleep(0.2)
        return False

    fl = os.path.join(SCRATCH, "liveA")
    os.makedirs(fl, exist_ok=True)
    logpath = os.path.join(fl, "sunrise.log")
    client_log = os.path.join(fl, "client.log")   # never created: tailer waits
    brief_l = os.path.join(fl, "brief_live.md")
    with open(logpath, "w") as fh:
        fh.write("PRE1 level=info t=1 ev=old result=ok\n")  # pre-existing; must be skipped
    with open(brief_l, "w") as fh:
        fh.write(BRIEF_OK)
    p = subprocess.Popen([SYS_PY, RECORDER, "--brief", brief_l, "--out", OUT,
                          "--label", "selftest_live_tail",
                          "--server-log", logpath, "--client-log", client_log,
                          "--min-duration", "3", "--quiet-timeout", "2",
                          "--max-duration", "60"],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    ok_start = wait_for(lambda: os.path.exists(os.path.join(OUT,
                       [d for d in os.listdir(OUT) if "selftest_live_tail" in d][0],
                       "manifest.json")) if any("selftest_live_tail" in d
                       for d in os.listdir(OUT)) else False, timeout=30)
    check("live tail: recorder reached tail loop", ok_start, "manifest never appeared")
    time.sleep(0.8)                                  # open at END settled
    with open(logpath, "a") as fh:                   # append in place (same inode)
        fh.write("APP1 level=debug t=10 ev=append result=ok\n")
        fh.write("APP2 level=debug t=11 ev=append result=ok\n")
    time.sleep(0.6)
    os.rename(logpath, logpath + ".old")            # rotation at app start
    with open(logpath, "w") as fh:                   # fresh file (new inode)
        fh.write("NEW1 level=info t=1 ev=rotation result=ok\n")
        fh.write("NEW2 level=debug t=2 ev=rotation result=ok\n")
        fh.write("NEW3 level=debug t=3 ev=rotation result=ok\n")
    out, err = p.communicate(timeout=90)
    check("live tail: exit 0", p.returncode == 0,
          "rc=%s err=%s" % (p.returncode, err[-400:]))
    live_dir = os.path.join(OUT, [d for d in os.listdir(OUT)
                                  if "selftest_live_tail" in d][0])
    with open(os.path.join(live_dir, "record.json")) as fh:
        rj_l = json.load(fh)
    check("live tail: quiet_timeout stop", rj_l.get("stop_reason") == "quiet_timeout",
          str(rj_l.get("stop_reason")))
    con = sqlite3.connect(os.path.join(live_dir, "events.sqlite"))
    raws = [r[0] for r in con.execute("SELECT raw FROM events ORDER BY rowid")]
    con.close()
    have = set()
    for r in raws:
        have.add(r.split(" ")[0])
    check("live tail: PRE1 skipped (start at end)", "PRE1" not in have, str(raws))
    check("live tail: appended + rotated lines all captured",
          all(x in have for x in ("APP1", "APP2", "NEW1", "NEW2", "NEW3")), str(raws))

    print("-" * 72)
    if fails:
        print("SELFTEST FAILURES: %d" % len(fails))
        for f in fails:
            print("  - %s" % f)
        return 1
    print("SELFTEST PASS (%s)" % time.strftime("%Y-%m-%d %H:%M:%S"))
    return 0


if __name__ == "__main__":
    sys.exit(run())