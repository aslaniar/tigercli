"""Watch for destiny2.exe launch and dump the image at timed intervals.

Maps the packer's decryption/re-encryption timeline:
  t0  = as fast as possible after process creation
  t30 = 30s after first sighting
  t120 = 2min after
  t600 = 10min after

Each dump is written as RE_output/dump_t{secs}.exe. Run this BEFORE the
user launches the game, or it only captures the "already running" state.
"""
import ctypes
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dump_sunrise_memory as dsm  # noqa: E402

INTERVALS = [0, 30, 120, 600]
OUT_DIR = Path(__file__).parent.parent / "RE_output"


def wait_for_pid(name: str, poll_s: float = 1.0, timeout_s: float = 900) -> int:
    print(f"waiting for {name} to appear...")
    start = time.time()
    while time.time() - start < timeout_s:
        pid = dsm.find_pid(name)
        if pid:
            return pid
        time.sleep(poll_s)
    raise TimeoutError(f"{name} did not appear within {timeout_s}s")


def dump_once(handle, pid: int, tag: str) -> int:
    """Dump image to OUT_DIR/dump_{tag}.exe, return count of pages in .text#2
    that are still byte-identical to the on-disk (encrypted) image."""
    on_disk = (Path(__file__).parent.parent / "dcv build" / "destiny2.exe").read_bytes()
    exe_base = 0
    for attempt in range(120):
        try:
            exe_base = dsm.find_module_base(pid, "destiny2.exe")
        except OSError:
            exe_base = 0
        if exe_base:
            break
        time.sleep(0.5)
    if not exe_base:
        raise RuntimeError("module base never became available")
    headers = dsm.read_memory(handle, exe_base, 0x1000)
    image_base, entry_rva, sections = dsm.parse_pe(headers)
    rebuilt = bytearray(on_disk)
    encrypted_pages = 0
    for name, vaddr, raw_ptr, raw_size, vsize in sections:
        if raw_size == 0:
            continue
        size = max(raw_size, min(vsize, 0x1000000))
        data = dsm.read_memory(handle, exe_base + vaddr, size)[:raw_size]
        rebuilt[raw_ptr:raw_ptr + raw_size] = data
        if name == ".text" and raw_size == 0x04D95A00:
            for off in range(0, len(data), 0x1000):
                if data[off:off + 0x1000] == on_disk[raw_ptr + off:raw_ptr + off + 0x1000]:
                    encrypted_pages += 1
    out = OUT_DIR / f"dump_t{tag}.exe"
    out.write_bytes(bytes(rebuilt))
    print(f"  [{tag:>4}s] wrote {out.name}  .text#2 encrypted pages: {encrypted_pages}")
    return encrypted_pages


def main() -> None:
    pid = dsm.find_pid("destiny2.exe")
    if pid:
        print(f"NOTE: game already running (pid={pid}) - timed series starts from now")
    else:
        pid = wait_for_pid("destiny2.exe")
        print(f"game launched: pid={pid}")
    handle = dsm.open_process(pid)
    try:
        start = time.time()
        for idx, interval in enumerate(INTERVALS):
            if idx > 0:
                wait = interval - INTERVALS[idx - 1]
                print(f"  waiting {wait}s...")
                time.sleep(wait)
            dump_once(handle, pid, str(interval))
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)
    print("done")


if __name__ == "__main__":
    main()
