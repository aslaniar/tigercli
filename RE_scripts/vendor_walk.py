"""Vendor walk: enumerate the investment root's child slots via the proven pipeline.

The investment root tag is found via the named tag "investment_globals"
(class 0x80805BB1 lives in w64_investment_globals_client). Sunrise's
definition_index_table.h: children are 16B records {tag, ...} after an 8B prefix,
at offset 16 (kChildTableOffset). This script decodes the container and root,
then lists every child slot's tag -> class so the vendor table can be identified.
"""
import struct
import sys
from pathlib import Path

PKG_DIR = Path(__file__).parent.parent / "dcv build" / "packages"
KEY_TABLE = Path(__file__).parent.parent / "RE_output" / "content" / "key_table.bin"

TOKEN = b"2MFioXto7iAUN4Qj"


def load_pkg(pkg_id: int) -> tuple[bytes, dict]:
    newest, best = None, -1
    for f in PKG_DIR.glob("*.pkg"):
        parts = f.stem.split("_")
        try:
            pid = int(parts[-2], 16)
            patch = int(parts[-1])
        except ValueError:
            continue
        if pid == pkg_id and patch > best:
            best, newest = patch, f
    data = newest.read_bytes()
    ec = struct.unpack_from("<I", data, 0xB4)[0]
    et = struct.unpack_from("<I", data, 0x110)[0] + 96
    return data, {"ec": ec, "et": et, "bt": et + ec * 16 + 32, "stem": newest.stem.rsplit("_", 1)[0]}


def decode_tag(tag: int, keys) -> bytes:
    pid = (tag - 0x80800000) >> 13
    idx = tag & 0x1FFF
    data, h = load_pkg(pid)
    ref, ti, bi = struct.unpack_from("<IIQ", data, h["et"] + idx * 16)
    sb = bi & 0x3FFF
    so = ((bi >> 14) & 0x3FFF) << 4
    sz = bi >> 28
    nonce = bytearray(keys["nonce"])
    nonce[0] ^= (pid >> 8) & 0xFF
    nonce[1] = 0xF9
    nonce[11] ^= pid & 0xFF
    nonce = bytes(nonce)
    blob = bytearray()
    b = sb
    while len(blob) < so + sz:
        rec = h["bt"] + b * 48
        off, bsize, bpatch, flags = struct.unpack_from("<IIHH", data, rec)
        btag = data[rec + 32:rec + 48]
        bf = PKG_DIR / (h["stem"] + "_" + str(bpatch) + ".pkg")
        bdata = bf.read_bytes() if bf.name != data and bf.exists() else data
        block = bdata[off:off + bsize]
        if flags & 2:
            block = aes_gcm(keys["alt"] if flags & 4 else keys["primary"], nonce, block, btag)
            if block is None:
                raise RuntimeError(f"auth fail block {b} tag 0x{tag:X}")
        if flags & 1:
            block = oodle(block)
            if block is None:
                raise RuntimeError(f"oodle fail block {b} tag 0x{tag:X}")
        blob += block
        b += 1
    return bytes(blob[so:so + sz])


_bc = None


def init_crypto():
    global _bc
    import ctypes
    kt = KEY_TABLE.read_bytes()
    identity = kt[16:32]
    primary = bytes((t + c) & 0xFF for t, c in zip(TOKEN, identity))
    _bc = {"primary": primary, "alt": kt[0:16], "nonce": kt[32:44]}
    return _bc


