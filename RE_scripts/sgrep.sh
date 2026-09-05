#!/usr/bin/env bash
# REGISTRY: caps: repo-search, shadow-safe
# sgrep.sh - the shadow-proof repo search (TOOLING_AUDIT_2026-09-05 T1.1).
#
# WHY IT EXISTS: the interactive-shell `grep` can be a ugrep wrapper honouring
# .gitignore (-I skips "binary" files). This repo gitignores RE_build/ AND
# RE_output/ - the entire server source tree and the entire evidence corpus -
# and the capture logs are flagged "core file (Xenix)" (binary). The wrapped
# grep therefore returns EXIT 0 with NO OUTPUT over both trees, which published
# two false claims before it was caught (ENVIRONMENTS TRAP 19).
#
# This wrapper execs /usr/bin/grep directly with -r -n -a (recurse, line
# numbers, treat binary as text). It cannot be blinded by the wrapper.
#
# Usage: sgrep.sh [-E|-i|-w|-c ...] <pattern> [path...]
#   Paths default to RE_build RE_output (the blind trees) when none are given.
#   bootstrap_check.sh PROVES the search tool each session; if it ever reports
#   SEARCH TOOL BLIND, use this script (or /usr/bin/grep) for those trees.
set -u
flags=()
while [ $# -gt 0 ]; do
  case "$1" in
    -*) flags+=("$1"); shift ;;
    *) break ;;
  esac
done
if [ -z "${1:-}" ]; then
  echo "usage: sgrep.sh [-E|-i|-w|-c] <pattern> [path...]  (default paths: RE_build RE_output)" >&2
  exit 2
fi
pat="$1"; shift
if [ $# -eq 0 ]; then
  set -- RE_build RE_output
fi
exec /usr/bin/grep -rna ${flags[@]+"${flags[@]}"} -- "$pat" "$@"
