#!/usr/bin/env bash
# Snapshot one boot's evidence into a capture folder: server log + both client
# logs + deployed hashes + relevant settings. Run right after the boot window.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
stamp="$(date +%Y%m%d_%H%M%S)"
dest="$root/RE_output/captures/${stamp}_${1:-boot}"
mkdir -p "$dest"

cp RE_output/s1_accept/Sunrise/logs/sunrise.log "$dest/server_sunrise.log" 2>/dev/null || true
cp Game/bin/x64/Sunrise/logs/sunrise.log "$dest/mac_client_sunrise.log" 2>/dev/null || true
echo "server exe $(shasum -a 256 RE_output/s1_accept/sunrise-server.exe | cut -c1-16)" > "$dest/provenance.txt"
echo "mac dll   $(shasum -a 256 Game/bin/x64/steam_api64.dll | cut -c1-16)" >> "$dest/provenance.txt"
if ssh -o ConnectTimeout=5 -o BatchMode=yes -o ControlPath="$HOME/.ssh/cm-rig" rasla@192.168.1.136 \
     "certutil -hashfile \"C:\Users\rasla\Downloads\destiny-preservation\dcv build\bin\x64\steam_api64.dll\" SHA256" 2>/dev/null | grep -v ':' > /tmp/righash.txt; then
  echo "rig dll   $(tr -d ' \r\n' < /tmp/righash.txt | tr 'A-F' 'a-f' | cut -c1-16) (remote)" >> "$dest/provenance.txt"
fi
grep -E "local_account_key|membership_sweep_pin|membership_peer_retry_cap" RE_output/s1_accept/Sunrise/settings.json >> "$dest/provenance.txt" || true
scp -o ControlPath="$HOME/.ssh/cm-rig" "rasla@192.168.1.136:C:/Users/rasla/Downloads/destiny-preservation/dcv build/bin/x64/Sunrise/logs/sunrise.log" "$dest/rig_client_sunrise.log" 2>/dev/null \
  || echo "(rig log not captured - socket down?)" >> "$dest/provenance.txt"
echo "captured -> $dest"
ls "$dest"
