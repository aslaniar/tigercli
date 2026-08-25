#!/usr/bin/env python3
"""Restamp build_data.bin's identity header from a rebuilt sunrise-server.exe.

The cache stores the server exe's PE identity at offsets 12 (imageTimestamp)
and 16 (imageSize), u32 LE, packed (#pragma pack(push,1)). A rebuilt exe fails
content_swap until these match. Reads both values straight from the PE headers
(NT FileHeader.TimeDateStamp + OptionalHeader.SizeOfImage).

Usage:
  restamp_build_data.py <cache.bin> <server.exe> [--apply]
  restamp_build_data.py <cache.bin> --set-eqhash <hex64> [--apply]
Without --apply: prints what would change and verifies against the running
pair (smoke mode).

--set-eqhash writes ONLY the configuredEquipmentHash (offset 20, u64 LE) -
the P2 provisioned-union identity. Use it whenever the provisioned set
changes: obtain the value via
  wine sunrise-server.exe --print-provisioned-hash
and stamp BEFORE restarting, or every pass loads stale with an empty catalog.
"""
import struct
import sys


def pe_identity(path):
    data = open(path, "rb").read()
    assert data[:2] == b"MZ", "not a PE"
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[e_lfanew:e_lfanew + 4] == b"PE\0\0", "bad PE signature"
    # FileHeader.TimeDateStamp: COFF header starts at e_lfanew+4, ts at +4.
    ts = struct.unpack_from("<I", data, e_lfanew + 4 + 4)[0]
    # OptionalHeader magic at nt+24; SizeOfImage at optional+56 for PE32+.
    opt = e_lfanew + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    assert magic in (0x10B, 0x20B), f"unknown optional-header magic {magic:#x}"
    size_of_image = struct.unpack_from("<I", data, opt + 56)[0]
    return ts, size_of_image


def main():
    if "--set-eqhash" in sys.argv:
        i = sys.argv.index("--set-eqhash")
        eqhash = int(sys.argv[i + 1], 16)
        # cache_path is bound here too: the eqhash branch returns before the
        # positional parse below, so without this --apply raised NameError.
        cache_path = sys.argv[1]
        data = bytearray(open(cache_path, "rb").read())
        assert data[:8] == b"SUNRISEB", "not a Sunrise cache"
        old_hash = struct.unpack_from("<Q", data, 20)[0]
        struct.pack_into("<Q", data, 20, eqhash)
        print(f"cache : eqHash@20 {old_hash:#018x} -> {eqhash:#018x}")
        if "--apply" in sys.argv:
            open(cache_path, "wb").write(data)
            print(f"wrote {cache_path} (--apply)")
        else:
            print("(dry run - pass --apply)")
        return
    cache_path, exe_path = sys.argv[1], sys.argv[2]
    apply_mode = "--apply" in sys.argv[3:]
    ts, size = pe_identity(exe_path)

    data = bytearray(open(cache_path, "rb").read())
    assert data[:8] == b"SUNRISEB", "not a Sunrise cache"
    old_ts, old_size = struct.unpack_from("<II", data, 12)
    print(f"exe   : imageTimestamp={ts} ({ts:#x}) imageSize={size} ({size:#x})")
    print(f"cache : imageTimestamp={old_ts} ({old_ts:#x}) imageSize={old_size} "
          f"({old_size:#x})")
    if (ts, size) == (old_ts, old_size):
        print("MATCH - no restamp needed")
        return
    print(f"restamp: 12<-{ts} 16<-{size} {'APPLY' if apply_mode else '(dry run)'}")
    if apply_mode:
        struct.pack_into("<II", data, 12, ts, size)
        open(cache_path, "wb").write(data)
        print(f"wrote {cache_path}")
        print("NOTE: payload checksum covers constants+domains only, NOT the "
              "identity fields - no checksum update required")


if __name__ == "__main__":
    main()
