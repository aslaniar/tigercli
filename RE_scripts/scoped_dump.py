#!/usr/bin/env python3
"""scoped_dump.py - RIG-SIDE (Windows) scoped memory dumper: a real minidump
containing ONLY the regions that matter, readable by minidump_reader.py /
dump_search.py / femu --graft-dump like any full dump.

Generalizes full_dump.py (same dbghelp MiniDumpWriteDump call) with the
documented MemoryCallback include-list (MiniDumpCallbackType::MemoryCallback,
value 5 - MS docs: "returns a region of memory to be included in the dump;
called only for dumps generated WITHOUT MiniDumpWithFullMemory"; supply
MemoryBase/MemorySize in the output union, return FALSE when exhausted).

Usage:
  python scoped_dump.py <out.dmp> <pid> [base size]...      (hex, as many
  base/size SPANS as wanted; each span is expanded to ALLOCATION granularity -
  the whole heap allocation of every committed region it intersects - so the
  arena around a target comes along, not just the target bytes)

Auto-included besides the spans:
  - every thread's stack (MiniDumpNormal default)
  - the main module's .data section (live globals; found by parsing the PE
    header of the first executable module in memory)

ALWAYS verify the result with minidump_reader.py + an oracle before treating
it as evidence. A scoped dump that fails its oracle is storage debt.
"""
import ctypes, ctypes.wintypes as wt, struct, sys, os

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
MemoryCallbackType = 5  # MINIDUMP_CALLBACK_TYPE (msdocs, verified 2026-08-31)

MiniDumpWithHandleData = 0x00000004
MiniDumpWithUnloadedModules = 0x00000020
MiniDumpWithFullMemoryInfo = 0x00000800
MiniDumpWithThreadInfo = 0x00001000
FLAGS = (MiniDumpWithHandleData | MiniDumpWithUnloadedModules |
         MiniDumpWithFullMemoryInfo | MiniDumpWithThreadInfo)  # stacks included by default

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
dbghelp = ctypes.WinDLL(r"C:\Users\rasla\Downloads\destiny-preservation\dcv build\dbghelp.dll",
                        use_last_error=True)


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_uint64),
                ("AllocationBase", ctypes.c_uint64),
                ("AllocationProtect", wt.DWORD),
                ("__align1", wt.DWORD),
                ("RegionSize", ctypes.c_uint64),
                ("State", wt.DWORD),
                ("Protect", wt.DWORD),
                ("Type", wt.DWORD),
                ("__align2", wt.DWORD)]

# explicit signatures - default c_int restype TRUNCATES 64-bit handles and
# silently broke VirtualQueryEx during the notepad test (0 regions found)
kernel32.OpenProcess.restype = wt.HANDLE
kernel32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
kernel32.VirtualQueryEx.restype = ctypes.c_size_t
kernel32.VirtualQueryEx.argtypes = [wt.HANDLE, wt.LPCVOID,
                                    ctypes.POINTER(MEMORY_BASIC_INFORMATION),
                                    ctypes.c_size_t]
kernel32.CreateFileW.restype = wt.HANDLE
kernel32.CreateFileW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD, wt.LPVOID,
                                 wt.DWORD, wt.DWORD, wt.HANDLE]
