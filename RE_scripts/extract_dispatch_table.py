"""Dump the BAP dispatch table(s) found via the recipient-lookup thunks.

Thunk bytes: 48 63 C1 48 8D 0D <disp32> 48 8B 04 C1 C3
  = movsxd rax,ecx; lea rcx,[rip+disp32]; mov rax,[rcx+rax*8]; ret
Table VA = thunk VA + 10 + disp32.  (.data entries in the dump hold
runtime-relocated pointers; convert back to image-base VAs.)
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scan_sunrise_patterns import parse_pe  # noqa: E402

EXE = Path(__file__).parent.parent / "RE_output" / "destiny2_unpacked.exe"
IMAGE_BASE = 0x140000000
RUNTIME_BASE = 0x7FF6300A0000

THUNKS = [("receive", 0x14106F860), ("pending", 0x14106F870)]
ENTRIES = 320


def main() -> None:
    data = EXE.read_bytes()
    _ib, _e, sections = parse_pe(data)

    def va_to_off(va):
        rva = va - IMAGE_BASE
        for _n, vaddr, raw_ptr, raw_size, _vs in sections:
            if vaddr <= rva < vaddr + raw_size:
                return raw_ptr + (rva - vaddr)
        raise ValueError(f"{hex(va)} unmapped")

    def read_va(va, size):
        off = va_to_off(va)
        return data[off:off + size]

    def norm(val):
        # runtime-relocated pointer -> image VA
        if 0x7FF000000000 <= val < 0x800000000000:
            return IMAGE_BASE + (val - RUNTIME_BASE)
        return val

    def classify(va):
        rva = va - IMAGE_BASE
        for name, vaddr, _r, raw_size, vsize in sections:
            if vaddr <= rva < vaddr + max(raw_size, vsize):
                return name
        return "OUTSIDE"

    for label, va in THUNKS:
        raw = read_va(va, 16)
        disp = struct.unpack_from("<i", raw, 6)[0]
        table = va + 10 + disp
        print(f"=== {label}-path thunk @ 0x{va:X} -> TABLE 0x{table:X} ===")
        for i in range(ENTRIES):
            try:
                val = norm(int.from_bytes(read_va(table + i * 8, 8), "little"))
            except ValueError:
                continue
            if val == 0:
                continue
            sect = classify(val)
            print(f"  [{i:3d}] 0x{val:X}  ({sect})")


if __name__ == "__main__":
    main()
