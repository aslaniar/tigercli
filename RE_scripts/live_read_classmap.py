# -*- coding: utf-8 -*-
"""Inventory live-read: the 71-class decoder table + the CUI equip-component globals.

The L1 lane's OPEN items that need a live session (runtime-relocated pointers):
1. DAT_141fbef60 (RVA 0x1FBEF60) = the static 71-entry class table the populator
   FUN_140e75790 walks. Each entry = a vtable-ish object pointer; method 0 = the 5-byte
   "mov eax,<type>; ret" getter naming the BAP message type. This names the svc-10/11
   decoder class (the web-service envelope + status-pair decoder) for the Ghidra pass.
2. The CUI equip-component globals (DAT_143049320 / 143043790 / 142021A30 / 143048EE0,
   RVAs 0x3049320 / 0x3043790 / 0x2021A30 / 0x3048EE0) = runtime-initialized vtable holders
   for cui::c_investment_equip_inventory_item_component — the press-and-hold handler's class.
Run WHILE the game is at the character select or in orbit (the registry = populated after
the BAP signin). READ-ONLY on the game process. Output = the console + the json dump.
ASLR rule: the base resolves per boot via find_module_base + the MZ verify.
"""
import json
import struct
import sys

sys.path.insert(0, r"C:\Users\rasla\Downloads\destiny-preservation\RE_scripts")
from dump_sunrise_memory import find_pid, open_process, read_memory, find_module_base  # noqa: E402

CLASS_TABLE_RVA = 0x1FBEF60
CLASS_TABLE_ENTRIES = 71
CUI_GLOBALS = {"equip_g1": 0x3049320, "equip_g2": 0x3043790,
               "equip_g3": 0x2021A30, "equip_g4": 0x3048EE0}


def u32(blob, off):
    return struct.unpack_from("<I", blob, off)[0]


def main():
    pid = find_pid("destiny2.exe")
    if pid is None:
        print("destiny2.exe not running")
        return 1
    h = open_process(pid)
    mb = find_module_base(pid, "destiny2.exe")
    if mb is None:
        print("module base not found")
        return 1
    mz = read_memory(h, mb, 2)
    assert mz == b"MZ", f"MZ verify failed at 0x{mb:X} (got {mz!r})"
    print(f"base 0x{mb:016X} (MZ verified)")

    # --- 1. the 71-entry class table ---
    table_bytes = read_memory(h, mb + CLASS_TABLE_RVA, CLASS_TABLE_ENTRIES * 8)
    pointers = struct.unpack_from(f"<{CLASS_TABLE_ENTRIES}Q", table_bytes, 0)
    type_map = {}
    print(f"class table @ 0x{mb + CLASS_TABLE_RVA:X}:")
    for i, ptr in enumerate(pointers):
        if ptr == 0:
            print(f"  [{i:2d}] NULL")
            continue
        vtable = read_memory(h, ptr, 8)
        vtable_ptr = struct.unpack_from("<Q", vtable, 0)[0]
        getter = read_memory(h, vtable_ptr, 8) if vtable_ptr else b""
        # the "mov eax,<imm>; ret" shape: B8 imm32 C3
        type_id = None
        if len(getter) >= 6 and getter[0] == 0xB8 and getter[5] == 0xC3:
            type_id = u32(getter, 1)
        type_map[i] = {"obj": ptr, "vtable": vtable_ptr, "type": type_id,
                       "getter": getter.hex(" ")}
        print(f"  [{i:2d}] obj=0x{ptr:X} vtable=0x{vtable_ptr:X} "
              f"type={type_id if type_id is not None else '?(' + getter.hex(' ') + ')'}")

    # --- 2. the CUI equip-component globals ---
    print("CUI equip-component globals:")
    cui = {}
    for name, rva in CUI_GLOBALS.items():
        raw = read_memory(h, mb + rva, 8)
        value = struct.unpack_from("<Q", raw, 0)[0]
        cui[name] = {"rva": hex(rva), "value": value}
        print(f"  {name} @ +0x{rva:X}: 0x{value:X}")

    out = {"base": mb, "class_table": type_map, "cui_globals": cui}
    with open(r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\content"
              r"\live_read_classmap.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote RE_output/content/live_read_classmap.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
