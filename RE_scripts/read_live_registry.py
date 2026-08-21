"""Read the runtime-built message-type registry DAT_142808A70 live.

The registry is XOR-obfuscated and built at runtime (static dump = zeros).
Entry stride 0xa8; claimed layout: +0x88 valid flag, +8 name ptr, +0x8c u32,
+0x98 u64. Try simple de-obfuscation heuristics (fixed XOR key, self-XOR).
"""
import ctypes
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dump_sunrise_memory as dsm  # noqa: E402

IMAGE_BASE_DISK = 0x140000000
REG_VA = 0x142808A70
ENTRIES = 64
STRIDE = 0xA8


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
        print(f"exe base: 0x{exe_base:X}")
        reg = exe_base + (REG_VA - IMAGE_BASE_DISK)
        raw = dsm.read_memory(handle, reg, ENTRIES * STRIDE)
        for i in range(ENTRIES):
            off = i * STRIDE
            chunk = raw[off:off + STRIDE]
            if chunk == b"\x00" * STRIDE:
                continue
            q0 = int.from_bytes(chunk[0:8], "little")
            q1 = int.from_bytes(chunk[8:16], "little")
            q11 = int.from_bytes(chunk[0x88:0x90], "little")
            u32 = int.from_bytes(chunk[0x8C:0x90], "little")
            q13 = int.from_bytes(chunk[0x98:0xA0], "little")
            print(f"[{i:2d}] q0=0x{q0:016X} name?=0x{q1:016X} "
                  f"flag88=0x{q11:016X} u32=0x{u32:08X} q98=0x{q13:016X}")
        # de-obfuscation heuristic: try a few plausible fixed keys on q1
        print("\nheuristics on +8 (name pointer):")
        for i in range(min(8, ENTRIES)):
            v = int.from_bytes(raw[i * STRIDE + 8:i * STRIDE + 16], "little")
            if v == 0:
                continue
            for label, key in [("exe_base", exe_base), ("entry_self", reg + i * STRIDE + 8)]:
                d = v ^ key
                if exe_base <= d < exe_base + 0x9000000:
                    print(f"  [{i}] xor {label} -> 0x{d:X} (in image!)")
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


if __name__ == "__main__":
    main()
