# -*- coding: utf-8 -*-
"""Phase-1 boot rider (passive RPM, no DLL changes): the live reads the campaign's
OPEN items asked for, on top of the live_read_classmap.py recipes.

1. THE BOOTFLOW CONTROLLER (boot-b OPEN 1): *0x14280E1F8 = the wc instance ->
   wc+0x200+id*8 = the state-object pointer array -> each object's qword[0] = its
   vtable (the per-state handlers, runtime-established).
2. THE CUI EQUIP GLOBALS (cuia OPEN 1 / L1): the 4 component globals.
3. THE TICK-2 STATIC VTABLE CANDIDATE (cuia OPEN 1): DAT_141c25cd8 = the manager's
   stack-struct vtable candidate.

Run WHILE the game is at the character select or in orbit (post-BAP-signin).
READ-ONLY on the game process. ASLR rule: the base resolves per boot (the MZ verify).
"""
import json
import struct
import sys

sys.path.insert(0, r"C:\Users\rasla\Downloads\destiny-preservation\RE_scripts")
from dump_sunrise_memory import find_pid, open_process, read_memory, find_module_base  # noqa: E402

WC_GLOBAL_RVA = 0x14280E1F8 - 0x140000000  # 0x280E1F8
STATE_IDS = (0, 1, 7, 16, 21, 22, 23, 24, 27, 28, 29, 38)
CUI_GLOBALS = {"equip_g1": 0x3049320, "equip_g2": 0x3043790,
               "equip_g3": 0x2021A30, "equip_g4": 0x3048EE0}
TICK2_VTABLE_RVA = 0x141C25CD8 - 0x140000000  # 0x1C25CD8


def qword(h, addr):
    raw = read_memory(h, addr, 8)
    return struct.unpack_from("<Q", raw, 0)[0] if len(raw) == 8 else 0


def main():
    pid = int(sys.argv[1]) if len(sys.argv) > 1 else find_pid("destiny2.exe")
    if pid is None:
        print("destiny2.exe not running")
        return 1
    print(f"target pid {pid}")
    h = open_process(pid)
    mb = find_module_base(pid, "destiny2.exe")
    if mb is None:
        print("module base not found")
        return 1
    mz = read_memory(h, mb, 2)
    assert mz == b"MZ", f"MZ verify failed at 0x{mb:X}"
    print(f"base 0x{mb:016X} (MZ verified)")

    out = {"base": mb}

    # 1. the bootflow controller
    wc = qword(h, mb + WC_GLOBAL_RVA)
    print(f"wc instance = *0x{mb + WC_GLOBAL_RVA:X} -> 0x{wc:X}")
    states = {}
    if wc:
        for sid in STATE_IDS:
            obj = qword(h, wc + 0x200 + sid * 8)
            vtable = qword(h, obj) if obj else 0
            states[sid] = {"obj": obj, "vtable": vtable}
            print(f"  state[{sid:2d}] obj=0x{obj:X} vtable=0x{vtable:X}")
    out["wc"] = {"ptr": wc, "states": states}

    # 2. the CUI equip globals
    cui = {}
    for name, rva in CUI_GLOBALS.items():
        v = qword(h, mb + rva)
        cui[name] = v
        print(f"  {name} @ +0x{rva:X}: 0x{v:X}")
    out["cui_globals"] = cui

    # 3. the tick-2 vtable candidate
    t2 = qword(h, mb + TICK2_VTABLE_RVA)
    print(f"  tick2 vtable candidate @ +0x{TICK2_VTABLE_RVA:X}: 0x{t2:X}")
    out["tick2_vtable_candidate"] = t2

    with open(r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\content"
              r"\live_read_phase1.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote RE_output/content/live_read_phase1.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
