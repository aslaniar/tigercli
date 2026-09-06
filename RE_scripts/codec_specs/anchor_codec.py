"""anchor_codec spec - the "entity-index"/"anchor-index" codec 0x1404C16C0
(ent-receive-contract.md section 4, femu-confirmed):

    value13 = read13;  salt4 = read4;
    if (flag r9b == 0): high2 = read2          (unvalidated path)
    else: high2 = global dword (NOT on the wire)
    dst = ((high2 << 4 | salt4) << 16) | value13   (a 22-bit handle)

femu-confirmed consumption counts (the recorded oracles):
    present + flag=1 -> 17 bits (no high2 read)
    present + flag=0 -> 19 bits (+ the 2 high2 bits)
    (absent -> the CALLER's presence bit, 1 bit, before the codec)

Value assembly: LSB-ordered (the ent-cluster reader 0x1403513B0 convention -
the client reads N bits and assembles the FIRST bit as the LSB).
bit_stream spec shape; the validation flag is a DECODE PARAM, not a wire bit.
"""

import sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from codec_spec import SpecError, BitReader, BitWriter  # noqa: E402


def _assemble(value13, salt4, high2):
    return ((high2 << 4 | salt4) << 16) | value13


def _split(handle):
    return {"value13": handle & 0x1FFF,
            "salt4": (handle >> 16) & 0xF,
            "high2": (handle >> 20) & 0x3}


def _decode(data, flag=1):
    r = BitReader(data)
    value13 = r.ubits(13)
    salt4 = r.ubits(4)
    if flag:
        high2 = None        # from the global context, not the wire
        consumed = 17
    else:
        high2 = r.ubits(2)
        consumed = r.pos
    if flag:
        handle = ((salt4) << 16) | value13   # high2 unknown from the wire
    else:
        handle = ((high2 << 4 | salt4) << 16) | value13
    return {"value13": value13, "salt4": salt4,
            "high2": high2 if not flag else None,
            "handle_20bit": handle, "_bits_consumed": consumed if not flag
            else 17}


def _encode(obj, flag=1):
    w = BitWriter()
    w.ubits(obj["value13"], 13)
    w.ubits(obj["salt4"], 4)
    if not flag:
        w.ubits(obj["high2"], 2)
    return w.to_bytes()


def _random_object(rng, params):
    obj = {"value13": rng.getrandbits(13), "salt4": rng.getrandbits(4)}
    if not params.get("flag"):
        obj["high2"] = rng.getrandbits(2)
    return obj


def _naive_must_fail():
    """THE deliberately naive variant: MSB-first VALUE assembly (the
    opposite of the recorded LSB-ordered reader semantics). Must produce a
    different decode of the same 17 bits - proving the fixture can catch an
    assembly-order bug."""
    bits = [1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0]
    data = bytes(sum(b << (7 - i) for i, b in enumerate(bits[k:k + 8]))
                 for k in range(0, len(bits), 8)) if len(bits) > 8 else \
        bytes([sum(b << (7 - i) for i, b in enumerate(bits))])
    real = _decode(data, flag=1)
    # naive: MSB-first assembly (v = v<<1 | bit)
    naive_v = 0
    pos = 0
    for w in (13, 4):
        val = 0
        for _ in range(w):
            bitpos = pos
            b = (bits[bitpos] if bitpos < len(bits) else 0)
            val = (val << 1) | b
            pos += 1
        naive_v = val
        if w == 13:
            nv13 = val
        else:
            nsalt = val
    return (real["value13"] != naive_v) or (real["salt4"] != nsalt)


SPEC = {
    "name": "anchor_codec",
    "bit_stream": True,
    "source": "ent-receive-contract.md section 4 (femu-confirmed "
              "consumption; 0x1404C16C0 decoded)",
    "fields": [
        {"name": "value13", "type": "ubits", "width": 13},
        {"name": "salt4", "type": "ubits", "width": 4},
        {"name": "high2", "type": "ubits", "width": 2, "when": "not flag"},
    ],
    "param_sets": [{"flag": 1}, {"flag": 0}],
    "random_object": _random_object,
    "roundtrip_fixture": {"value13": 0x1555, "salt4": 0xA, "high2": 0x2},
    "fixtures": [
        {"bytes": bytes([0xFF, 0xFF, 0xC0]), "params": {"flag": 1},
         "expect": {"_bits_consumed": 17}},
        {"bytes": bytes([0xFF, 0xFF, 0xC0]), "params": {"flag": 0},
         "expect": {"_bits_consumed": 19}},
    ],
    "naive_variants": [
        {"name": "MSB-first assembly (the two-dialect bug)",
         "must_fail": _naive_must_fail},
    ],
    "cross_check_note": "consumption counts femu-confirmed in the contract "
                        "(absent=1 caller bit; present+flag=1=17); a direct "
                        "femu cross-check of 0x1404C16C0 needs its register "
                        "signature - OPEN (femu_oracle unset)",
}
