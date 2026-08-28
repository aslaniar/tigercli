#!/usr/bin/env bash
# loggrep.sh - zero-infra locate convention over project logs (2026-08-27).
# Usage: loggrep.sh <file-or-dir> <pattern...>
#   - dir form: greps *.log in it (with -a: NUL-bearing captures need it)
#   - FULL-WIDTH lines always (truncation hides the exact key=value evidence)
#   - warns when the target was modified <60s ago (live log: line numbers rot;
#     prefer logq.py over an index, or snapshot first)
# Output lines carry file:line: prefix for direct citation in FINDINGS/claims.
set -u
target="$1"; shift
[ -n "${target:-}" ] || { echo "usage: loggrep.sh <file-or-dir> <pattern>"; exit 2; }

if [ -d "$target" ]; then
  files=$(find "$target" -maxdepth 1 -name '*.log' 2>/dev/null)
  [ -n "$files" ] || { echo "no .log files in $target"; exit 2; }
else
  files="$target"
fi

for f in $files; do
  m=$(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f")
  now=$(date +%s)
  if [ $((now - m)) -lt 60 ]; then
    echo "WARN: $f modified <60s ago (live file - line numbers will rot)" >&2
  fi
  grep -an -- "$@" "$f" | sed "s|^|$f:|"
done
exit 0
