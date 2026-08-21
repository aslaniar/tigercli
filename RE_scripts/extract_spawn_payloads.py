"""Live key-table read (48 bytes) + full spawn-set payload extraction.

1. Find the kKeyTableText site in the LIVE process (same signature scan we ran on
   the dump), resolve the movups rip-displacement to the runtime key-table address.
2. Read 48 bytes: identityConstant[16], alternateKey[16], nonceBase[16].
3. Derive primary = bootstrapToken + identityConstant (byte-wise, mod 256).
4. For every spawn-set entry: AES-GCM decrypt its blocks, Oodle-decompress via the
   game's own oo2core_3_win64.dll, parse descriptor @8 -> 48-byte spawn points
   (rotation quat, position, name hash), dump to JSON.
"""
import ctypes
import json
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dump_sunrise_memory as dsm  # noqa: E402
from scan_sunrise_patterns import parse_signature  # noqa: E402

IMAGE_BASE_DISK = 0x140000000
KEY_TABLE_SIG = ("0F 10 05 ? ? ? ? 48 8D 64 24 F8 48 89 2C 24 48 8D 2D ? ? ? ? E9")
PKG_DIR = Path(__file__).parent.parent / "dcv build" / "packages"
OUT = Path(__file__).parent.parent / "RE_output" / "content"
ENTRIES = OUT / "class_80809162_entries.json"

# ---- BCrypt AES-GCM via ctypes ----
bcrypt = ctypes.WinDLL("bcrypt")


def aes_gcm_decrypt(key: bytes, nonce: bytes, ct: bytes, tag: bytes) -> bytes | None:
    class BCRYPT_AUTHENTICATED_CIPHER_INFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_ulong), ("dwInfoVersion", ctypes.c_ulong),
            ("pbNonce", ctypes.c_void_p), ("cbNonce", ctypes.c_ulong),
            ("pbAuthData", ctypes.c_void_p), ("cbAuthData", ctypes.c_ulong),
            ("pbTag", ctypes.c_void_p), ("cbTag", ctypes.c_ulong),
            ("pbMacContext", ctypes.c_void_p), ("cbMacContext", ctypes.c_ulong),
            ("cbAAD", ctypes.c_ulong), ("cbData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
        ]

    hAlg = ctypes.c_void_p()
    if bcrypt.BCryptOpenAlgorithmProvider(ctypes.byref(hAlg), "AES", None, 0) != 0:
        return None
    if bcrypt.BCryptSetProperty(hAlg, "ChainingMode", ctypes.c_wchar_p("ChainingModeGCM"),
                                ctypes.sizeof(ctypes.c_wchar * 17), 0) != 0:
        return None
    hKey = ctypes.c_void_p()
    kb = ctypes.create_string_buffer(key)
    if bcrypt.BCryptGenerateSymmetricKey(hAlg, ctypes.byref(hKey), None, 0, kb, len(key), 0) != 0:
        return None
    nb = ctypes.create_string_buffer(nonce)
    tg = ctypes.create_string_buffer(bytes(tag))
    info = BCRYPT_AUTHENTICATED_CIPHER_INFO()
    info.cbSize = ctypes.sizeof(info)
    info.dwInfoVersion = 1
    info.pbNonce = ctypes.cast(nb, ctypes.c_void_p)
    info.cbNonce = len(nonce)
    info.pbTag = ctypes.cast(tg, ctypes.c_void_p)
    info.cbTag = len(tag)
    ctbuf = ctypes.create_string_buffer(bytes(ct))
    ptbuf = ctypes.create_string_buffer(len(ct))
    ptlen = ctypes.c_ulong(0)
    st = bcrypt.BCryptDecrypt(hKey, ctbuf, len(ct), ctypes.byref(info), None, 0,
                              ptbuf, len(ct), ctypes.byref(ptlen), 0)
    ok = st == 0
    bcrypt.BCryptDestroyKey(hKey)
    bcrypt.BCryptCloseAlgorithmProvider(hAlg, 0)
    return ptbuf.raw[:ptlen.value] if ok else None


def oodle_init():
    dll = ctypes.WinDLL(r"C:\Users\rasla\Downloads\destiny-preservation\dcv build\bin\x64\oo2core_3_win64.dll")
    return dll.OodleLZ_Decompress


def oodle_decompress(fn, src: bytes, dst_size: int) -> bytes | None:
    sb = ctypes.create_string_buffer(bytes(src))
    db = ctypes.create_string_buffer(dst_size)
    out = fn(sb, len(src), db, dst_size, None, None, None, None, None, None)
    return db.raw[:out] if out > 0 else None


def parse_header(data: bytes):
    version = struct.unpack_from("<H", data, 0)[0]
    if version != 38:
        return None
    entry_count = struct.unpack_from("<I", data, 0xB4)[0]
    block_count = struct.unpack_from("<I", data, 0xD0)[0]
    entry_table = struct.unpack_from("<I", data, 0x110)[0] + 96
    return entry_count, entry_table, block_count


def leaf_ids(name: str):
    parts = name[:-4].split("_")
    if len(parts) < 4:
        return None
    try:
        return int(parts[-2], 16), int(parts[-1])
    except ValueError:
        return None


