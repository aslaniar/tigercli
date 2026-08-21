"""Capture the two cold encrypted runs LIVE (they are plaintext while at a
destination; the on-disk dump sees them re-encrypted).

Reads both runs page-by-page via RPM, tolerates unreadable holes, patches the
bytes into the unpacked image, and writes destiny2_unpacked_full.exe.
"""
import ctypes
import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dump_sunrise_memory as dsm  # noqa: E402
from scan_sunrise_patterns import parse_pe  # noqa: E402

IMAGE_BASE = 0x140000000
RUNS = [(0x5D0D000, 0x609C000), (0x896A000, 0x8A5E000)]
SRC = Path(__file__).parent.parent / "RE_output" / "destiny2_unpacked.exe"
DST = Path(__file__).parent.parent / "RE_output" / "destiny2_unpacked_full.exe"


def main() -> None:
    pid = dsm.find_pid("destiny2.exe")
    if not pid:
        print("game not running")
        sys.exit(1)
    handle = dsm.open_process(pid)
    try:
        exe = dsm.find_module_base(pid, "destiny2.exe")
        print(f"exe 0x{exe:X}")
        img = bytearray(SRC.read_bytes())
        _ib, _e, sections = parse_pe(bytes(img))

        def rva_to_off(rva):
            for _n, vaddr, raw_ptr, raw_size, _vs in sections:
                if vaddr <= rva < vaddr + raw_size:
                    return raw_ptr + (rva - vaddr)
            return None

        total_pages = ok_pages = bad_pages = 0
        for rva_start, rva_end in RUNS:
            base = exe + rva_start
            n = (rva_end - rva_start) // 0x1000
            for p in range(n):
                total_pages += 1
                try:
                    pg = dsm.read_memory(handle, base + p * 0x1000, 0x1000)
                except OSError:
                    bad_pages += 1
                    continue
                off = rva_to_off(rva_start + p * 0x1000)
                if off is None:
                    bad_pages += 1
                    continue
                img[off:off + len(pg)] = pg
                ok_pages += 1
            print(f"run 0x{rva_start:X}: captured {ok_pages}/{total_pages} cumulative "
                  f"({bad_pages} bad)", flush=True)
        DST.write_bytes(bytes(img))
        print(f"\nwrote {DST} ({len(img):,} bytes); "
              f"{ok_pages}/{total_pages} cold pages captured, {bad_pages} holes remain")

        # report: how much of each run came back
        for rva_start, rva_end in RUNS:
            n = (rva_end - rva_start) // 0x1000
            ent = []
            for p in range(0, n, max(1, n // 20)):
                off = rva_to_off(rva_start + p * 0x1000)
                chunk = bytes(img[off:off + 0x1000])
                if chunk:
                    counts = [0] * 256
                    for b in chunk:
                        counts[b] += 1
                    nn = len(chunk)
                    ent.append(round(-sum(c / nn * math.log2(c / nn)
                                          for c in counts if c), 2))
            print(f"  post-patch entropy sample @0x{rva_start:X}: {ent[:10]}")
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


if __name__ == "__main__":
    main()
