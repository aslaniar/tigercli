#!/usr/bin/env bash
# REGISTRY: caps: server-deploy
# P2-D6 deploy: the gameplay/entity plane wired into the standalone server.
#
# ORDER MATTERS, and the first version of this script got it wrong. The harness
# runs `content_swap`, which validates the cache's stored PE identity (offsets
# 12/16) against the EXE UNDER TEST. Gating the candidate against a cache still
# stamped for the old exe makes every domain read cache=0 and the gate fails for
# a reason that has nothing to do with the build. So the restamp happens BEFORE
# the gate, the cache is backed up BEFORE the restamp, and a refused gate puts
# the cache back so the old exe and the old cache stay a consistent pair.
#
#   1 stop the server        (the harness cannot open the log/state.db while it
#                             is live - that is why the gate runs here)
#   2 back up exe + cache    (*.bak_p2d6_<stamp>)
#   3 restamp the cache to the CANDIDATE's identity
#   4 harness gates (SEVEN)  (refused -> restore the cache, abort, deploy nothing)
#   5 deploy the exe
#   6 relaunch + verify the listeners, INCLUDING the new UDP 30976
#
# Rollback after a successful deploy: restore both *.bak_p2d6_<stamp> files.
# Rollback of the plane alone needs no rebuild: set
# server.gameplay.topology = "disabled" in settings.json.
bash "$(dirname "${BASH_SOURCE[0]}")/log_archive.sh" --label auto || true
set -uo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRV_HOST="$(/usr/bin/python3 -c "import json;print(json.load(open('$root/RE_output/s1_accept/Sunrise/settings.json'))['server']['bind_address'])" 2>/dev/null)"
[ -n "$SRV_HOST" ] || { echo "ABORT: cannot derive server host from settings.json" >&2; exit 1; }
accept="$root/RE_output/s1_accept"
cache="$accept/Sunrise/cache/build_data.bin"
candidate="$accept/sunrise-server.exe.NEW_candidate"
live="$accept/sunrise-server.exe"
wine="/Applications/Game Porting Toolkit.app/Contents/Resources/wine/bin/wine64"
stamp="$(date +%Y%m%d_%H%M%S)"
export WINEPREFIX="$HOME/Library/Application Support/SunriseServer/pfx"
export WINEDEBUG='-all'

die() { echo "ABORT: $*" >&2; exit 1; }

# STAGING. The script used to REQUIRE a hand-staged candidate and never produced one, so a run
# with no staging step silently redeployed whatever stale binary was sitting there - reporting
# success the whole way. Two boots were burned on a binary that predated the instruments they
# were meant to test. The build output is now the default source, and staging is this script's
# job. Pass an explicit path as $1 to deploy something else.
build_out="${1:-$root/RE_build/Sunrise-fork-inventory/build/sunrise-server.exe}"
[[ -f "$build_out" ]] || die "no build output at $build_out"
cp "$build_out" "$candidate" || die "staging copy failed"
echo "== 0. staged candidate from $build_out =="
echo "   candidate $(shasum -a 256 "$candidate" | cut -c1-16)"

[[ -f "$candidate" ]] || die "no candidate at $candidate"
[[ -x "$wine" ]] || die "no GPTK wine at $wine"

# THE DARK-WINDOW FIX (p2225_weasel_marionberry.md FIX A): the gates run in a
# SANDBOX (copies of the mutable files, symlinks for the heavy content) while
# the LIVE server KEEPS SERVING - the stop->relaunch window drops to seconds,
# so the clients' BAP links survive (the weasel/marionberry arc's root cause
# was the 1-2 minute dark window degrading the clients' network bring-up).
echo "== 1. the harness sandbox (the server keeps serving) =="
SANDBOX="$accept/sandbox_p2d6"
rm -rf "$SANDBOX"
mkdir -p "$SANDBOX/Sunrise"
cp -p "$accept/state.db" "$SANDBOX/state.db"          || die "state.db snapshot copy failed"
[[ -f "$accept/state.db-wal" ]] && cp -p "$accept/state.db-wal" "$SANDBOX/" || true
[[ -f "$accept/state.db-shm" ]] && cp -p "$accept/state.db-shm" "$SANDBOX/" || true
cp -pR "$accept/Sunrise/cache" "$SANDBOX/Sunrise/cache" || die "cache snapshot copy failed"
ln -s "$accept/content" "$SANDBOX/content"             || die "content link failed"
cp -p "$accept/settings.json" "$SANDBOX/" 2>/dev/null || true
cp -p "$accept/oo2core_3_win64.dll" "$SANDBOX/" 2>/dev/null || true
echo "   sandbox $SANDBOX ready (the live server untouched)"

