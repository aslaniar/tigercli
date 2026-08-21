"""Full-installation class census: histogram the reference field of every entry
in every newest-patch package (2.8M entries). Output = the complete content-class
inventory of the Arrivals build.
"""
import json
import struct
import sys
from collections import Counter
from pathlib import Path

PKG_DIR = Path(__file__).parent.parent / "dcv build" / "packages"
OUT = Path(__file__).parent.parent / "RE_output" / "content" / "class_reference_census.json"


def parse_header(data: bytes):
    version = struct.unpack_from("<H", data, 0)[0]
    if version != 38:
        return None
    entry_count = struct.unpack_from("<I", data, 0xB4)[0]
    if entry_count == 0 or entry_count > 8192:
        return None
    entry_table = struct.unpack_from("<I", data, 0x110)[0] + 96
    return entry_count, entry_table


def leaf_ids(name: str):
    parts = name[:-4].split("_")
    if len(parts) < 4:
        return None
    try:
        return int(parts[-2], 16), int(parts[-1])
    except ValueError:
        return None


def main() -> None:
    latest: dict = {}
    for f in PKG_DIR.glob("*.pkg"):
        ids = leaf_ids(f.name)
        if not ids:
            continue
        pid, patch = ids
        cur = latest.get(pid)
        if cur is None or patch > cur[0]:
            latest[pid] = (patch, f.name)
    print(f"families: {len(latest)}")

    census: Counter = Counter()
    tag_classes: Counter = Counter()
    total = 0
    for n, (pid, entry) in enumerate(latest.items()):
        fname = entry[1]
        data = (PKG_DIR / fname).read_bytes()
        h = parse_header(data)
        if not h:
            continue
        entry_count, entry_table = h
        for i in range(entry_count):
            ref = struct.unpack_from("<I", data, entry_table + i * 16)[0]
            census[ref] += 1
            total += 1
            if 0x80800000 <= ref < 0x82000000:
                tag_classes[ref] += 1
        if (n + 1) % 100 == 0:
            print(f"  {n+1}/{len(latest)} pkgs, {total:,} entries, {len(census)} classes",
                  flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(
        {"total_entries": total, "distinct_reference_values": len(census),
         "census": {f"0x{k:08X}": v for k, v in census.most_common()},
         "tag_range_values": len(tag_classes)}))
    print(f"\nDONE: {total:,} entries, {len(census)} distinct reference values "
          f"({len(tag_classes)} in tag range 0x80800000-0x82000000)")
    print("top 30:")
    for k, v in census.most_common(30):
        print(f"  0x{k:08X}  x{v:,}")


if __name__ == "__main__":
    main()
