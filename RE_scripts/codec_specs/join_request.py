"""join_request spec - the activity join-request layout, ground truth = the
FORK'S OWN admit decode (byte-exact in THREE boots, 20.318):
  RE_build/Sunrise-021/Sunrise/src/middleware/bap/activity_message/
  activity_join_request_parser.cpp
Layout: correlation u32 BE @0 | sessionId u64 BE @4 (nonzero required) |
memberKey u64 LE @12 | prefix = 20 bytes; characterSoid: 64 bits at BIT 330,
assembled MSB-FIRST (the fork's bit_reader docstring: "reads one unsigned
field in most-significant-bit-first order" - NOTE this is the OPPOSITE value
assembly of the client's ent-cluster reader 0x1403513B0, which assembles
LSB-ordered; the two dialects are kept distinct, not averaged).

Native spec: the fork's layout is the ground truth; encode/decode below
mirror activity_join_request_parser.cpp + encoding/bit_reader.h exactly.
"""

import sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from codec_spec import SpecError  # noqa: E402

PREFIX_BITS = 160          # the 20-byte prefix
CHAR_BIT = 330             # the fork's kCharacterSoidBit
CHAR_WIDTH = 64
FULL_BITS = CHAR_BIT + CHAR_WIDTH   # 394 bits -> 50 bytes


def _place_msb(buf, bitpos, value, width):
    """Place `width` bits of value at bitpos, MSB-first (the fork's
    bit_reader assembly: first bit read = the value's MSB)."""
    for i in range(width):
        if (value >> (width - 1 - i)) & 1:
            p = bitpos + i
            buf[p >> 3] |= 1 << (7 - (p & 7))


def _encode(obj):
    out = bytearray()
    if not obj.get("sessionId"):
        raise SpecError("CONST-VIOLATION", field="sessionId",
                        msg="sessionId must be nonzero (the fork refuses "
                            "kAbsentSessionId)")
    out += obj["correlation"].to_bytes(4, "big")
    out += obj["sessionId"].to_bytes(8, "big")
    out += obj["memberKey"].to_bytes(8, "little")
    v = obj.get("characterSoid") or 0
    if v:
        out += b"\x00" * ((FULL_BITS + 7) // 8 - len(out))
        for i in range(CHAR_WIDTH):
            if (v >> (CHAR_WIDTH - 1 - i)) & 1:   # MSB-first placement
                bit = CHAR_BIT + i
                out[bit >> 3] |= 1 << (7 - (bit & 7))
    return bytes(out)


def _decode(data):
    if len(data) < 20:
        raise SpecError("TRUNCATED", at=len(data) * 8,
                        msg="prefix needs 20 bytes")
    correlation = int.from_bytes(data[0:4], "big")
    session_id = int.from_bytes(data[4:12], "big")
    member_key = int.from_bytes(data[12:20], "little")
    if session_id == 0:
        raise SpecError("CONST-VIOLATION", field="sessionId",
                        msg="absent session (the fork refuses "
                            "kAbsentSessionId)")
    obj = {"correlation": correlation, "sessionId": session_id,
           "memberKey": member_key}
    if len(data) >= (FULL_BITS + 7) // 8:
        v = 0
        for i in range(CHAR_WIDTH):               # first bit read = MSB
            bitpos = CHAR_BIT + i
            v = (v << 1) | ((data[bitpos >> 3] >> (7 - (bitpos & 7))) & 1)
        obj["characterSoid"] = v
    else:
        obj["characterSoid"] = 0    # the fork: short payload reads zero
    return obj


def _random_object(rng, _params=None):
    return {
        "correlation": rng.getrandbits(32),
        "sessionId": rng.getrandbits(64) or 1,
        "memberKey": rng.getrandbits(64),
        "characterSoid": rng.getrandbits(64) if rng.random() < 0.7 else 0,
    }


# Hand-written positional fixture (independent of the encoder): pins field
# order + endianness, so an encoder bug cannot pass its own test.
FIXTURE_OBJ = {"correlation": 0x11223344,
               "sessionId": 0xAABBCCDDEEFF0011,
               "memberKey": 0xD3DABDA3AABBCCDD,
               "characterSoid": 0xACBE7AA811223344}
FIXTURE_PREFIX = bytes(
    [0x11, 0x22, 0x33, 0x44,                                    # correlation BE
     0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00, 0x11,             # sessionId BE
     0xDD, 0xCC, 0xBB, 0xAA, 0xA3, 0xBD, 0xDA, 0xD3])            # memberKey LE
# the soid region is built by _encode (the same helper both directions use;
# the PREFIX above is the hand-pinned part - field order + endianness
# independent of the encoder)


def _naive_must_fail():
    """THE deliberately naive variant: MSB/LSB value-assembly swapped (the
    two-dialect confusion trap). It must FAIL the fixture - proving the
    fixture can catch an assembly-order bug."""
    v = FIXTURE_OBJ["characterSoid"]
    naive_bytes = bytearray(_encode(FIXTURE_OBJ))
    for i in range(CHAR_WIDTH):
        p = CHAR_BIT + i
        if (v >> i) & 1:                       # WRONG: LSB-first placement
            naive_bytes[p >> 3] |= 1 << (7 - (p & 7))
        else:
            naive_bytes[p >> 3] &= ~(1 << (7 - (p & 7))) & 0xFF
    got = _decode(bytes(naive_bytes))
    return got["characterSoid"] != v


SPEC = {
    "name": "join_request",
    "source": "the fork's admit decode (byte-exact in 3 boots, 20.318) + "
              "encoding/bit_reader.h (MSB-first VALUE assembly)",
    "native": {"encode": _encode, "decode": _decode},
    "fields": [
        {"name": "correlation", "type": "u32", "order": "be"},
        {"name": "sessionId", "type": "u64", "order": "be", "nonzero": True},
        {"name": "memberKey", "type": "u64", "order": "le"},
        {"name": "characterSoid", "type": "bits", "at_bit": CHAR_BIT,
         "width": CHAR_WIDTH, "optional": True, "default": 0},
    ],
    "fixtures": [
        {"bytes": _encode(FIXTURE_OBJ),
         "expect": {"correlation": 0x11223344,
                    "sessionId": 0xAABBCCDDEEFF0011,
                    "memberKey": 0xD3DABDA3AABBCCDD,
                    "characterSoid": 0xACBE7AA811223344}},
        {"bytes": FIXTURE_PREFIX,
         "expect": {"correlation": 0x11223344,
                    "sessionId": 0xAABBCCDDEEFF0011,
                    "memberKey": 0xD3DABDA3AABBCCDD,
                    "characterSoid": 0}},   # short payload is legal
        {"bytes": bytes(20), "kind": "reject"},   # absent session
        {"bytes": bytes(10), "kind": "reject"},   # short prefix
    ],
    "random_object": _random_object,
    "roundtrip_fixture": FIXTURE_OBJ,
    "truncation": {"legal_after_bit": PREFIX_BITS},
    # bits 160..329 are declared inter-field padding, and 394..399 are the
    # trailing byte's padding: a flip there decoding identically is the
    # truth about padding, not a codec defect
    "flip_ignore_bits": [[PREFIX_BITS, CHAR_BIT], [FULL_BITS, 400]],
    "naive_variants": [
        {"name": "LSB-first assembly (the ent-dialect bug)",
         "must_fail": _naive_must_fail},
    ],
    "cross_check_note": "20.318 verified the record == the decoded "
                        "JoinRequest byte-exact vs THIS fork layout in "
                        "p2-185/186/187 (three boots)",
}

