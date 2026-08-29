#!/usr/bin/env bash
# THE BAP-WIRE INSTRUMENT (FINDINGS 20.145) - capture tcp/30975 on both interfaces.
# Usage: bash RE_scripts/capture_bap30975.sh <seconds>
#   en0 : rig client <-> mac server (LAN leg)
#   lo0 : mac client <-> mac server (loopback leg - en0 never sees 127.0.0.1)
# Output: RE_output/captures/bap30975_<timestamp>/{bap_en0.pcap,bap_lo0.pcap}
# No sudo needed (user is in access_bpf). Run BEFORE forming the client-hosted
# fireteam; the MAC client should host (a rig-hosted client<->client stream does
# not cross the mac - see TOOLS.md row).
set -euo pipefail

DUR="${1:?usage: capture_bap30975.sh <seconds>}"
OUT="RE_output/captures/bap30975_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT"

echo "[bap30975] capturing ${DUR}s -> $OUT (en0 + lo0, filter: tcp port 30975)"
tcpdump -i en0 -s0 -U -w "$OUT/bap_en0.pcap" 'tcp port 30975' > "$OUT/en0.log" 2>&1 &
PID_EN0=$!
tcpdump -i lo0 -s0 -U -w "$OUT/bap_lo0.pcap" 'tcp port 30975' > "$OUT/lo0.log" 2>&1 &
PID_LO0=$!

trap 'kill "$PID_EN0" "$PID_LO0" 2>/dev/null || true' EXIT
sleep "$DUR"
kill "$PID_EN0" "$PID_LO0" 2>/dev/null || true
wait "$PID_EN0" 2>/dev/null || true
wait "$PID_LO0" 2>/dev/null || true
trap - EXIT

echo "[bap30975] done. Sizes:"
ls -l "$OUT"/*.pcap
echo "[bap30975] quick packet counts:"
for f in "$OUT"/*.pcap; do
  printf '  %s: ' "$f"
  tcpdump -r "$f" 2>/dev/null | wc -l
done
echo "[bap30975] REMINDERS: (1) grep client logs with grep -a for 'pc=' membership"
echo "  dump lines; the host client's self-row should read pc=1. (2) Bodies may be"
echo "  session-sealed - framing/sizes are still readable; decode reference is the"
echo "  fork's bap_listener framing (FINDINGS 20.145)."
