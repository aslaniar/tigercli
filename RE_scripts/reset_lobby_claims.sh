#!/usr/bin/env bash
# REGISTRY: caps: server-reset, lobby-claims, idempotent, idempotent
# Clears the server's in-memory lobby-claim table by restarting the server.
#
# WHY THIS EXISTS: the claim table is what pairs the two clients (FINDINGS 20.101,
# p2(67)), and it is IN-MEMORY with no expiry. A solo control boot claims every
# ordinal for itself, so a two-machine run started afterwards would hand the rig
# room numbers belonging to a session that has already exited - a silently invalid
# test that still produces plausible-looking log lines. Run this between ANY two
# runs, not just after a solo boot.
#
# 2026-09-05 (instrumentation DEFECT 7 + 08-30 A3):
#   - the readiness check compared a COUNT of listeners (== 3) but port 30975
#     legitimately binds twice, so a HEALTHY server reported 4 and failed the
#     check EVERY run - "an alarm that is always wrong trains its reader to
#     skip it". Fixed: compare the SET of required ports (each present?),
#     never a count.
#   - IDEMPOTENCE: if the server is already running with claims == 0 and the
#     full port set bound, this is a NO-OP that says so - the 08-30 A3 class
#     (a reset invoked while the user's clients were mid-launch) cannot
#     happen by reflex. --force overrides (a deliberate restart).
#   - --check: run every READ-ONLY probe (state, claims, port set, nat) and
#     print what the real run WOULD do; never kills anything.
set -uo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
host="$(/usr/bin/python3 -c "import json;print(json.load(open('$root/RE_output/s1_accept/Sunrise/settings.json'))['server']['bind_address'])" 2>/dev/null)"
[ -n "$host" ] || { echo "ABORT: cannot derive server host from settings.json" >&2; exit 1; }

mode=real
[ "${1:-}" = "--check" ] && mode=check
[ "${1:-}" = "--force" ] && mode=force

server_pid="$(pgrep -f 'wine64-preloader .*sunrise-server\.exe' | head -1 || true)"
before="$(curl -s -m 5 "http://$host:8099/lobby" | wc -l | tr -d ' ')"
echo "server pid: ${server_pid:-none}   claims before: $before"

# --- the port SET (DEFECT 7: a count cannot express "30975 binds twice") ---
REQUIRED_PORTS="8443 30975 8099"
missing=""
for p in $REQUIRED_PORTS; do
  if ! lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep -q ":${p}[[:space:]]"; then
    missing="$missing $p"
  fi
done
if [ -z "$missing" ]; then
  echo "port set: complete ($(echo $REQUIRED_PORTS))"
else
  echo "port set: MISSING:$missing"
fi

if [ "$mode" = "check" ]; then
  if [ -n "$server_pid" ] && [ "$before" = "0" ] && [ -z "$missing" ]; then
    echo "CHECK: a real run would NO-OP (server up, claims=0, port set complete)."
  else
    echo "CHECK: a real run would RESTART (pid ${server_pid:-none} -> relaunch) then verify."
  fi
  echo "CHECK: no state was changed (read-only)."
  exit 0
fi

if [ -n "$server_pid" ] && [ "$before" = "0" ] && [ -z "$missing" ] && [ "$mode" != "force" ]; then
  echo "ALREADY CLEAR - claims=0, server healthy, port set complete."
  echo "NO-OP: not restarting (the 08-30 A3 class: this step may already have"
  echo "been done - if the user said 'launching', the reset likely happened)."
  echo "Use --force to restart anyway."
  exit 0
fi

if [ -n "$server_pid" ]; then
  kill "$server_pid"
  for _ in $(seq 1 20); do
    pgrep -f 'wine64-preloader .*sunrise-server\.exe' >/dev/null || break
    sleep 0.5
  done
  pgrep -f 'wine64-preloader .*sunrise-server\.exe' >/dev/null \
    && { echo "ABORT: pid $server_pid did not exit" >&2; exit 1; }
  echo "stopped $server_pid"
fi

cd "$root" && nohup bash mac-port/launch-server-macos.sh >/dev/null 2>&1 &
for _ in $(seq 1 40); do
  lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep -q ':8099' && break
  sleep 1
done

missing_after=""
for p in $REQUIRED_PORTS; do
  if ! lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep -q ":${p}[[:space:]]"; then
    missing_after="$missing_after $p"
  fi
done
after="$(curl -s -m 5 "http://$host:8099/lobby" | wc -l | tr -d ' ')"
nat="$(/usr/bin/python3 -c "
import socket,struct
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.settimeout(4)
try:
    s.sendto(struct.pack('>HH',1,1),('$host',3074))
    print('ok' if len(s.recvfrom(64)[0])==16 else 'BAD')
except Exception: print('NO REPLY')" 2>/dev/null)"

echo "port set after: $( [ -z "$missing_after" ] && echo complete || echo "MISSING:$missing_after" )   nat: $nat   claims after: $after"
[ -z "$missing_after" ] && [ "$after" = "0" ] && [ "$nat" = "ok" ] \
  && echo "READY for a two-machine run" \
  || { echo "NOT READY - check the server" >&2; exit 1; }
