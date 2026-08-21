"""Live session reads per claims/live-reads-spec.md (game must be running).
SPEC 1A: name-hash registry @0x141FBCD08 (0x40000 window)
SPEC 1B: schema tree re-dump with raw persistence
SPEC 3:  runtime registry DAT_142808A70
SPEC 2A: decoder registry PRE-logout read
Usage: python live_session_reads.py [phase]  (phase=pre runs 1A/1B/3/2A; phase=post runs 2B)
"""
import base64
import ctypes
import json
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dump_sunrise_memory as dsm  # noqa: E402

IB = 0x140000000
OUT = Path(__file__).parent.parent / "RE_output" / "content"


def read(h, rt, size):
    """Chunked tolerant read: returns bytes (short if tail unmapped)."""
    buf = bytearray()
    CH = 0x10000
    for off in range(0, size, CH):
        n = min(CH, size - off)
        try:
            buf += dsm.read_memory(h, rt + off, n)
        except OSError:
            break
    return bytes(buf)


def classify_pairs(blob, exe):
    """Layout-agnostic: for each 0x40 row, the single derefable qword = name ptr."""
    rows = []
    for off in range(0, len(blob) - 0x40, 0x40):
        qw = struct.unpack_from("<8Q", blob, off)
        derefs = [(i, q) for i, q in enumerate(qw)
                  if 0x7FF000000000 <= q < 0x800000000000]
        rows.append(qw)
    return rows


def spec_1a(h, exe, out):
    print("== SPEC 1A: name registry ==")
    rt = exe + (0x141FBCD08 - IB)
    head = dsm.read_memory(h, rt, 0x40)
    q = struct.unpack("<8Q", head)
    print(f"  head: {' '.join(f'0x{x:X}' for x in q)}")
    blob = read(h, rt, 0x40000)
    print(f"  read {len(blob):,} B")
    (OUT / "name_registry_raw.bin").write_bytes(blob)
    entries = []
    # row = 0x40; find name ptrs (runtime derefable) and hash candidates
    names = {}
    for off in range(0, len(blob) - 0x40, 0x40):
        qw = struct.unpack_from("<8Q", blob, off)
        ptrs = [x for x in qw if 0x7FF000000000 <= x < 0x800000000000]
        if not ptrs:
            continue
        name = None
        for p in ptrs:
            try:
                s = dsm.read_memory(h, p, 64)
                z = s.find(b"\x00")
                if 0 < z < 64 and all(32 <= c < 127 for c in s[:z]):
                    name = s[:z].decode("ascii")
                    break
            except OSError:
                continue
        others = [x for x in qw if x not in ptrs and x != 0]
        if name or others:
            entries.append({"row_off": off,
                            "ptrs": [f"0x{x:X}" for x in ptrs],
                            "name": name,
                            "vals": [f"0x{x:X}" for x in others[:6]]})
    print(f"  rows with content: {len(entries)}; named: "
          f"{sum(1 for e in entries if e['name'])}")
    (OUT / "name_registry_live.json").write_text(json.dumps(entries, indent=1))
    # quick look
    for e in entries[:12]:
        print(f"   +0x{e['row_off']:X} {e['name']!r: <40} {e['vals'][:3]}")


