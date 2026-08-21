"""Classify Sunrise-resolved game addresses: which are Detours hook sites?

A Detours patch overwrites the target's first 5 bytes with E9 rel32 (JMP)
into the hooking DLL's range. Reading the bytes at each resolved address
from the live process identifies hook sites vs call-through targets.
"""
import ctypes
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dump_sunrise_memory as dsm  # noqa: E402
import extract_sunrise_targets as est  # noqa: E402

IMAGE_BASE_DISK = 0x140000000


def main() -> None:
    pid = dsm.find_pid("destiny2.exe")
    if not pid:
        print("FATAL: game not running")
        sys.exit(1)
    handle = dsm.open_process(pid)
    try:
        exe_base = 0
        for _ in range(120):
            try:
                exe_base = dsm.find_module_base(pid, "destiny2.exe")
            except OSError:
                pass
            if exe_base:
                break
            time.sleep(0.5)
        sunrise_base = dsm.find_module_base(pid, "steam_api64.dll")
        if not sunrise_base:
            print("FATAL: sunrise dll not found")
            sys.exit(1)

        sunrise_headers = dsm.read_memory(handle, sunrise_base, 0x1000)
        _ib, _e, sunrise_sections = dsm.parse_pe(sunrise_headers)
        sunrise_size = max(s[1] + max(s[3], s[4]) for s in sunrise_sections)
        sunrise_end = sunrise_base + sunrise_size

        # Collect the same 60 game-range pointer slots as the extraction run
        hits = {}
        for sect in (".data", ".rdata"):
            va_start, data = est.read_section_bytes(handle, sunrise_base, sect)
            if not data:
                continue
            for off in range(0, len(data) - 8, 8):
                val = int.from_bytes(data[off:off + 8], "little")
                if exe_base <= val < exe_base + 0x9000000:
                    hits[va_start + off] = val

        print(f"sunrise range: 0x{sunrise_base:X} .. 0x{sunrise_end:X}")
        print(f"scanning {len(hits)} resolved addresses for E9->Sunrise patches...\n")

        hooked = []
        for slot_va, target in sorted(hits.items()):
            try:
                head = dsm.read_memory(handle, target, 16)
            except OSError:
                continue
            jmp = False
            dest = 0
            if head[0] == 0xE9:
                rel = int.from_bytes(head[1:5], "little", signed=True)
                dest = target + 5 + rel
                jmp = sunrise_base <= dest < sunrise_end
            elif head[0] == 0x48 and head[1] == 0xB8:  # mov rax, imm64 (Detours alt)
                dest = int.from_bytes(head[2:10], "little")
                jmp = sunrise_base <= dest < sunrise_end
            disk_va = IMAGE_BASE_DISK + (target - exe_base)
            mark = "HOOK" if jmp else "    "
            if jmp:
                hooked.append((disk_va, dest))
            print(f"{mark} 0x{disk_va:X}  {head[:8].hex(' ')}  -> 0x{dest:X}")

        print(f"\n{len(hooked)} hook sites found:")
        for disk_va, dest in hooked:
            print(f"  0x{disk_va:X} jumps to sunrise+0x{dest - sunrise_base:X}")
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


if __name__ == "__main__":
    main()
