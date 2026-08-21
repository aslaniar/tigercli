"""Full-installation named-tag extractor (expansion pass 1).

Walks every .pkg, parses the named-tag directory (Sunrise named_tag_parser port),
and builds a global index: classId -> [(package, tag, name)]. Output feeds:
  - the FNV-1a hash -> name resolution (spawn sets etc.)
  - the class census (what content classes exist install-wide)
No decompression needed: named tables ride uncompressed in the misc directory.
"""
import json
import struct
import sys
from pathlib import Path

PKG_DIR = Path(__file__).parent.parent / "dcv build" / "packages"
OUT = Path(__file__).parent.parent / "RE_output" / "content"
K_NAME_CAP = 256


def fnv1a64(s: str) -> int:
    h = 0xcbf29ce484222325
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return h


def fnv1a32(s: str) -> int:
    h = 0x811C9DC5
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def extract(data: bytes, pkg_name: str, index: dict, census: dict, errors: list):
    if len(data) < 244:
        return False
    version, platform, package_id = struct.unpack_from("<HHH", data, 0)
    if version != 38:
        return False
    variant = data[26]
    misc_size, misc_offset = struct.unpack_from("<II", data, 236)
    if misc_offset == 0 or misc_offset + misc_size > len(data):
        return True  # no named directory - valid
    dir_off = misc_offset + (8 if variant == 0 else 16)
    count, rel_off, _res = struct.unpack_from("<QQQ", data, dir_off)
    if count > 8192:
        errors.append((pkg_name, f"count {count}"))
        return False
    table_off = dir_off + 24 + rel_off
    if table_off + count * 16 > len(data):
        errors.append((pkg_name, "table oob"))
        return False
    for i in range(count):
        off = table_off + i * 16
        tag, class_id = struct.unpack_from("<II", data, off)
        name_rel = struct.unpack_from("<Q", data, off + 8)[0]
        name_off = off + name_rel
        end = data.find(b"\x00", name_off, min(name_off + K_NAME_CAP, len(data)))
        if end <= name_off:
            continue
        name = data[name_off:end].decode("utf-8", errors="replace")
        index.setdefault(name, []).append({"pkg": pkg_name, "tag": f"0x{tag:08X}",
                                           "class": f"0x{class_id:08X}"})
        census[class_id] = census.get(class_id, 0) + 1
    return True


def main() -> None:
    pkgs = sorted(PKG_DIR.glob("*.pkg"))
    index: dict = {}
    census: dict = {}
    errors: list = []
    parsed = 0
    with_named = 0
    for n, pkg in enumerate(pkgs):
        data = pkg.read_bytes()
        before = len(index)
        ok = extract(data, pkg.name, index, census, errors)
        parsed += ok
        if len(index) > before:
            with_named += 1
        if (n + 1) % 400 == 0:
            print(f"  {n+1}/{len(pkgs)} packages, {len(index)} names", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "named_tags.json").write_text(json.dumps(index, indent=0))
    top = sorted(census.items(), key=lambda kv: -kv[1])[:40]
    (OUT / "class_census.txt").write_text(
        "\n".join(f"0x{c:08X}x{n}" for c, n in sorted(census.items(), key=lambda kv: -kv[1])))
    # hash resolution table for known vocabulary
    probes = ["spawn_set", "spawn", "scenario", "bubble", "slice_set"]
    resolved = {}
    for name in index:
        for p in probes:
            if p in name.lower():
                resolved[name] = {"fnv1a64": f"0x{fnv1a64(name):016X}",
                                  "fnv1a32": f"0x{fnv1a32(name):08X}",
                                  "count": len(index[name])}
                break
    (OUT / "spawn_related_names.json").write_text(json.dumps(resolved, indent=1))
    print(f"\nDONE: {parsed}/{len(pkgs)} parsed, {with_named} carry named tables, "
          f"{len(index)} unique names, {len(census)} classes, {len(errors)} errors")
    print("top classes: " + ", ".join(f"0x{c:08X}x{n}" for c, n in top[:12]))
    print(f"spawn-related names: {len(resolved)}")


if __name__ == "__main__":
    main()
