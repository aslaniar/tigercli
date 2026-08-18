"""Tiger package (.pkg) decoder for Destiny 2 client content.

A self-contained Python port of the tiger-pkg 0.21.0 ``d2_prebl`` decode path:
AES-128-GCM block decryption + Oodle decompression. Reads ANY entry from ANY
patch file of a package set - unlike tigercli, which only resolves entries
from a set's final (highest) patch file.

Validated 6/6 byte-identical against tigercli.exe outputs on the
Shadowkeep-era build this repository was developed against.
"""

from __future__ import annotations

import ctypes
import struct
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ---------------------------------------------------------------------------
# Build constants (the Destiny 2 Shadowkeep-era pkg format)
# ---------------------------------------------------------------------------
# AES-128-GCM keys. These are the same crypto constants tiger-pkg 0.21.0's
# d2_prebl/d2_shared carries for this build family.
KEY0 = bytes.fromhex("D62AB2C10CC01BC535DB7B8655C7DC3B")
KEY1 = bytes.fromhex("3A4A5D3673A660587E63E676E40892B5")

# Fixed 12-byte nonce base; per-package derived in make_nonce().
NONCE_BASE = bytearray.fromhex("84DF11C0ACABFA2033112699")

BLOCK_SIZE = 0x40000


def make_nonce(pkg_id: int) -> bytes:
    """Derive the per-package GCM nonce from the fixed base + pkg_id."""
    n = bytearray(NONCE_BASE)
    n[0] ^= (pkg_id >> 8) & 0xFF
    n[1] = 0xF9  # Destiny2Shadowkeep
    n[11] ^= pkg_id & 0xFF
    return bytes(n)


# ---------------------------------------------------------------------------
# Oodle decompression (wraps the proprietary oo2core DLL via ctypes)
# ---------------------------------------------------------------------------

class Oodle:
    """ctypes binding to oo2core (OodleLZ). Requires a local copy of the DLL
    from a Destiny 2 install (or the RAD Oodle SDK) - it is proprietary and
    MUST NOT be redistributed with this package."""

    def __init__(self, dll_path):
        self.lib = ctypes.WinDLL(str(dll_path))
        self.fn = self.lib.OodleLZ_Decompress
        self.fn.restype = ctypes.c_longlong
        self.fn.argtypes = [ctypes.c_void_p, ctypes.c_longlong,
                            ctypes.c_void_p, ctypes.c_longlong,
                            ctypes.c_int, ctypes.c_int, ctypes.c_int,
                            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                            ctypes.c_int]

    def decompress(self, comp: bytes, raw_len: int = BLOCK_SIZE) -> bytes:
        raw = ctypes.create_string_buffer(raw_len)
        out = self.fn(comp, len(comp), raw, raw_len,
                      1, 0, 1, None, None, None, None, None, None, 3)
        if out < 0:
            raise ValueError(f"Oodle decompress failed: {out}")
        # This oo2core build returns 0 on success (tiger-pkg ignores the
        # return too); the block occupies the full raw_len in block space.
        return raw.raw[:raw_len]


# ---------------------------------------------------------------------------
# Pkg file format
# ---------------------------------------------------------------------------

