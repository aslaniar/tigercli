# -*- coding: utf-8 -*-
"""The live registry dump (the ruling's #2): read the runtime definition-registry
cells + the wc controller (via the W3 getter-call fix) + the loop-table targets.

1. THE WC (the W3 fix): a remote thread runs the getter FUN_140e35820 (the
   null-safe no-arg decode of the ENCODED global) -> the exit code = the wc
   instance -> the B4 offsets (+0x200+id*8 = the state objects).
2. THE REGISTRY CELLS: 0x14322E530+/0x1432367B0+ = the boot registrar
   FUN_1418326a0's pointer cells (the runtime-filled entries the walker
   FUN_140372a60 resolves the 0x8080-tags against).
3. THE LOOP-TABLE TARGETS: 0x141A25B20-family relocated pointers (the runtime
   descriptor objects the big builder appends).

Run WHILE the game is at the character select or in orbit. READ-ONLY.
ASLR rule: the base resolves per boot (the MZ verify).
"""
import ctypes
import json
import struct
import sys

sys.path.insert(0, r"C:\Users\rasla\Downloads\destiny-preservation\RE_scripts")
from dump_sunrise_memory import find_pid, open_process, read_memory, find_module_base  # noqa: E402

GETTER_RVA = 0x140E35820 - 0x140000000  # 0xE35820
WC_GLOBAL_RVA = 0x14280E1F8 - 0x140000000
STATE_IDS = (0, 1, 7, 16, 21, 22, 23, 24, 27, 28, 29, 38)
CELL_BASES = (0x14322E530 - 0x140000000, 0x1432367B0 - 0x140000000)
CELL_COUNT = 16
LOOP_TABLE_RVA = 0x141F9D238 - 0x140000000
LOOP_ROWS = 10


def qword(h, addr):
    raw = read_memory(h, addr, 8)
    return struct.unpack_from("<Q", raw, 0)[0] if len(raw) == 8 else 0


def call_getter(pid, h, base):
    """Remote-thread call of FUN_140e35820 -> its return = the wc instance."""
    kernel32 = ctypes.windll.kernel32
    getter = base + GETTER_RVA
    # shellcode: mov rax, imm64; call rax; mov eax,0; ret (leave the return in rax
    # is unreliable for GetExitCodeThread on all builds - use the ret-value form).
    shell = (b"\x48\xB8" + struct.pack("<Q", getter) +
             b"\xFF\xD0" +          # call rax
             b"\x48\x89\xC3" +      # mov rbx, rax
             b"\x48\x83\xEC\x20" +  # shadow space (already used by the call)
             b"\x48\x89\xD8" +      # mov rax, rbx
             b"\xC3")               # ret
    addr = kernel32.VirtualAllocEx(h, 0, len(shell), 0x3000, 0x40)
    if not addr:
        return 0, "alloc failed"
    written = ctypes.c_size_t(0)
    kernel32.WriteProcessMemory(h, addr, shell, len(shell), ctypes.byref(written))
    tid = ctypes.c_ulong(0)
    th = kernel32.CreateRemoteThread(h, 0, 0, addr, 0, 0, ctypes.byref(tid))
    if not th:
        kernel32.VirtualFreeEx(h, addr, 0, 0x8000)
        return 0, "thread failed"
    kernel32.WaitForSingleObject(th, 10000)
    code = ctypes.c_ulong(0)
    kernel32.GetExitCodeThread(th, ctypes.byref(code))
    kernel32.CloseHandle(th)
    kernel32.VirtualFreeEx(h, addr, 0, 0x8000)
    return code.value, None


def main():
    pid = int(sys.argv[1]) if len(sys.argv) > 1 else find_pid("destiny2.exe")
    if pid is None:
        print("destiny2.exe not running")
        return 1
    print("target pid %d" % pid)
    h = open_process(pid)
    mb = find_module_base(pid, "destiny2.exe")
    mz = read_memory(h, mb, 2)
    assert mz == b"MZ"
    print("base 0x%016X (MZ verified)" % mb)

    out = {"base": mb}

    # 1. the wc via the getter
    wc, err = call_getter(pid, h, mb)
    print("getter -> wc = 0x%X%s" % (wc, (" (%s)" % err) if err else ""))
    states = {}
    if wc and not err:
        raw_global = qword(h, mb + WC_GLOBAL_RVA)
        out["wc_raw_global"] = raw_global
        print("  raw global = 0x%X" % raw_global)
        for sid in STATE_IDS:
            obj = qword(h, wc + 0x200 + sid * 8)
            vtable = qword(h, obj) if obj else 0
            states[sid] = {"obj": obj, "vtable": vtable}
            print("  state[%2d] obj=0x%X vtable=0x%X" % (sid, obj, vtable))
    out["wc"] = {"ptr": wc, "states": states, "err": err}

    # 2. the registry cells
    cells = {}
    for base_rva in CELL_BASES:
        vals = []
        for i in range(CELL_COUNT):
            vals.append(qword(h, mb + base_rva + i * 8))
        cells[hex(base_rva)] = vals
        print("cells @+0x%X: %s" % (base_rva,
              " ".join("0x%X" % v for v in vals[:8])))
    out["cells"] = cells

    # 3. the loop-table targets
    loop = []
    for i in range(LOOP_ROWS):
        row = mb + LOOP_TABLE_RVA + i * 32
        h1, h2, h3, cnt = struct.unpack_from("<IIII", read_memory(h, row, 16))
        ptr = qword(h, row + 16)
        loop.append({"row": i, "hashes": [h1, h2, h3], "count": cnt, "ptr": ptr})
        print("loop[%d] hashes=%08X %08X %08X cnt=%d ptr=0x%X"
              % (i, h1, h2, h3, cnt, ptr))
    out["loop_table"] = loop

    with open(r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\content"
              r"\live_read_registry.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote RE_output/content/live_read_registry.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
