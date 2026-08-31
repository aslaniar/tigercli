#!/usr/bin/env python3
# REGISTRY: caps: pe-parse, section-map, pdata-bounds, static-read
"""Minimal PE reader for static analysis of destiny2_unpacked_full.exe.

Reused pattern from the 08-23 direction-codec recovery (peer-visibility-codec-
findings PART 2): map VA -> file offset through the section table, imagebase
0x140000000, then read/disassemble directly. No Ghidra, no rig.
"""
import struct


class PE:
    def __init__(self, path):
        self.data = open(path, "rb").read()
        assert self.data[:2] == b"MZ", "not a PE"
        e_lfanew = struct.unpack_from("<I", self.data, 0x3C)[0]
        assert self.data[e_lfanew:e_lfanew + 4] == b"PE\0\0", "bad PE signature"
        coff = e_lfanew + 4
        num_sections = struct.unpack_from("<H", self.data, coff + 2)[0]
        opt_size = struct.unpack_from("<H", self.data, coff + 16)[0]
        opt = coff + 20
        self.imagebase = struct.unpack_from("<Q", self.data, opt + 24)[0]
        sec = opt + opt_size
        self.sections = []
        for i in range(num_sections):
            o = sec + i * 40
            name = self.data[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
            vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", self.data, o + 8)
            self.sections.append((name, vaddr, vsize, rawptr, rawsize))

    def off(self, va):
        """@return file offset for a virtual address, or None when unmapped."""
        rva = va - self.imagebase
        for _name, vaddr, vsize, rawptr, rawsize in self.sections:
            if vaddr <= rva < vaddr + max(vsize, rawsize):
                delta = rva - vaddr
                if delta < rawsize:
                    return rawptr + delta
        return None

    def section_of(self, va):
        rva = va - self.imagebase
        for name, vaddr, vsize, rawptr, rawsize in self.sections:
            if vaddr <= rva < vaddr + max(vsize, rawsize):
                return name
        return None

    # The file is a PROCESS DUMP: its headers keep the static base 0x140000000, but .data
    # holds live pointers from the dumped process. Derived empirically - 19,990 of 20,000
    # sampled .data pointers land inside the image with this base.
    RUNTIME_BASE = 0x7FF6AF7F0000

    def to_static(self, runtime_va):
        """@return static VA for a pointer read out of dumped .data, or None if implausible."""
        if not (0x7FF000000000 <= runtime_va <= 0x7FFFFFFFFFFF):
            return runtime_va          # already static
        rva = runtime_va - self.RUNTIME_BASE
        static = self.imagebase + rva
        return static if self.section_of(static) else None

    def read(self, va, n):
        o = self.off(va)
        return None if o is None else self.data[o:o + n]

    def pdata_bounds(self, va):
        """Exact function bounds from .pdata (RUNTIME_FUNCTION entries).
        @return (start_va, end_va) or None when va is not in a pdata entry.
        The exception-directory range is authoritative where present - it
        ends the 'heuristic end truncated at the first jump-out' failure."""
        sec = [s for s in self.sections if s[0] == ".pdata"]
        if not sec or not sec[0][4]:
            return None
        _n, vaddr, _vs, rawptr, rawsize = sec[0]
        rva = va - self.imagebase
        lo, hi = 0, rawsize // 12 - 1
        while lo <= hi:                      # binary search by start rva
            mid = (lo + hi) // 2
            s_rva, e_rva = struct.unpack_from("<II", self.data,
                                              rawptr + mid * 12)
            if rva < s_rva:
                hi = mid - 1
            elif rva >= e_rva:
                lo = mid + 1
            else:
                return (self.imagebase + s_rva, self.imagebase + e_rva)
        return None

    def qword(self, va):
        b = self.read(va, 8)
        return None if b is None or len(b) < 8 else struct.unpack("<Q", b)[0]
