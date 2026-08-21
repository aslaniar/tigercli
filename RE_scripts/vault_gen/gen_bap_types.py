"""Generate the 71 bap-type registry notes (kind: bap-type) from the lane-C
crossmap (registry_fill_crossmap.json). Source: RE_output/content/registry_fill/."""
from __future__ import annotations
import json, sys
sys.path.insert(0, __file__ and str(__import__('pathlib').Path(__file__).parent) or ".")
from common import write_note, PROJECT

SRC = (PROJECT / r"RE_output\content\registry_fill\registry_fill_crossmap.json").read_text(encoding="utf-8")
data = json.loads(SRC)
rows = data["rows"] if isinstance(data, dict) else data

n = 0
for row in rows:
    typ = int(row["type"])
    name = row.get("name", "")
    svc = row.get("service", "")
    feature = row.get("feature", "")
    front = {
        "kind": "bap-type",
        "id": str(typ),
        "name": name,
        "status": "VERIFIED" if typ in (10, 11, 123) else "STRUCTURAL",
        "subsystem": "dispatch",
        "type": typ,
        "svc": svc,
        "direction": row.get("direction", ""),
        "decoder_addr": row.get("decoder_addr", ""),
        "vtable_addr": row.get("vtable_addr", ""),
        "fill_slot": row.get("table_slot", ""),
        "evidence": "RE_output/claims/decoder-registry-fill-order.md",
        "notes": feature,
    }
    body = (
        f"BAP message type. Decoder object + vtable, fill slot {row.get('table_slot')} of 71.\n\n"
        f"- service: {svc}\n- feature: {feature}\n"
        f"- the 237 other slots are structurally impossible (factory FUN_140E75790, static-init).\n\n"
        f"Backlink: [[BAP dispatch]] (Canvas B)."
    )
    write_note("02 Registry/bap-types", f"bap-type-{typ}", front, body)
    n += 1
print(f"wrote {n} bap-type notes")
