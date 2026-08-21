"""Dump the decrypted in-memory image of the running destiny2.exe.

Reads each PE section from the live process (ReadProcessMemory), rebuilds
a valid PE file with decrypted section content (headers from the on-disk
file, bytes from memory), and prints a memory-usage summary first.

Output: RE_output/destiny2_unpacked.exe  (import this into Ghidra)
"""
import ctypes
import ctypes.wintypes as wt
import struct
import sys
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent / "RE_output"
ON_DISK_EXE = Path(__file__).parent.parent / "dcv build" / "destiny2.exe"

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
TH32CS_SNAPPROCESS = 0x2
MEM_COMMIT = 0x1000
MEM_IMAGE = 0x1000000
MEM_MAPPED = 0x40000
MEM_PRIVATE = 0x20000

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_size_t),
        ("AllocationBase", ctypes.c_size_t),
        ("AllocationProtect", wt.DWORD),
        ("_pad1", wt.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wt.DWORD),
        ("Protect", wt.DWORD),
        ("Type", wt.DWORD),
        ("_pad2", wt.DWORD),
    ]


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD),
        ("cntUsage", wt.DWORD),
        ("th32ProcessID", wt.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wt.DWORD),
        ("cntThreads", wt.DWORD),
        ("th32ParentProcessID", wt.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wt.DWORD),
        ("szExeFile", ctypes.c_wchar * 260),
    ]


class MODULEENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD),
        ("th32ModuleID", wt.DWORD),
        ("th32ProcessID", wt.DWORD),
        ("GlblcntUsage", wt.DWORD),
        ("ProccntUsage", wt.DWORD),
        ("modBaseAddr", ctypes.c_size_t),
        ("modBaseSize", wt.DWORD),
        ("hModule", ctypes.c_void_p),
        ("szModule", ctypes.c_wchar * 256),
        ("szExePath", ctypes.c_wchar * 260),
    ]


def find_pid(name: str) -> int:
    """Return the pid of the LIVE process with this name (skip zombies: a crashed
    leftover can still appear in the snapshot with no accessible path)."""
    kernel32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    kernel32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
    kernel32.Process32FirstW.argtypes = [ctypes.c_void_p, ctypes.POINTER(PROCESSENTRY32W)]
    kernel32.Process32NextW.argtypes = [ctypes.c_void_p, ctypes.POINTER(PROCESSENTRY32W)]
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == ctypes.c_void_p(-1).value:
        raise OSError(ctypes.get_last_error(), "CreateToolhelp32Snapshot failed")
    entry = PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
    candidates = []
    try:
        if not kernel32.Process32FirstW(snap, ctypes.byref(entry)):
            raise OSError(ctypes.get_last_error(), "Process32FirstW failed")
        while True:
            if entry.szExeFile.lower() == name.lower():
                candidates.append(int(entry.th32ProcessID))
            if not kernel32.Process32NextW(snap, ctypes.byref(entry)):
                break
        # prefer a pid we can actually open
        for pid in candidates:
            kernel32.OpenProcess.restype = ctypes.c_void_p
            h = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
            if h:
                kernel32.CloseHandle(h)
                return pid
        return candidates[0] if candidates else 0
    finally:
        kernel32.CloseHandle(snap)


def find_module_base(pid: int, name: str) -> int:
    kernel32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    kernel32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
    kernel32.Module32FirstW.argtypes = [ctypes.c_void_p, ctypes.POINTER(MODULEENTRY32W)]
    kernel32.Module32NextW.argtypes = [ctypes.c_void_p, ctypes.POINTER(MODULEENTRY32W)]
    snap = kernel32.CreateToolhelp32Snapshot(0x8 | 0x10, pid)  # SNAPMODULE | SNAPMODULE32
    if snap == ctypes.c_void_p(-1).value:
        raise OSError(ctypes.get_last_error(), "CreateToolhelp32Snapshot(modules) failed")
    entry = MODULEENTRY32W()
    entry.dwSize = ctypes.sizeof(MODULEENTRY32W)
    try:
        if not kernel32.Module32FirstW(snap, ctypes.byref(entry)):
            raise OSError(ctypes.get_last_error(), "Module32FirstW failed")
        while True:
            if entry.szModule.lower() == name.lower():
                return int(entry.modBaseAddr)
            if not kernel32.Module32NextW(snap, ctypes.byref(entry)):
                return 0
    finally:
        kernel32.CloseHandle(snap)


def open_process(pid: int):
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not handle:
        raise OSError(ctypes.get_last_error(), f"OpenProcess({pid}) failed")
    return handle


def read_memory(handle, address: int, size: int) -> bytes:
    buffer = ctypes.create_string_buffer(size)
    bytes_read = ctypes.c_size_t(0)
    kernel32.ReadProcessMemory.restype = wt.BOOL
    kernel32.ReadProcessMemory.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    if not kernel32.ReadProcessMemory(handle, ctypes.c_void_p(address), buffer, size,
                                      ctypes.byref(bytes_read)):
        raise OSError(ctypes.get_last_error(), f"ReadProcessMemory failed @0x{address:X}")
    return buffer.raw[:bytes_read.value]


