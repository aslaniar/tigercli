import struct, sys, hashlib, json

def read_minidump_regions(path):
    f = open(path, 'rb')
    hdr = f.read(32)
    if hdr[:4] != b'MDMP':
        raise ValueError('not a minidump')
    num_streams, dir_rva = struct.unpack_from('<II', hdr, 8)
    f.seek(dir_rva)
    streams = []
    for i in range(num_streams):
        s = f.read(12)
        typ, size, rva = struct.unpack('<III', s)
        streams.append((typ, size, rva))
    regions = []
    for typ, size, rva in streams:
        if typ == 9:
            f.seek(rva)
            n, base_rva = struct.unpack('<QQ', f.read(16))
            for i in range(n):
                start, sz = struct.unpack('<QQ', f.read(16))
                regions.append((start, sz, base_rva + sum(r[1] for r in regions[-n:]) if False else 0))
            break
    if not regions:
        raise ValueError('no Memory64ListStream')
    out = []
    cum = 0
    f.seek(rva)
    n, base_rva = struct.unpack('<QQ', f.read(16))
    for i in range(n):
        start, sz = struct.unpack('<QQ', f.read(16))
        out.append((start, sz, base_rva + cum))
        cum += sz
    f.close()
    return out

def extract(path, regions, va, size):
    f = open(path, 'rb')
    for start, sz, rva in regions:
        if start <= va and va + size <= start + sz:
            f.seek(rva + (va - start))
            return f.read(size)
    return None

if __name__ == '__main__':
    a = sys.argv[1]
    b = sys.argv[2]
    ra = read_minidump_regions(a)
    rb = read_minidump_regions(b)
    print(a, 'regions:', len(ra))
    print(b, 'regions:', len(rb))

    out = {}
    # the game's .data globals region: the image base + (0x141F00000 - 0x140000000) = the base + 0x1F00000
    for name, va, size in [
        ('globals_141f9', 0x7ff641bf0000 + 0x1F00000, 0x100000),
        ('globals_1426', 0x7ff641bf0000 + 0x260000, 0x20000),
    ]:
        da = extract(a, ra, va, size)
        db = extract(b, rb, va, size)
        if da is None or db is None:
            print(name, 'region not found in one dump', 'healthy' if da is None else '', 'failing' if db is None else '')
            continue
        diffs = [(i, da[i], db[i]) for i in range(size) if da[i] != db[i]]
        out[name] = {'size': size, 'diff_count': len(diffs)}
        print(f'{name}: {len(diffs)} byte diffs of {size}')
        if diffs:
            for i, x, y in diffs[:8]:
                print(f'   @+0x{i:X}: healthy=0x{x:02X} failing=0x{y:02X}')
    json.dump(out, open(r'C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_pair_globals_diff.json', 'w'), indent=1)
