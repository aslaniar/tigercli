"""Command-line interface for the Tiger .pkg decoder.

Examples
--------
Decode entry 1 from a single globals package (patch 2):

    python -m tiger_pkg.cli decode \\
        --oodle path\\to\\oo2core_3_win64.dll \\
        --files w64_globals_0377_en_2.pkg \\
        --entry 1 --out entry1.bin

Decode entry 0 from a sandbox set across all three patch files:

    python -m tiger_pkg.cli decode \\
        --oodle path\\to\\oo2core_3_win64.dll \\
        --files w64_sandbox_01da_en_0.pkg,w64_sandbox_01da_en_1.pkg,\\
                    w64_sandbox_01da_en_2.pkg \\
        --entry 0 --out entry0.bin

The entry tag is printed too (the 0x80800000 + set<<13 + entry form other
parts of the game ecosystem address content by).
"""

import argparse
import sys
from pathlib import Path

from .decoder import PkgReader


def parse_args(argv):
    p = argparse.ArgumentParser(prog="tiger_pkg.cli")

    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("decode", help="decode one entry to stdout/stderr")
    d.add_argument("--oodle", required=True, metavar="DLL",
                   help="path to oo2core_3_win64.dll (from a Destiny 2 "
                        "install or the Oodle SDK - not redistributed here)")
    d.add_argument("--files", required=True,
                   help="comma-separated pkg files of the set; pass every "
                        "patch file of the set (the highest patch's tables "
                        "are used as the base)")
    d.add_argument("--entry", type=int, required=True,
                   help="entry index within the pkg set")
    d.add_argument("--out", metavar="FILE", help="write the blob to a file")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    from .decoder import parse_pkg_file
    paths = [Path(f) for f in args.files.split(",")]
    patched = {parse_pkg_file(f)["patch_id"]: f for f in paths}
    reader = PkgReader(patched, args.oodle)
    blob = reader.entry_blob(args.entry)
    tag = reader.entry_tag(args.entry)
    print(f"{tag} entry {args.entry}: {len(blob)} B")
    if args.out:
        Path(args.out).write_bytes(blob)
        print(f"wrote {args.out}")
    else:
        sys.stdout.buffer.write(blob)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())