def enumerate_regions(handle):
    kernel32.VirtualQueryEx.restype = ctypes.c_size_t
    kernel32.VirtualQueryEx.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(MEMORY_BASIC_INFORMATION),
        ctypes.c_size_t,
    ]
    regions = []
    address = 0
    mbi = MEMORY_BASIC_INFORMATION()
    while True:
        n = kernel32.VirtualQueryEx(handle, ctypes.c_void_p(address),
                                    ctypes.byref(mbi), ctypes.sizeof(mbi))
        if n == 0:
            break
        regions.append((mbi.BaseAddress, mbi.RegionSize, mbi.State, mbi.Type,
                        mbi.Protect))
        address = mbi.BaseAddress + mbi.RegionSize
    return regions


def parse_pe(data: bytes):
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    n_sections = struct.unpack_from("<H", data, e_lfanew + 6)[0]
    opt_size = struct.unpack_from("<H", data, e_lfanew + 20)[0]
    magic = struct.unpack_from("<H", data, e_lfanew + 24)[0]
    entry_rva = struct.unpack_from("<I", data, e_lfanew + 24 + 16)[0]
    image_base = struct.unpack_from("<Q", data, e_lfanew + 24 + (24 if magic == 0x20B else 28))[0]
    section_off = e_lfanew + 24 + opt_size
    sections = []
    for i in range(n_sections):
        off = section_off + i * 40
        name = data[off:off + 8].rstrip(b"\0").decode(errors="replace")
        vsize, vaddr, raw_size, raw_ptr = struct.unpack_from("<IIII", data, off + 8)
        sections.append((name, vaddr, raw_ptr, raw_size, vsize))
    return image_base, entry_rva, sections


def entropy(chunk: bytes) -> float:
    import math
    if not chunk:
        return 0.0
    counts = [0] * 256
    for b in chunk:
        counts[b] += 1
    n = len(chunk)
    return -sum(c / n * math.log2(c / n) for c in counts if c)


def main() -> None:
    pid = find_pid("destiny2.exe")
    if not pid:
        print("FATAL: destiny2.exe process not found — is the game running?")
        sys.exit(1)
    print(f"found destiny2.exe pid={pid}")

    handle = open_process(pid)
    try:
        regions = enumerate_regions(handle)
        total = {MEM_IMAGE: 0, MEM_PRIVATE: 0, MEM_MAPPED: 0}
        for _base, size, state, rtype, _prot in regions:
            if state == MEM_COMMIT:
                total[rtype] = total.get(rtype, 0) + size
        committed = sum(total.values())
        print(f"\ncommitted memory summary (before writing anything):")
        print(f"  MEM_IMAGE   {total[MEM_IMAGE]/2**30:7.2f} GiB  (modules)")
        print(f"  MEM_PRIVATE {total[MEM_PRIVATE]/2**30:7.2f} GiB  (heaps/stacks)")
        print(f"  MEM_MAPPED  {total[MEM_MAPPED]/2**30:7.2f} GiB  (file mappings)")
        print(f"  TOTAL       {committed/2**30:7.2f} GiB  ({len(regions)} regions)")

        exe_base = find_module_base(pid, "destiny2.exe")
        if not exe_base:
            print("FATAL: destiny2.exe module not found in process")
            sys.exit(1)
        try:
            head = read_memory(handle, exe_base, 0x1000)
        except OSError:
            print("FATAL: cannot read module headers")
            sys.exit(1)
        if not (head[:2] == b"MZ" and head[struct.unpack_from("<I", head, 0x3C)[0]:
                                        struct.unpack_from("<I", head, 0x3C)[0] + 4] == b"PE\0\0"):
            print(f"FATAL: bad headers at module base 0x{exe_base:X}")
            sys.exit(1)
        print(f"\nmain image base: 0x{exe_base:X}")

        headers = read_memory(handle, exe_base, 0x1000)
        image_base, entry_rva, sections = parse_pe(headers)
        print(f"PE: image_base=0x{image_base:X} entry=0x{exe_base + entry_rva:X} "
              f"sections={len(sections)}")

        section_bytes = []
        for name, vaddr, raw_ptr, raw_size, vsize in sections:
            if raw_size == 0:
                section_bytes.append(b"")
                continue
            size = max(raw_size, min(vsize, 0x1000000))
            data = read_memory(handle, exe_base + vaddr, size)
            data = data[:raw_size] if len(data) >= raw_size else data
            e = entropy(data[:raw_size])
            print(f"  read {name:<10} rva=0x{vaddr:08X} {len(data):>10,} bytes "
                  f"entropy={e:.2f} {'<-- DECRYPTED' if e < 7.2 else '<-- still packed?'}")
            section_bytes.append(data)

        on_disk = ON_DISK_EXE.read_bytes()
        rebuilt = bytearray(on_disk)
        for (name, vaddr, raw_ptr, raw_size, vsize), data in zip(sections, section_bytes):
            if raw_size and len(data) >= raw_size:
                rebuilt[raw_ptr:raw_ptr + raw_size] = data[:raw_size]
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUT_DIR / "destiny2_unpacked.exe"
        out_path.write_bytes(bytes(rebuilt))
        print(f"\nwrote unpacked image: {out_path}  ({len(rebuilt):,} bytes)")
    finally:
        kernel32.CloseHandle(handle)


if __name__ == "__main__":
    main()
