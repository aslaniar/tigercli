#!/bin/bash
# REGISTRY: caps: freeze-watch, crash-capture, stall-detect
# freeze_watch.sh - THE FREEZE/CRASH CAPTURE WATCHDOG (host-side, read-only).
#
# WHAT IT IS FOR: a client that crashes "whenever it feels like it" currently
# leaves NO artifact ("Couldn't get first exception / No backtrace available"
# is all Wine ever gives), and a freeze leaves even less. This watcher polls
# the client log for growth; the moment the log goes silent while the client
# process is still alive - a freeze, OR a hard crash sitting on Wine's crash
# dialog (the process is suspended there and STILL DUMPABLE) - it captures:
#   1. a macOS `sample` (native thread stacks of every wine thread)
#   2. a PE minidump via `winedbg --minidump` (attaches, dumps, detaches -
#      LIVE-VALIDATED 2026-09-06 on a running wine process: 152KB .mdmp,
#      parsed by minidump_parse.py; exception + module list recovered)
#   3. the client log tail (what the client said last)
# into RE_output/crashes/<stamp>_freeze/. It NEVER kills, pokes, or configures
# anything - the kill decision stays with the user.
#
# Scope: the launch->Tower window is exactly where it matters, but the rule
# is time-based only (log silence), so it works anywhere in the boot.
#
# Usage:
#   freeze_watch.sh [--stall SEC] [--interval SEC] [--log PATH] [--dir DIR]
#                   [--once] [--selftest]
#   --stall SEC    log-silence that counts as a stall (default 45)
#   --interval SEC poll interval (default 5)
#   --once         one check, no loop (for running alongside a boot script)
#   --selftest     offline arms (fixture log, NO wine spawned, NO popups)
#
# Exit: loops forever unless --once/--selftest. Ctrl-C always safe.
set -u
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLIENT_LOG="${CLIENT_LOG:-$root/Game/bin/x64/Sunrise/logs/sunrise.log}"
OUT_BASE="${CRASH_DIR:-$root/RE_output/crashes}"
WH_WINE="${WH_WINE:-$HOME/Library/Application Support/com.franke.Whisky/Libraries/Wine/bin/wine64}"
WH_PREFIX="${WINEPREFIX:-$HOME/Library/Application Support/Sunrise/pfx}"
stall=${STALL:-30}
interval=${INTERVAL:-2}
mode=loop
persistent=1
[ "${1:-}" = "--once" ] && { mode=once; shift; }
[ "${1:-}" = "--selftest" ] && mode=selftest
[ "${1:-}" = "--single-session" ] && { persistent=0; shift; }
while [ $# -ge 2 ]; do
  case "$1" in
    --stall) stall=$2; shift 2;;
    --interval) interval=$2; shift 2;;
    --log) CLIENT_LOG=$2; shift 2;;
    --dir) OUT_BASE=$2; shift 2;;
    *) echo "unknown arg $1" >&2; exit 2;;
  esac
done

client_pid() {
  # 1. any process whose argv mentions destiny2.exe (matches wine64-preloader,
  #    bare wine64, and GUI-wrapper launches - 2026-09-07: the old
  #    'wine64-preloader.*destiny2' pattern matched NOTHING while a real
  #    client was running and the watcher watched a healthy boot die)
  local p
  p=$(pgrep -f 'destiny2\.exe' 2>/dev/null | head -1)
  [ -n "$p" ] && { echo "$p"; return; }
  # 2. independent source: whoever holds the client log open
  lsof -t "$CLIENT_LOG" 2>/dev/null | head -1
  return 0
}

log_size() { [ -f "$CLIENT_LOG" ] && stat -f%z "$CLIENT_LOG" 2>/dev/null || echo 0; }

