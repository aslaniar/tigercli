#!/usr/bin/env python3
"""name_codec.py - the profile-block name obfuscation, both directions (2026-08-30).

The region-A name reader (0x14129AA80, deobfuscation at 0x1416D3460) transforms each
16-bit wire word in place, per FINDINGS 20.179 RESULT 1:

    plain[i] = key16(i) ^ ((wire[i] * 0x7b4f) & 0xFFFF)
    key16(0) = 0
    key16(i>0) = rotl32(0xC245B0C4, i mod 31) & 0xFFFF

The writer needs the inverse, which exists because 0x7b4f is odd and therefore a unit
mod 2^16:

    wire[i] = ((plain[i] ^ key16(i)) * inv(0x7b4f)) & 0xFFFF

TERMINATOR: the reader walks words until it sees a ZERO WIRE WORD. It writes the
deobfuscated value back BEFORE testing, so the stored terminator is key16(L) - nonzero
for any L>0. That is a property of the stored buffer, not of the terminator condition:
a writer terminates the name by emitting a zero wire word, always.

Usage:
  name_codec.py --selftest
  name_codec.py --encode "TEXT"      -> wire words, hex
  name_codec.py --decode <hex...>    -> plain words + a UTF-16LE / latin-1 reading
  name_codec.py --try-both <hex...>  -> print BOTH readings of a captured buffer, so a
                                        dump of unknown form (wire or stored) can be told
                                        apart by which one is legible
"""
import sys

MUL = 0x7B4F
SEED = 0xC245B0C4


def _inv16(a: int) -> int:
    """Modular inverse mod 2^16 (a must be odd)."""
    assert a % 2 == 1, "0x7b4f is odd; a even multiplier would not be invertible"
    x = 1
    for _ in range(16):
        x = (x * (2 - a * x)) & 0xFFFF
    assert (a * x) & 0xFFFF == 1
    return x


INV = _inv16(MUL)


def key16(i: int) -> int:
    if i == 0:
        return 0
    r = i % 31
    return ((SEED << r | SEED >> (32 - r)) & 0xFFFFFFFF) & 0xFFFF


def decode(wire):
    """wire words -> plain words (what the client stores)."""
    return [key16(i) ^ ((w * MUL) & 0xFFFF) for i, w in enumerate(wire)]


def encode(plain):
    """plain words -> wire words (what the server must publish)."""
    return [((p ^ key16(i)) * INV) & 0xFFFF for i, p in enumerate(plain)]


def _words(hexstr):
    b = bytes.fromhex(hexstr.replace(" ", "").replace(",", ""))
    return [int.from_bytes(b[i:i + 2], "little") for i in range(0, len(b) - 1, 2)]


def _read(words):
    b = b"".join(w.to_bytes(2, "little") for w in words)
    try:
        u = b.decode("utf-16-le").rstrip("\x00")
    except UnicodeDecodeError:
        u = "<not utf-16le>"
    lat = "".join(chr(c) if 32 <= c < 127 else "." for c in b)
    return u, lat


def selftest() -> int:
    checks, fails = 0, 0

    def ck(name, got, want):
        nonlocal checks, fails
        checks += 1
        if got != want:
            fails += 1
            print(f"  FAIL {name}: got {got!r} want {want!r}")

    ck("inv is a true inverse", (MUL * INV) & 0xFFFF, 1)
    ck("key16(0) is zero", key16(0), 0)
    # i=31 rotates by ZERO, which is NOT the same as key16(0): the zero key at index 0 is a
    # SPECIAL CASE in the formula, not a consequence of the rotation. Getting this backwards
    # would corrupt every name 31 words or longer.
    ck("key16(31) is an unrotated seed", key16(31), SEED & 0xFFFF)
    ck("key16(31) differs from the index-0 special case", key16(31) == key16(0), False)
    ck("key16(1) == rotl32(seed,1)&0xffff", key16(1), ((SEED << 1 | SEED >> 31) & 0xFFFFFFFF) & 0xFFFF)

    # round trip over every index the 128-byte name field can hold
    plain = [(i * 2654435761) & 0xFFFF for i in range(64)]
    ck("round trip, 64 words", decode(encode(plain)), plain)

    # the empty name: a single zero wire word must deobfuscate to zero at index 0,
    # which is exactly why the minimal block's empty name survives the zero scan.
    ck("empty name stores zero", decode([0])[0], 0)
    # and a zero wire word at any LATER index stores key16(i), i.e. is NOT zero
    ck("terminator at i=3 stores key16(3)", decode([0, 0, 0, 0])[3], key16(3))

    # a real string round trips through the wire form
    s = "Guardian"
    w = encode([ord(c) for c in s])
    ck("string round trip", "".join(chr(c) for c in decode(w)), s)
    ck("encoding is not the identity", w == [ord(c) for c in s], False)

    print(f"selftest: {checks - fails}/{checks} passed")
    return 1 if fails else 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if "--encode" in argv:
        text = argv[argv.index("--encode") + 1]
        w = encode([ord(c) for c in text])
        print("plain :", " ".join(f"{ord(c):04X}" for c in text))
        print("wire  :", " ".join(f"{x:04X}" for x in w))
        print("bytes :", "".join(x.to_bytes(2, "little").hex() for x in w))
        return 0
    if "--decode" in argv or "--try-both" in argv:
        flag = "--decode" if "--decode" in argv else "--try-both"
        words = _words(" ".join(argv[argv.index(flag) + 1:]))
        print(f"{len(words)} words")
        p = decode(words)
        u, lat = _read(p)
        print(f"  as WIRE -> plain: utf16={u!r} latin={lat!r}")
        if flag == "--try-both":
            u2, lat2 = _read(words)
            print(f"  as STORED (raw): utf16={u2!r} latin={lat2!r}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
