#!/usr/bin/env bash
# Sync the corrected schema walker to the rig and run the calibration search
# there, so the 5.7 GB dump never moves. Run INTERACTIVELY - it will ask for
# the rig password twice (scp + ssh).
#
#   bash RE_scripts/rig_find.sh [bits] [tolerance]
#
# Default search: fully-expanded type-12 body = 29968 bits +/- 64 (20.57).
set -euo pipefail

RIG=rasla@192.168.1.136
RIG_DIR="C:/Users/rasla/Downloads/destiny-preservation/RE_output"
# cygwin/git-bash style path used by python on the rig
DUMP='C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\dump_healthy_inproc.dmp'

BITS="${1:-29968}"
TOL="${2:-64}"

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== 1. syncing corrected schema_walk.py =="
scp "$here/schema_walk.py" "$here/minidump_reader.py" "$RIG:$RIG_DIR/scripts/"
echo "== 2. hash check both sides (lesson 14) =="
local_hash="$(shasum -a 256 "$here/schema_walk.py" | cut -d' ' -f1)"
remote_hash="$(ssh "$RIG" "certutil -hashfile \"$RIG_DIR\\scripts\\schema_walk.py\" SHA256 | findstr /v :")"
remote_hash="$(echo "$remote_hash" | tr -d ' \r\n' | tr 'A-F' 'a-f')"
echo "local  $local_hash"
echo "remote $remote_hash"
[[ "$local_hash" == "$remote_hash" ]] || { echo "HASH MISMATCH - aborting"; exit 1; }

echo "== 3. registry sanity (--table 24) =="
ssh "$RIG" "python \"$RIG_DIR\\scripts\\schema_walk.py\" \"$DUMP\" --table 24"

echo "== 4. calibration search: $BITS bits +/-$TOL, keys printed per hit =="
exec ssh "$RIG" "python \"$RIG_DIR\\scripts\\schema_walk.py\" \"$DUMP\" --find $BITS $TOL"
