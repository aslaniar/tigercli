# -*- coding: utf-8 -*-
"""name_cipher spec - WRAPS RE_scripts/name_codec.py (the profile-block name
cipher, both directions). Never reimplements it: the native adapter converts
bytes (LE u16 words) <-> {"words": [...], "text": str} at the spec layer.

Ground truth: name_codec.py (20.179 R1 / 20.195; plain[i] = key16(i) ^
((wire[i]*0x7b4f)&0xFFFF); the encode side was validated against the
client's own writer output in boot p2-123 - that recorded match IS this
spec's client cross-check (T3-P3 substitute).
Traps carried from the source: key16(0)=0 is a SPECIAL CASE (not a rotation
result); at i=31 the rotation is by ZERO and key16(31)=0xB0C4; names 31+
words long break if that is collapsed.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import name_codec  # noqa: E402


def _bytes_to_words(data):
    if len(data) % 2:
        data = data[:-1]
    return [int.from_bytes(data[i:i + 2], "little")
            for i in range(0, len(data), 2)]


def _words_to_bytes(words):
    return b"".join((w & 0xFFFF).to_bytes(2, "little") for w in words)


def _decode(data):
    words = _bytes_to_words(data)
    plain = name_codec.decode(words)
    try:
        text = b"".join(w.to_bytes(2, "little") for w in plain) \
            .decode("utf-16-le").rstrip("\x00")
    except UnicodeDecodeError:
        text = None
    return {"words": plain, "text": text}


def _encode(obj):
    words = obj["words"]
    return _words_to_bytes(name_codec.encode(words))


def _naive_key16(i):
    """THE deliberately naive variant: treats i=0 as an ordinary zero
    rotation instead of the key16(0)=0 special case. At i=0 the rotation is
    r=0 so a naive impl returns SEED&0xFFFF - the special case it misses."""
    if i == 0:
        return name_codec.SEED & 0xFFFF      # WRONG: the special case
    r = i % 31
    return ((name_codec.SEED << r | name_codec.SEED >> (32 - r))
            & 0xFFFFFFFF) & 0xFFFF


def _naive_must_fail():
    """Assert the naive cipher produces different wire than the real one for
    ANY name whose first word is nonzero - i.e. the fixture CAN catch the
    special-case bug. Returns True when the naive variant indeed diverges."""
    plain = [ord("A")] * 31          # 31 words: also crosses the i=31 trap
    real_wire = name_codec.encode(plain)
    naive_wire = [((p ^ _naive_key16(i)) * name_codec.INV) & 0xFFFF
                  for i, p in enumerate(plain)]
    diverged = naive_wire != real_wire
    # and the i=31 trap: naive key16(31) must NOT equal the real key16(31)
    # (real key16(31) = rotation by zero = SEED&0xFFFF truncated - the trap
    # is that a rotation impl gets i=0 wrong; assert divergence at i=0)
    diverged0 = _naive_key16(0) != name_codec.key16(0)
    return diverged0 and diverged


SPEC = {
    "name": "name_cipher",
    "source": "RE_scripts/name_codec.py (20.179 R1 / 20.195); encode side "
              "validated against the client's own writer in boot p2-123",
    "native": {"encode": _encode, "decode": _decode},
    "fields": [
        {"name": "words", "type": "u16-words-LE", "doc": "the plain/wire "
         "u16 word list; the native adapter owns byte<->word conversion"},
    ],
    "random_object": lambda rng, _p=None: {
        "words": [rng.randrange(1, 0x10000) for _ in
                  range(rng.choice([0, 1, 8, 31, 32, 64]))]},
    "roundtrip_fixture": {"words": [ord("A")] * 31},
    # the name cipher has NO minimum length: any byte cut is a legal
    # shorter word list (the empty name is a valid name - key16 special case)
    "truncation": {"legal_after_bit": 0},
    "fixtures": [
        # the name "A" (single word): words=[0x41]; special case i=0:
        # key16(0)=0 so wire[0] == (0x41 * INV) & 0xFFFF
        {"bytes": _words_to_bytes(name_codec.encode([0x41])),
         "expect": {"words": [0x41]}},
        {"bytes": b"", "expect": {"words": []}},
    ],
    "naive_variants": [
        {"name": "key16-as-rotation (misses the key16(0)=0 special case)",
         "must_fail": _naive_must_fail},
    ],
    "cross_check_note": "encode side matched the client's own writer bytes "
                        "in boot p2-123 (the recorded p2(123) expected bytes "
                        "were computed here and registered pre-boot)",
}
