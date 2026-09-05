#!/usr/bin/env bash
# REGISTRY: caps: server-reset, lobby-claims
# Clears the server's in-memory lobby-claim table by restarting the server.
#
# WHY THIS EXISTS: the claim table is what pairs the two clients (FINDINGS 20.101,
# p2(67)), and it is IN-MEMORY with no expiry. A solo control boot claims every
# ordinal for itself, so a two-machine run started afterwards would hand the rig
# room numbers belonging to a session that has already exited - a silently invalid
# test that still produces plausible-looking log lines. Run this between ANY two
# runs, not just after a solo boot.
set -uo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
host="$(/usr/bin/python3 -c "import json;print(json.load(open('$root/RE_output/s1_accept/Sunrise/settings.json'))['server']['bind_address'])" 2>/dev/null)"
[ -n "$host" ] || { echo "ABORT: cannot derive server host from settings.json" >&2; exit 1; }

before="$(curl -s -m 5 "http://$host:8099/lobby" | wc -l | tr -d ' ')"
echo "claims before: $before"

pid="$(pgrep -f 'wine64-preloader .*sunrise-server\.exe' | head -1 || true)"
if [[ -n "$pid" ]]; then
  kill "$pid"
  for _ in $(seq 1 20); do
    pgrep -f 'wine64-preloader .*sunrise-server\.exe' >/dev/null || break
    sleep 0.5
  done
  pgrep -f 'wine64-preloader .*sunrise-server\.exe' >/dev/null \
    && { echo "ABORT: pid $pid did not exit" >&2; exit 1; }
  echo "stopped $pid"
fi

cd "$root" && nohup bash mac-port/launch-server-macos.sh >/dev/null 2>&1 &
for _ in $(seq 1 40); do
  lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep -q ':8099' && break
  sleep 1
done

listeners="$(lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep -cE '8443|30975|8099')"
after="$(curl -s -m 5 "http://$host:8099/lobby" | wc -l | tr -d ' ')"
nat="$(python3 -c "
import socket,struct
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.settimeout(4)
try:
    s.sendto(struct.pack('>HH',1,1),('$host',3074))
    print('ok' if len(s.recvfrom(64)[0])==16 else 'BAD')
except Exception: print('NO REPLY')" 2>/dev/null)"

echo "listeners: $listeners/3   nat: $nat   claims after: $after"
[[ "$listeners" == "3" && "$after" == "0" && "$nat" == "ok" ]] \
  && echo "READY for a two-machine run" \
  || { echo "NOT READY - check the server" >&2; exit 1; }
