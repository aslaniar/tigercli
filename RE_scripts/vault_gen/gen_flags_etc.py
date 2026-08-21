"""Generate the flags + records + queuez families + activity-message types +
authority slots + rvas + hooks registry notes (kinds: flag, record,
queuez-family, activity-msg, authority-slot, rva, hook).

Sources (verified 2026-08-18/19):
- flags: RE_output/content/lane_dict_assembly/flag-dictionary.json (named rows)
- records: the record bridge map (FINDINGS 10.99 project: 25 MoT records 190-214)
- queues/activity/authority vocab: community_forks/Wow.md + FINDINGS 11.8b
- rvas: community_forks/Wow.md RVA atlas + the claims' dispatch anchors
- hooks: the fork client/hooks tree + the gate_trace observer targets
"""
from __future__ import annotations
import json, sys
sys.path.insert(0, __file__ and str(__import__('pathlib').Path(__file__).parent) or ".")
from common import write_note, PROJECT

# ------------------- FLAGS (named bank rows) -------------------
src = (PROJECT / r"RE_output\content\lane_dict_assembly\flag-dictionary.json").read_text(encoding="utf-8")
fd = json.loads(src)
rows = fd["rows"]
named = [r for r in rows if r.get("name")]
count = 0
for r in named:
    bank = int(r["bank"])
    front = {
        "kind": "flag",
        "id": f"bank-{bank}",
        "name": r["name"],
        "status": "VERIFIED",
        "subsystem": "flags",
        "bank_index": bank,
        "manifest_index": r.get("manifest"),
        "hash": r.get("hash", ""),
        "family": r.get("family"),
        "evidence": "RE_output/claims/flag-dictionary.md",
        "notes": r.get("empirical") or r.get("name"),
    }
    body = (
        f"Account flag bank byte {bank} (manifest index {r.get('manifest')}, hash {r.get('hash')}).\n\n"
        f"- family: {r.get('family') or '—'}\n- empirical: {r.get('empirical') or '—'}\n\n"
        f"Backlink: [[Flag bank]] (Canvas B)."
    )
    write_note("02 Registry/flags", f"flag-bank-{bank:05d}", front, body)
    count += 1
print(f"flags: {count} named bank-row notes")

# ------------------- RECORDS (the 25 MoT records) -------------------
RECORDS = [(190,1682),(191,1683),(192,1684),(193,1685),(194,1686),(195,1687),
           (196,1688),(197,1689),(198,1691),(199,1690),(200,1692),(201,1693),
           (202,1701),(203,1694),(204,1695),(205,1696),(206,1697),(207,1698),
           (208,1699),(209,1702),(210,1703),(211,1709),(212,1710),(213,1712),(214,1711)]
for rec, obj in RECORDS:
    front = {
        "kind": "record",
        "id": f"record-{rec}",
        "name": f"D1-accomplishment Record {rec}",
        "status": "STRUCTURAL",
        "subsystem": "record-state",
        "record_index": rec,
        "objective_index": obj,
        "evidence": "RE_output/claims/lane_dict_record-bridge.md",
        "notes": f"MoT record {rec} → objective {obj}; record-state space is SEPARATE from the flag bank",
    }
    body = (
        f"DestinyRecordDefinition {rec} (the D1-accomplishment family). Its objective "
        f"(index {obj}) lives in the account objectiveValues bank @+0xA438 — a SEPARATE "
        f"space from the unlock/flag registry (proven by the MoT cross).\n\n"
        f"Backlink: [[Record bridge]] / [[Flag bank]] (Canvas B)."
    )
    write_note("02 Registry/flags", f"record-{rec:03d}", front, body)
print(f"records: 25")

# ------------------- QUEUEZ FAMILIES -------------------
Q = {
 0:("banner","family-0 banner refresh (the anchor + character record pair)","RE_output/claims/family3-roster.md"),
 3:("roster","the character-select roster (1 roster obj 1768 B + per-char records 3904 B)","RE_output/claims/family3-roster.md"),
 4:("investment/account","account + characters + inventory/loadout; VERSIONED — client requires exactly +1/frame","RE_output/claims/family4-decoders.md"),
 5:("family-5","small companion record (163 B; 47 override rows)","RE_output/claims/inventory-upstream-census-031-032.md"),
}
for fam, (nm, note, ev) in Q.items():
    front = {
        "kind": "queuez-family",
        "id": f"family-{fam}",
        "name": nm,
        "status": "VERIFIED",
        "subsystem": "queuez",
        "family": fam,
        "evidence": ev,
        "notes": note,
    }
    body = f"queuez push family {fam} — {note}\n\nBacklink: [[queuez]] (Canvas A)."
    write_note("02 Registry/queuez-families", f"queuez-family-{fam}", front, body)
print("queuez families: 4")

# ------------------- ACTIVITY-MESSAGE TYPES (Wow.md / FINDINGS 11.8b) -------------------
AM = {
 0:"entity-slot notification",1:"global activity-state selection push",3:"join request",
 4:"join result",5:"sensor/authority",12:"replicated membership",16:"keepalive",
 52:"patch epoch",54:"bubble/activity-host state",
 # peer/group channel (NOT BAP — the gameplay plane)
 11:"[peer] connect",12:"[peer] join complete",13:"[peer] join abort",15:"[peer] leave session",
 16:"[peer] leave ack",17:"[peer] session disband",18:"[peer] session boot",
 26:"[peer] peer establish",29:"[peer] time sync",30:"[peer] membership update/snapshot",
 31:"[peer] peer properties",34:"[peer] player add",36:"[peer] player remove",
 38:"[peer] parameter update",39:"[peer] parameter request",40:"[peer] view-signature message",
}
for t, nm in AM.items():
    is_peer = t in (11,12,13,15,16,17,18,26,29,30,31,34,36,38,39,40)
    front = {
        "kind": "activity-msg",
        "id": f"msg-{t}",
        "name": nm.split("] ")[-1],
        "status": "VERIFIED",
        "subsystem": "activity" if not is_peer else "gameplay-peer",
        "msg_type": t,
        "evidence": "community_forks/Wow.md",
        "notes": ("peer/group gameplay channel, NOT BAP" if is_peer else "BAP activity-message / activity host"),
    }
    body = f"Activity message type {t}: {nm}\n\nBacklink: [[activity]] (Canvas A) / [[activity pipeline]] (Canvas B)."
    write_note("02 Registry/activity-messages", f"activity-msg-{t:02d}", front, body)
print(f"activity-messages: {len(AM)}")

# ------------------- AUTHORITY SLOTS (Wow.md) -------------------
SLOTS = {
 8:"Configuration",13:"Player participation",16:"Package state",17:"Lifetime",
 18:"Activity script (critical mission pair)",25:"observed during abdication investigation",
 35:"Mission director (critical mission pair)",41:"Queues",67:"Spawn keys",
}
for s, nm in SLOTS.items():
    front = {
        "kind": "authority-slot",
        "id": f"slot-{s}",
        "name": nm,
        "status": "VERIFIED",
        "subsystem": "activity-authority",
        "slot": s,
        "evidence": "community_forks/Wow.md",
        "notes": f"authority slot {s} = {nm}",
    }
    body = f"Authority slot {s} = {nm}. Publishing authority objects ALONE did not produce authored mode 1 (Wow.md).\n\nBacklink: [[activity authority]] (Canvas B)."
    write_note("02 Registry/authority-slots", f"authority-slot-{s}", front, body)
print(f"authority-slots: {len(SLOTS)}")
