#!/usr/bin/env python3
"""Probe the CURRENT deployed cache's item-detail records (the armorfix method, Mac paths).

Checks: the weapon items' (bucket 0/1/2) socketCount/initialPlugs/socketTypes and every
detail's renderOverrideCount + sandboxPerkCount - the count-vs-array gap that the armorfix
found for the material rows, looked for again at the socket + perk layers.
"""
import struct

CACHE = "/Users/rubenaslanian/Documents/opencode/sunrise-fork/RE_output/s1_accept/Sunrise/cache/build_data.bin"
CACHE_HEADER = 96
ITEM_DETAIL_RECORD = 288
DETAIL_FMT = ('<HBBBBBiH' + 'H' * 12 + 'H' * 12 + 'B' + 'B' * 16 + 'i' * 16
              + 'IHH' + 'B' + 'H' * 4 + 'B' + 'B' * 32 + 'b' * 32 + 'H' * 32)

def parse_cache(data):
    assert data[:8] == b'SUNRISEB'
    version = struct.unpack_from('<I', data, 8)[0]
    counts = struct.unpack_from('<13I', data, 28)
    (named_count, item_count, detail_count, bucket_count, sel_count, set_count,
     ability_count, prog_count, scen_count, roster_count, stem_count, namehash_count,
     hashname_count) = counts
    off = CACHE_HEADER
    offsets = {}
    for key, count, rec in (("named", named_count, 140), ("items", item_count, 8),
                            ("details", detail_count, ITEM_DETAIL_RECORD),
                            ("buckets", bucket_count, 6), ("selists", sel_count, 16),
                            ("setables", set_count, 220), ("abilities", ability_count, 928),
                            ("progressions", prog_count, 4), ("scenarios", scen_count, 622),
                            ("rosters", roster_count, 2570), ("stems", stem_count, 44),
                            ("namehashes", namehash_count, 72), ("hashnames", hashname_count, 56)):
        offsets[key] = off
        off += count * rec
    print("domain totals vs file size: computed %d, file %d -> %s" % (
        off, len(data), "MATCH" if off == len(data) else "MISMATCH"))
    return {"version": version, "counts": counts, "offsets": offsets,
            "stored_checksum": struct.unpack_from('<Q', data, 88)[0],
            "eqhash": struct.unpack_from('<Q', data, 20)[0]}

def decode_detail(rec):
    fields = struct.unpack(DETAIL_FMT, rec)
    return {
        "definitionIndex": fields[0], "bucketId": fields[1],
        "equipmentSlot": fields[2] & 0xFF, "instanced": fields[3],
        "socketState": fields[4], "socketCount": fields[5], "maxStackSize": fields[6],
        "socketEntryListIndex": fields[7],
        "initialPlugs": list(fields[8:20]), "socketTypes": list(fields[20:32]),
        "statCount": fields[32],
        "definitionHash": fields[65], "gearArtIndex": fields[66],
        "artArrangementIndex": fields[67], "sandboxPerkCount": fields[68],
        "renderOverrideCount": fields[73],
    }

data = open(CACHE, "rb").read()
info = parse_cache(data)
print("version", info["version"], "counts", info["counts"])
off = info["offsets"]["details"]
details = []
for i in range(info["counts"][2]):
    rec = data[off + i * 288: off + (i + 1) * 288]
    details.append(decode_detail(rec))

print("\n=== ALL details, weapons (bucket 0-2) first ===")
for d in sorted(details, key=lambda x: (x["bucketId"], x["definitionIndex"])):
    tag = ""
    if d["bucketId"] <= 2:
        tag = "  <-- WEAPON"
    print("%s buck=%d slot=%d h=%08X socketCount=%d entryList=%d sandboxPerk=%d renderOverrides=%d%s"
          % (("0x%08X" % (d["definitionHash"] & 0xFFFFFFFF)), d["bucketId"],
             d["equipmentSlot"], d["definitionHash"] & 0xFFFFFFFF, d["socketCount"],
             d["socketEntryListIndex"], d["sandboxPerkCount"], d["renderOverrideCount"], tag))
print("\nnotes: socketCount vs the first initialPlug entries; renderOverrideCount vs the "
      "armorfix's 3-material-era baseline (3/armor).")