"""Read Detours' near-stub/trampoline table and recover hooked-function prologues.

Detours patched 11 game functions with E9 -> slot table @ ~0x7FF5F0490000
(within rel32 of the game image). Each slot is 0x60 bytes:
  - far-stub:  48 B8 <imm64> FF E0   (mov rax, addr64; jmp rax -> Sunrise)
  - trampoline: <original prologue bytes> ... E9 <rel32 back into game>
The trampolines hold the pristine first bytes of functions whose signatures
we could never see (they are patched in the game image).
"""
import ctypes
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dump_sunrise_memory as dsm  # noqa: E402

TABLE_BASE = 0x7FF5F0490000
TABLE_SIZE = 0x1000
SLOT = 0x60

# The 8 patterns that failed our dump scan; try matching against trampolines.
MISSING = {
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
    "content_config_tick":
        "4C 8B DC 55 56 57 49 8D AB ? ? ? ? 48 81 EC ? ? ? ? 48 8B 05 ? ? ? ? 48 33 C4 48 89 85 "
        "? ? ? ? 48 8B F9 49 89 5B",
    "bubble_authority_decoder":
        "40 55 53 56 41 55 48 8D AC 24 ? ? ? ? 48 81 EC ? ? ? ? 48 8B 05 ? ? ? ? 48 33 C4 "
        "48 89 85 ? ? ? ? 4C 8B E9 48 89 BC 24",
    "content_untracked_getter":
        "48 83 EC ? C7 44 24 ? 00 00 00 00 0F B6 05 ? ? ? ? 85 C0 74 ? 0F B6 05 ? ? ? ?",
    "retail_log_enqueue":
        "83 F9 FF 74 ? 48 89 5C 24 ? 56",
}


def parse_pattern(text):
    out = []
    for tok in text.split():
        out.append(None if tok == "?" else int(tok, 16))
    return out


def pattern_matches(byteview, pattern):
    if len(byteview) < len(pattern):
        return False
    for b, e in zip(byteview, pattern):
        if e is not None and b != e:
            return False
    return True


def main() -> None:
    pid = dsm.find_pid("destiny2.exe")
    if not pid:
        print("FATAL: game not running")
        sys.exit(1)
    handle = dsm.open_process(pid)
    try:
        table = b""
        try:
            table = dsm.read_memory(handle, TABLE_BASE, TABLE_SIZE)
        except OSError as exc:
            print(f"table read failed: {exc}")
            # Probe forward for the real allocation
            for base in range(TABLE_BASE, TABLE_BASE + 0x100000, 0x1000):
                try:
                    table = dsm.read_memory(handle, base, 0x1000)
                    print(f"found readable page at 0x{base:X}")
                    break
                except OSError:
                    continue
        if not table:
            print("could not read any table page")
            sys.exit(1)

        print("slot-by-slot analysis:")
        print(f"{'slot':>4} {'page off':>8}  {'first 16 bytes':<50} {'kind':<12} detail")
        for idx in range(TABLE_SIZE // SLOT):
            off = idx * SLOT
            head = table[off:off + 16]
            if head == b"\x00" * 16:
                continue
            kind = "?"
            detail = ""
            if head[0] == 0xE9:
                rel = int.from_bytes(head[1:5], "little", signed=True)
                dest = TABLE_BASE + off + 5 + rel
                kind = "JMP rel32"
                detail = f"-> 0x{dest:X}"
            elif head[0:2] == b"\x48\xB8":
                imm = int.from_bytes(head[2:10], "little")
                kind = "FAR STUB"
                detail = f"-> 0x{imm:X} (Sunrise+0x{imm - 0x7FFA840C0000:X})"
            elif head[0:2] == b"\xFF\x25":
                kind = "JMP [abs]"
                detail = ""
            print(f"{idx:>4} {off:>8X}  {head.hex(' '):<50} {kind:<12} {detail}")

        # Try matching the missing signatures against every slot's start
        print("\nmissing-pattern matches against slot starts:")
        for name, text in MISSING.items():
            pat = parse_pattern(text)
            for idx in range(TABLE_SIZE // SLOT):
                off = idx * SLOT
                if pattern_matches(table[off:off + len(pat)], pat):
                    print(f"  MATCH {name:<30} slot {idx} (page off 0x{off:X})")
                    break
            else:
                print(f"  no full match for {name} (trampolines hold only ~5-16 "
                      f"bytes; checking prefixes next)")
        print()
        for name, text in MISSING.items():
            pat = parse_pattern(text)
            best = []
            for idx in range(TABLE_SIZE // SLOT):
                off = idx * SLOT
                n = 0
                for b, e in zip(table[off:off + len(pat)], pat):
                    if e is not None and b != e:
                        break
                    n += 1
                if n >= 5:
                    best.append((n, idx))
            if best:
                n, idx = max(best)
                print(f"  PREFIX {name:<30} slot {idx}: first {n} pattern bytes match")
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


if __name__ == "__main__":
    main()