def main() -> None:
    pid = dsm.find_pid("destiny2.exe")
    if not pid:
        print("FATAL: game not running")
        sys.exit(1)
    handle = dsm.open_process(pid)
    try:
        exe_base = 0
        for _ in range(120):
            try:
                exe_base = dsm.find_module_base(pid, "destiny2.exe")
            except OSError:
                pass
            if exe_base:
                break
            time.sleep(0.5)
        print(f"exe base: 0x{exe_base:X}")
        # 1. scan live .text#1 AND .text#2 for the key-table signature
        sig = parse_signature(KEY_TABLE_SIG)
        offs = []
        for sec_rva, sec_size in ((0x1000, 0x1B8F600), (0x3CC9000, 0x4D95A00)):
            first = exe_base + sec_rva
            window = dsm.read_memory(handle, first, sec_size)
            pos = 0
            while True:
                pos = window.find(sig[0], pos)
                if pos < 0 or pos + len(sig) > len(window):
                    break
                if all(e is None or window[pos + j] == e for j, e in enumerate(sig)):
                    offs.append((sec_rva + pos, first + pos))
                pos += 1
        print(f"live signature hits: {len(offs)}")
        if not offs:
            print("FATAL: key-table site not found in live image")
            sys.exit(1)
        site_rva, site_rt = offs[0]
        window = dsm.read_memory(handle, site_rt, 16)
        disp = struct.unpack_from("<i", window, 3)[0]
        table_rt = site_rt + 7 + disp
        print(f"site RVA 0x{site_rva:X} runtime 0x{site_rt:X} -> key table 0x{table_rt:X}")
        table = dsm.read_memory(handle, table_rt, 48)
        # KeyTable layout (packages.h): alternateKey[16], identityConstant[16], nonceBase[12]
        alternate = table[0:16]
        identity = table[16:32]
        nonce_base = table[32:44]
        print(f"alternateKey:     {alternate.hex(' ')}")
        print(f"identityConstant: {identity.hex(' ')}")
        print(f"nonceBase:        {nonce_base.hex(' ')}")
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "key_table.bin").write_bytes(table)
    # VERIFIED combo (dotnet AesGcm proof): ASCII token + kt[16:32] as identityConstant
    token = b"2MFioXto7iAUN4Qj"
    primary = bytes((t + c) & 0xFF for t, c in zip(token, identity))
    print(f"primary key:      {primary.hex(' ')}")

    # 2. extraction pass
    entries = json.loads(ENTRIES.read_text())
    print(f"spawn-set entries: {len(entries)}")
    oodle = oodle_init()
    results = []
    pkgs: dict = {}
    decrypted_blocks = 0
    failed = 0
    for n, e in enumerate(entries[:60]):  # first 60 sets as the proof pass
        pkg = e["pkg"]
        if pkg not in pkgs:
            data = (PKG_DIR / pkg).read_bytes()
            h = parse_header(data)
            if not h:
                pkgs[pkg] = None
                continue
            pkgs[pkg] = (data, h)
        if pkgs[pkg] is None:
            continue
        data, (entry_count, entry_table, block_count) = pkgs[pkg]
        block_table = entry_table + entry_count * 16 + 32
        # package nonce per Sunrise package_nonce(): copy base 12B; [0]^=pid>>8; [1]=0xF9; [11]^=pid&0xFF
        pkg_ids = leaf_ids(pkg)
        pkg_id = pkg_ids[0] if pkg_ids else 0
        nonce = bytearray(nonce_base[:12])
        nonce[0] ^= (pkg_id >> 8) & 0xFF
        nonce[1] = 0xF9
        nonce[11] ^= pkg_id & 0xFF
        nonce = bytes(nonce)
        tag = int(e["tag"], 16)
        idx = (tag - 0x80800000) & 0x1FFF
        ref, ti, bi = struct.unpack_from("<IIQ", data, entry_table + idx * 16)
        start_block = bi & 0x3FFF
        start_offset = ((bi >> 14) & 0x3FFF) << 4
        size = bi >> 28
        # gather blocks covering [start_offset, start_offset+size)
        blob = bytearray()
        b = start_block
        while len(blob) < start_offset + size and b < block_count:
            off, bsize, bpatch, flags = struct.unpack_from("<IIHH", data, block_table + b * 48)
            btag = data[block_table + b * 48 + 32:block_table + b * 48 + 48]
            # blocks may live in ANY patch file of the family: keep family id, swap patch suffix
            stem = pkg[:-4]
            sp = stem.split("_")
            block_file = "_".join(sp[:-1] + [str(bpatch)]) + ".pkg"
            bdata = (PKG_DIR / block_file).read_bytes() if block_file != pkg else data
            block = bdata[off:off + bsize]
            if flags & 2:
                block = aes_gcm_decrypt(alternate if flags & 4 else primary, nonce, block, btag)
                if block is None:
                    failed += 1
                    break
                decrypted_blocks += 1
            if flags & 1:
                block = oodle_decompress(oodle, block, 0x40000)
                if block is None:
                    failed += 1
                    break
            blob += block
            b += 1
        else:
            if len(blob) >= start_offset + size:
                payload = bytes(blob[start_offset:start_offset + size])
                results.append({"tag": e["tag"], "pkg": pkg, "size": size,
                                "head": payload[:32].hex(' ')})
        if (n + 1) % 20 == 0:
            print(f"  {n+1}/60 processed, {decrypted_blocks} blocks decrypted, {failed} failed",
                  flush=True)
    print(f"\nproof pass: {len(results)} sets extracted, {decrypted_blocks} blocks decrypted, "
          f"{failed} failures")
    (OUT / "spawn_payloads_proof.json").write_text(json.dumps(results, indent=1))
    for r in results[:6]:
        print(f"  {r['tag']} size={r['size']} head: {r['head']}")


if __name__ == "__main__":
    main()
