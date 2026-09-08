#!/usr/bin/env python3
# REGISTRY: caps: dashboard-fixture-test
"""Fixture replay for the v3 dashboard serving layer. No game, no ssh."""
import importlib.util, json, os, sys, tempfile, time
from pathlib import Path

spec = importlib.util.spec_from_file_location("dash", sys.argv[1])
D = importlib.util.module_from_spec(spec); spec.loader.exec_module(D)

tmp = Path(tempfile.mkdtemp())
D._segments_dir = tmp / "segments"
live = tmp / "live.log"
live.write_bytes(b"")

st = D.SourceState("mac", live)
D.SOURCES["mac"] = st
st.truncate_snapshot()
fails = []


def check(name, cond, extra=""):
    print(("  ok   " if cond else "  FAIL ") + name + (("  " + str(extra)) if not cond else ""))
    if not cond:
        fails.append(name)


def w(b):
    with open(live, "ab") as fh:
        fh.write(b)


def cycle():
    st.ingest_file()
    st.scan()


L = b"client level=info t=%d ev=bootflow stage=%s\n"

print("\n[1] partial-line buffer (the torn-line bug)")
# a live writer caught mid-line: the chunk ends inside the record
w(b"client level=info t=10 ev=activity stage=push type=12 len=100\nclient level=info t=11 ev=act")
cycle()
lines, cur, gap = st.read_window(None)
check("torn tail is withheld, not emitted", len(lines) == 1, lines)
check("type=12 counted once", st.scanner.type_counts.get("12") == 1, st.scanner.type_counts)
w(b"ivity stage=push type=45 len=9\n")
cycle()
lines2, cur2, _ = st.read_window(cur)
check("the completed line arrives whole, once",
      len(lines2) == 1 and lines2[0].endswith("type=45 len=9"), lines2)
check("type=45 counted once, type=12 not double-counted",
      st.scanner.type_counts.get("45") == 1 and st.scanner.type_counts.get("12") == 1,
      st.scanner.type_counts)

print("\n[2] cursor is incremental (a poll costs the delta, not the window)")
before = cur2
w(L % (12, b"character_select"))
cycle()
rows, cur3, _ = st.read_window(before)
check("only the new line comes back", len(rows) == 1, rows)
rows, cur4, _ = st.read_window(cur3)
check("a caught-up cursor returns nothing", rows == [] and cur4 == cur3, rows)

print("\n[3] boot epoch on an in-log restart")
ep0 = st.epoch
for stg in (b"slice_set", b"composition", b"region", b"world_step"):
    w(L % (20, stg))
cycle()
check("no epoch bump mid-boot", st.epoch == ep0, st.epoch)
check("census accumulated across the boot", len(st.scanner.stages) == 5, st.scanner.stages)
w(L % (1, b"character_select"))          # a new boot cycle in the same process
w(L % (2, b"slice_set"))
cycle()
check("epoch bumped on character_select after a late stage", st.epoch == ep0 + 1, st.epoch)
check("epoch reason recorded", "character_select" in st.epoch_reason, st.epoch_reason)
check("census reset to the new boot", len(st.scanner.stages) == 2, st.scanner.stages)
check("old boot's wire counts are gone", st.scanner.type_counts == {}, st.scanner.type_counts)
lines, cur5, _ = st.read_window(None)
check("snapshot holds the new boot only", len(lines) == 2 and "character_select" in lines[0], lines)

print("\n[4] boot epoch on a new pid")
ep1 = st.epoch
st.note_pid(4321)
check("first pid observation is not a restart", st.epoch == ep1, st.epoch)
st.note_pid(4321)
check("same pid is not a restart", st.epoch == ep1, st.epoch)
st.note_pid(9999)
check("a new pid IS a restart", st.epoch == ep1 + 1, st.epoch)
check("snapshot cleared with it", st.read_window(None)[0] == [], st.read_window(None)[0])
st.note_pid(None)
check("a closed process does NOT reset (log stays inspectable)", st.epoch == ep1 + 1, st.epoch)

print("\n[5] log rotation")
ep2 = st.epoch
w(L % (5, b"character_select"))
cycle()
live.write_bytes(b"")                     # rotated
w(L % (1, b"character_select"))
cycle()
check("rotation bumps the epoch", st.epoch == ep2 + 1, st.epoch)

print("\n[6] alignment gate (the green-chip-over-31s bug)")
D.SOURCES["server"].epoch = 0
D.SOURCES["rig"].epoch = 0
st.epoch = 0
D._clock_offsets["server"] = {"offset": 0, "spread": None, "pairs": 0, "epoch": 0}
D._clock_offsets["mac"] = {"offset": -2285, "spread": 31167, "pairs": 57, "epoch": 0}
D._clock_offsets["rig"] = {"offset": -79926, "spread": 20453, "pairs": 21, "epoch": 0}
ok, meta = D.alignment_view()
check("the measured 09-06 drift is REFUSED", ok is False, meta["unaligned"])
check("mac's refusal names the spread and the pairs",
      "31.2" in meta["unaligned"]["mac"] and "57" in meta["unaligned"]["mac"],
      meta["unaligned"]["mac"])
