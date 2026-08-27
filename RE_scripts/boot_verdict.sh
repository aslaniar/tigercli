#!/usr/bin/env bash
# Reads BOTH clients' logs plus the server's and prints the lobby-lane verdict.
#
# WHY A SCRIPT: the success signal is not "did a line appear" but "WHICH xuid does
# Adding player name" (FINDINGS 20.101 - the line fires every boot for the caller's
# own xuid and proves nothing on its own). That comparison is easy to eyeball wrong
# at 2am, so it is mechanical here. Also spares transcribing four greps per machine.
#
# Usage: bash RE_scripts/boot_verdict.sh
set -uo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mac_log="$root/Game/bin/x64/Sunrise/logs/sunrise.log"
srv_log="$root/RE_output/s1_accept/Sunrise/logs/sunrise.log"
rig_host="rasla@192.168.1.136"
rig_log='C:\Users\rasla\Downloads\destiny-preservation\dcv build\bin\x64\Sunrise\logs\sunrise.log'
ssh_opts=(-o ControlPath="$HOME/.ssh/cm-rig" -o ConnectTimeout=6)
tmp="${CLAUDE_JOB_DIR:-/tmp}/tmp"; mkdir -p "$tmp"
rig_copy="$tmp/rig_sunrise.log"

# Identities are BOOT-SCOPED in general, but the steam ids are authored and stable.
MAC_XUID="110000130aa9ec5"
RIG_XUID="110000130aa9ec6"

echo "======== BOOT VERDICT  $(date '+%Y-%m-%d %H:%M') ========"

if ssh "${ssh_opts[@]}" "$rig_host" "rem" 2>/dev/null; then
  scp "${ssh_opts[@]}" "$rig_host:${rig_log// /\\ }" "$rig_copy" >/dev/null 2>&1 \
    || ssh "${ssh_opts[@]}" "$rig_host" "type \"$rig_log\"" > "$rig_copy" 2>/dev/null
  echo "rig log: $(wc -l < "$rig_copy" | tr -d ' ') lines"
else
  echo "rig log: UNREACHABLE (control socket down) - mac-only verdict"
  : > "$rig_copy"
fi

section() { echo; echo "-- $* --"; }

section "1. LOBBY PAIRING (want the SAME lobby id at the same create=N)"
for pair in "MAC:$mac_log" "RIG:$rig_copy"; do
  name="${pair%%:*}"; file="${pair#*:}"
  [[ -s "$file" ]] || { echo "  $name: no log"; continue; }
  # Keep create=N and lobby=0x.. on ONE line - the pairing IS the thing being read.
  grep -a 'stage=lobby_create\|stage=lobby_claim' "$file" \
    | sed -E "s/^.*ev=steamnet/  $name /; s/ +/ /g" | head -12
done
section "1b. SERVER's view (want host on one machine, join on the other)"
grep -a 'ev=lobby stage=claim' "$srv_log" | sed 's/^.*ev=lobby/  ev=lobby/' | tail -8

section "2. THE ANSWER: which xuid does the roster name?"
verdict="NO PEER ON ROSTER"
for pair in "MAC:$mac_log:$MAC_XUID:$RIG_XUID" "RIG:$rig_copy:$RIG_XUID:$MAC_XUID"; do
  IFS=: read -r name file own peer <<< "$pair"
  [[ -s "$file" ]] || continue
  own_n="$(grep -a 'Adding player' "$file" | grep -ci "$own")"
  peer_n="$(grep -a 'Adding player' "$file" | grep -ci "$peer")"
  echo "  $name: own xuid ...${own: -4} = $own_n ;  PEER xuid ...${peer: -4} = $peer_n"
  [[ "$peer_n" -gt 0 ]] && verdict="PEER IS ON THE ROSTER"
done
grep -a 'Adding player' "$mac_log" | sed 's/^.*Adding player/  MAC Adding player/' | head -4

section "3. THE RELEASE (absent = milestone)"
rel_mac="$(grep -ac 'Could not find tracking data' "$mac_log")"
rel_rig=0; [[ -s "$rig_copy" ]] && rel_rig="$(grep -ac 'Could not find tracking data' "$rig_copy")"
echo "  mac: $rel_mac    rig: $rel_rig"

section "4. FREE MAP: unimplemented slots called, with argument shapes"
echo "  (argument capture ships in p2(68); slot names only on p2(67))"
for pair in "MAC:$mac_log" "RIG:$rig_copy"; do
  name="${pair%%:*}"; file="${pair#*:}"
  [[ -s "$file" ]] || continue
  grep -a 'stage=stub' "$file" | sed "s/^.*ev=steamnet/  $name /" | sort -u | head -20
done

echo
echo "======== VERDICT: $verdict ========"
if [[ "$verdict" == "PEER IS ON THE ROSTER" && "$rel_mac" -eq 0 && "$rel_rig" -eq 0 ]]; then
  echo "MILESTONE: two guardians, one Tower instance."
elif [[ "$verdict" == "PEER IS ON THE ROSTER" ]]; then
  echo "Roster shared but the release STILL fires -> next target is the 828-bit"
  echo "session-plane member table (0x808086F8, activity-schema-global-table.md, 20.95)."
else
  echo "Roster still names only self. If pairing in section 1 DID agree, a shared"
  echo "lobby id is not sufficient: the game needs a membership CHANGE EVENT."
  echo "That is step 3 (LobbyChatUpdate via queue_callback) = p2(68)."
fi