echo "== 2. restamping the SANDBOX cache to the candidate's identity =="
python3 "$root/RE_scripts/restamp_build_data.py" "$SANDBOX/Sunrise/cache" "$candidate" --apply \
  || die "restamp failed (the live cache was never touched - nothing to restore)"

echo "== 3. harness gates on the candidate, in the sandbox =="
cd "$SANDBOX" || die "no $SANDBOX"
for flag in --s1-test --cache-check --equip-diff --selection-version-test --membership-sweep-test --membership-wire-test --local-account-test --sensor-auth-peer-test; do
  out="$("$wine" "$candidate" "$flag" 2>&1)"; rc=$?
  echo "   $flag rc=$rc"
  [[ -n "$out" ]] && echo "$out" | tail -6
  if [[ $rc -ne 0 ]]; then
    die "harness gate $flag failed (rc=$rc). The sandbox is discarded; the live server, cache and state.db were NEVER touched. Nothing else changed."
  fi
done

echo "== 4. backups (*.bak_p2d6_$stamp) =="
cp -p "$live" "$live.bak_p2d6_$stamp"   || die "exe backup failed"
cp -p "$cache" "$cache.bak_p2d6_$stamp" || die "cache backup failed"
echo "   $(basename "$live").bak_p2d6_$stamp"
echo "   $(basename "$cache").bak_p2d6_$stamp"

echo "== 5. restamping the LIVE cache + stopping the server (seconds) =="
python3 "$root/RE_scripts/restamp_build_data.py" "$cache" "$candidate" --apply \
  || die "live-cache restamp failed; the old exe is still deployed"
pid="$(pgrep -f 'wine64-preloader .*sunrise-server\.exe' | head -1 || true)"
if [[ -n "$pid" ]]; then
  kill "$pid"
  for _ in $(seq 1 20); do
    pgrep -f 'wine64-preloader .*sunrise-server\.exe' >/dev/null || break
    sleep 0.5
  done
  pgrep -f 'wine64-preloader .*sunrise-server\.exe' >/dev/null && die "pid $pid did not exit"
  echo "   stopped pid $pid"
else
  echo "   not running"
fi

echo "== 6. deploying the exe =="
cp "$candidate" "$live" || die "deploy copy failed"
# The deployed file must BE the thing we built. A mismatch here is the failure mode above,
# and it is silent unless something asserts it.
built_hash="$(shasum -a 256 "$build_out" | cut -d' ' -f1)"
live_hash="$(shasum -a 256 "$live" | cut -d' ' -f1)"
[[ "$built_hash" == "$live_hash" ]] || die "deployed exe != build output ($live_hash vs $built_hash)"
echo "   exe  $(shasum -a 256 "$live" | cut -c1-16)"

echo "== 6. relaunching =="
nohup bash "$root/mac-port/launch-server-macos.sh" > "$root/mac-port/launch.log" 2>&1 &
for _ in $(seq 1 40); do
  curl -s -m 2 "http://${SRV_HOST}:8099/ladder" >/dev/null 2>&1 && break
  sleep 0.5
done

echo
echo "== VERIFY =="
echo "-- ladder --"
curl -s -m 3 "http://${SRV_HOST}:8099/ladder" | head -c 300; echo
echo "-- listeners (UDP 30976 is the new one) --"
netstat -an 2>/dev/null | grep -E '\.(30975|30976|8099|8443|3074|3075)\b' | head
echo "== 8. post-restart log archive (the re-login discriminator's evidence) =="
bash "$root/RE_scripts/log_archive.sh" --label post-restart || true

echo
echo "== VERIFY =="
grep -a 'ev=gameplay' "$accept/Sunrise/logs/sunrise.log" 2>/dev/null | tail -20 \
  || echo "   (none yet)"
