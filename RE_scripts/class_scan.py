"""Global tag-class scanner (expansion pass 1b): scan ALL packages for entries of a
given class id (spawn sets 0x80809162, spawn points 0x80809164, or any class).

Class matching is on EntryRecord.reference == classId (the package_class_scan rule).
Only the highest patch of each package family is scanned. No decompression needed.
"""
import struct
import sys
from pathlib import Path

PKG_DIR = Path(__file__).parent.parent / "dcv build" / "packages"
TAG_BASE = 0x80800000
TAG_ENTRY_BITS = 13


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
    # w64_<family>_<hexid>_<patch>.pkg -> (package_id, patch)
    stem = name[:-4]
    parts = stem.split("_")
    if len(parts) < 4:
        return None
    try:
        return int(parts[-2], 16), int(parts[-1])
    except ValueError:
        return None


def main() -> None:
    classes = [int(c, 16) for c in sys.argv[1].split(",")] if len(sys.argv) > 1 else [0x80809162]
    # collect newest patch per family
    latest: dict = {}
    for f in PKG_DIR.glob("*.pkg"):
        ids = leaf_ids(f.name)
        if not ids:
            continue
        pid, patch = ids
        fam = f.name.rsplit("_", 2)[0]
        cur = latest.get(pid)
        if cur is None or patch > cur[0]:
            latest[pid] = (patch, fam, f.name)
    print(f"package families (newest patch): {len(latest)}")

    hits: dict = {c: [] for c in classes}
    total_entries = 0
    scanned = 0
    for pid, entry in latest.items():
        patch, fam, fname = entry
        data = (PKG_DIR / fname).read_bytes()
        h = parse_header(data)
        if not h:
            continue
        entry_count, entry_table = h
        scanned += 1
        for i in range(entry_count):
            off = entry_table + i * 16
            ref, type_info = struct.unpack_from("<II", data, off)
            total_entries += 1
            if ref in hits:
                tag = TAG_BASE + (pid << TAG_ENTRY_BITS) + i
                hits[ref].append({"tag": f"0x{tag:08X}", "pkg": fname, "family": fam,
                                  "typeInfo": f"0x{type_info:08X}", "index": i})
    print(f"scanned {scanned} packages, {total_entries:,} entries")
    for c, lst in hits.items():
        print(f"\nclass 0x{c:08X}: {len(lst)} entries")
        by_fam: dict = {}
        for e in lst:
            by_fam.setdefault(e["family"], 0)
            by_fam[e["family"]] += 1
        for fam, n in sorted(by_fam.items(), key=lambda kv: -kv[1]):
            print(f"  {fam:<44} x{n}")
        # save full detail
        out = Path(__file__).parent.parent / "RE_output" / "content"
        out.mkdir(parents=True, exist_ok=True)
        (out / f"class_{c:08X}_entries.json").write_text(
            __import__("json").dumps(lst, indent=0))


if __name__ == "__main__":
    main()