def parse_pkg_file(path: Path) -> dict:
    """Parse one pkg file's header + entry/block tables.

    NOTE: the package id lives at u16 @0x04. A pkg_reader variant that reads
    @0x02 instead gets the PLATFORM field - a known off-by-2 trap.
    """
    data = path.read_bytes()
    version, _plat, pkg_id = struct.unpack_from("<HHH", data, 0)
    assert version == 38, f"unexpected pkg version {version}"
    patch_id = struct.unpack_from("<H", data, 0x20)[0]
    entry_count = struct.unpack_from("<I", data, 0xB4)[0]
    block_count = struct.unpack_from("<I", data, 0xD0)[0]
    entry_table = struct.unpack_from("<I", data, 0x110)[0] + 96
    block_table = entry_table + entry_count * 16 + 32

    entries = []
    for i in range(entry_count):
        off = entry_table + i * 16
        reference, type_info, block_info = struct.unpack_from("<IIQ", data, off)
        entries.append({
            "index": i,
            "reference": reference,
            "file_type": (type_info >> 9) & 0x7F,
            "subtype": (type_info >> 6) & 0x7,
            "start_block": block_info & 0x3FFF,
            "start_offset": ((block_info >> 14) & 0x3FFF) << 4,
            "file_size": block_info >> 28,
        })

    blocks = []
    for i in range(block_count):
        off = block_table + i * 48
        offset, size, bpatch, flags = struct.unpack_from("<IIHH", data, off)
        gcm_tag = data[off + 32: off + 48]
        blocks.append({"offset": offset, "size": size, "patch_id": bpatch,
                       "flags": flags, "gcm_tag": gcm_tag})
    return {"pkg_id": pkg_id, "patch_id": patch_id, "entries": entries,
            "blocks": blocks, "size": len(data)}


class PkgReader:
    """Decode entries across a patch set.

    Base = the highest-patch file of the set (its tables are authoritative);
    block bytes are fetched from the sibling file matching each block's
    patch_id (the ``<name>_<patch>.pkg`` naming rule, per tiger-pkg).
    """

    def __init__(self, files: dict[int, Path], oodle_path):
        """files = {patch_id: path}; pass every patch file of the set."""
        self.files = {pid: f.read_bytes() for pid, f in files.items()}
        base_pid = max(self.files)
        self.parsed = parse_pkg_file(files[base_pid])
        self.nonce = make_nonce(self.parsed["pkg_id"])
        self.c0 = AESGCM(KEY0)
        self.c1 = AESGCM(KEY1)
        self.oodle = Oodle(oodle_path)
        self.block_cache = {}

    @property
    def entries(self):
        return self.parsed["entries"]

    def raw_block(self, bi: int) -> bytes:
        b = self.parsed["blocks"][bi]
        src = self.files[b["patch_id"]]
        return src[b["offset"]: b["offset"] + b["size"]]

    def decoded_block(self, bi: int) -> bytes:
        if bi in self.block_cache:
            return self.block_cache[bi]
        b = self.parsed["blocks"][bi]
        data = self.raw_block(bi)
        flags = b["flags"]
        if flags & 0x2:  # ENCRYPTED
            cipher = self.c1 if (flags & 0x4) else self.c0  # ALT_CIPHER
            data = cipher.decrypt(self.nonce, data + b["gcm_tag"], b"")
        if flags & 0x1:  # COMPRESSED
            data = self.oodle.decompress(data)
        self.block_cache[bi] = data
        return data

    def entry_blob(self, index: int) -> bytes:
        """Decode the full content blob for one entry (empty if a null entry).

        NOTE: an entry's ``reference`` may be 0xFFFFFFFF without being null -
        tigercli reads a 1-byte blob at such an index in the reference set.
        The only true null test is file_size == 0 (which yields b"" anyway);
        the reference field is NOT a read-path gate.
        """
        e = self.parsed["entries"][index]
        if e["file_size"] == 0:
            return b""
        end_off = e["start_block"] * BLOCK_SIZE + e["start_offset"] + e["file_size"]
        end_block = (end_off + BLOCK_SIZE - 1) // BLOCK_SIZE
        out = bytearray()
        for bi in range(e["start_block"], end_block):
            out.extend(self.decoded_block(bi))
        start = e["start_offset"]
        return bytes(out[start: start + e["file_size"]])

    def entry_tag(self, index: int) -> str:
        """The content tag this entry is addressed by: 0x80800000 + set<<13 + entry."""
        return f"0x{0x80800000 + (self.parsed['pkg_id'] << 13) + index:08X}"


__all__ = ["make_nonce", "Oodle", "parse_pkg_file", "PkgReader", "BLOCK_SIZE"]