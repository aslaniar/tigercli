#!/usr/bin/env bash
# REGISTRY: caps: log-archive, rig-fetch, dedupe
# log_archive.sh - boot-log capture + backup (2026-08-31, open-items #13).
#
# THE GAP THIS CLOSES: client logs live at fixed paths and are overwritten
# (or truncated) at every client relaunch - so only the current + previous
# boot's logs survive unless someone hand-copies them. This archives ALL
# three logs (mac client, rig client, server) into a timestamped, provenance-
# stamped directory every time it runs.
#
# DEDUPE: each source's sha256 is compared against the newest archived copy
# for that machine; identical = skipped (no archive spam across verdict reruns).
#
# RIG FETCH: best-effort via the boot_verdict.sh ssh pattern (ControlPath
# + scp, falling back to remote `type`). UNREACHABLE = skipped with a loud
# line, never a silent gap.
#
# Usage:
#   bash RE_scripts/log_archive.sh [--label <boot-or-front-id>] [--force]
# Exit: 0 archived (or all-dupes), 1 nothing archived at all, 2 usage.
set -u
cd "$(dirname "$0")/.." || exit 2

LABEL="${LABEL:-}"
args=()
while [ $# -gt 0 ]; do
  case "$1" in
    --label) LABEL="$2"; shift 2;;
    --force) FORCE=1; shift;;
    *) args+=("$1"); shift;;
  esac
done
stamp=$(date +%Y%m%d_%H%M%S)
outdir="RE_output/logs/${stamp}${LABEL:+_$LABEL}"
mkdir -p "$outdir"

# dedupe state: machine=sha of the newest archived copy per machine
# (portable: no associative arrays - macOS bash 3.2)
STATE="RE_output/logs/.last_sha"
touch "$STATE"

fetch_rig() {
  local dest="$1"
  local ssh_opts=(-o ControlPath="$HOME/.ssh/cm-rig" -o ConnectTimeout=8)
  local remote='C:\Users\rasla\Downloads\destiny-preservation\dcv build\bin\x64\Sunrise\logs\sunrise.log'
  scp "${ssh_opts[@]}" "rasla@192.168.1.136:${remote// /\\ }" "$dest" >/dev/null 2>&1 \
    || ssh "${ssh_opts[@]}" "rasla@192.168.1.136" "type \"$remote\"" > "$dest" 2>/dev/null
  [ -s "$dest" ]
}

archive_one() {
  local machine="$1" src="$2"
  [ -f "$src" ] && [ -s "$src" ] || { echo "skip    $machine (no log at $src)"; return 0; }
  local sha size
  sha=$(shasum -a 256 "$src" | cut -d' ' -f1)
  size=$(stat -f %z "$src" 2>/dev/null || stat -c %s "$src")
  if [ "$(sed -n "s/^$machine //p" "$STATE")" = "$sha" ]; then
    echo "dupe    $machine (identical to newest archive)"
    printf '{"machine":"%s","sha256":"%s","dupe":true,"ts":"%s"}\n' \
      "$machine" "$sha" "$stamp" >> "$outdir/manifest.jsonl"
    return 0
  fi
  local dst="$outdir/${machine}_sunrise.log"
  cp "$src" "$dst"
  local lines first_t last_t
  lines=$(wc -l < "$dst" | tr -d ' ')
  first_t=$(grep -aom1 't=[0-9]*' "$dst" | cut -d= -f2)
  last_t=$(grep -ao 't=[0-9]*' "$dst" | tail -1 | cut -d= -f2)
  printf '{"machine":"%s","file":"%s","sha256":"%s","bytes":%s,"lines":%s,"t_first":"%s","t_last":"%s","ts":"%s"}\n' \
    "$machine" "$dst" "$sha" "$size" "$lines" "${first_t:-?}" "${last_t:-?}" "$stamp" >> "$outdir/manifest.jsonl"
  sed -i '' "/^$machine /d" "$STATE" 2>/dev/null || sed -i "/^$machine /d" "$STATE"
  echo "$machine $sha" >> "$STATE"
  echo "saved   $machine  $size bytes, $lines lines  (sha ${sha:0:8})"
}

: > "$outdir/manifest.jsonl"
archive_one mac   "Game/bin/x64/Sunrise/logs/sunrise.log"
archive_one server "RE_output/s1_accept/Sunrise/logs/sunrise.log"

# rig: fetch to scratch, then archive
tmp="${TMPDIR:-/tmp}/rig_log_fetch"; mkdir -p "$tmp"
rig_src="$tmp/rig_sunrise.log"
if fetch_rig "$rig_src"; then
  archive_one rig "$rig_src"
else
  echo "LOUD    rig log UNREACHABLE (ssh control socket down) - recorded, not silent"
  printf '{"machine":"rig","unreachable":true,"ts":"%s"}\n' "$stamp" >> "$outdir/manifest.jsonl"
fi

n=$(ls "$outdir"/*.log 2>/dev/null | wc -l | tr -d ' ')
echo "LIVENESS: archived $n log file(s) -> $outdir"
[ "$n" -eq 0 ] && { echo "DEGENERATE: nothing archived"; exit 1; }
exit 0