D._clock_offsets["mac"] = {"offset": -12, "spread": 40, "pairs": 94, "epoch": 0}
ok, meta = D.alignment_view()
check("a tight offset IS accepted", ok is True and "mac" in meta["offsets"], meta)
check("the still-loose rig stays out with a reason",
      "rig" not in meta["offsets"] and "20.5" in meta["unaligned"]["rig"],
      meta["unaligned"])
D._clock_offsets["mac"]["epoch"] = 99      # a restart invalidates it
ok, meta = D.alignment_view()
check("a stale-epoch offset is refused", ok is False
      and "re-anchoring" in meta["unaligned"]["mac"], meta["unaligned"])

print("\n[7] api_tail: epoch handshake and source filtering")
D._clock_offsets = {"mac": None, "server": None, "rig": None}
st.truncate_snapshot(); st.scanner.reset("test")
w(L % (7, b"character_select")); cycle()
r = D.api_tail({"sources": ["mac"], "n": ["50"]})
check("a first poll resets and delivers", r["sources"]["mac"]["reset"] is True
      and len(r["sources"]["mac"]["rows"]) == 1, r["sources"]["mac"])
c, e = r["sources"]["mac"]["cursor"], r["sources"]["mac"]["epoch"]
r2 = D.api_tail({"sources": ["mac"], "cur_mac": [str(c)], "ep_mac": [str(e)]})
check("a matching handshake does not reset", r2["sources"]["mac"]["reset"] is False
      and r2["sources"]["mac"]["rows"] == [], r2["sources"]["mac"])
r3 = D.api_tail({"sources": ["mac"], "cur_mac": [str(c)], "ep_mac": [str(e + 5)]})
check("a stale epoch forces a reset", r3["sources"]["mac"]["reset"] is True, r3["sources"]["mac"])
r4 = D.api_tail({"sources": [""], "n": ["50"]})
check("an explicitly empty source list means NONE (the all-off bug)",
      r4["sources"] == {}, r4["sources"])
r5 = D.api_tail({"n": ["50"]})
check("an absent source list means all", set(r5["sources"]) == set(D.ALL_SOURCES), list(r5["sources"]))
r6 = D.api_tail({"sources": ["mac"], "filter": ["nothingmatches"], "n": ["50"]})
check("a filter reports what it hid", r6["sources"]["mac"]["rows"] == []
      and r6["sources"]["mac"]["hidden"] >= 1, r6["sources"]["mac"])

print("\n[8] contract counters are boot totals, not a 2-second window")
# a real contract file, so bind_contract() takes the same path api_now does
cf = tmp / "contract.json"
cf.write_text(json.dumps({"counters": [
    {"name": "peer rows gained", "source": "mac", "match": "result=gained"}]}))
D.CONTRACT_FILE = cf
D.bind_contract()
sc = st.scanner
check("bind_contract wired the declared pattern",
      sc.contract_patterns == [("peer rows gained", "result=gained")], sc.contract_patterns)
for i in range(3):
    w(b"server level=info t=%d ev=activity stage=membership_peer result=gained\n" % (100 + i))
    cycle()
    D.bind_contract()          # the api_now path calls this on EVERY poll
check("counts accumulate across polls (v2 zeroed them on every bind)",
      sc.contract_counts.get("peer rows gained") == 3, sc.contract_counts)
cf.write_text(json.dumps({"counters": [
    {"name": "peer rows gained", "source": "mac", "match": "result=DIFFERENT"}]}))
D.bind_contract()
check("but a CHANGED declaration clears them (old tallies counted another question)",
      sc.contract_counts == {}, sc.contract_counts)

print("\n[9] snapshot trim leaves a visible gap, not a silent skip")
st.trim_base = 0
big = D._SNAPSHOT_CAP
st.append_snapshot(b"x" * 64)
old_cur = 0
st._SNAP = None
st.trim_base = 5000                        # simulate a trim past a live cursor
lines, cur, gap = st.read_window(0)
check("a cursor behind trim_base reports gap=True", gap is True, (lines, gap))

print("\n[10] a restart inside a size-bounded scan pass keeps the bytes it did not reach")
D.SCAN_CHUNK = 400                     # force the bounded path without 4 MB of I/O
st.truncate_snapshot(); st.scanner.reset("test"); st.pending = b""
w(L % (1, b"character_select")); w(L % (2, b"region"))   # a late stage, so the next
cycle(); cycle(); cycle()                                 # character_select restarts
ep = st.epoch
w(L % (1, b"character_select"))                          # the restart...
n_after = 30
for i in range(n_after):                                 # ...then more than one
    w(b"client level=info t=%d ev=activity stage=push type=12\n" % (100 + i))  # pass can read
for _ in range(20):
    cycle()
check("the restart was detected", st.epoch == ep + 1, (ep, st.epoch))
lines, _c, _g = st.read_window(None, tail_bytes=1 << 20)
check("every post-restart line survived the bounded passes",
      len(lines) == n_after + 1, len(lines))
check("and none of the pre-restart boot did",
      not any("stage=region" in l for l in lines), lines[:2])
check("the census counted each one exactly once",
      st.scanner.type_counts.get("12") == n_after, st.scanner.type_counts)
D.SCAN_CHUNK = 4 * 1024 * 1024

print("\n" + ("ALL PASS" if not fails else "FAILURES: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
