"""Read a full-memory minidump and resolve virtual addresses in it.

Written for the 08-15 captures in destiny-preservation/RE_output/content/, which are
real full-memory dumps (5.7 GB) and therefore contain the RUNTIME-BUILT schema objects
our unpacked PE does not: that image stores only 7% of .data (FINDINGS 20.52), and both
schema globals fall past the cut.

Usage:
  minidump_reader.py <dump.dmp>                       - header, modules, memory summary
  minidump_reader.py <dump.dmp> --read <va> <count>   - hex/ascii at an absolute VA
  minidump_reader.py <dump.dmp> --rva <rva> <count>   - same, relative to destiny2.exe
"""
import struct
import sys

STREAM_MODULE_LIST = 4
STREAM_MEMORY64_LIST = 9


class Minidump:
    """Indexes a minidump's module and full-memory streams for VA lookups."""

    def __init__(self, path):
        self.path = path
        self.file = open(path, 'rb')
        head = self.file.read(32)
        if head[:4] != b'MDMP':
            raise ValueError('not a minidump (bad signature %r)' % head[:4])
        self.stream_count, self.dir_rva = struct.unpack_from('<II', head, 8)
        self.streams = {}
        self.file.seek(self.dir_rva)
        raw = self.file.read(12 * self.stream_count)
        for i in range(self.stream_count):
            kind, size, rva = struct.unpack_from('<III', raw, i * 12)
            self.streams[kind] = (size, rva)
        self.modules = self._modules()
        self.ranges = self._ranges()

    def _read(self, rva, count):
        self.file.seek(rva)
        return self.file.read(count)

    def _utf16(self, rva):
        length = struct.unpack_from('<I', self._read(rva, 4), 0)[0]
        return self._read(rva + 4, length).decode('utf-16-le', errors='replace')

    def _modules(self):
        if STREAM_MODULE_LIST not in self.streams:
            return []
        _, rva = self.streams[STREAM_MODULE_LIST]
        count = struct.unpack_from('<I', self._read(rva, 4), 0)[0]
        raw = self._read(rva + 4, 108 * count)
        out = []
        for i in range(count):
            base, size = struct.unpack_from('<QI', raw, i * 108)
            name_rva = struct.unpack_from('<I', raw, i * 108 + 20)[0]
            out.append({'base': base, 'size': size, 'name': self._utf16(name_rva)})
        return out

    def _ranges(self):
        """@return Sorted (start, size, file_offset) for every dumped memory range."""
        if STREAM_MEMORY64_LIST not in self.streams:
            return []
        _, rva = self.streams[STREAM_MEMORY64_LIST]
        count, base_rva = struct.unpack_from('<QQ', self._read(rva, 16), 0)
        raw = self._read(rva + 16, 16 * count)
        out = []
        offset = base_rva
        for i in range(count):
            start, size = struct.unpack_from('<QQ', raw, i * 16)
            out.append((start, size, offset))
            offset += size
        out.sort()
        return out

    def module(self, needle):
        """@return First module whose name contains `needle`, case-insensitively."""
        for m in self.modules:
            if needle.lower() in m['name'].lower():
                return m
        return None

    def read_va(self, va, count):
        """@return Bytes at an absolute VA, or None when that VA is not in the dump."""
        for start, size, offset in self.ranges:
            if start <= va < start + size:
                available = min(count, start + size - va)
                return self._read(offset + (va - start), available)
        return None


def dump_hex(data, va):
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16]
        hexs = ' '.join('%02X' % b for b in chunk)
        text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print('  %012X  %-47s  %s' % (va + i, hexs, text))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    md = Minidump(sys.argv[1])
    game = md.module('destiny2')

    if '--read' in sys.argv or '--rva' in sys.argv:
        flag = '--read' if '--read' in sys.argv else '--rva'
        i = sys.argv.index(flag)
        value = int(sys.argv[i + 1], 0)
        count = int(sys.argv[i + 2], 0) if len(sys.argv) > i + 2 else 64
        va = value if flag == '--read' else (game['base'] + value)
        data = md.read_va(va, count)
        if data is None:
            print('VA 0x%X is NOT present in this dump' % va)
            return 1
        print('VA 0x%X (%d bytes):' % (va, len(data)))
        dump_hex(data, va)
        return 0

    total = sum(size for _, size, _ in md.ranges)
    print('dump    : %s' % md.path)
    print('streams : %d   memory ranges: %d   mapped: %.2f GB'
          % (md.stream_count, len(md.ranges), total / (1024 ** 3)))
    print('modules : %d' % len(md.modules))
    if game:
        print('destiny2: base 0x%X  size 0x%X  (%s)'
              % (game['base'], game['size'], game['name']))
        print('          static 0x140000000 maps to this base; RVA = static - 0x140000000')
    for m in md.modules[:1]:
        print('first   : 0x%X %s' % (m['base'], m['name']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
