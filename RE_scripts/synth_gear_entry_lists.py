#!/usr/bin/env python3
"""Synthesize socket-entry-list rows for every socketed gear detail (experiment 14.21).

One catalog row per detail with socketCount>0 and entryList==0:
  definitionIndex = 14.. (dense append), entryCount = the detail's socket count,
  readyMask = all its lanes, definitionHash = the item's own hash.
Writes BOTH the deployed cache (selists domain grown, details repointed, checksum
fixed) and the runtime-swapped s1_domains_socketEntryLists.json (the loader's
swap replaces the catalog with these rows at every boot).
"""
import json
import shutil
import struct
import sys

sys.path.insert(0, "/Users/rubenaslanian/Documents/opencode/sunrise-fork/RE_scripts")
from probe_cache_v24 import parse, checksum, fnv, DOMAINS, HEADER, DETAIL_FMT  # noqa: E402

CACHE = ("/Users/rubenaslanian/Documents/opencode/sunrise-fork/"
         "RE_output/s1_accept/Sunrise/cache/build_data.bin")
JSON_PATH = ("/Users/rubenaslanian/Documents/opencode/sunrise-fork/"
             "RE_output/s1_accept/content/s1_domains_socketEntryLists.json")

data = bytearray(open(CACHE, "rb").read())
d = parse(CACHE)
counts = list(d["counts"])
off, selist_count, selist_rec = d["offsets"]["selists"]
det_off, det_count, det_rec = d["offsets"]["details"]

# --- collect targets + build new rows -------------------------------------
targets = []  # (detail_record_offset, item_hash, socket_count)
for i in range(det_count):
    rec_off = det_off + i * det_rec
    f = struct.unpack_from(DETAIL_FMT, data, rec_off)
    def_idx, _buck, _slot, _inst, _state, sock, _mss, entry_list = f[:8]
    item_hash = f[65]
    if sock > 0 and entry_list == 0 and item_hash != 0:
        targets.append((rec_off, item_hash, sock))

new_base = selist_count
rows = []
for n, (_off, item_hash, sock) in enumerate(targets):
    idx = new_base + n
    mask = (1 << sock) - 1
    rows.append({"definitionHash": item_hash, "definitionIndex": idx,
                 "entryCount": sock, "readyMask": mask})
print(f"gear details to repoint: {len(targets)}; new list rows {new_base}..{new_base + len(rows) - 1}")
if not rows:
    print("nothing to do")
    sys.exit(0)

# --- rewrite details' entryList (details domain sits BEFORE selists: no shift) --
# Field offsets within the 288-B record: definitionIndex@0, bucketId@2,
# equipmentSlot@3, instanced@4, ordinarySocketState@5, ordinarySocketCount@6,
# maxStackSize i32@7, socketEntryListIndex u16@11.
ENTRY_LIST_OFFSET = 11
before = {}
for (rec_off, item_hash, sock) in targets:
    before[rec_off] = struct.unpack_from("<i", data, rec_off + 7)[0]  # maxStackSize
for (rec_off, item_hash, sock), row in zip(targets, rows):
    struct.pack_into("<H", data, rec_off + ENTRY_LIST_OFFSET, row["definitionIndex"])
# Post-write verification: entryList took the value AND maxStackSize is untouched.
for (rec_off, _h, _s), row in zip(targets, rows):
    got = struct.unpack_from("<H", data, rec_off + ENTRY_LIST_OFFSET)[0]
    mss = struct.unpack_from("<i", data, rec_off + 7)[0]
    assert got == row["definitionIndex"], f"entryList write failed at {rec_off:#x}"
    assert mss == before[rec_off], f"maxStackSize clobbered at {rec_off:#x}"
print("post-write spot-check: entryList set, maxStackSize intact on all "
      f"{len(targets)} details")

# --- grow the selists domain -----------------------------------------------
new_rows_bytes = b"".join(struct.pack("<IHBBQ", r["definitionHash"], r["definitionIndex"],
                                     r["entryCount"], 0, r["readyMask"]) for r in rows)
insert_at = off + selist_count * selist_rec
data[insert_at:insert_at] = new_rows_bytes
counts[4] += len(rows)
struct.pack_into("<14I", data, 28, *counts)

# --- recompute checksum over constants + payload ---------------------------
ck_off = d["ck_off"]
ck = fnv(bytes(data[ck_off + 8:]), fnv(bytes(data[ck_off - 8:ck_off])))
struct.pack_into("<Q", data, ck_off, ck)

shutil.copy(CACHE, CACHE + ".bak_pre_synth")
open(CACHE, "wb").write(bytes(data))
print(f"cache written: selists {selist_count} -> {counts[4]}, checksum {ck:#x}")

# --- verify by re-parsing ---------------------------------------------------
d2 = parse(CACHE)
ok_layout = d2["ok"]
ok_ck = d2["ck"] == checksum(d2)
print(f"verify: layout {'MATCH' if ok_layout else 'MISMATCH'} checksum "
      f"{'OK' if ok_ck else 'BAD'}")

# --- mirror into the runtime-swapped JSON ----------------------------------
shutil.copy(JSON_PATH, JSON_PATH + ".bak_pre_synth")
jdoc = json.load(open(JSON_PATH))
jrows = jdoc.get("rows", jdoc)
known = {r["definitionIndex"] for r in jrows}
for r in rows:
    assert r["definitionIndex"] not in known, f"index collision {r['definitionIndex']}"
    jrows.append(r)
jrows.sort(key=lambda r: r["definitionIndex"])
json.dump(jdoc, open(JSON_PATH, "w"), indent=1)
print(f"json written: {len(jrows)} rows total")