def aes_gcm(key, nonce, ct, tag):
    # BCrypt via ctypes (working wrapper pattern from symbolize attempts was broken;
    # use the .NET-free path: call CNG through powershell-free minimal binding)
    # Simplest reliable: use Windows CNG BCryptDecrypt with correct marshaling.
    import ctypes
    import ctypes.wintypes as wt
    b = ctypes.windll.bcrypt

    class INFO(ctypes.Structure):
        _fields_ = [("cbSize", wt.ULONG), ("dwInfoVersion", wt.ULONG),
                    ("pbNonce", ctypes.c_void_p), ("cbNonce", wt.ULONG),
                    ("pbAuthData", ctypes.c_void_p), ("cbAuthData", wt.ULONG),
                    ("pbTag", ctypes.c_void_p), ("cbTag", wt.ULONG),
                    ("pbMacContext", ctypes.c_void_p), ("cbMacContext", wt.ULONG),
                    ("cbAAD", wt.ULONG), ("cbData", wt.ULONG), ("dwFlags", wt.ULONG)]

    hAlg = ctypes.c_void_p()
    if b.BCryptOpenAlgorithmProvider(ctypes.byref(hAlg), "AES", None, 0) != 0:
        return None
    if b.BCryptSetProperty(hAlg, "ChainingMode", ctypes.c_wchar_p("ChainingModeGCM"),
                           ctypes.sizeof(ctypes.c_wchar * 17), 0) != 0:
        return None
    hKey = ctypes.c_void_p()
    kb = ctypes.create_string_buffer(key)
    if b.BCryptGenerateSymmetricKey(hAlg, ctypes.byref(hKey), None, 0, kb, len(key), 0) != 0:
        return None
    nb = ctypes.create_string_buffer(nonce)
    tg = ctypes.create_string_buffer(bytes(tag))
    info = INFO()
    info.cbSize = ctypes.sizeof(INFO)
    info.dwInfoVersion = 1
    info.pbNonce = ctypes.cast(nb, ctypes.c_void_p)
    info.cbNonce = len(nonce)
    info.pbTag = ctypes.cast(tg, ctypes.c_void_p)
    info.cbTag = 16
    ctb = ctypes.create_string_buffer(bytes(ct))
    ptb = ctypes.create_string_buffer(len(ct))
    produced = ctypes.c_ulong(0)
    st = b.BCryptDecrypt(hKey, ctb, len(ct), ctypes.byref(info), None, 0,
                         ptb, len(ct), ctypes.byref(produced), 0)
    b.BCryptDestroyKey(hKey)
    b.BCryptCloseAlgorithmProvider(hAlg, 0)
    if st != 0:
        return None
    return ptb.raw[:produced.value]


_oodle_fn = None


def oodle(src: bytes):
    global _oodle_fn
    import ctypes
    if _oodle_fn is None:
        dll = ctypes.WinDLL(r"C:\Users\rasla\Downloads\destiny-preservation\dcv build"
                            r"\bin\x64\oo2core_3_win64.dll")
        _oodle_fn = dll.OodleLZ_Decompress
    sb = ctypes.create_string_buffer(bytes(src))
    db = ctypes.create_string_buffer(0x40000)
    out = _oodle_fn(sb, len(src), db, 0x40000, None, None, None, None, None, None)
    return db.raw[:out] if out > 0 else None


def main() -> None:
    keys = init_crypto()
    # find investment_globals container tag: class 0x80805BB1 in w64_investment_globals_client
    # locate the package by glob
    for f in PKG_DIR.glob("w64_investment_globals_client_*.pkg"):
        parts = f.stem.split("_")
        pid = int(parts[-2], 16)
        data, h = load_pkg(pid)
        for i in range(h["ec"]):
            ref = struct.unpack_from("<I", data, h["et"] + i * 16)[0]
            if ref == 0x80805BB1:
                tag = 0x80800000 + (pid << 13) + i
                print(f"investment_globals container tag: 0x{tag:08X} (pkg {f.name})")
                blob = decode_tag(tag, keys)
                print(f"container blob: {len(blob)} B")
                # children: 16B records {u32 tag, 12B}, after 8B prefix at +16
                # First child = investment root (kInvestmentRootChild = 0)
                n_children = (len(blob) - 16) // 16
                print(f"declared children space: {n_children}")
                root_tag = struct.unpack_from("<I", blob, 16)[0]
                print(f"child[0] (investment root) tag: 0x{root_tag:08X}")
                root_blob = decode_tag(root_tag, keys)
                print(f"root blob: {len(root_blob)} B")
                # slots: 16B records after 8B prefix at +8
                slots = (len(root_blob) - 8) // 16
                print(f"root slots: {slots}")
                # resolve each slot's tag -> class for identification
                for s in range(min(slots, 120)):
                    stag = struct.unpack_from("<I", root_blob, 8 + s * 16)[0]
                    if stag == 0:
                        continue
                    try:
                        pid2 = (stag - 0x80800000) >> 13
                        d2, h2 = load_pkg(pid2)
                        idx2 = stag & 0x1FFF
                        cls = struct.unpack_from("<I", d2, h2["et"] + idx2 * 16)[0]
                        print(f"  slot[{s:3d}] tag=0x{stag:08X} class=0x{cls:08X}")
                    except Exception as e:
                        print(f"  slot[{s:3d}] tag=0x{stag:08X} (unresolved: {e})")
                break
        break


if __name__ == "__main__":
    main()
