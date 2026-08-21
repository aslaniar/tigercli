"""Scan destiny2.exe for all 16 Sunrise byte-signature anchors.

Ports the signature text from Sunrise/src/client/patterns/*.cpp (IDA-style
hex bytes + '?' wildcards) and resolves each against the PE sections,
reporting file offset -> RVA -> VA and match uniqueness.
"""
import struct
import sys
from pathlib import Path

EXE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent / "dcv build" / "destiny2.exe"

SIGNATURES = {
    "transport_kind":
        "40 53 48 83 EC ? 80 3D ? ? ? ? 00 BB 01 00 00 00 74 ? 48 8B 0D ? ? ? ? 48 85 C9 74 ? "
        "48 8B 01 FF 50 60 84 C0 B9 02 00 00 00 0F 44 D9 8B C3 48 83 C4 ? 5B C3",
    "http_execute_request":
        "48 8B C4 55 57 48 8D 68 ? 48 81 EC ? ? ? ? 48 89 70 ? 33 FF 48 8B F2 4C 89 70 ? 4C "
        "8B F1 40 38 7A 0D",
    "signon_readiness_failure":
        "48 89 5C 24 ? 48 89 74 24 ? 57 48 83 EC ? 48 8B 05 ? ? ? ? 40 32 FF",
    "signon_readiness_ready":
        "48 89 5C 24 ? 48 89 74 24 ? 57 48 83 EC ? 48 8B 05 ? ? ? ? 33 F6 48 8B 15 ? ? ? ? "
        "8B DE 40 B7 01",
    "content_config_fetch":
        "48 89 5C 24 ? 48 89 74 24 ? 57 48 83 EC ? 41 0F B6 F8 48 8B DA",
    "content_config_tick":
        "4C 8B DC 55 56 57 49 8D AB ? ? ? ? 48 81 EC ? ? ? ? 48 8B 05 ? ? ? ? 48 33 C4 48 89 85 "
        "? ? ? ? 48 8B F9 49 89 5B",
    "content_manifest_gate":
        "4C 89 B4 24 ? ? ? ? E8 ? ? ? ? 80 3D ? ? ? ? 00 74",
    "bubble_authority_decoder":
        "40 55 53 56 41 55 48 8D AC 24 ? ? ? ? 48 81 EC ? ? ? ? 48 8B 05 ? ? ? ? 48 33 C4 "
        "48 89 85 ? ? ? ? 4C 8B E9 48 89 BC 24",
    "content_untracked_getter":
        "48 83 EC ? C7 44 24 ? 00 00 00 00 0F B6 05 ? ? ? ? 85 C0 74 ? 0F B6 05 ? ? ? ?",
    "content_id_token_load":
        "0F 10 44 24 ? 41 B8 14 00 00 00 48 8D 15 ? ? ? ? 0F 10 4C 24 ? 48 8D 8C 24 ? ? ? ?",
    "queuez_object_resolver":
        "4C 8B 1D ? ? ? ? 45 33 C9 48 63 C2 45 8B D0 48 05 1A 25 00 00 48 8D 14 40 48 C1 E2 05",
    "queuez_family5_subscribe":
        "40 57 48 83 EC ? 48 8B F9 E8 ? ? ? ? 0F B6 47 50 84 C0 75 ? E8 ? ? ? ?",
    "get_item_stat_value":
        "40 53 56 41 54 41 56 41 57 48 83 EC ? 45 33 E4 41 0F B6 D9 4C 8B 8C 24 ? ? ? ? "
        "4D 8B F0 44 89 21",
    "light_value_to_scalar":
        "48 89 5C 24 ? 48 89 74 24 ? 57 48 83 EC ? 0F 29 74 24 ? 41 0F B6 D8",
    "retail_log_enqueue":
        "83 F9 FF 74 ? 48 89 5C 24 ? 56",
    "retail_log_set_category_verbosity":
        "40 55 53 57 48 8D AC 24 ? ? ? ? 48 81 EC ? ? ? ? 48 8B 05 ? ? ? ? 48 33 C4 48 89 85 "
        "? ? ? ? 48 63 F9 8B DA",
}


def parse_signature(text: str) -> list[int | None]:
    """Space-separated 2-hex-digit bytes and '?' wildcards -> pattern list."""
    pattern = []
    for token in text.split():
        if token == "?":
            pattern.append(None)
        else:
            pattern.append(int(token, 16))
    return pattern


