#!/usr/bin/env bash
# REGISTRY: caps: boot-verdict, per-arm-discriminator
# Reads BOTH clients' logs plus the server's and prints the lobby-lane verdict.
#
# WHY A SCRIPT: the success signal is not "did a line appear" but "WHICH xuid does
# Adding player name" (FINDINGS 20.101 - the line fires every boot for the caller's
# own xuid and proves nothing on its own). That comparison is easy to eyeball wrong
# at 2am, so it is mechanical here. Also spares transcribing four greps per machine.
#
# v2 (2026-09-05, empty-mask #2 / TOOLING_AUDIT): --sigtable mode prints the
# PER-ARM FAILURE-SIGNATURE TABLE. The solo control boot is a DISCRIMINATOR,
# not just a crash guard: a failure signature present in BOTH arms is NOT
# peer-attributable, no matter how it correlates with peer arrival.
#
# Usage:
#   bash RE_scripts/boot_verdict.sh                        (legacy lobby verdict)
#   bash RE_scripts/boot_verdict.sh --sigtable <archive-solo> <archive-paired> \
#        "signature-regex" ["more"...]
#        Each archive is a directory of *.log (or a single .log file). Counts
#        every signature in EVERY arm side by side. Exit 0 always (visibility).
#
# All greps pinned to /usr/bin/grep (T1.1: the interactive-shell grep can be a
# ugrep wrapper blind to RE_output/ and Game/ captures).
set -uo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GREP=/usr/bin/grep

# ---------- v2: the per-arm signature discriminator table ----------
if [[ "${1:-}" == "--sigtable" ]]; then
  shift
  [[ $# -ge 3 ]] || { echo "usage: boot_verdict.sh --sigtable <archive-A> <archive-B> \"sig\" [...]"; exit 2; }
  arm_a="$1"; arm_b="$2"; shift 2
  collect() {
    local t="$1"
    if [ -f "$t" ]; then echo "$t"
    elif [ -d "$t" ]; then find "$t" -maxdepth 1 -name '*.log'
    fi
  }
  files_a=$(collect "$arm_a"); files_b=$(collect "$arm_b")
  [ -n "$files_a" ] || { echo "no logs in arm A: $arm_a"; exit 2; }
  [ -n "$files_b" ] || { echo "no logs in arm B: $arm_b"; exit 2; }
  label() { basename "$1"; }
  la=$( [ -f "$arm_a" ] && basename "$arm_a" || label "$arm_a" )
  lb=$( [ -f "$arm_b" ] && basename "$arm_b" || label "$arm_b" )
  count_arm() { # <files...> <sig>
    local sig="$1"; shift; local total=0 n
    for f in "$@"; do
      n=$("$GREP" -ac -- "$sig" "$f" 2>/dev/null) || n=0
      total=$((total + n))
    done
    echo "$total"
  }
  echo "======== PER-ARM SIGNATURE TABLE (empty-mask #2: a signature in BOTH arms is NOT peer-attributable) ========"
  printf '  %-42s %12s %12s  %s\n' "signature" "$la" "$lb" "verdict"
  for sig in "$@"; do
    ca=$(count_arm "$sig" $files_a)
    cb=$(count_arm "$sig" $files_b)
    if [ "$ca" -gt 0 ] && [ "$cb" -gt 0 ]; then v="BOTH ARMS - NOT PEER-ATTRIBUTABLE"
    elif [ "$cb" -gt 0 ]; then v="only in $lb - attributable to that arm's condition"
    elif [ "$ca" -gt 0 ]; then v="only in $la - attributable to that arm's condition"
    else v="absent in both (check the input gate / pre-named absence negative)"
    fi
    printf '  %-42s %12s %12s  %s\n' "${sig:0:42}" "$ca" "$cb" "$v"
  done
  echo "(signatures come from the brief's FALSIFIABLE CLAIM / ABSENCE NEGATIVE; the solo arm is a DISCRIMINATOR)"
  exit 0
fi

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

bash "$(dirname "${BASH_SOURCE[0]}")/log_archive.sh" --label auto

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

section "3b. THE LOBBY LANE INSTRUMENTS (did the event fire, and what answered?)"
for pair in "MAC:$mac_log" "RIG:$rig_copy"; do
  name="${pair%%:*}"; file="${pair#*:}"
  [[ -s "$file" ]] || continue
  grep -a 'lobby_member_entered\|num_lobby_members\|lobby_member_by_index\|rich_presence_store\|rich_presence_relay' "$file" \
    | sed -E "s/^.*ev=steamnet/  $name /" | sort -u | head -10
done
echo "  (no lobby_member_entered = the member list never grew past one)"

section "4. FREE MAP: unimplemented slots called, with argument shapes"
echo "  a1 is the first real argument. Identical across machines = a constant/flag;"
echo "  an xuid = an account query; module-offset pointers = strings."
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
  echo "Roster still names only self. As of 20.104 the shared lobby id, the membership"
  echo "event and the peer name lookup are ALL done and none of them reach the roster."
  echo "Every remaining Steam-side lever is downstream of it, so the open question is"
  echo "WHO CALLS \"Adding player\" - static analysis on managed_session, not a boot."
fi
