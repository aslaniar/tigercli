"""Symbolize Sunrise far-stub targets using the local build's PDB via dbghelp.

Loads steam_api64.pdb, maps symbol names for the Detours replacement addresses
we captured live (read_stub_table far-stubs), and prints name + RVA.
Runtime base of the Sunrise DLL during our captures: 0x7FFA840C0000.
"""
import ctypes
import ctypes.wintypes as wt
import sys
from pathlib import Path

PDB = Path(r"C:\Users\rasla\Downloads\destiny-preservation\RE_build\Sunrise-021"
           r"\build\x64\Release\steam_api64.pdb")
SUNRISE_RUNTIME_BASE = 0x7FFA840C0000

# Far-stub replacement addresses captured from the live trampoline table
# (read_stub_table.py output, slot+0x58 far-stubs).
STUB_TARGETS = [
    0x7FF5F0490178, 0x7FF5F04901D8, 0x7FF5F0490238, 0x7FF5F0490298,
    0x7FF5F04902F8, 0x7FF5F0490358, 0x7FF5F04903B8, 0x7FF5F0490418,
    0x7FF5F0490598, 0x7FF5F04905F8, 0x7FF5F0490658,
]


class SYMBOL_INFOW(ctypes.Structure):
    _fields_ = [
        ("SizeOfStruct", wt.ULONG),
        ("TypeIndex", wt.ULONG),
        ("Reserved", ctypes.c_uint64 * 2),
        ("Index", wt.ULONG),
        ("Size", wt.ULONG),
        ("ModBase", ctypes.c_uint64),
        ("Flags", wt.ULONG),
        ("Value", ctypes.c_uint64),
        ("Address", ctypes.c_uint64),
        ("Register", wt.ULONG),
        ("Scope", wt.ULONG),
        ("Tag", wt.ULONG),
        ("NameLen", wt.ULONG),
        ("MaxNameLen", wt.ULONG),
        ("Name", ctypes.c_wchar * 256),
    ]


def main() -> None:
    if not PDB.exists():
        print(f"FATAL: no PDB at {PDB}")
        sys.exit(1)
    dbghelp = ctypes.WinDLL("dbghelp")
    process = ctypes.c_void_p(-1)  # pseudo-handle

    dbghelp.SymSetOptions(0x00000010)  # SYMOPT_UNDNAME
    if not dbghelp.SymInitializeW(process, None, False):
        print(f"SymInitialize failed: {ctypes.GetLastError()}")
        sys.exit(1)
    base = 0x10000000
    if not dbghelp.SymLoadModuleExW(process, None, str(PDB), None, base, 0, None, 0):
        print(f"SymLoadModuleEx failed: {ctypes.GetLastError()}")
        sys.exit(1)

    sym = SYMBOL_INFOW()
    sym.SizeOfStruct = 88
    sym.MaxNameLen = 256
    disproff = ctypes.c_uint64(0)

    # Sunrise RVA of a replacement = target - SUNRISE_RUNTIME_BASE
    for t in STUB_TARGETS:
        rva = t - SUNRISE_RUNTIME_BASE
        if rva < 0 or rva > 0x2000000:
            print(f"0x{t:X} -> outside sunrise dll (rva 0x{rva:X})")
            continue
        addr = base + rva
        ok = dbghelp.SymFromAddrW(process, ctypes.c_uint64(addr),
                                  ctypes.byref(disproff), ctypes.byref(sym))
        if ok:
            print(f"stub 0x{t:X} -> sunrise+0x{rva:X} = {sym.Name} +0x{disproff.value:X}")
        else:
            print(f"stub 0x{t:X} -> sunrise+0x{rva:X} = <no symbol>")
    dbghelp.SymCleanup(process)


if __name__ == "__main__":
    main()
