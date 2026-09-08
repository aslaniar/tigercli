#!/usr/bin/env python3
# REGISTRY: caps: chain-status, stage-b-readout
"""chain_status.py - measure FRONT_multiplayer-chain.md's rows from a boot's logs.

THE POINT: the chain chart must never be re-derived by hand. Every row that a
log can settle is settled here, from the archive, in one command. Rows that need
a memory dump (D1) say so rather than guessing.

    python3 RE_scripts/chain_status.py RE_output/logs/<stamp>_<boot>

Reads server_sunrise.log / mac_sunrise.log / rig_sunrise.log if present. Runs the
20.336 archive audit FIRST: a startup-only log cannot settle any row, and saying
so is the whole lesson of p2-207.

Exit 0 always (a readout, not a gate).
"""
import re
import sys
from pathlib import Path

MIN_LINES = 500


def read(p):
    try:
        return p.read_text(encoding="utf8", errors="replace")
    except OSError:
        return ""


def count(text, needle):
    return text.count(needle)


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 0
    d = Path(argv[0])
    if not d.is_dir():
        print(f"not a directory: {d}")
        return 0

    logs, lines = {}, {}
    for m in ("server", "mac", "rig"):
        f = d / f"{m}_sunrise.log"
        logs[m] = read(f) if f.exists() else ""
        lines[m] = logs[m].count("\n")

    print(f"== CHAIN STATUS: {d.name}\n")
    print("-- ARCHIVE AUDIT (20.336 R1: a startup-only log settles nothing) --")
    usable = {}
    for m in ("server", "mac", "rig"):
        if not logs[m]:
            print(f"   {m:<7} MISSING")
            usable[m] = False
        elif lines[m] < MIN_LINES:
            print(f"   {m:<7} {lines[m]:>8} lines   STARTUP-ONLY - rows below are BLIND on this machine")
            usable[m] = False
        else:
            print(f"   {m:<7} {lines[m]:>8} lines   ok")
            usable[m] = True

    clients = [m for m in ("mac", "rig") if usable[m]]

    def bits(text, label):
        vals = set(re.findall(label + r": (0x[0-9a-f]+)", text))
        return sorted(vals, key=lambda v: int(v, 16))

    print("\n-- STAGE A: transport, session, roster --")
    for m in clients:
        chk = count(logs[m], "membership checksum")
        print(f"   A3 roster accepted      {m}: {chk} checksum failure(s)"
              f"{'  <- rejected' if chk else '  OK'}")
    for m in clients:
        print(f"   A4 peers valid          {m}: {bits(logs[m], 'peers valid') or 'none'}")
        print(f"   A5 players valid        {m}: {bits(logs[m], 'players valid') or 'none'}")
    for m in clients:
        worlds = re.findall(r"successfully changed world to: (\S+)", logs[m])
        print(f"   A6 worlds reached       {m}: {sorted(set(worlds)) or 'none'}")

    print("\n-- STAGE B: is the peer row composed, and is it published? --")
    if usable["server"]:
        snaps = re.findall(r"stage=wire_snapshot .*?peer=(\d+)", logs["server"])
        withpeer = sum(1 for p in snaps if p != "0")
        print(f"   B1 composition   : {withpeer} of {len(snaps)} snapshots carried a peer")
        reasons = re.findall(r"stage=wire_snapshot .*?peer=0 reason=(\w+)", logs["server"])
        tally = {}
        for r in reasons:
            tally[r] = tally.get(r, 0) + 1
        for r, n in sorted(tally.items(), key=lambda kv: -kv[1]):
            print(f"        peer=0 reason={r}: {n}")
        print("        (only REFUSALS carry reason=; never infer the total from them)")
        results = re.findall(r"stage=membership_peer result=(\w+)", logs["server"])
        rt = {}
        for r in results:
            rt[r] = rt.get(r, 0) + 1
        print(f"   B2 publication   : " + ", ".join(
            f"{k}={v}" for k, v in sorted(rt.items(), key=lambda kv: -kv[1])) or "none")
        print("        paced = held by membership_peer_duty_cycle_ms, NOT a failure")
        keys = re.findall(r"stage=membership_peer result=included key=(0x[0-9A-F]+)",
                          logs["server"])
        tk = {}
        for k in keys:
            tk[k] = tk.get(k, 0) + 1
        print("   B3 rows by PEER NAMED (a row naming machine X is delivered to the OTHER):")
        for k, n in sorted(tk.items(), key=lambda kv: -kv[1]):
            print(f"        {k}: {n}")
        print("        an imbalance here is NOT itself a defect - check the duty cycle,")
        print("        each machine's join time, and B1 before calling it starvation.")
    else:
        print("   BLIND - the server log did not observe this boot")

    print("\n-- STAGE C: entity supply --")
    for m in clients:
        free = re.findall(r"fn=idx_alloc when=enter.*?mgr_free=(\d+)", logs[m])
        zero = sum(1 for v in free if v == "0")
        print(f"   C1 idx_alloc            {m}: {len(free)} call(s), {zero} with an EMPTY pool")
        pb = count(logs[m], "failed to create 'player_broadcast' entity")
        print(f"   C3 player_broadcast     {m}: {pb} creation failure(s)")
    if usable["server"]:
        push = re.findall(r"stage=index_allocation push members=(\d+)", logs["server"])
        print(f"   C2 allocation pushes     server: {len(push)}, members= {sorted(set(push)) or 'n/a'}")

    print("\n-- STAGE D: the replication receive path --")
    print("   D1 receive blocks constructed: NEEDS A DUMP - run")
    print("        python3 RE_scripts/transition_readout.py --dump <full.dmp>")
    print("      and read section 4a (vtable bases). 4b must show exactly 4 image hits.")
    for m in clients:
        # READ THE CENSUS COUNTER, NOT THE MENTIONS. The probe emits
        # `fn=ent_recv ... attached=1 calls=N` periodically; counting the string
        # counts the CENSUS LINES (34 of them on p2-206) and reports a live
        # receiver where calls= is flatly 0. That is the 09-03 postmortem's rule:
        # read the code that PRODUCES the field before the field means anything.
        calls = [int(c) for c in re.findall(r"fn=ent_recv\b.*?\bcalls=(\d+)", logs[m])]
        if calls:
            print(f"   D4 ent_recv fires       {m}: {max(calls)} "
                  f"(from {len(calls)} census lines; 0 = the receiver never ran)")
        else:
            print(f"   D4 ent_recv fires       {m}: no census line - probe not installed")

    print("\n-- STAGE E --")
    print("   E2 renders and moves: USER-VISUAL ONLY. No log line settles it.")
    print("\n(chart: FRONT_multiplayer-chain.md - update its rows from this readout)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
