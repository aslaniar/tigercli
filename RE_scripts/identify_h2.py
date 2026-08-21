import struct, zlib, os, hashlib

TARGET = 0x596767B4
name = b'w64_activities_0199_0'

def crc32(d):
    return zlib.crc32(d) & 0xFFFFFFFF

def fnv1a(d, seed=0x811C9DC5):
    h = seed
    for b in d:
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h

def fnv1(d, seed=0x811C9DC5):
    h = seed
    for b in d:
        h = (h * 0x01000193) & 0xFFFFFFFF
        h ^= b
    return h

def djb2(d):
    h = 5381
    for b in d:
        h = ((h << 5) + h + b) & 0xFFFFFFFF
    return h

def sdbm(d):
    h = 0
    for b in d:
        h = (b + (h << 6) + (h << 16) - h) & 0xFFFFFFFF
    return h

def adler(d):
    return zlib.adler32(d) & 0xFFFFFFFF

cands = {}
cands['crc32(name)'] = crc32(name)
cands['fnv1a(name)'] = fnv1a(name)
cands['fnv1(name)'] = fnv1(name)
cands['djb2(name)'] = djb2(name)
cands['sdbm(name)'] = sdbm(name)
cands['adler32(name)'] = adler(name)
cands['crc32(name+_0)'] = crc32(name + b'_0')
cands['crc32(name w/ NUL)'] = crc32(name + b'\x00')
for ln, v in cands.items():
    mark = '  <== MATCH' if v == TARGET else ''
    print(f'{ln:<24} = 0x{v:08X}{mark}')

pkg = os.path.join(r'C:\Users\rasla\Downloads\destiny-preservation\dcv build\packages', name.decode() + '.pkg')
if os.path.exists(pkg):
    sz = os.path.getsize(pkg)
    d = open(pkg, 'rb').read()
    print()
    print('pkg size:', len(d), 'header[0:16]:', d[:16].hex())
    print('crc32(pkg whole)        =', hex(crc32(d)), 'MATCH' if crc32(d) == TARGET else '')
    print('crc32(pkg body)         =', hex(crc32(d[16:])), 'MATCH' if crc32(d[16:]) == TARGET else '')
    print('adler32(pkg whole)      =', hex(adler(d)), 'MATCH' if adler(d) == TARGET else '')
    print('md5(pkg)[0:4] LE        =', hex(struct.unpack('<I', hashlib.md5(d).digest()[:4])[0]), 'MATCH' if struct.unpack('<I', hashlib.md5(d).digest()[:4])[0] == TARGET else '')
    print('sha1(pkg)[0:4] LE       =', hex(struct.unpack('<I', hashlib.sha1(d).digest()[:4])[0]), 'MATCH' if struct.unpack('<I', hashlib.sha1(d).digest()[:4])[0] == TARGET else '')
    print('sha256(pkg)[0:4] LE     =', hex(struct.unpack('<I', hashlib.sha256(d).digest()[:4])[0]), 'MATCH' if struct.unpack('<I', hashlib.sha256(d).digest()[:4])[0] == TARGET else '')
else:
    print('pkg missing:', pkg)

idv = 0x199
print()
print('id-related:')
print('  crc32(2B id LE) =', hex(crc32(struct.pack('<H', idv))))
print('  fnv1a(2B id LE) =', hex(fnv1a(struct.pack('<H', idv))))
print('  sig+id combos:')
sig = bytes.fromhex('9fe57c13e73f31ea')
for combo_name, combo in [
    ('sig8+id2', sig + struct.pack('<H', idv)),
    ('id2+sig8', struct.pack('<H', idv) + sig),
    ('kind1+id2+sig8', b'\x01' + struct.pack('<H', idv) + sig),
]:
    print(f'  crc32({combo_name}) =', hex(crc32(combo)), 'MATCH' if crc32(combo) == TARGET else '')
