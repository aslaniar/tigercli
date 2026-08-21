"""Per-page comparison: on-disk (encrypted) vs in-memory (dumped) .text sections.

Answers: does ReadProcessMemory ever see decrypted pages for .text #2, and
how much of each code section actually changes between disk and memory?
"""
import sys
from pathlib import Path

DISK = Path(__file__).parent.parent / "dcv build" / "destiny2.exe"
MEM = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent / "RE_output" / "destiny2_unpacked.exe"

# (name, raw_ptr, raw_size) from the PE section table of the Arrivals build
SECTIONS = [(".text", 0x00000600, 0x01B8F600), (".text", 0x027B0000, 0x04D95A00)]
PAGE = 0x1000


def page_diff(disk: bytes, mem: bytes, name: str, raw_ptr: int, raw_size: int) -> None:
    d = disk[raw_ptr:raw_ptr + raw_size]
    m = mem[raw_ptr:raw_ptr + raw_size]
    identical = same = diff = 0
    for off in range(0, len(d), PAGE):
        dpage = d[off:off + PAGE]
        mpage = m[off:off + PAGE]
        if dpage == mpage:
            identical += 1
        else:
            diff += 1
    print(f"{name} raw=0x{raw_ptr:X} size={raw_size:,}")
    print(f"  pages identical to disk (still encrypted / never touched): {identical:,} "
          f"({identical * PAGE / 1e6:.1f} MB)")
    print(f"  pages different from disk (decrypted):                     {diff:,} "
          f"({diff * PAGE / 1e6:.1f} MB)")


def main() -> None:
    disk = DISK.read_bytes()
    mem = MEM.read_bytes()
    print(f"disk: {len(disk):,} bytes   mem-dump: {len(mem):,} bytes")
    for name, raw_ptr, raw_size in SECTIONS:
        page_diff(disk, mem, name, raw_ptr, raw_size)


if __name__ == "__main__":
    main()