def scan(data: bytes, pattern: list[int | None]) -> list[int]:
    """Return all file offsets where the pattern matches (first byte exact)."""
    first = pattern[0]
    matches = []
    pos = 0
    while True:
        pos = data.find(first, pos)
        if pos < 0:
            break
        ok = True
        for j, expected in enumerate(pattern[1:], start=1):
            if expected is not None and data[pos + j] != expected:
                ok = False
                break
        if ok:
            matches.append(pos)
        pos += 1
    return matches


def parse_pe(data: bytes):
    """Parse PE headers -> (image_base, entry_rva, [(name, rva, raw_ptr, raw_size, vsize)])."""
    assert data[:2] == b"MZ", "not a PE file"
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[e_lfanew:e_lfanew + 4] == b"PE\0\0", "no PE signature"
    n_sections = struct.unpack_from("<H", data, e_lfanew + 6)[0]
    opt_size = struct.unpack_from("<H", data, e_lfanew + 20)[0]
    magic = struct.unpack_from("<H", data, e_lfanew + 24)[0]
    entry_rva = struct.unpack_from("<I", data, e_lfanew + 24 + 16)[0]
    image_base = struct.unpack_from("<Q", data, e_lfanew + 24 + (24 if magic == 0x20B else 28))[0]
    section_off = e_lfanew + 24 + opt_size
    sections = []
    for i in range(n_sections):
        off = section_off + i * 40
        name = data[off:off + 8].rstrip(b"\0").decode(errors="replace")
        vsize, vaddr, raw_size, raw_ptr = struct.unpack_from("<IIII", data, off + 8)
        sections.append((name, vaddr, raw_ptr, raw_size, vsize))
    return image_base, entry_rva, sections


def rva_of(file_off: int, sections) -> int | None:
    for _name, vaddr, raw_ptr, raw_size, _vsize in sections:
        if raw_ptr <= file_off < raw_ptr + raw_size:
            return vaddr + (file_off - raw_ptr)
    return None


def entropy(chunk: bytes) -> float:
    import math
    counts = [0] * 256
    for b in chunk:
        counts[b] += 1
    n = len(chunk)
    return -sum(c / n * math.log2(c / n) for c in counts if c)


def main() -> None:
    data = EXE.read_bytes()
    print(f"exe: {EXE}  ({len(data):,} bytes)")
    image_base, entry_rva, sections = parse_pe(data)
    print(f"image base: 0x{image_base:X}  entry_rva: 0x{entry_rva:08X}  sections: {len(sections)}")
    entry_sec = next((s[0] for s in sections if s[1] <= entry_rva < s[1] + max(s[3], s[4])), "?")
    print(f"entry point section: {entry_sec}")
    for marker in (b"VMProtect", b"vmp0", b"Themida", b"Enigma"):
        hits = data.count(marker)
        if hits:
            print(f"packer marker {marker!r}: {hits} occurrences")
    for name, vaddr, raw_ptr, raw_size, vsize in sections:
        e = entropy(data[raw_ptr:raw_ptr + raw_size]) if raw_size else 0
        print(f"  {name:<10} rva=0x{vaddr:08X} raw=0x{raw_ptr:08X} raw_size=0x{raw_size:08X} "
              f"vsize=0x{vsize:08X} entropy={e:.2f}")
    print()
    all_unique = True
    for name, text in SIGNATURES.items():
        pattern = parse_signature(text)
        offsets = scan(data, pattern)
        status = "UNIQUE" if len(offsets) == 1 else ("AMBIGUOUS" if len(offsets) > 1 else "MISSING")
        if status != "UNIQUE":
            all_unique = False
        line = f"  {name:<32} {status:<9} len={len(pattern):>3} matches={len(offsets)}"
        if offsets:
            rva = rva_of(offsets[0], sections)
            va = image_base + rva if rva is not None else None
            sec = next((s[0] for s in sections if s[2] <= offsets[0] < s[2] + s[3]), "?")
            line += f"  @ file=0x{offsets[0]:08X} rva=0x{rva:08X} va=0x{va:016X} ({sec})"
            if len(offsets) > 1:
                line += f"  +{len(offsets) - 1} more"
        print(line)
    print()
    print("RESULT:", "ALL 16 ANCHORS RESOLVED UNIQUELY" if all_unique else "SOME ANCHORS FAILED")


if __name__ == "__main__":
    main()
