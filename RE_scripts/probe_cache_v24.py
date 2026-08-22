#!/usr/bin/env python3
"""v24 build_data.bin probe (the authoritative layout from cache/records/format.h).

Fixes the stale RE_scripts/probe_cache_itemdetails.py: header=100, 14 count fields,
spawnPoints domain between namehashes and hashnames. Dumps per-detail
socketEntryListIndex and diffs two caches when given a second path.
"""
import struct
import sys

HEADER = 100
DETAIL = 288

DETAIL_FMT = ('<HBBBBBBiH'               # defIdx,bucket,slot,instanced,sockState,sockCount,pad? no: see below
              )
# Exact field walk (packed, no padding):
# u16 definitionIndex, u8 bucketId, i8 equipmentSlot, u8 instancedDefinition,
# u8 ordinarySocketState, u8 ordinarySocketCount, i32 maxStackSize,
# u16 socketEntryListIndex,
# 12xu16 initialPlugIndices, 12xu16 socketTypes,
# u8 statCount, 16xu8 statRows, 16xi32 statValues,
# u32 definitionHash, u16 gearArtIndex, u16 artArrangementIndex,
# u8 sandboxPerkCount, 4xu16 sandboxPerks,
# u8 renderOverrideCount, 32x(u8,u8,u16) overrides
DETAIL_FMT = ('<HBBBBBiH' + 'H' * 12 + 'H' * 12 + 'B' + 'B' * 16 + 'i' * 16
              + 'IHH' + 'B' + 'H' * 4 + 'B' + 'B' * 32 + 'b' * 32 + 'H' * 32)
assert struct.calcsize(DETAIL_FMT) == DETAIL, struct.calcsize(DETAIL_FMT)

DOMAINS = [("named", 140), ("items", 8), ("details", DETAIL), ("buckets", 6),
           ("selists", 16), ("setables", 220), ("abilities", 928), ("progressions", 4),
           ("scenarios", 622), ("rosters", 2570), ("stems", 44), ("namehashes", 72),
 ("spawnp", 20), ("hashnames", 56)]


def parse(path):
    data = open(path, "rb").read()
    assert data[:8] == b'SUNRISEB', "bad magic"
    version = struct.unpack_from('<I', data, 8)[0]
    assert version in (23, 24), f"expected v23/v24, got {version}"
    # v23 = pre-spawnPoints: 13 count fields, header 96; v24 = 14 fields, header 100.
    doms = DOMAINS if version == 24 else [d for d in DOMAINS if d[0] != "spawnp"]
    header = HEADER if version == 24 else 96
    ncounts = len(doms)
    ts, size = struct.unpack_from('<II', data, 12)
    eqhash = struct.unpack_from('<Q', data, 20)[0]
    counts = struct.unpack_from('<%dI' % ncounts, data, 28)
    light_off = 28 + 4 * ncounts
    light_row = data[light_off]
    stat_rows = list(data[light_off + 1:light_off + 7])
    extracted = data[light_off + 7]
    ck_off = light_off + 8
    stored_ck = struct.unpack_from('<Q', data, ck_off)[0]
    off = ck_off + 8
    offsets = {}
    for (key, rec), count in zip(doms, counts):
        offsets[key] = (off, count, rec)
        off += count * rec
    ok = off == len(data)
    return dict(data=data, version=version, ts=ts, size=size, eqhash=eqhash,
                counts=counts, light=(light_row, stat_rows, extracted), ck=stored_ck,
                ck_off=ck_off, offsets=offsets, total=off, ok=ok)


def fnv(bs, h=14695981039346656037):
    for b in bs:
        h ^= b
        h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h


def checksum(d):
    """FNV-1a from the basis over the constants block then every domain byte.
    Two segments: [ck_off-8 : ck_off] (InvestmentConstants) and [ck_off+8 : end]
    (the whole payload) - the stored checksum's own slot is skipped."""
    off = d["ck_off"]
    return fnv(d["data"][off + 8:], fnv(d["data"][off - 8:off]))


