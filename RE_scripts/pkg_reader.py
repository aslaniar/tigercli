"""Tiger .pkg reader (Python port of Sunrise's middleware reader layout).

Header v38 (0x180 bytes): version@0, packageId@4, patchId@0x20, entryCount@0xB4,
blockCount@0xD0, entryTableOffset@0x110 (+96). Entry table: 16B records
{u32 reference, u32 typeInfo, u64 blockInfo}; block table follows +32B gap with
48B records. Blocks: 0x40000 decompressed; flags 1=oodle 2=encrypted 4=alt-key.
Tag base 0x80800000, 13-bit entry index.

Stage 1 (this file): parse + enumerate entries; scan typeInfo for tag classes
(spawn-set = 0x80809162). No decompression yet.
"""
import struct
import sys
from pathlib import Path

PKG_DIR = Path(__file__).parent.parent / "dcv build" / "packages"

TAG_BASE = 0x80800000
TAG_ENTRY_MASK = (1 << 13) - 1
SPAWN_SET_CLASS = 0x80809162


def parse_header(data: bytes) -> dict:
    version, package_id = struct.unpack_from("<HH", data, 0x00)
    if version != 38:
        raise ValueError(f"unsupported version {version}")
    patch_id = struct.unpack_from("<H", data, 0x20)[0]
    entry_count = struct.unpack_from("<I", data, 0xB4)[0]
    block_count = struct.unpack_from("<I", data, 0xD0)[0]
    entry_table = struct.unpack_from("<I", data, 0x110)[0] + 96
    block_table = entry_table + entry_count * 16 + 32
    return {
        "version": version, "package_id": package_id, "patch_id": patch_id,
        "entry_count": entry_count, "block_count": block_count,
        "entry_table": entry_table, "block_table": block_table,
    }


def parse_entries(data: bytes, header: dict) -> list:
    out = []
    for i in range(header["entry_count"]):
        off = header["entry_table"] + i * 16
        reference, type_info, block_info = struct.unpack_from("<IIQ", data, off)
        start_block = block_info & 0x3FFF
        start_offset = ((block_info >> 14) & 0x3FFF) << 4
        size = block_info >> 28
        out.append({
            "index": i, "reference": reference, "type_info": type_info,
            "start_block": start_block, "start_offset": start_offset, "size": size,
        })
    return out


def main() -> None:
    pattern = sys.argv[1] if len(sys.argv) > 1 else "w64_city_tower"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    pkgs = sorted(PKG_DIR.glob(f"{pattern}_*.pkg"), key=lambda p: p.stat().st_size)
    if not pkgs:
        print(f"no packages match {pattern}")
        return
    for pkg in pkgs[:limit]:
        data = pkg.read_bytes()
        try:
            h = parse_header(data)
        except ValueError as e:
            print(f"{pkg.name}: {e}")
            continue
        entries = parse_entries(data, h)
        classes: dict[int, int] = {}
        spawn_hits = []
        for e in entries:
            classes[e["type_info"]] = classes.get(e["type_info"], 0) + 1
            if e["type_info"] == SPAWN_SET_CLASS:
                spawn_hits.append(e)
        print(f"\n{pkg.name} ({len(data):,} B): pkgId={h['package_id']} patch={h['patch_id']} "
              f"entries={h['entry_count']} blocks={h['block_count']}")
        print(f"  distinct typeInfo: {len(classes)}; spawn-set(0x80809162) hits: {len(spawn_hits)}")
        for e in spawn_hits[:8]:
            print(f"    entry[{e['index']}] ref=0x{e['reference']:08X} "
                  f"block={e['start_block']} off={e['start_offset']} size={e['size']}")
        top = sorted(classes.items(), key=lambda kv: -kv[1])[:10]
        print("  top typeInfo: " + ", ".join(f"0x{c:08X}x{n}" for c, n in top))


if __name__ == "__main__":
    main()
