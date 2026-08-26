#!/usr/bin/env bash
# Deploy the freshly built client DLL to <target>, with provenance asserted.
#
#   deploy_client_dll.sh <mac|rig> "<literal>" ["<more literals>"...]
#
# The 2026-08-25 incident (loop 1): two boots tested a binary that was never
# deployed. And on 2026-08-26 this script took a <mac|rig> argument and IGNORED
# it - a rig deploy would silently have written the Mac's file. Both failure
# classes are now impossible to express:
#   - the target argument is REQUIRED and validated;
#   - the deployed file's hash must equal the build output's hash, checked
#     AFTER the copy, on the machine that will run it;
#   - every named instrument literal must be present IN the deployed file.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
built="$root/RE_build/Sunrise-fork-inventory/build/steam_api64.dll"
helper="$root/RE_scripts/rig_dll_helper.py"
RIG_HOST="rasla@192.168.1.136"
RIG_DLL='C:\Users\rasla\Downloads\destiny-preservation\dcv build\bin\x64\steam_api64.dll'
MAC_DLL="$root/Game/bin/x64/steam_api64.dll"

die() { echo "ABORT: $*" >&2; exit 1; }

target="${1:-}"
case "$target" in
  mac|rig) shift ;;
  *) die "usage: deploy_client_dll.sh <mac|rig> \"<literals...>\" (got target='${target:-}')"
esac

[[ -f "$built" ]] || die "no build output at $built"
[[ $# -ge 1 ]] || die "no instrument literals given - nothing would be proven deployed"

stamp="$(date +%Y%m%d_%H%M%S)"
built_hash="$(shasum -a 256 "$built" | cut -d' ' -f1)"
echo "== deploying client DLL to $target =="
echo "   built ${built_hash:0:16} ($(stat -f%z "$built") bytes)"

# NOTE: -o ControlPath (not ssh's -S) - the two tools disagree on what -S means:
# for scp it would name the ssh BINARY, i.e. "execute the socket file".
ssh_opts=(-o ControlPath="$HOME/.ssh/cm-rig")

if [[ "$target" == "mac" ]]; then
  live="$MAC_DLL"
  [[ -f "$live" ]] || die "no live DLL at $live"
  cp -p "$live" "$live.bak_p2d7_$stamp"
  echo "backed up $(basename "$live").bak_p2d7_$stamp"
  cp "$built" "$live"
  live_hash="$(shasum -a 256 "$live" | cut -d' ' -f1)"
  [[ "$live_hash" == "$built_hash" ]] || die "deployed DLL != build output ($live_hash vs $built_hash)"
  echo "hash match ${live_hash:0:16}"
  for literal in "$@"; do
    count="$(grep -ac "$literal" "$live" || true)"
    [[ "$count" -ge 1 ]] || die "instrument literal '$literal' NOT present in deployed $live"
    echo "literal ok ($count): $literal"
  done
else
  # The control master is REQUIRED for rig deploys: a non-interactive fallback
  # cannot answer a password prompt, so falling back would just fail later and
  # louder. Probe it once and die with instructions if it is down.
  # NOTE: the rig's default shell is cmd.exe - 'true' does not exist there.
  if ! ssh -o ConnectTimeout=4 -o BatchMode=yes "${ssh_opts[@]}" "$RIG_HOST" "rem" 2>/dev/null; then
    die "rig control socket dead. Open it first (asks your password ONCE):
  ssh -M -S $HOME/.ssh/cm-rig -o ControlPersist=8h -N -f $RIG_HOST"
  fi
  # backup + verify run ON THE RIG via a GENERATED python file: cmd.exe
  # mangles quoted arguments containing spaces ("dcv build"), so every value
  # is baked in as a python literal and only the script name crosses the shell.
  gen="$root/RE_output/.rig_dll_deploy.py"
  stage='C:\Users\rasla\Downloads\destiny-preservation\RE_output\scripts\steam_api64.dll.STAGE'
  {
    echo "import hashlib, sys, time"
    echo "dll = r'$RIG_DLL'"
    echo "stage = r'$stage'"
    echo "expect = '$built_hash'"
    printf "literals = [%s]\n" "$(printf "'%s', " "$@")"
    echo "data = open(stage,'rb').read()"
    echo "if hashlib.sha256(data).hexdigest() != expect:"
    echo "    print('STAGE-HASH-MISMATCH'); sys.exit(1)"
    echo "missing = [l for l in literals if l.encode() not in data]"
    echo "if missing:"
    echo "    print('LITERAL-MISSING-IN-BUILD', missing); sys.exit(1)"
    echo "live = open(dll,'rb').read()"
    echo "bak = '%s.bak_p2d7_%s' % (dll, time.strftime('%Y%m%d_%H%M%S'))"
    echo "open(bak,'wb').write(live)"
    echo "print('BACKUP', bak, len(live), 'bytes')"
    echo "open(dll,'wb').write(data)"
    echo "check = open(dll,'rb').read()"
    echo "if hashlib.sha256(check).hexdigest() != expect:"
    echo "    print('POST-COPY-HASH-MISMATCH - restore from', bak); sys.exit(1)"
    echo "print('DEPLOYED-OK', expect[:16], len(check), 'bytes,', len(literals), 'literals pre-checked')"
  } > "$gen"
  scp ${ssh_opts[@]+"${ssh_opts[@]}"} "$built" "$RIG_HOST:C:/Users/rasla/Downloads/destiny-preservation/RE_output/scripts/steam_api64.dll.STAGE" \
    || die "staging scp failed"
  scp ${ssh_opts[@]+"${ssh_opts[@]}"} "$gen" "$RIG_HOST:C:/Users/rasla/Downloads/destiny-preservation/RE_output/scripts/_rig_dll_deploy.py" \
    || die "deploy-script scp failed"
  ssh ${ssh_opts[@]+"${ssh_opts[@]}"} "$RIG_HOST" "python C:\Users\rasla\Downloads\destiny-preservation\RE_output\scripts\_rig_dll_deploy.py" \
    || die "remote deploy failed"
fi

echo "deployed to $target OK"
