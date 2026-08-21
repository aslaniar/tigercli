"""Generate the web-service opcode notes (kind: opcode) — the complete Bases
table: every opcode in the server's shape tables + the fork's dedicated codecs,
with VERIFIED/INFERRED/UNMAPPED/RETIRED status filled from the 2026-08-19 lanes.

Sources: Sunrise/.../opcode_routes.cpp (shape tables), the opcode/upstream/vendor
claims, the merged boot log.
"""
from __future__ import annotations
import sys
sys.path.insert(0, __file__ and str(__import__('pathlib').Path(__file__).parent) or ".")
from common import write_note

# --- the shape tables (opcode_routes.cpp, verbatim) ---
STATUS_ONLY = [206,304,305,1101,1102,1214,1218,1225,1226,1231,1232,1233,1234,1235,
               1237,1239,1241,1242,1244,1245,1301,1822,2100]
STATUS_PAIR = [105,106,303,402,403,404,405,406,502,504,506,701,702,801,802,803,804,
               902,903,904,905,1103,
               *range(1201,1214),1215,1216,*range(1219,1225),*range(1227,1231),1236,
               1238,1240,1243,1307,1309,1310,1401,*range(1615,1619),1701,1702,
               *range(1801,1804),1820,1821,1901,2002,2200,2300,2400]
STATUS_PAIR_BOOL = [104, 901]
SHAPES = {}
for o in STATUS_ONLY: SHAPES[o] = "statusOnly (5-bit)"
for o in STATUS_PAIR: SHAPES[o] = "statusPair (37-bit)"
for o in STATUS_PAIR_BOOL: SHAPES[o] = "statusPairWithBool (5+32+1)"
# fork's dedicated codecs (outside the shape tables)
FORK_CODECS = {205:"investment snapshot",206:"queuez subscribe",501:"selected-character soid query",
               503:"primary-soid bootstrap/adopt",504:"select character",
               505:"change character (family-4 version handshake)",601:"loot pickup"}

