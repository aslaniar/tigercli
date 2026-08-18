#!/usr/bin/env python3
"""Cross-validate the Python decoder against the bundled tigercli binary.

Both implementations decode the same tags; the blobs must be byte-identical
(the validation contract this project passes 6/6 on the Shadowkeep build).

No game-derived bytes ship in this repository: tigercli's decoded outputs are
written to a scratch dir, compared, and can be deleted afterward.

Usage
-----
python tools/validate_cross.py \
    --oodle <oo2core_3_win64.dll> \
    --tigercli tools/tigercli/tigercli.exe \
    --packages <dir> \
    --set 0x377  --files w64_globals_0377_en_2.pkg                 --entries 1,2,63 \
    --set 0x1DA  --files w64_sandbox_01da_en_0.pkg,w64_sandbox_01da_en_1.pkg,w64_sandbox_01da_en_2.pkg \
                 --entries 0,30,62

Exit code 0 = every tag MATCH ed.
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def tag_for(pkg_id: int, entry: int) -> str:
    return f"0x{0x80800000 + (pkg_id << 13) + entry:08X}"


def run_tigercli(tigercli: Path, packages_dir: Path, tags, out_dir: Path):
    import shlex
    cmd = [str(tigercli), str(packages_dir)] + [t[2:] for t in tags] + \
          ["--out", str(out_dir)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr, file=sys.stderr)
        raise SystemExit(f"tigercli failed: {r.returncode}")
    return {t: (out_dir / f"{t[2:]}.bin") for t in tags}, r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oodle", required=True)
    ap.add_argument("--tigercli", default=str(REPO / "tools" / "tigercli" / "tigercli.exe"))
    ap.add_argument("--packages", required=True, help="pkg files directory")
    ap.add_argument("--scratch", help="scratch dir for tigercli outputs "
                                      "(default: a temp dir)")
    ap.add_argument("--set", action="append", required=True, metavar="PKGID",
                    help="pkg set id hex, e.g. 0x377; repeat per set")
    ap.add_argument("--files", action="append", required=True, metavar="CSV",
                    help="comma-separated patch files of the set; one per --set")
    ap.add_argument("--entries", action="append", required=True, metavar="CSV",
                    help="entry indices to compare; one per --set")
    args = ap.parse_args()

    assert len(args.set) == len(args.files) == len(args.entries), \
        "--set/--files/--entries must come in matching triples"
    packages_dir = Path(args.packages)
    scratch = Path(args.scratch) if args.scratch else Path(tempfile.mkdtemp(prefix="tiger_xval_"))
    scratch.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(REPO))
    from tiger_pkg import PkgReader
    from tiger_pkg.decoder import parse_pkg_file

    total_ok = 0
    total = 0
    for set_hex, files_csv, entries_csv in zip(args.set, args.files, args.entries):
        pkg_id = int(set_hex, 16)
        file_paths = [packages_dir / f for f in files_csv.split(",")]
        patched = {parse_pkg_file(p)["patch_id"]: p for p in file_paths}
        entries = [int(x) for x in entries_csv.split(",")]
        tags = [tag_for(pkg_id, e) for e in entries]

        py = PkgReader(patched, args.oodle)
        py_blobs = {e: py.entry_blob(e) for e in entries}

        tcli_bins, tcli_log = run_tigercli(
            Path(args.tigercli), packages_dir, tags, scratch)
        for e in entries:
            tag = tag_for(pkg_id, e)
            expect = tcli_bins[tag].read_bytes() if tcli_bins[tag].exists() else b""
            got = py_blobs[e]
            ok = got == expect
            total += 1
            total_ok += ok
            print(f"{tag} entry {e}: python {len(got)} B vs tigercli "
                  f"{len(expect)} B -> {'MATCH' if ok else 'MISMATCH'}")

    print(f"RESULT: {total_ok}/{total} byte-identical")
    return 0 if total_ok == total else 1


if __name__ == "__main__":
    raise SystemExit(main())