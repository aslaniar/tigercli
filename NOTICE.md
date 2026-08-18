# NOTICE — provenance, license mapping, bundle contents

## What this repository ships (and what it deliberately does not)

| item | status |
|---|---|
| Python decoder (`tiger_pkg/`) | ours — CC0-1.0, regenerated from the project's validated decoder |
| `tools/validate_cross.py` | ours — CC0-1.0 |
| `tools/tigercli/tigercli.exe` | bundled binary — wrapper crate ours, decode core = the **MIT** `tiger-pkg` crate (v0.21.0) |
| `tools/tigercli/src+toml+lock` | wrapper source — MIT (see `LICENSE.tigercli`) |
| `oo2core` (Oodle) DLL | **NOT shipped** — proprietary; the user supplies it from a local Destiny 2 install or the RAD Oodle SDK |
| decoded package blobs | **NOT shipped** — cross-validation generates them on the fly and compares byte-for-byte |

## Integrity

`tools/tigercli/tigercli.exe` SHA-256:

    21729526d2e64571f4a3d898df0a89a94435ff20631700c303eaae1cda781634

Rebuild: `cd tools/tigercli && cargo build --release` (needs the rust toolchain).

## Crypto constants

`tiger_pkg/decoder.py` carries the AES-128-GCM keys and nonce base for the
Destiny 2 **Shadowkeep-era** pkg format. These are the same constants the
tiger-pkg crate's `d2_prebl` module carries for that build family. They are
exposed here so the decoder is self-contained; they only decrypt this build's
client packages.

## Origin

Produced as part of a preservation/RE effort against the Destiny 2 Season-of-
Arrivals client. The game and its content are © Bungie. This repository
contains no game content, only decoders, format documentation, and build
constants.