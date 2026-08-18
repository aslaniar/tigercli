# d2-tiger-pkg-decoder — pure-Python Tiger `.pkg` decoder for Destiny 2 client content

A self-contained Python implementation of the Destiny 2 client's package
decryption/decompression path: **AES-128-GCM block decryption + Oodle
decompression**, with no C++/Rust build step.

The pitch: the existing reference tool (tigercli, bundled here) only resolves
entries from a package set's **final** patch file. This decoder reads **any
entry from any patch file** of a set — which is what you need when a content
block lives in an earlier patch of the set (very common in real installs).

Validated **6/6 byte-identical** against tigercli outputs on the
Shadowkeep-era build.

## What it does

- Parses the v38 pkg header + entry/block tables (`parse_pkg_file`)
- Derives the per-package GCM nonce from the fixed base + `pkg_id`
  (`make_nonce`)
- Decrypts blocks (key selected by block flags: `0x2` encrypted, `0x4`
  alternate key) and decompresses them (Oodle via ctypes) (`PkgReader`)
- Assembles full entry blobs across block boundaries — including blocks that
  live in a *different* patch file of the same set
- Derives the content **tag** each entry is addressed by:
  `0x80800000 + (pkg_id << 13) + entry_index`

## Requirements

- Python 3.8+ and `cryptography` (`pip install cryptography`)
- `oo2core_3_win64.dll` (the Oodle DLL) — **not shipped here**: it is
  proprietary. Take it from a local Destiny 2 install (`bin/x64/`) or the RAD
  Oodle SDK, and pass its path via `--oodle`.

## Quick start

Decode entry 1 of a globals set to a file:

```bash
python -m tiger_pkg.cli decode \
    --oodle <path>/oo2core_3_win64.dll \
    --files w64_globals_0377_en_2.pkg \
    --entry 1 --out entry1.bin
```

Decode entry 0 of a three-patch sandbox set (blocks spread across patches —
the case tigercli misses):

```bash
python -m tiger_pkg.cli decode \
    --oodle <path>/oo2core_3_win64.dll \
    --files w64_sandbox_01da_en_0.pkg,w64_sandbox_01da_en_1.pkg,w64_sandbox_01da_en_2.pkg \
    --entry 0 --out entry0.bin
```

As a library:

```python
from pathlib import Path
from tiger_pkg import PkgReader
from tiger_pkg.decoder import parse_pkg_file

files = {p: Path(p) for p in ("w64_sandbox_01da_en_0.pkg",
                              "w64_sandbox_01da_en_1.pkg",
                              "w64_sandbox_01da_en_2.pkg")}
patched = {parse_pkg_file(p)["patch_id"]: p for p in files.values()}
reader = PkgReader(patched, "path/to/oo2core_3_win64.dll")
blob = reader.entry_blob(0)          # decoded content
tag  = reader.entry_tag(0)           # "0x8080D0080" etc.
```

## Format notes (format documentation)

- Header: v38; **pkg_id = u16 @0x04** — a known trap: reading @0x02 gets the
  platform field instead (an off-by-2 bug found in another pkg_reader).
- Entry table: `{reference u32, type_info u32, block_info u64}` — 16 B each;
  `file_type = (type_info >> 9) & 0x7F`, `subtype = (type_info >> 6) & 0x7`;
  `start_block = block_info & 0x3FFF`, `start_offset = ((block_info >> 14)
  & 0x3FFF) << 4`, `file_size = block_info >> 28`.
- Block table: 48 B per block `{offset u32, size u32, patch_id u16, flags u16,
  GCM tag @+32}`. Flag bits: `0x1` compressed, `0x2` encrypted, `0x4`
  alternate cipher key.
- GCM: 12-byte nonce from the fixed base (n[1] = 0xF9 for the Shadowkeep
  family), tag appended to the ciphertext, empty AAD.
- Oodle: this build's OodleLZ_Decompress returns 0 on success; the block
  occupies the full 0x40000 block space.

## Cross-validation (the bundled reference)

This repo bundles the private `tigercli` build (MIT, see NOTICE) so the Python
decoder can be proven against an independent implementation — no game-derived
bytes are shipped; both decoders run locally and the outputs are compared
byte-for-byte:

```bash
python tools/validate_cross.py \
    --oodle <path>/oo2core_3_win64.dll \
    --tigercli tools/tigercli/tigercli.exe \
    --packages <dir-with-pkg-files> \
    --set 0x377 --files w64_globals_0377_en_2.pkg --entries 1,2,63 \
    --set 0x1DA --files w64_sandbox_01da_en_0.pkg,w64_sandbox_01da_en_1.pkg,w64_sandbox_01da_en_2.pkg --entries 0,30,62
```

Expected: `RESULT: 6/6 byte-identical`.

## Repository layout

| path | contents |
|---|---|
| `tiger_pkg/decoder.py` | the decoder (library) |
| `tiger_pkg/cli.py` | `python -m tiger_pkg.cli` command line |
| `tools/validate_cross.py` | python-vs-tigercli byte comparison |
| `tools/tigercli/` | bundled reference binary + wrapper source (MIT) |
| `NOTICE.md` | provenance, license mapping, SHA-256, what is **not** shipped |

## License

- `tiger_pkg/` + `tools/validate_cross.py`: **CC0-1.0** (`LICENSE`)
- `tools/tigercli/`: **MIT** (`LICENSE.tigercli`; decode core = the MIT
  `tiger-pkg` crate, github.com/v4nguard/tiger-pkg)
- The game and its content are © Bungie. This repository ships no game
  content — only decoders, format documentation, and build constants.