winedbg_winpid() {
  # windows pid of destiny2.exe from the wine session that ACTUALLY owns it.
  # The prefix is discovered, not assumed: a GUI (Whisky) launch runs from
  # ~/Library/Containers/com.franke.Whisky/Bottles/<id>, a script launch from
  # ~/Library/Application Support/Sunrise/pfx - probing the wrong one shows a
  # process list with NO destiny2 (hit 2026-09-07 20:31).
  local pid="$1" pfx
  pfx=$(lsof -p "$pid" 2>/dev/null \
        | /usr/bin/grep -oE '/Users/[^ ]*(Sunrise/pfx|Whisky/Bottles/[A-F0-9-]+)' | head -1)
  [ -n "$pfx" ] || return 0
  WINEPREFIX="$pfx" WINEDEBUG=-all "$WH_WINE" winedbg --command "info process" 2>/dev/null \
    | /usr/bin/grep -i 'destiny2' | head -1 | awk '{print "0x"$1}'
}

capture() {
  local pid="$1" wpid="$2" why="$3"
  local stamp dir
  stamp="$(date +%Y%m%d_%H%M%S)"
  dir="$OUT_BASE/${stamp}_${why}"
  mkdir -p "$dir"
  echo "=== STALL CAPTURE ($why) t=$(date +%H:%M:%S) pid=$pid wpid=${wpid:-none} log=${CLIENT_LOG}:$(log_size) ==="
  echo "     last log line: $(tail -1 "$CLIENT_LOG" 2>/dev/null | cut -c1-160)"
  # 1. native thread sample (read-only; works on own processes)
  if /usr/bin/sample "$pid" 3 -file "$dir/native_sample.txt" >/dev/null 2>&1; then
    echo "     native sample   -> $dir/native_sample.txt"
  else
    echo "     native sample   -> FAILED (L13)"
  fi
  # 2. PE minidump (attach + dump + detach; dumpable even on the crash dialog)
  if [ -n "$wpid" ]; then
    if WINEPREFIX="$WH_PREFIX" WINEDEBUG=-all "$WH_WINE" winedbg --minidump "$dir/freeze.mdmp" "$wpid" >/dev/null 2>&1 \
       && [ -s "$dir/freeze.mdmp" ]; then
      echo "     PE minidump     -> $dir/freeze.mdmp ($(stat -f%z "$dir/freeze.mdmp") B)"
      echo "     parse with: /usr/bin/python3 RE_scripts/minidump_parse.py $dir/freeze.mdmp"
    else
      echo "     PE minidump     -> FAILED (L13) - native sample still captured"
    fi
  else
    echo "     PE minidump     -> SKIPPED (no destiny2.exe windows pid)"
  fi
  # 3. log tail
  tail -c 200000 "$CLIENT_LOG" > "$dir/log_tail.txt" 2>/dev/null
  echo "     log tail        -> $dir/log_tail.txt"
  echo "=== capture complete: $dir (process NOT killed) ==="
}

if [ "$mode" = selftest ]; then
  # offline arms: fixture log + stall math; NO wine, NO popups, NO killing.
  tmp="$(mktemp -d)"
  # arm 1 (oracle): the crasher PE generator must produce an MZ/PE image
  /usr/bin/python3 "$root/RE_scripts/make_test_crasher.py" "$tmp/c.exe" >/dev/null \
    && [ "$(head -c2 "$tmp/c.exe")" = "MZ" ] && echo "SELFTEST crasher-PE: PASS (MZ header)" \
    || { echo "SELFTEST crasher-PE: FAIL"; rm -rf "$tmp"; exit 1; }
  # arm 2 (negative): fresh log (growing) -> silence must be < stall
  printf 'core t=1 ev=initialize phase=begin\n' > "$tmp/log"
  CLIENT_LOG="$tmp/log"
  now=$(date +%s); slept=$(stat -f%m "$tmp/log"); silence=$(( now - slept ))
  if [ "$silence" -lt 5 ]; then echo "SELFTEST fresh-log: PASS (silence=${silence}s < 5s -> no stall)"; else
    echo "SELFTEST fresh-log: FAIL"; rm -rf "$tmp"; exit 1; fi
  # arm 3 (positive): stale log (mtime far in the past) -> stall detected by mtime math
  touch -t 202001010000 "$tmp/log"
  now=$(date +%s); slept=$(stat -f%m "$tmp/log"); silence=$(( now - slept ))
  if [ "$silence" -ge "$stall" ]; then echo "SELFTEST stall-math: PASS (silence=${silence}s >= ${stall}s)"; else
    echo "SELFTEST stall-math: FAIL"; rm -rf "$tmp"; exit 1; fi
  rm -rf "$tmp"
  echo "SELFTEST OK (3/3 arms; no wine touched)"
  exit 0
