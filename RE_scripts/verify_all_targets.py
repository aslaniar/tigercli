"""Definitive mapping of all 16 Sunrise game targets.

For hooked functions the first 5 bytes are the E9 patch (wildcarded);
bytes 5..N are original. Match each full pattern against (5 wildcards +
live tail bytes) to identify every target, including the signon pair.
"""
import ctypes
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dump_sunrise_memory as dsm  # noqa: E402

IMAGE_BASE_DISK = 0x140000000

ALL = {
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

# Candidate game addresses: the 11 E9-patched sites + 8 known dump VAs
CANDIDATES = {
    "0x140405F80": 0x140405F80, "0x14039AC90": 0x14039AC90, "0x1403C9FC0": 0x1403C9FC0,
    "0x1402FACA0": 0x1402FACA0, "0x140405450": 0x140405450, "0x1404053A0": 0x1404053A0,
    "0x14039B710": 0x14039B710, "0x140D4C550": 0x140D4C550, "0x14035D860": 0x14035D860,
    "0x140474660": 0x140474660, "0x140474610": 0x140474610,
    "0x1404C9E00": 0x1404C9E00, "0x1404CA36A": 0x1404CA36A, "0x14005FD6F": 0x14005FD6F,
    "0x140E002D0": 0x140E002D0, "0x140BE9370": 0x140BE9370, "0x140524720": 0x140524720,
    "0x14054CC10": 0x14054CC10, "0x14035DC80": 0x14035DC80,
}


def parse_pattern(text):
    return [None if t == "?" else int(t, 16) for t in text.split()]


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

        heads = {}
        for label, disk_va in CANDIDATES.items():
            addr = exe_base + (disk_va - IMAGE_BASE_DISK)
            try:
                raw = dsm.read_memory(handle, addr, 64)
            except OSError:
                continue
            patched = raw[0] == 0xE9
            heads[disk_va] = (patched, list(raw))

        print("matching all 16 patterns against live heads:\n")
        for name, text in ALL.items():
            pat = parse_pattern(text)
            found = None
            for disk_va, (patched, raw) in heads.items():
                if patched:
                    for patchlen in range(5, min(16, len(pat))):
                        view = [None] * patchlen + raw[patchlen:]
                        if len(view) < len(pat):
                            continue
                        if all(v is None or e is None or e == v
                               for v, e in zip(view, pat)):
                            found = (disk_va, patchlen)
                            break
                    if found:
                        break
                else:
                    if len(raw) < len(pat):
                        continue
                    if all(e is None or e == v for v, e in zip(raw, pat)):
                        found = (disk_va, 0)
                        break
            status = f"0x{found[0]:X} (patchlen {found[1]})" if found else "---"
            print(f"  {name:<34} {status}")
        print()
        print("unidentified hooked candidates (full 64-byte heads):")
        for disk_va, (patched, raw) in sorted(heads.items()):
            matched = False
            for t in ALL.values():
                pat = parse_pattern(t)
                if patched:
                    for patchlen in range(5, min(16, len(pat))):
                        view = [None] * patchlen + raw[patchlen:]
                        if len(view) >= len(pat) and all(
                                v is None or e is None or e == v
                                for v, e in zip(view, pat)):
                            matched = True
                            break
                elif all(e is None or e == v for v, e in zip(raw, pat)):
                    matched = True
                if matched:
                    break
            if not matched and patched:
                print(f"  0x{disk_va:X}: {bytes(raw[:32]).hex(' ')}")
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


if __name__ == "__main__":
    main()
