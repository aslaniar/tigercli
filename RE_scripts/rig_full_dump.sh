#!/usr/bin/env bash
# rig_full_dump.sh - take a FULL user-mode dump of the rig's live destiny2 process and
# pull it to RE_output/dumps/<label>/. Run it WHILE the scenario you want to interrogate
# is on screen: a dump only contains states the process actually reached, so a dump taken
# solo or at the main menu cannot answer a question about a peer (FINDINGS 20.219/20.220).
#
# Uses dbghelp MiniDumpWriteDump via RE_scripts/full_dump.py run ON the rig
# (the comsvcs.dll rundll32 route FAILS on this rig - HANDOFF_2026-08-31_GATE-FEEDERS;
# do not reintroduce it). "full memory" is required: a triage minidump omits the heap,
# and femu would report holes exactly where the manager and roster pages should be.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RIG="rasla@192.168.1.136"
CM="$HOME/.ssh/cm-rig"
label="${1:?usage: rig_full_dump.sh <label>   (e.g. p2-146-paired-tower)}"
out="$root/RE_output/dumps/$label"; mkdir -p "$out"
remote='C:\Users\rasla\dump_'"$label"'.dmp'

echo "== locating destiny2 on the rig =="
pid="$(ssh -o ControlPath="$CM" -o BatchMode=yes "$RIG" \
  'powershell -NoProfile -Command "(Get-Process destiny2 -ErrorAction SilentlyContinue | Select-Object -First 1).Id"' | tr -d "\r\n ")"
[[ -n "$pid" ]] || { echo "ABORT: destiny2 is not running on the rig"; exit 1; }
echo "   pid $pid"

echo "== writing FULL dump on the rig via dbghelp MiniDumpWriteDump (game pauses during this) =="
ssh -o ControlPath="$CM" -o BatchMode=yes "$RIG" \
  "python C:\\Users\\rasla\\Downloads\\destiny-preservation\\RE_scripts\\full_dump.py $remote"

echo "== pulling (tar-over-ssh, NEVER scp/sftp - ENVIRONMENTS 'RIG<->MAC FILE TRANSFER') =="
ssh -S "$CM" "$RIG" "tar cf - -C C:/Users/rasla dump_${label}.dmp" > "$out/dump_${label}.dmp.tar"
echo "== SHA256 both ends (FIXED 2026-09-07, the 20.330 defect): the pulled file "
echo "   is a TAR STREAM, so the hash is taken on the EXTRACTED inner file - "
echo "   the raw .dmp - matching the rig's certutil on the raw file. The old "
echo "   compare (tar stream vs raw file) structurally mismatched and aborted "
echo "   every intact pull (p2-205 was verified manually by extraction). =="
mkdir -p "$out/extract"
tar -xf "$out/dump_${label}.dmp.tar" -C "$out/extract" \
  && mv "$out/extract/dump_${label}.dmp" "$out/dump_${label}.dmp" \
  && rmdir "$out/extract" 2>/dev/null || true
rm -f "$out/dump_${label}.dmp.tar"
rhash="$(ssh -o ControlPath="$CM" -o BatchMode=yes "$RIG" "certutil -hashfile C:\\Users\\rasla\\dump_${label}.dmp SHA256" | tr -d '\r ' | sed -n '2p')"
lhash="$(shasum -a 256 "$out/dump_${label}.dmp" | cut -d' ' -f1)"
echo "   rig: $rhash"
echo "   mac: $lhash"
[[ -n "$rhash" && "$rhash" == "$lhash" ]] || { echo "ABORT: SHA256 MISMATCH - the transfer is NOT evidence"; exit 1; }
ssh -o ControlPath="$CM" -o BatchMode=yes "$RIG" "cmd /c del C:\\Users\\rasla\\dump_${label}.dmp" || true
ls -la "$out"
echo "== provenance (U14: assert what this dump IS) =="
{ echo "label: $label"; echo "taken: $(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo "rig pid: $pid";
  echo "client dll: $(shasum -a 256 "$root/Game/bin/x64/steam_api64.dll" | cut -c1-16) (mac copy; rig deployed identical)";
  echo "scenario: FILL THIS IN - a dump is scenario-scoped, not time-scoped."; } > "$out/PROVENANCE.txt"
cat "$out/PROVENANCE.txt"
