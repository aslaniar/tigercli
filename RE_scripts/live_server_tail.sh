#!/usr/bin/env bash
# LIVE SERVER LOG TAIL - the recording view (Mac, bash).
# One window showing the standalone server's log as it happens. The game client
# talks to THIS process; every line below = the live session. Colors mirror the
# old live_server_tail.ps1: magenta = ws_capture (a client request arrived),
# green = queuez family-4/banner publishes, cyan = request/listen/swap stages,
# yellow = result=fail / warn, gray = everything else.
# Usage:  bash RE_scripts/live_server_tail.sh
set -u
LOG="/Users/rubenaslanian/Documents/opencode/sunrise-fork/RE_output/s1_accept/Sunrise/logs/sunrise.log"
R=$'\033[31m'; G=$'\033[32m'; Y=$'\033[33m'; B=$'\033[34m'; M=$'\033[35m'; C=$'\033[36m'
W=$'\033[37m'; D=$'\033[90m'; X=$'\033[0m'; BOLD_G=$'\033[1;32m'

printf '%s\n' "${C}==================================================${X}"
printf '%s\n' "${C}  SUNRISE PRIVATE SERVER - LIVE LOG${X}"
pgrep -f sunrise-server >/dev/null 2>&1 \
    && printf '%s\n' "${G}  server process running${X}" \
    || printf '%s\n' "${R}  WARNING: no sunrise-server process found - start it first!${X}"
printf '%s\n' "${G}  every line below = the live session, unfiltered${X}"
printf '%s\n' "${C}==================================================${X}"

tail -F -n 0 "$LOG" 2>/dev/null | while IFS= read -r line; do
    case "$line" in
        *'ws_capture'*) printf '%s>>> CLIENT REQUEST ARRIVED: %s%s\n' "$M" "$line" "$X" ;;
        *'subclass_select'*|*'subclass_equip'*)
                         printf '%s>>> SERVER PUBLISHED the family-4 answer: %s%s\n' "$BOLD_G" "$line" "$X" ;;
        *'banner_refresh'*|*'family=4'*)
                         printf '%s%s%s\n' "$G" "$line" "$X" ;;
        *'stage=request'*) printf '%s%s%s\n' "$C" "$line" "$X" ;;
        *'result=fail'*|*'warn'*)
                         printf '%s%s%s\n' "$Y" "$line" "$X" ;;
        *'stage=listen'*|*'initialize result=ok'*|*'stage=swap'*)
                         printf '%s%s%s\n' "$C" "$line" "$X" ;;
        *)               printf '%s%s%s\n' "$D" "$line" "$X" ;;
    esac
done