"""Locate the package key table statically + test-decrypt one spawn-set block.

1. Scan for kKeyTableText: 0F 10 05 ? ? ? ? 48 8D 64 24 F8 48 89 2C 24 48 8D 2D ? ? ? ? E9
   -> movups xmm0,[rip+X] loads the 48-byte key table (identityConstant, alternateKey,
   nonceBase per Sunrise's targets::game::packages::KeyTable).
2. Derive primary = bootstrapToken + identityConstant (byte-wise) for both token
   candidates.
3. BCrypt AES-GCM decrypt of one spawn-set block; tag validation = proof.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scan_sunrise_patterns import parse_signature, scan, parse_pe  # noqa: E402

EXE = Path(__file__).parent.parent / "RE_output" / "destiny2_unpacked.exe"
IMAGE_BASE = 0x140000000

KEY_TABLE_SIG = ("0F 10 05 ? ? ? ? 48 8D 64 24 F8 48 89 2C 24 48 8D 2D ? ? ? ? E9")

TOKEN_A = b"2MFioXto7iAUN4Qj"
TOKEN_B = b"Ijaknsg9bwVH3Hv"


def main() -> None:
    data = EXE.read_bytes()
    _ib, _e, sections = parse_pe(data)
    hits = scan(data, parse_signature(KEY_TABLE_SIG))
    print(f"key-table signature hits: {len(hits)}")
    for off in hits:
        # movups xmm0, [rip+disp32]: opcode 0F 10 05 at offset 0, disp at +3, next insn +7
        disp = struct.unpack_from("<i", data, off + 3)[0]
        table_off = off + 7 + disp
        table = data[table_off:table_off + 48]
        identity = table[0:16]
        alternate = table[16:32]
        nonce = table[32:48]
        print(f"\nsite file=0x{off:X} -> key table VA 0x{IMAGE_BASE + table_off:X}")
        print(f"  identityConstant: {identity.hex(' ')}")
        print(f"  alternateKey:     {alternate.hex(' ')}")
        print(f"  nonceBase:        {nonce.hex(' ')}")
        for name, token in (("token A (2MFioXto)", TOKEN_A), ("token B (Ijaknsg)", TOKEN_B)):
            primary = bytes((t + c) & 0xFF for t, c in zip(token, identity))
            print(f"  primary[{name}]: {primary.hex(' ')}")


if __name__ == "__main__":
    main()
