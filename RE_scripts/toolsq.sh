#!/usr/bin/env bash
# toolsq.sh - THE CAPABILITY SEARCH (2026-09-06; ENFORCEMENT open-candidate P6,
# POSTMORTEM_2026-08-30 A4: "the tool already existed" cost three separate
# misses). Before building any new tool or lane, ask the project what it
# already has.
#
#   toolsq.sh <term> [more terms...]      (all terms AND-ed within a line)
#
# Searches, in order of authority:
#   1. TOOLS.md registered tool rows        (the instrument registry)
#   2. RE_output/claims/*.md                (what the lanes ANSWERED - specs,
#                                            verdicts, acceptance sections)
#   3. docs/ (postmortems + handoffs)       (rules + precedent)
#
# Every hit cites file:line (claim-ready per the evidence rules). Capped at
# 15 lines per source with a TRUNCATED marker. Exit 1 = no hits (a RESULT,
# not silence); exit 2 = wrong usage.
# Pinned to /usr/bin/grep (T1.1: the shadowed grep is blind to RE_build//
# RE_output via --ignore-files and -I).
set -u
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ $# -ge 1 ] || { echo "usage: toolsq.sh <term> [more terms...]"; exit 2; }

pattern="$(printf '%s\n' "$@" | tr ' ' '|')"
echo "== toolsq: /$pattern/ (tool registry + answered questions) =="

hits=0
emit() { # capped section emitter: $1=header $2=file $3=cap
  local n
  n="$(/usr/bin/grep -icE "$pattern" "$2" 2>/dev/null || true)"
  [ "${n:-0}" -gt 0 ] || return 0
  echo "--- $1 ($(basename "$2")): $n line(s) [cap $3]"
  /usr/bin/grep -inE "$pattern" "$2" | head -"$3" | cut -c1-150
  if [ "$n" -gt "$3" ]; then
    echo "    TRUNCATED: $3 of $n shown (counts exact)"
  fi
  hits=$((hits + 1))
}

[ -f "$root/TOOLS.md" ] && emit "TOOL REGISTRY" "$root/TOOLS.md" 15
for f in "$root"/RE_output/claims/*.md; do
  [ -f "$f" ] || continue
  emit "CLAIM ANSWERS" "$f" 6
done
if [ -d "$root/docs" ]; then
  while IFS= read -r f; do
    emit "DOCS PRECEDENT" "$f" 6
  done < <(find "$root/docs" -name "*.md" | head -60)
fi

if [ "$hits" -eq 0 ]; then
  echo "no hits - check the terms: try the tool's FUNCTION (e.g. 'walk map') before its name, and RE_output/claims/*.md for answered questions."
  exit 1
fi
echo "(searched the registry + claims + docs; q.sh = supersession chains; funcq --corpus = function-map terms)"
