"""payload_kind2 spec - the kind-2 (player/guardian) ent payload: RAW 8 BYTES
(64 bits, no presence bit, no transforms), femu-validated bit-exact against
the real dump codec object (20.304: "kind 2 = RAW 8 BYTES (64 bits, no
presence, no transforms)").

The payload is opaque to THIS spec (a 64-bit value carried verbatim); the
anchor_codec spec owns its internal 13/4[/2] decomposition when a payload is
known to be an anchor handle.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from codec_spec import SpecError  # noqa: E402


def _decode(data):
    if len(data) < 8:
        raise SpecError("TRUNCATED", at=len(data) * 8,
                        msg="kind-2 payload is exactly 8 bytes")
    v = int.from_bytes(data[:8], "big")   # big-endian u64 words (ent wire)
    return {"payload64": v, "raw": data[:8].hex(),
            "_bits_consumed": 64}


def _encode(obj):
    if "raw" in obj:
        raw = bytes.fromhex(obj["raw"])
        if len(raw) != 8:
            raise SpecError("BAD-VALUE", field="raw",
                            msg="kind-2 payload is exactly 8 bytes")
        return raw
    return obj["payload64"].to_bytes(8, "big")


SPEC = {
    "name": "payload_kind2",
    "source": "ent-receive-contract.md + 20.304 (raw 8 bytes, no presence, "
              "no transforms; femu-validated bit-exact vs the real dump "
              "codec object)",
    "fields": [
        {"name": "payload64", "type": "u64", "order": "be"},
    ],
    "fixtures": [
        {"bytes": bytes.fromhex("1122334455667788"),
         "expect": {"payload64": 0x1122334455667788}},
    ],
    "roundtrip_fixture": {"payload64": 0x0102030405060708},
    "truncation": {"legal_after_bit": None},
    "cross_check_note": "20.304's femu-validated bit-exactness vs the real "
                        "dump codec object (kind 2 = RAW 8 BYTES)",
}
