#!/usr/bin/env python3
"""Probe: native socketEntryListIndex per cached item detail, read from the item blobs.

Method = the fork's own s1_domains_step3.py / upstream read_socket_entry_list:
rel = i64@128 in the definition blob; block = 128+rel; native index = u16@block.
hash->tag join via item_definitions_full.jsonl; blobs from item_blobs/.
"""
import json
import os
import struct
import sys

BASE = "/Users/rubenaslanian/Documents/opencode/sunrise-fork/RE_output/content"
CACHE = ("/Users/rubenaslanian/Documents/opencode/sunrise-fork/"
         "RE_output/s1_accept/Sunrise/cache/build_data.bin")
sys.path.insert(0, os.path.join(os.path.dirname(BASE), "..", "sunrise-fork", "RE_scripts"))

from probe_cache_v24 import parse, details  # noqa: E402

d = parse(CACHE)
det = details(d)
print(f"cached details: {len(det)}")

# hash -> tag
hash2tag = {}
with open(os.path.join(BASE, "item_definitions_full.jsonl")) as f:
    for line in f:
        r = json.loads(line)
        dh = r["definitionHash"]
        dh = int(dh, 16) if isinstance(dh, str) else int(dh) & 0xFFFFFFFF
        hash2tag[dh] = r["tag"]

rows = []
missing_blob = missing_block = zero_rel = 0
for x in det:
    h = x["definitionHash"] & 0xFFFFFFFF
    tag = hash2tag.get(h)
    if tag is None:
        print(f"  {h:08X} buck={x['bucketId']} NOT IN JSONL")
        continue
    tagi = int(tag, 16) if isinstance(tag, str) else int(tag)
    bp = os.path.join(BASE, "item_blobs", f"{tagi:08X}.bin")
    if not os.path.exists(bp):
        missing_blob += 1
        continue
    blob = open(bp, "rb").read()
    rel = struct.unpack_from("<q", blob, 128)[0]
    if rel == 0:
        zero_rel += 1
        idx = None
    else:
        block = 128 + rel
        if block < 0 or block + 2 > len(blob):
            missing_block += 1
            idx = None
        else:
            idx = struct.unpack_from("<H", blob, block)[0]
    rows.append((x["bucketId"], h, tagi, idx, x["entryList"], x["socketCount"]))

print(f"\nbucket hash nativeIdx(served) sock  | summary: no-rel={zero_rel} "
      f"oob={missing_block} noblob={missing_blob}")
for buck, h, tag, idx, served, sock in sorted(rows):
    mark = "  <-- GEAR-INDEX!" if (buck <= 18 and idx not in (None,) and idx > 13) else ""
    print(f"{buck:3d} {h:08X} tag={tag:08X} native={idx!s:>5} served={served:5d} "
          f"sock={sock:2d}{mark}")

nat = [r[3] for r in rows if r[3] is not None]
gear_nat = [r[3] for r in rows if r[3] is not None and r[0] != 39]
print(f"\nnative indices present: n={len(nat)} min={min(nat) if nat else '-'} "
      f"max={max(nat) if nat else '-'} distinct={len(set(nat))}")
print(f"non-subclass(bucket!=39) with native idx: {sorted(set(gear_nat))}")