# --- named semantics (2026-08-19 lanes: VERIFIED=traffic/codec; INFERRED=upstream codec/emitter) ---
NAMED = {
 205:("VERIFIED","investment snapshot (fork codec)","RE_output/claims/upstream-opcode-codec-diff.md"),
 206:("VERIFIED","queuez family subscription","RE_output/claims/roster-queuez-fix.md"),
 402:("INFERRED","Dismantle (character screen)","RE_output/claims/upstream-opcode-codec-diff.md"),
 403:("VERIFIED","Equip — client ×6 in boot log, byte-exact","RE_output/claims/upstream-opcode-codec-diff.md"),
 404:("INFERRED","Unequip (shared 403 codec)","RE_output/claims/upstream-opcode-codec-diff.md"),
 406:("INFERRED","lock / finisher-favorite (flags 0x3)","RE_output/claims/upstream-opcode-codec-diff.md"),
 501:("VERIFIED","selected-character SOID query (fork codec)","RE_output/claims/upstream-opcode-codec-diff.md"),
 503:("VERIFIED","primary-SOID bootstrap/adopt","RE_output/claims/upstream-opcode-codec-diff.md"),
 504:("VERIFIED","select character (roster pick)","RE_output/claims/upstream-opcode-codec-diff.md"),
 505:("VERIFIED","change character (family-4 version to wait for)","RE_output/claims/upstream-opcode-codec-diff.md"),
 601:("VERIFIED","loot pickup (fork codec)","RE_output/claims/upstream-opcode-codec-diff.md"),
 701:("VERIFIED","sync (42×/boot; payload 2,463 B unmapped)","RE_output/claims/upstream-opcode-codec-diff.md"),
 702:("VERIFIED","sync (38×/boot; payload 4,800 B unmapped)","RE_output/claims/upstream-opcode-codec-diff.md"),
 801:("VERIFIED","subclass socket select (client ×6, 10 B)","RE_output/claims/upstream-opcode-codec-diff.md"),
 901:("INFERRED","vendor purchase (incl. clock policy)","RE_output/claims/upstream-opcode-codec-diff.md"),
 903:("INFERRED","socket-plug insert","RE_output/claims/upstream-opcode-codec-diff.md"),
 904:("VERIFIED","category/collections acquire (FUN_140f2d890)","RE_output/claims/inventory-purchase-emitters.md"),
 1820:("VERIFIED","collections reacquire (FUN_1414d7620)","RE_output/claims/inventory-purchase-emitters.md"),
 1901:("VERIFIED","equipped socket-plug / shader apply (FUN_1414b9560)","RE_output/claims/inventory-purchase-emitters.md"),
 2100:("RETIRED","status-only; scenario hashes, NO handler","RE_output/claims/opcode-decoder-map.md"),
}
# INFERRED candidates (ranked, from lane D's vendor-verb inference)
CANDIDATES = {
 1101:("INFERRED","quest accept / rank-up family (candidate)","RE_output/claims/vendor-verb-inference.md"),
 1102:("INFERRED","quest accept / rank-up family (candidate)","RE_output/claims/vendor-verb-inference.md"),
 1103:("INFERRED","quest accept / rank-up family (candidate)","RE_output/claims/vendor-verb-inference.md"),
 1301:("INFERRED","vendor OPEN (candidate — the P1-1 probe)","RE_output/claims/vendor-verb-inference.md"),
 1302:("INFERRED","vendor open follow-up (candidate)","RE_output/claims/vendor-verb-inference.md"),
 1307:("INFERRED","vendor open follow-up (candidate)","RE_output/claims/vendor-verb-inference.md"),
 1309:("INFERRED","vendor open follow-up (candidate)","RE_output/claims/vendor-verb-inference.md"),
 1310:("INFERRED","vendor open follow-up (candidate)","RE_output/claims/vendor-verb-inference.md"),
 902:("INFERRED","record/triumph claim (candidate)","RE_output/claims/vendor-verb-inference.md"),
 905:("INFERRED","record/triumph claim (candidate)","RE_output/claims/vendor-verb-inference.md"),
}
# 1200-band buy/sell family (candidates, list them individually at low detail)
BUY_SELL_BAND = [o for o in STATUS_PAIR if 1200 <= o <= 1249] + [o for o in STATUS_ONLY if 1200 <= o <= 1249]
BUY_SELL_BAND = sorted(set(BUY_SELL_BAND))

def svc_note(op):
    if op in FORK_CODECS:
        return "fork dedicated codec (svc 10/11)"
    return f"shape table: {SHAPES.get(op, 'generic echo (unlisted)')} (svc 10/11)"

count = 0
# 1) the fork codecs + the shape-table members + the named set
all_ops = set(FORK_CODECS) | set(SHAPES) | set(NAMED) | set(CANDIDATES) | set(BUY_SELL_BAND)
for op in sorted(all_ops):
    if op in NAMED:
        status, sem, ev = NAMED[op]
    elif op in CANDIDATES:
        status, sem, ev = CANDIDATES[op]
    elif op in FORK_CODECS:
        status, sem, ev = "VERIFIED", FORK_CODECS[op], "RE_output/claims/upstream-opcode-codec-diff.md"
    else:
        status, sem, ev = "UNMAPPED", "shape-known; client semantics unmapped", "Sunrise/Sunrise/src/server/web_service/opcode_routes.cpp"
    front = {
        "kind": "opcode",
        "id": str(op),
        "name": sem.split(" (")[0] if status != "UNMAPPED" else f"opcode {op}",
        "status": status,
        "subsystem": "web-service",
        "direction": "c2s",
        "svc": "10/11",
        "shape": SHAPES.get(op, "generic"),
        "opcode": op,
        "evidence": ev,
        "notes": sem,
    }
    body = (
        f"Web-service verb, rides BAP svc 10/11. {svc_note(op)}\n\n"
        f"- client-side dispatch: BAP type 11 → record R19 → txnId correlation (NO opcode switch; lane B).\n"
        f"- semantics: {sem}\n"
        f"- see [[Opcode map]] and [[web-service]] (Canvas A)."
    )
    write_note("02 Registry/opcodes", f"opcode-{op}", front, body)
    count += 1
print(f"wrote {count} opcode notes (named+shape+candidates)")