fi

echo "freeze_watch: watching $CLIENT_LOG (stall=${stall}s interval=${interval}s); Ctrl-C safe"
last_size=$(log_size); last_change=$(date +%s); fired=0; tick=0; seen=0; gone=0; captures=0; death_archived=0
while :; do
  sleep "$interval"
  pid=$(client_pid)
  if [ -z "$pid" ]; then
    if [ "$seen" -eq 1 ]; then
      # the client WAS seen and is now gone. FIRST: archive what it said last
      # (the death may be instant - no dump window - and the next launch
      # truncates this log; the 2026-09-07 16:0x crash lost its 108MB record
      # exactly this way). Race note: if a relaunch already truncated the log,
      # say so loudly instead of archiving the wrong boot.
      if [ "$death_archived" -eq 0 ]; then
        death_archived=1
        stamp="$(date +%Y%m%d_%H%M%S)"
        dir="$OUT_BASE/${stamp}_death"
        mkdir -p "$dir"
        if /usr/bin/grep -aq 't=1 ev=initialize phase=begin' "$CLIENT_LOG" 2>/dev/null \
           && [ "$(log_size)" -lt 100000 ]; then
          echo "freeze_watch: CLIENT DIED but the log was ALREADY TRUNCATED by a relaunch - death tail lost (L13)"
        else
          tail -c 2000000 "$CLIENT_LOG" > "$dir/log_tail.txt" 2>/dev/null
          # the crash dialog the user sees is NOT the game process (proven
          # 2026-09-07 16:25: game dead between 2s polls while a dialog was
          # still up) - snapshot who IS alive so the dialog's owner gets named
          ps auxww > "$dir/processes_at_death.txt" 2>/dev/null
          echo "freeze_watch: CLIENT DIED (instant exit, no dump window); last lines archived -> $dir/log_tail.txt"
          echo "     process snapshot  -> $dir/processes_at_death.txt"
          echo "     last line at death: $(tail -1 "$CLIENT_LOG" 2>/dev/null | cut -c1-160)"
        fi
      fi
      gone=$((gone+1))
      if [ "$gone" -ge 2 ]; then
        if [ "$persistent" -eq 1 ]; then
          echo "freeze_watch: client exited; captures: $captures - re-arming for the next launch (persistent)"
          seen=0; gone=0; fired=0; death_archived=0; tick=0; captures=0
          continue
        fi
        echo "freeze_watch: client exited; captures this session: $captures - exiting"
        exit 0
      fi
      continue
    fi
    if [ "$tick" -eq 0 ]; then echo "freeze_watch: no destiny2.exe client process yet - waiting for launch (L13 liveness)"; fi
    last_size=$(log_size); last_change=$(date +%s); tick=$((tick+1))
    [ "$mode" = once ] && exit 0
    continue
  fi
  seen=1; gone=0
  size=$(log_size)
  now=$(date +%s)
  if [ "$size" != "$last_size" ]; then last_size=$size; last_change=$now; fired=0; fi
  silence=$(( now - last_change ))
  tick=$((tick+1))
  if [ $((tick % 12)) -eq 0 ]; then echo "freeze_watch: healthy tick (log=${size}B, silence=${silence}s)"; fi
  if [ "$silence" -ge "$stall" ] && [ "$fired" -eq 0 ]; then
    fired=1; captures=$((captures+1))
    wpid=$(winedbg_winpid)
    capture "$pid" "$wpid" "stall${silence}s"
    [ "$mode" = once ] && exit 0
  fi
  [ "$mode" = once ] && { echo "freeze_watch: once-check done (alive, silence=${silence}s)"; exit 0; }
done
