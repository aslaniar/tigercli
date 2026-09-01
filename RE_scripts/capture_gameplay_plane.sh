#!/usr/bin/env bash
# THE GAMEPLAY-PLANE INSTRUMENT (p2-143; claim Q, entity-index-allocation-schema.md).
# Usage: bash RE_scripts/capture_gameplay_plane.sh <seconds>
#
# Captures UDP 30976 (gameplay plane) plus the peer-channel ports 3097/3074/3075,
# on EVERY leg that can carry them:
#   en0/en13 : rig client <-> mac server  (WHICH ONE IS LIVE IS NOT A CONSTANT -
#              resolved below via `route -n get`, and BOTH are captured anyway)
#   lo0      : mac client <-> mac server loopback
# A client<->client donation also crosses en0/en13, so the wide net sees it.
#
# LIVENESS (TOOLS.md hard rule, earned 20.166): the "received by filter" counter is
# BOGUS on this mac, so after starting the capture a probe packet is sent to
# 127.0.0.1:3097 and MUST appear in the lo0 pcap - an empty pcap without that probe
# line is not a null result, it is a broken instrument.
#
# Output: RE_output/captures/gameplay_<timestamp>/{en0,en13,lo0}.pcap + flow census.
set -uo pipefail

DUR="${1:?usage: capture_gameplay_plane.sh <seconds>}"
OUT="RE_output/captures/gameplay_$(date +%Y%m%d_%H%M%S)"
FILTER='udp port 30976 or udp port 3097 or udp port 3074 or udp port 3075'
mkdir -p "$OUT"

echo "[gplane] route to the rig (which NIC is live right now):"
route -n get 192.168.1.136 | sed -n 's/.*interface: */  interface: /p' || echo "  (route lookup failed - captures continue on both NICs)"

echo "[gplane] capturing ${DUR}s -> $OUT"
tcpdump -i en0  -s0 -U -w "$OUT/en0.pcap"  "$FILTER" > "$OUT/en0.log"  2>&1 & PID_EN0=$!
tcpdump -i en13 -s0 -U -w "$OUT/en13.pcap" "$FILTER" > "$OUT/en13.log" 2>&1 & PID_EN13=$!
tcpdump -i lo0  -s0 -U -w "$OUT/lo0.pcap"  "$FILTER" > "$OUT/lo0.log"  2>&1 & PID_LO0=$!
trap 'kill $PID_EN0 $PID_EN13 $PID_LO0 2>/dev/null || true' EXIT
sleep 2

# LIVENESS PROBE: one throwaway packet the filter must catch on lo0.
python3 - <<'EOF'
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(b'gplane-liveness-probe', ('127.0.0.1', 3097))
s.close()
EOF
sleep 1
probe_hits="$(tcpdump -r "$OUT/lo0.pcap" 2>/dev/null | grep -c '3097' || true)"
if [[ "$probe_hits" -eq 0 ]]; then
  echo "[gplane] LIVENESS FAIL: probe packet did not reach the lo0 pcap -"
  echo "  every empty result from this capture is VOID. Check interfaces; do not read a null."
else
  echo "[gplane] liveness ok (probe visible in lo0.pcap)"
fi

sleep "$((DUR > 3 ? DUR - 3 : 1))"
kill "$PID_EN0" "$PID_EN13" "$PID_LO0" 2>/dev/null || true
wait "$PID_EN0" 2>/dev/null || true
wait "$PID_EN13" 2>/dev/null || true
wait "$PID_LO0" 2>/dev/null || true
trap - EXIT

echo "[gplane] done. Sizes and packet counts:"
for f in "$OUT"/*.pcap; do
  n="$(tcpdump -r "$f" 2>/dev/null | wc -l | tr -d ' ')"
  printf '  %s: %s packets, %s bytes\n' "$(basename "$f")" "$n" "$(stat -f%z "$f")"
done

echo "[gplane] flow-pair census (top 12 per pcap; classify by pair, the mac-side"
echo "  port is NOT fixed - 20.167: mac:30976<->rig:3097 carried a whole session):"
for f in "$OUT"/en0.pcap "$OUT"/en13.pcap; do
  [[ -s "$f" ]] || continue
  echo "  -- $(basename "$f")"
  tcpdump -r "$f" 2>/dev/null \
    | sed -n 's/.* \(.*\)\.\([0-9]*\) > \(.*\)\.\([0-9]*\):.*/\1:\2 > \3:\4/p' \
    | sort | uniq -c | sort -rn | head -12 | sed 's/^/     /'
done
echo "[gplane] READ-OUT: the pool request is a ~4-byte-payload UDP frame from a"
echo "  CLIENT; the donation is a ~1024-byte-payload UDP frame. Correlate the"
echo "  timestamps with ev=mtrace fn=pool_send_req / pool_recv in the client log."
