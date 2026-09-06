#!/usr/bin/env python3
# REGISTRY: caps: needle-search, dump-sweep, static-const-scan
"""needle_scan.py - search a binary for byte needles: a loaded minidump, a
static PE, or any file. Also the STATIC CONSTANT SCANNER (TOOLING_AUDIT M2:
"find every site referencing constant X in .text" was a recurring need with
no tool - the 0x2AC0 stride scan that broke the 20.298-20.301 analysis open
was 20 lines of throwaway python).

WHY THIS WAS REWRITTEN (T1.2): the old version was hardcoded to a machine
that does not exist (C:\\Users\\rasla\\...dump_healthy_inproc.dmp) and was
registered in TOOLS.md as if general. It cost a dead end mid-analysis; the
hand-rolled replacement worked in one pass and is promoted here.

Usage:
  needle_scan.py --pe [PATH] <hex-u32> [more...]     static PE .text scan
  needle_scan.py --const [PATH] <hex-const> [more]   STATIC CONSTANT SITES:
                                                     every .text offset whose
                                                     bytes contain the
                                                     little-endian constant
                                                     (the "who references
                                                     stride X" question)
  needle_scan.py --dump <dmp> <hex-u32> [more...]    minidump search (any dump)
  needle_scan.py --any <file> <hex|needle-hex>       raw file byte search
  needle_scan.py --selftest

Defaults: --pe/--const without a PATH use RE_output/destiny2_unpacked_full.exe.
Needles are u32 little-endian unless given as `hex:<rawhex>` (raw bytes).
Exit: 0 hits found; 1 no hits (a result, not silence - run loud); 2 usage.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PE = ROOT / "RE_output" / "destiny2_unpacked_full.exe"


def parse_needle(tok):
    """`0x...` -> u32 LE; `hex:...` -> raw bytes."""
    if tok.lower().startswith("hex:"):
        return bytes.fromhex(tok[4:])
    v = int(tok, 16)
    if v > 0xFFFFFFFF:
        print(f"needle {tok} exceeds u32 - use hex:<rawbytes> form", file=sys.stderr)
        sys.exit(2)
    return struct.pack("<I", v)


def scan_bytes(data, base, needles, label, ctx_before=12, ctx_after=16, cap=5000):
    """Shared scan: report every hit VA/offset + context. Returns hit count."""
    hits = 0
    for ni, needle in enumerate(needles):
        pos = 0
        while True:
            p = data.find(needle, pos)
            if p < 0:
                break
            pos = p + 1
            hits += 1
            if hits <= cap:
                ctx = data[max(0, p - ctx_before):p + ctx_after].hex()
                print(f"  {label} needle#{ni}: @ {base + p:#x}  ctx {ctx}")
    return hits


def minidump_scan(dump_path, needles):
    dump_path = str(dump_path)
    sys_path_note = False
    try:
        from minidump_reader import Minidump  # repo/adjacent module
    except ImportError:
        # the rig-side location the old version hardcoded; try repo-relative
        sys.path.insert(0, str(ROOT / "RE_scripts"))
        try:
            from minidump_reader import Minidump
        except ImportError:
            print("minidump_reader module not available on this machine - "
                  "dump mode is rig-side (or place minidump_reader.py in RE_scripts)",
                  file=sys.stderr)
            return None
    md = Minidump(dump_path)
    hits = 0
    for start, size, offset in md.ranges:
        data = md._read(offset, size)
        hits += scan_bytes(data, start, needles, "dump", cap=5000)
    return hits


def pe_sections(pe):
    for name, vaddr, vsize, rawptr, rawsize in pe.sections:
        if name == ".text":
            data = pe.data[rawptr:rawptr + rawsize]
            yield name, pe.imagebase + vaddr, data


def static_pe_scan(pe_path, needles, const_mode=False):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from pe_reader import PE
    pe = PE(str(pe_path))
    hits = 0
    for name, base, data in pe_sections(pe):
        for ni, needle in enumerate(needles):
            pos = 0
            while True:
                p = data.find(needle, pos)
                if p < 0:
                    break
                pos = p + 1
                hits += 1
                if hits <= 5000:
                    ctx = data[max(0, p - 12):p + 16].hex()
                    print(f"  .text @{base + p:#x}  needle#{ni}  ctx {ctx}")
    return hits


def selftest():
    """Positive: a constant that MUST be in .text (the 0x2AC0 stride, the
    20.298-20.301 oracle) and a byte needle with a known raw form. Negative:
    a constant that must not exist. Fixture bytes test the parser."""
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print(f"  {'PASS' if cond else 'FAIL'} {name:<52s} {detail}")
        if not cond:
            ok = False

    check("u32 parse 0x2AC0 -> LE bytes", parse_needle("0x2AC0") == b"\xc0\x2a\x00\x00")
    check("raw parse hex:caffeedead -> bytes", parse_needle("hex:caffeedead") == bytes.fromhex("caffeedead"))

    if not DEFAULT_PE.exists():
        print(f"  SKIP live arms (no {DEFAULT_PE})")
    else:
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            n = static_pe_scan(DEFAULT_PE, [struct.pack("<I", 0x2AC0)])
        check("live: stride 0x2AC0 has >=1 .text site", n >= 1, f"{n} hits")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            n2 = static_pe_scan(DEFAULT_PE, [struct.pack("<I", 0x9ABCDEF0)])
        # NOTE: the negative oracle is a VERIFIED-absent constant. The first
        # choice (0xDEADBEEF) exists in .text 4 times - the negative arm
        # caught its own bad fixture.
        check("live: verified-absent constant -> 0 hits (loud)", n2 == 0, f"{n2} hits")
    print("SELFTEST", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    mode, pe_path = None, DEFAULT_PE
    idx = 0
    if argv[0] == "--selftest":
        return selftest()
    if argv[0] in ("--pe", "--const", "--dump", "--any"):
        mode = argv[0][2:]
        idx = 1
        # an existing file right after the flag is the target; otherwise the
        # default target applies (and --dump REQUIRES an explicit path)
        if idx < len(argv) and Path(argv[idx]).is_file():
            pe_path = Path(argv[idx])
            idx += 1
        elif mode == "dump":
            print("--dump requires a dump path", file=sys.stderr)
            return 2
    needles = [parse_needle(t) for t in argv[idx:] if not t.startswith("--")]
    if not needles:
        print(__doc__)
        return 2
    if mode in ("pe", "const"):
        if not Path(pe_path).exists():
            print(f"target missing: {pe_path}", file=sys.stderr)
            return 2
        n = static_pe_scan(Path(pe_path), needles)
        print(f"-- {n} hit(s) in {Path(pe_path).name} "
              f"({'constant sites' if mode == 'const' else 'byte needles'})")
        return 0 if n else 1
    if mode == "dump":
        n = minidump_scan(pe_path, needles)
        if n is None:
            return 2
        print(f"-- {n} hit(s) in dump {Path(pe_path).name}")
        return 0 if n else 1
    if mode == "any":
        p = pe_path
        if not p.exists():
            print(f"target missing: {p}", file=sys.stderr)
            return 2
        data = p.read_bytes()
        n = scan_bytes(data, 0, needles, "file")
        print(f"-- {n} hit(s) in {p.name}")
        return 0 if n else 1
    # no mode: default to the static PE (the common case)
    if not DEFAULT_PE.exists():
        print(f"no default PE at {DEFAULT_PE} - pass --pe <path>", file=sys.stderr)
        return 2
    n = static_pe_scan(DEFAULT_PE, needles)
    print(f"-- {n} hit(s) in {DEFAULT_PE.name} (default target)")
    return 0 if n else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
