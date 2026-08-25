#!/usr/bin/env bash
# Deploy one freshly built client DLL beside the Mac game install, with provenance asserted.
#
# The incident of 2026-08-25 (loop 1) was two boots spent testing a binary that was never
# deployed. This script refuses to report success unless:
#   - the deployed file's hash EQUALS the build output's hash, checked after the copy;
#   - every instrument literal named on the command line is present IN the deployed file.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
built="$root/RE_build/Sunrise-fork-inventory/build/steam_api64.dll"
live="$root/Game/bin/x64/steam_api64.dll"

die() { echo "ABORT: $*" >&2; exit 1; }

[[ -f "$built" ]] || die "no build output at $built"
[[ -f "$live" ]] || die "no live DLL at $live"

stamp="$(date +%Y%m%d_%H%M%S)"
cp -p "$live" "$live.bak_p2d7_$stamp" || die "backup failed"
echo "backed up $(basename "$live").bak_p2d7_$stamp"

cp "$built" "$live" || die "deploy copy failed"

built_hash="$(shasum -a 256 "$built" | cut -d' ' -f1)"
live_hash="$(shasum -a 256 "$live" | cut -d' ' -f1)"
[[ "$built_hash" == "$live_hash" ]] || die "deployed DLL != build output ($live_hash vs $built_hash)"
echo "hash match ${live_hash:0:16}"

for literal in "${@:2}"; do
  count="$(grep -ac "$literal" "$live" || true)"
  [[ "$count" -ge 1 ]] || die "instrument literal '$literal' NOT present in deployed $live"
  echo "literal ok ($count): $literal"
done

echo "deployed $(basename "$live") ${live_hash:0:16}"
