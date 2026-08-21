"""Create the anchor/index (MOC) notes that generated backlinks point to, so no
link dangles: BAP dispatch, Flag bank, Record bridge, Opcode map, web-service,
queuez, activity, activity pipeline, activity authority."""
from __future__ import annotations
import sys
sys.path.insert(0, __file__ and str(__import__('pathlib').Path(__file__).parent) or ".")
from common import write_note

ANCHORS = {
 "BAP dispatch": ("bap-type", "The client's message-type dispatch: the 71-decoder registry (DAT_14280E3E0), the two lookup thunks (FUN_14106F860/FUN_14106F870), 8 class descriptors, 37 response records. See [[B Target.canvas|Canvas B]]. Source: RE_output/claims/bap-dispatch.md + decoder-registry-fill-order.md."),
 "Flag bank": ("flag", "The account flag bank: 12,300 bytes @+0x742C = the 12,300-index bank, diffs on every push. Registry: 02 Registry/flags. Source: RE_output/claims/flag-dictionary.md."),
 "Record bridge": ("record", "The record-state space (DestinyRecordDefinition 190-214) vs the objectiveValues bank @+0xA438 — SEPARATE from the unlock registry. Source: RE_output/claims/lane_dict_record-bridge.md."),
 "Opcode map": ("opcode", "The web-service opcode registry (Bases table). Named set VERIFIED; the rest UNMAPPED = the queue. Source: the 2026-08-19 opcode lanes."),
 "web-service": ("opcode", "The web-service layer (BAP svc 10/11): the opcode envelope + the shape tables. The workhorse the client talks to the server through."),
 "queuez": ("queuez-family", "The queuez subscription/push layer (BAP svc 121/123): families 0 (banner), 3 (roster), 4 (investment, versioned), 5 (companion)."),
 "activity": ("activity-msg", "The activity plane: BAP services 6/7/8/9/16/17 + the activity-message types (0/1/3/4/5/12/16/52/54) + the peer/group channel."),
 "activity pipeline": ("rva", "The activity selection/launch pipeline: selection pump 0x175E520, local vs authored managers (mode 6 / mode 1), the route byte."),
 "activity authority": ("authority-slot", "The authority-slot vocabulary the activity host publishes (13 participation .. 35 mission director .. 67 spawn keys)."),
}
for name, (kind, body) in ANCHORS.items():
    front = {
        "kind": "index",
        "id": name.lower().replace(" ", "-"),
        "name": name,
        "status": "VERIFIED",
        "subsystem": "vault-index",
        "evidence": "RE_output/claims/",
        "notes": body.split(". ")[0],
    }
    write_note("02 Registry/_anchors", name, front, body)
print(f"wrote {len(ANCHORS)} anchor notes")
