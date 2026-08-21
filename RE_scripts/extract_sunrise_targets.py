"""Extract the 16 resolved game-target VAs from Sunrise's in-process memory.

Sunrise resolved every anchor at DLL load and stores them as pointer arrays
in its .data. 8 values are known (from our pattern scan of the unpacked
image); locating them reveals the arrays, and the unknowns sit next to them.

Known (0x140000000-based, from the unpacked dump):
  content_config_fetch           0x1404C9E00
  content_manifest_gate          0x1404CA36A
  content_id_token_load          0x14005FD6F
  queuez_object_resolver         0x140E002D0
  queuez_family5_subscribe       0x140BE9370
  get_item_stat_value            0x140524720
  light_value_to_scalar          0x14054CC10
  retail_log_set_category_verbosity 0x14035DC80
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dump_sunrise_memory as dsm  # noqa: E402

IMAGE_BASE_DISK = 0x140000000

KNOWN = {
    "content_config_fetch": 0x1404C9E00,
    "content_manifest_gate": 0x1404CA36A,
    "content_id_token_load": 0x14005FD6F,
    "queuez_object_resolver": 0x140E002D0,
    "queuez_family5_subscribe": 0x140BE9370,
    "get_item_stat_value": 0x140524720,
    "light_value_to_scalar": 0x14054CC10,
    "retail_log_set_category_verbosity": 0x14035DC80,
}

EXPECTED = {  # names of the unknowns, per target group
    "network": ["transport_kind", "http_execute_request",
                "signon_readiness_failure", "signon_readiness_ready"],
    "content": ["content_config_tick", "bubble_authority_decoder",
                "content_untracked_getter"],
    "retail_log": ["retail_log_enqueue"],
}


def read_section_bytes(handle, mod_base: int, section_name: str) -> tuple[int, bytes]:
    headers = dsm.read_memory(handle, mod_base, 0x1000)
    _image_base, _entry, sections = dsm.parse_pe(headers)
    for name, vaddr, raw_ptr, raw_size, vsize in sections:
        if name == section_name:
            size = max(raw_size, min(vsize, 0x1000000))
            data = dsm.read_memory(handle, mod_base + vaddr, size)
            return mod_base + vaddr, data
    raise RuntimeError(f"section {section_name} not found")


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
            import time
            time.sleep(0.5)
        if not exe_base:
            print("FATAL: exe module not found")
            sys.exit(1)
        sunrise_base = dsm.find_module_base(pid, "steam_api64.dll")
        if not sunrise_base:
            print("FATAL: steam_api64.dll (Sunrise) module not found")
            sys.exit(1)
        print(f"exe base: 0x{exe_base:X}   sunrise base: 0x{sunrise_base:X}")

        exe_headers = dsm.read_memory(handle, exe_base, 0x1000)
        _ib, _e, exe_sections = dsm.parse_pe(exe_headers)
        exe_size = max(s[1] + max(s[3], s[4]) for s in exe_sections)
        exe_end = exe_base + exe_size
        print(f"exe image range: 0x{exe_base:X} .. 0x{exe_end:X}")

        def in_exe(val: int) -> bool:
            return exe_base <= val < exe_end

        # Collect game-range pointers from Sunrise .data + .rdata
        hits = {}
        for sect in (".data", ".rdata"):
            va_start, data = read_section_bytes(handle, sunrise_base, sect)
            if not data:
                continue
            for off in range(0, len(data) - 8, 8):
                val = int.from_bytes(data[off:off + 8], "little")
                if in_exe(val):
                    hits[va_start + off] = val
        print(f"game-range pointer slots in Sunrise: {len(hits)}")

        # Cluster consecutive slots
        addrs = sorted(hits)
        clusters = []
        run = [addrs[0]]
        for a in addrs[1:]:
            if a == run[-1] + 8:
                run.append(a)
            else:
                clusters.append(run)
                run = [a]
        clusters.append(run)
        clusters = [c for c in clusters if len(c) >= 2]
        print(f"pointer runs (>=2): {len(clusters)}")

        # Locate known values
        known_locs = {}
        for name, va in KNOWN.items():
            target = exe_base + (va - IMAGE_BASE_DISK)
            loc = next((a for a, v in hits.items() if v == target), None)
            known_locs[name] = loc
            print(f"  known {name:<34} {'FOUND' if loc else 'MISSING'}")

        # Assign clusters
        for cluster in clusters:
            known_here = [n for n, loc in known_locs.items() if loc in cluster]
            label = "?"
            if len(cluster) == 10 and len(known_here) >= 7:
                label = "content (10)"
            elif len(cluster) == 2 and known_here:
                label = "retail_log (2)"
            elif len(cluster) == 4 and not known_here:
                label = "network (4)"
            print(f"\ncluster @0x{cluster[0]:X} len={len(cluster)} known={known_here} -> {label}")
            for a in cluster:
                val = hits[a]
                va_disk = IMAGE_BASE_DISK + (val - exe_base)
                print(f"    0x{a:X} -> 0x{val:X}  (disk VA 0x{va_disk:X})")
    finally:
        import ctypes
        ctypes.windll.kernel32.CloseHandle(handle)


if __name__ == "__main__":
    main()