def details(d):
    off, count, rec = d["offsets"]["details"]
    out = []
    for i in range(count):
        f = struct.unpack_from(DETAIL_FMT, d["data"], off + i * rec)
        out.append({
            "definitionIndex": f[0], "bucketId": f[1], "equipmentSlot": f[2] & 0xFF,
            "instanced": f[3], "ordinarySocketState": f[4], "socketCount": f[5],
            "maxStackSize": f[6], "entryList": f[7],
            "initialPlugs": list(f[8:20]), "socketTypes": list(f[20:32]),
            "statCount": f[32],
            "definitionHash": f[65], "gearArtIndex": f[66], "artArrangementIndex": f[67],
            "sandboxPerkCount": f[68], "renderOverrideCount": f[73],
        })
    return out


def selists(d):
    off, count, rec = d["offsets"]["selists"]
    out = []
    for i in range(count):
        h, idx, ec, _r, mask = struct.unpack_from('<IHBBQ', d["data"], off + i * rec)
        out.append({"definitionHash": h, "definitionIndex": idx,
                    "entryCount": ec, "readyMask": mask})
    return out


def main():
    paths = sys.argv[1:] or ["/Users/rubenaslanian/Documents/opencode/sunrise-fork/"
                             "RE_output/s1_accept/Sunrise/cache/build_data.bin"]
    parsed = []
    for p in paths:
        d = parse(p)
        print(f"== {p}")
        print(f"   v{d['version']} ts={d['ts']} size={d['size']} eqhash={d['eqhash']:#x} "
              f"lightRow={d['light'][0]} extracted={d['light'][2]}")
        print(f"   counts={list(d['counts'])}")
        print(f"   layout {'MATCH' if d['ok'] else 'MISMATCH'} "
              f"(computed {d['total']}, file {len(d['data'])})")
        print(f"   checksum stored={d['ck']:#018x} computed={checksum(d):#018x} "
              f"{'OK' if d['ck'] == checksum(d) else 'BAD'}")
        parsed.append(d)
    if len(parsed) < 2:
        ds = details(parsed[0])
        print(f"\n=== details ({len(ds)}) ===")
        for x in sorted(ds, key=lambda r: (r["bucketId"], r["definitionIndex"])):
            tag = " <-- WEAPON" if x["bucketId"] <= 2 else ""
            print(f"{x['definitionHash']:08X} buck={x['bucketId']:3d} slot={x['equipmentSlot']:3d} "
                  f"sock={x['socketCount']:2d} entryList={x['entryList']:5d} "
                  f"perks={x['sandboxPerkCount']:3d} rovr={x['renderOverrideCount']:3d}{tag}")
        print("\n=== selists ===")
        for s in selists(parsed[0]):
            print(s)
        return
    a, b = parsed
    da = {x["definitionHash"]: x for x in details(a)}
    db = {x["definitionHash"]: x for x in details(b)}
    only_a = sorted(set(da) - set(db))
    only_b = sorted(set(db) - set(da))
    changed = sorted(k for k in set(da) & set(db)
                     if da[k]["entryList"] != db[k]["entryList"])
    print(f"\n=== DIFF details: onlyA={len(only_a)} onlyB={len(only_b)} entryListChanged={len(changed)}")
    for k in only_a[:10]:
        print(f"  A-only {k:08X} bucket={da[k]['bucketId']} entryList={da[k]['entryList']}")
    for k in only_b[:10]:
        print(f"  B-only {k:08X} bucket={db[k]['bucketId']} entryList={db[k]['entryList']}")
    for k in changed[:40]:
        print(f"  CHG {k:08X} bucket={da[k]['bucketId']} entryList {da[k]['entryList']} -> {db[k]['entryList']}")
    la, lb = selists(a), selists(b)
    print(f"=== selists: A={len(la)} B={len(lb)}")
    sa = {s['definitionIndex']: s for s in la}
    sb = {s['definitionIndex']: s for s in lb}
    for i in sorted(set(sa) | set(sb)):
        if sa.get(i) != sb.get(i):
            print(f"  selist[{i}] A={sa.get(i)} B={sb.get(i)}")


if __name__ == "__main__":
    main()
