#!/usr/bin/env python3
# REGISTRY: caps: minidump-parse
"""Parse a Windows minidump enough to name the faulting module.
Usage: python3 minidump_parse.py <dump>"""
import struct, sys

def u16(b, o): return struct.unpack_from("<H", b, o)[0]
def u32(b, o): return struct.unpack_from("<I", b, o)[0]
def u64(b, o): return struct.unpack_from("<Q", b, o)[0]

def parse(path):
    d = open(path, "rb").read()
    assert d[:4] == b"MDMP", "not a minidump"
    streams = u32(d, 8)
    dir_off = u32(d, 12)
    modules, exc = [], None
    for i in range(streams):
        stype, size, rva = struct.unpack_from("<III", d, dir_off + i * 12)
        if stype == 4:  # ModuleList
            count = u32(d, rva)
            for m in range(count):
                ent = rva + 8 + m * 108
                base = u64(d, ent)
                name_rva = u32(d, ent + 8 + 16)
                nlen = u32(d, name_rva)
                name = d[name_rva + 4:name_rva + 4 + nlen].decode("utf-16-le", "replace")
                modules.append((base, name))
        elif stype == 6:  # Exception
            # MINIDUMP_EXCEPTION_STREAM: tid u32, alignment 4, EXCEPTION_RECORD (152 bytes),
            # context RVA u32
            er = rva + 8
            code = u32(d, er)
            addr = u64(d, er + 16)
            param0 = u64(d, er + 24)
            exc = (code, addr, param0)
    print(f"== {path}")
    if not exc:
        print("  no exception stream")
        return
    code, addr, p0 = exc
    code_map = {0xC0000005: "ACCESS_VIOLATION", 0x80000003: "BREAKPOINT",
                0xC000001D: "ILLEGAL_INSTRUCTION", 0xC0000094: "INT_DIVIDE_BY_ZERO",
                0xC00000FD: "STACK_OVERFLOW", 0xC0000409: "STACK_BUFFER_OVERRUN"}
    print(f"  exception 0x{code:08X} {code_map.get(code, '')}")
    print(f"  faulting address 0x{addr:016X} (param0=0x{p0:016X})")
    if code == 0xC0000005:
        print(f"  AV type: {'read' if p0 == 0 else 'write'} @ 0x{p0:016X}")
    bases = sorted(modules, reverse=True)
    for base, name in bases:
        if base <= addr:
            print(f"  -> module: {name}  (base 0x{base:016X} + offset 0x{addr - base:X})")
            break
    else:
        print("  -> no module covers the address")
    print(f"  loaded modules: {len(modules)}")
    interesting = [n for _, n in modules if any(k in n.lower() for k in
                   ("destiny", "steam_api", "d3d11", "dxgi", "d3d12"))]
    print("  graphics/ours modules:", interesting[:8])

if __name__ == "__main__":
    parse(sys.argv[1])