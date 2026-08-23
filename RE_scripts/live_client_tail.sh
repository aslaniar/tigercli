#!/usr/bin/env bash
# LIVE CLIENT LOG TAIL - the recording's second window (Mac, bash).
# The GAME's own trace, filtered DOWN: everything except the ev=item_gate flood
# (65k+ lines a boot; see RE_output/claims/lane_cockpit.md). Colors:
#   cyan = handle_message (server pushes), green = queuez (server delivers),
#   magenta = retail (Bungie's narration), blue = bootflow, yellow = warn/fail,
#   gray = everything else.
# Start this AFTER the game launches (the game rotates its log at each boot;
# tail -F follows the in-place name so a rotation is picked up, but lines
# written before this starts are skipped).
# Usage:  bash RE_scripts/live_client_tail.sh
set -u
LOG="/Users/rubenaslanian/Documents/opencode/sunrise-fork/Game/bin/x64/Sunrise/logs/sunrise.log"
R=$'\033[31m'; G=$'\033[32m'; Y=$'\033[33m'; B=$'\033[34m'; M=$'\033[35m'; C=$'\033[36m'
W=$'\033[37m'; D=$'\033[90m'; X=$'\033[0m'

printf '%s\n' "${C}==================================================${X}"
printf '%s\n' "${C}  DESTINY 2 CLIENT - LIVE TRACE (item_gate flood suppressed)${X}"
printf '%s\n' "${G}  start this AFTER the game launches${X}"
printf '%s\n' "${C}==================================================${X}"

tail -F -n 0 "$LOG" 2>/dev/null | while IFS= read -r line; do
    case "$line" in
        *'ev=item_gate'*) continue ;;
        *'ev=retail'*)   printf '%s%s%s\n' "$M" "$line" "$X" ;;
        *'ev=handle_message'*) printf '%s%s%s\n' "$C" "$line" "$X" ;;
        *'ev=queuez'*)   printf '%s%s%s\n' "$G" "$line" "$X" ;;
        *'ev=bootflow'*) printf '%s%s%s\n' "$B" "$line" "$X" ;;
        *'result=fail'*|*'level=warn'*|*'level=error'*)
                         printf '%s%s%s\n' "$Y" "$line" "$X" ;;
        *)               printf '%s%s%s\n' "$D" "$line" "$X" ;;
    esac
done