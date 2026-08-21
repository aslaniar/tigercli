"""Map the still-encrypted pages inside .text #2 to their RVAs (as runs).

If the runs are scattered -> per-page cold-code re-encryption.
If they are contiguous -> a whole region that was never executed.
"""
from pathlib import Path

DISK = Path(__file__).parent.parent / "dcv build" / "destiny2.exe"
MEM = Path(__file__).parent.parent / "RE_output" / "destiny2_unpacked.exe"

TEXT2_RAW = 0x027B0000
TEXT2_SIZE = 0x04D95A00
TEXT2_RVA = 0x03CC9000
PAGE = 0x1000


def main() -> None:
    disk = DISK.read_bytes()[TEXT2_RAW:TEXT2_RAW + TEXT2_SIZE]
    mem = MEM.read_bytes()[TEXT2_RAW:TEXT2_RAW + TEXT2_SIZE]
    runs = []
    run_start = None
    for i in range(0, len(disk), PAGE):
        is_enc = disk[i:i + PAGE] == mem[i:i + PAGE]
        if is_enc and run_start is None:
            run_start = i
        elif not is_enc and run_start is not None:
            runs.append((run_start, i))
            run_start = None
    if run_start is not None:
        runs.append((run_start, len(disk)))

    total = sum(e - s for s, e in runs)
    print(f"encrypted runs: {len(runs)}  total: {total:,} bytes ({total / 1e6:.1f} MB)")
    print(f"{'run':>4} {'start rva':>12} {'end rva':>12} {'size KB':>9}  as VA (image base 0x140000000)")
    for idx, (s, e) in enumerate(sorted(runs)):
        start_va = 0x140000000 + TEXT2_RVA + s
        end_va = 0x140000000 + TEXT2_RVA + e
        print(f"{idx:>4} 0x{TEXT2_RVA + s:08X} 0x{TEXT2_RVA + e:08X} {(e - s) // 1024:>8,}  0x{start_va:016X} - 0x{end_va:016X}")


if __name__ == "__main__":
    main()
