"""Dump the 58 per-message-type descriptors (0x90 stride @ 0x141C3C600).

Each descriptor is expected to hold: handler ptr, name-string ptr, and
type metadata. Classify every qword and render name strings.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scan_sunrise_patterns import parse_pe  # noqa: E402

EXE = Path(__file__).parent.parent / "RE_output" / "destiny2_unpacked.exe"
IMAGE_BASE = 0x140000000

DESC_BASE = 0x141C3C600
DESC_STRIDE = 0x90
DESC_COUNT = 58
QWORDS = 6


def main() -> None:
    data = EXE.read_bytes()
    _ib, _e, sections = parse_pe(data)

    def va_to_off(va):
        rva = va - IMAGE_BASE
        for _n, vaddr, raw_ptr, raw_size, _vs in sections:
            if vaddr <= rva < vaddr + raw_size:
                return raw_ptr + (rva - vaddr)
        raise ValueError

    def sec_of(va):
        rva = va - IMAGE_BASE
        for name, vaddr, _r, raw_size, vsize in sections:
            if vaddr <= rva < vaddr + max(raw_size, vsize):
                return name
        return "OUT"

    def cstr(va, limit=64):
        off = va_to_off(va)
        out = bytearray()
        for i in range(limit):
            b = data[off + i]
            if b == 0:
                break
            if 32 <= b < 127:
                out.append(b)
            else:
                out.append(0x2E)
        return out.decode()

    for i in range(DESC_COUNT):
        base = DESC_BASE + i * DESC_STRIDE
        try:
            qw = [int.from_bytes(data[va_to_off(base + j * 8):va_to_off(base + j * 8) + 8], "little")
                  for j in range(QWORDS)]
        except ValueError:
            print(f"[{i:3d}] 0x{base:X} (unmapped)")
            continue
        parts = []
        for q in qw:
            if 0x140000000 <= q < 0x149000000:
                sec = sec_of(q)
                if sec in (".rdata", ".data"):
                    try:
                        parts.append(f"0x{q:X}(\"{cstr(q, 32)}\")")
                    except ValueError:
                        parts.append(f"0x{q:X}({sec})")
                else:
                    parts.append(f"0x{q:X}({sec})")
            else:
                parts.append(f"0x{q:X}")
        print(f"[{i:3d}] {base:08X}: " + "  ".join(parts))


if __name__ == "__main__":
    main()