def spec_1b(h, exe, out):
    print("== SPEC 1B: schema tree ==")
    root = int.from_bytes(dsm.read_memory(h, exe + (0x142439C70 - IB), 8), "little")
    print(f"  root=0x{root:X}")
    q0 = struct.unpack("<Q", dsm.read_memory(h, root, 8))[0]
    rows_raw = read(h, q0, 0x10000)
    (OUT / "schema_chain_head.bin").write_bytes(rows_raw)
    nodes = {}
    total = 0
    raw_all = bytearray()
    for i in range(0, 0x10000, 0x40):
        c1 = struct.unpack_from("<Q", rows_raw, i + 8)[0]
        if c1 == 0:
            continue
        if not (0x10000 < c1 < 0x7FFFFFFFFFFF):
            continue
        blob = read(h, c1, 0x20000)
        if len(blob) < 32:
            continue
        raw_all += struct.pack("<Q", c1) + struct.pack("<I", len(blob)) + blob
        fields = []
        off = 0
        while off + 32 <= len(blob):
            a = blob[off:off + 16]
            b = blob[off + 16:off + 32]
            if a[3] == 0xC0 and b[2:6] != b"\x00\x00\x00\x00":
                fields.append({"ordinal": struct.unpack_from("<H", b, 0)[0],
                               "bits": struct.unpack_from("<H", a, 0)[0],
                               "hash": f"0x{struct.unpack_from('<Q', a, 4)[0]:016X}",
                               "codec": b[10], "sub": b[11]})
                off += 32
                if len(fields) > 600:
                    break
            else:
                break
        if fields:
            nodes[f"n{i//0x40}_0x{c1:X}"] = fields
            total += len(fields)
    print(f"  nodes: {len(nodes)} fields: {total}")
    (OUT / "schema_tree_live2.json").write_text(json.dumps(nodes, indent=0))
    (OUT / "schema_streams2_raw.bin").write_bytes(bytes(raw_all))
    print(f"  raw streams saved ({len(raw_all):,} B)")


def spec_3(h, exe, out):
    print("== SPEC 3: runtime registry ==")
    reg = read(h, exe + (0x142808A70 - IB), 64 * 0xA8)
    entries = []
    for i in range(64):
        chunk = reg[i * 0xA8:(i + 1) * 0xA8]
        if chunk.count(0) == len(chunk):
            continue
        q0 = int.from_bytes(chunk[0:8], "little")
        entries.append({"i": i, "q0": f"0x{q0:016X}"})
    out["runtime_registry_b64"] = base64.b64encode(reg).decode()
    print(f"  nonempty entries: {len(entries)}")
    (OUT / "runtime_registry_live.json").write_text(
        json.dumps({"b64": out["runtime_registry_b64"],
                    "nonempty": entries}, indent=1))


def spec_2(h, exe, tag):
    print(f"== SPEC 2{tag}: decoder registry ==")
    raw = dsm.read_memory(h, exe + (0x14280E3E0 - IB), 308 * 8)
    vals = [int.from_bytes(raw[i * 8:i * 8 + 8], "little") for i in range(308)]
    live = sum(1 for v in vals if v != 0)
    print(f"  populated: {live}/308")
    (OUT / f"decoder_registry_{tag}.json").write_text(
        json.dumps([f"0x{v:016X}" for v in vals], indent=0))
    return live


def main():
    phase = sys.argv[1] if len(sys.argv) > 1 else "pre"
    pid = dsm.find_pid("destiny2.exe")
    if not pid:
        print("game not running")
        sys.exit(1)
    h = dsm.open_process(pid)
    try:
        exe = dsm.find_module_base(pid, "destiny2.exe")
        print(f"exe base 0x{exe:X}")
        OUT.mkdir(parents=True, exist_ok=True)
        out = {}
        if phase == "pre":
            spec_1a(h, exe, out)
            spec_1b(h, exe, out)
            spec_3(h, exe, out)
            spec_2(h, exe, "pre")
        else:
            live = spec_2(h, exe, "post")
            pre = json.loads((OUT / "decoder_registry_pre.json").read_text())
            pre_live = sum(1 for v in pre if v != "0x0000000000000000")
            print(f"  pre={pre_live} post={live} delta={live - pre_live}")
            post = json.loads((OUT / "decoder_registry_post.json").read_text())
            new_types = [i for i, (a, b) in enumerate(zip(pre, post))
                         if a == "0x0000000000000000" and b != "0x0000000000000000"]
            print(f"  NEW slots: {new_types}")
    finally:
        ctypes.windll.kernel32.CloseHandle(h)


if __name__ == "__main__":
    main()
