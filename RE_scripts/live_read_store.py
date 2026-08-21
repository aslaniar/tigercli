# -*- coding: utf-8 -*-
"""Live store-record dump: the remote-thread getter calls (the extended-rights
handle) for the wc (FUN_140e35820) + the runtime store (FUN_140e74c20), then
the family-4 store's record blocks + the character record's +0x2F00 region."""
import ctypes
import json
import struct
import sys

sys.path.insert(0, r"C:\Users\rasla\Downloads\destiny-preservation\RE_scripts")
from dump_sunrise_memory import find_pid, find_module_base, read_memory  # noqa: E402

PROCESS_CREATE_THREAD = 0x0002
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
RIGHTS = (PROCESS_CREATE_THREAD | PROCESS_VM_OPERATION | PROCESS_VM_WRITE
          | PROCESS_VM_READ | PROCESS_QUERY_INFORMATION)

WC_GETTER_RVA = 0x140E35820 - 0x140000000
STORE_GETTER_RVA = 0x140E74C20 - 0x140000000

kernel32 = ctypes.windll.kernel32


def open_full(pid):
    kernel32.OpenProcess.restype = ctypes.c_void_p
    return kernel32.OpenProcess(RIGHTS, False, pid)


def q(h, addr):
    raw = read_memory(h, addr, 8)
    return struct.unpack_from("<Q", raw, 0)[0] if len(raw) == 8 else 0


def call_getter(h, base, rva):
    getter = base + rva
    shell = (b"\x48\xB8" + struct.pack("<Q", getter) + b"\xFF\xD0" + b"\xC3")
    addr = kernel32.VirtualAllocEx(h, 0, len(shell), 0x3000, 0x40)
    if not addr:
        return 0, "alloc failed (%d)" % ctypes.get_last_error()
    written = ctypes.c_size_t(0)
    ok = kernel32.WriteProcessMemory(h, addr, shell, len(shell), ctypes.byref(written))
    if not ok:
        kernel32.VirtualFreeEx(h, addr, 0, 0x8000)
        return 0, "write failed"
    tid = ctypes.c_ulong(0)
    th = kernel32.CreateRemoteThread(h, 0, 0, addr, 0, 0, ctypes.byref(tid))
    if not th:
        kernel32.VirtualFreeEx(h, addr, 0, 0x8000)
        return 0, "thread failed (%d)" % ctypes.get_last_error()
    kernel32.WaitForSingleObject(th, 10000)
    code = ctypes.c_ulong(0)
    kernel32.GetExitCodeThread(th, ctypes.byref(code))
    kernel32.CloseHandle(th)
    kernel32.VirtualFreeEx(h, addr, 0, 0x8000)
    return code.value, None


def main():
    pid = int(sys.argv[1]) if len(sys.argv) > 1 else find_pid("destiny2.exe")
    print("target pid %d" % pid)
    h = open_full(pid)
    if not h:
        print("open failed")
        return 1
    mb = find_module_base(pid, "destiny2.exe")
    print("base 0x%016X" % mb)

    out = {"base": mb}

    wc, err = call_getter(h, mb, WC_GETTER_RVA)
    print("wc getter -> 0x%X%s" % (wc, (" (%s)" % err) if err else ""))
    out["wc"] = wc

    store, err2 = call_getter(h, mb, STORE_GETTER_RVA)
    print("store getter -> 0x%X%s" % (store, (" (%s)" % err2) if err2 else ""))
    out["store"] = store

    if store and not err2 and 0x10000 < store < 0x800000000000:
        for k in range(8):
            blk = store + k * 0x81E8
            print("  blk[%d] @0x%X head=0x%X" % (k, blk, q(h, blk)))
            # the character-record +0x2F00 region (the record = the block head?)
            head = q(h, blk)
            if head and 0x10000 < head < 0x800000000000:
                region = head + 0x2F00
                raw = read_memory(h, region, 32)
                u32s = struct.unpack_from("<8I", raw) if len(raw) == 32 else ()
                print("    rec+0x2F00: %s" % " ".join("%08X" % v for v in u32s))

    with open(r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\content"
              r"\live_read_store.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote RE_output/content/live_read_store.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