kernel32.ReadProcessMemory.restype = wt.BOOL
kernel32.ReadProcessMemory.argtypes = [wt.HANDLE, wt.LPCVOID, wt.LPVOID,
                                       ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
kernel32.CloseHandle.restype = wt.BOOL
kernel32.CloseHandle.argtypes = [wt.HANDLE]


class _MEMOUT(ctypes.Structure):
    _fields_ = [("MemoryBase", ctypes.c_uint64), ("MemorySize", ctypes.c_uint32)]


class MINIDUMP_CALLBACK_OUTPUT(ctypes.Union):
    # The real union contains MINIDUMP_MEMORY_INFO VmRegion (~56 B) and more;
    # undersizing it lets dbghelp write past the allocation (the AV caught in
    # the notepad test). Force a safe size with raw padding.
    _fields_ = [("ModuleWriteFlags", wt.DWORD), ("Memory", _MEMOUT),
                ("Status", ctypes.c_long), ("_raw", ctypes.c_byte * 256)]


class MINIDUMP_CALLBACK_INPUT(ctypes.Structure):
    # header is 24 bytes on x64 (ULONG, pad, HANDLE, ULONG, pad); the union
    # after it is sized by dbghelp - give it room via raw bytes (we only read
    # CallbackType, at offset 16).
    _fields_ = [("ProcessId", wt.ULONG), ("ProcessHandle", wt.HANDLE),
                ("CallbackType", wt.ULONG), ("_raw", ctypes.c_byte * 256)]


CALLBACK = ctypes.WINFUNCTYPE(wt.BOOL, wt.LPVOID,
                              ctypes.POINTER(MINIDUMP_CALLBACK_INPUT),
                              ctypes.POINTER(MINIDUMP_CALLBACK_OUTPUT))


class MINIDUMP_CALLBACK_INFORMATION(ctypes.Structure):
    # MiniDumpWriteDump's 7th arg is a POINTER to this, not the routine itself.
    _fields_ = [("CallbackRoutine", CALLBACK), ("CallbackParam", wt.LPVOID)]


def allocation_blocks(hproc, spans):
    """Expand each span to the set of whole ALLOCATIONS it intersects."""
    blocks, seen = [], set()
    dbg = os.environ.get("SCOPED_DEBUG")
    for lo, hi in spans:
        if dbg:
            print(f"span 0x{lo:x}..0x{hi:x}")
        addr = lo & ~0xFFFF
        while addr < hi:
            mbi = MEMORY_BASIC_INFORMATION()
            got = kernel32.VirtualQueryEx(hproc, ctypes.c_void_p(addr),
                                          ctypes.byref(mbi), ctypes.sizeof(mbi))
            if dbg:
                print(f"  VQE(0x{addr:x}) -> got={got} err={ctypes.get_last_error()} "
                      f"base=0x{mbi.BaseAddress:x} abase=0x{mbi.AllocationBase:x} "
                      f"size=0x{mbi.RegionSize:x} state=0x{mbi.State:x}")
            if not got:
                break
            base = mbi.AllocationBase or mbi.BaseAddress
            if mbi.State == MEM_COMMIT and base and base not in seen:
                # walk the whole allocation
                abase, aend, cur = base, base, base
                while True:
                    m = MEMORY_BASIC_INFORMATION()
                    if not kernel32.VirtualQueryEx(hproc, ctypes.c_void_p(cur),
                                                   ctypes.byref(m), ctypes.sizeof(m)):
                        break
                    if m.AllocationBase != base or m.State != MEM_COMMIT:
                        break
                    aend = m.BaseAddress + m.RegionSize
                    cur = aend
                    if aend - abase > (64 << 20):  # 64 MB per-allocation cap
                        break
                if aend > abase:
                    blocks.append((abase, aend - abase))
                    seen.add(base)
            addr = mbi.BaseAddress + mbi.RegionSize
    blocks.sort()
    return blocks


def find_module_data(hproc, pid):
    """The main module's .data section range, parsed from the in-memory PE."""
    CREATE_TOOLHELP_SNAPSHOT = 0x8
    TH32CS_SNAPMODULE = 0x8

    class MODULEENTRY32W(ctypes.Structure):
        _fields_ = [("dwSize", wt.DWORD), ("th32ModuleID", wt.DWORD),
                    ("th32ProcessID", wt.DWORD), ("GlblcntUsage", wt.DWORD),
                    ("ProccntUsage", wt.DWORD), ("modBaseAddr", ctypes.c_uint64),
                    ("modBaseSize", wt.DWORD), ("hModule", wt.HMODULE),
                    ("szModule", wt.WCHAR * 256), ("szExePath", wt.WCHAR * 260)]

    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, pid)
    if snap == -1 or snap == 0xFFFFFFFFFFFFFFFF:
        return None
    me = MODULEENTRY32W()
    me.dwSize = ctypes.sizeof(me)
    ok = kernel32.Module32FirstW(snap, ctypes.byref(me))
    result = None
    while ok:
        if me.szModule.lower().startswith("destiny2"):
            buf = (ctypes.c_char * 0x400)()
            n = ctypes.c_size_t(0)
            if kernel32.ReadProcessMemory(hproc, ctypes.c_void_p(me.modBaseAddr),
                                          buf, 0x400, ctypes.byref(n)):
                hdr = bytes(buf)
                e_lfanew = struct.unpack_from("<I", hdr, 0x3C)[0]
                numsec = struct.unpack_from("<H", hdr, e_lfanew + 6)[0]
                opt_size = struct.unpack_from("<H", hdr, e_lfanew + 20)[0]
                sec0 = e_lfanew + 24 + opt_size
                for i in range(numsec):
                    o = sec0 + i * 40
                    name = hdr[o:o + 8].rstrip(b"\0")
                    vsize, vaddr = struct.unpack_from("<II", hdr, o + 8)
                    if name == b".data":
                        result = (me.modBaseAddr + vaddr, max(vsize, 0x1000))
                        break
            break
        ok = kernel32.Module32NextW(snap, ctypes.byref(me))
    kernel32.CloseHandle(snap)
    return result


def main():
    out, pid = sys.argv[1], int(sys.argv[2])
    spans = [(int(sys.argv[i], 16), int(sys.argv[i + 1], 16))
             for i in range(3, len(sys.argv) - 1, 2)]
    h = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        raise OSError(ctypes.get_last_error(), "OpenProcess failed")

    extra = []
    md = find_module_data(h, pid)
    if md:
        extra.append(md)
    blocks = allocation_blocks(h, spans + extra)
    total = sum(sz for _, sz in blocks)
    print(f"include regions: {len(blocks)} blocks, {total / 1e6:.1f} MB "
          f"(spans={len(spans)}, module .data={'yes' if md else 'no'})")
    for b, s in blocks[:12]:
        print(f"   0x{b:x} +0x{s:x}")
    if len(blocks) > 12:
        print(f"   ... +{len(blocks) - 12} more")

    state = {"i": 0, "blocks": blocks}

    @CALLBACK
    def cb(_param, cin, cout):
        if not cin or not cout:
            return 0
        if cin.contents.CallbackType == MemoryCallbackType:
            i = state["i"]
            if i >= len(state["blocks"]):
                return 0
            base, size = state["blocks"][i]
            cout.contents.Memory.MemoryBase = base
            cout.contents.Memory.MemorySize = size
            state["i"] = i + 1
            return 1
        return 1

    f = kernel32.CreateFileW(out, 0x40000000, 0, None, 2, 0x80, None)
    if f == -1 or f == 0xFFFFFFFFFFFFFFFF:
        raise OSError(ctypes.get_last_error(), "CreateFile failed")
    cb_info = MINIDUMP_CALLBACK_INFORMATION()
    cb_info.CallbackRoutine = cb
    cb_info.CallbackParam = None
    ok = dbghelp.MiniDumpWriteDump(h, pid, f, FLAGS, None, None,
                                   ctypes.byref(cb_info))
    if not ok:
        print("MiniDumpWriteDump FAILED:", ctypes.get_last_error())
        sys.exit(1)
    kernel32.CloseHandle(f)
    print("dumped ->", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
