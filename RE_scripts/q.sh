#!/usr/bin/env bash
# q.sh - one-name recall query over generated indexes + raw archive
# (2026-08-26). Usage: bash RE_scripts/q.sh <term> [term2...]
# Prints: findings entries matching (with supersession links), claims matching.
# Designed for models AND humans: zero flags, works on a cold session.
set -u
cd "$(dirname "$0")/.." || exit 2

if [ $# -eq 0 ]; then
  echo "usage: q.sh <term> [term...]   e.g.: q.sh peer reservation type-13"
  exit 2
fi

pat="$(printf '%s|' "$@")"; pat="${pat%|}"

echo "== FINDINGS ENTRIES matching [$*] (check links before trusting an entry) =="
if [ -f RE_output/INDEX_findings.md ]; then
  grep -iE "$pat" RE_output/INDEX_findings.md | grep -v '^## SERIES ROLLUPS' | cut -c1-160 || echo "(none)"
else
  echo "(index missing - falling back to raw; regenerate with build_index.py)"
  for f in $(ls -t FINDINGS_2026-*.md | head -4); do grep -inE "$pat" "$f" | cut -c1-140 | head -8; done
fi

echo
echo "== CLAIMS matching [$*] (ORPHAN flag = cited by nothing) =="
if [ -f RE_output/INDEX_claims.md ]; then
  grep -iE "$pat" RE_output/INDEX_claims.md | cut -c1-150 || echo "(none)"
else
  ls RE_output/claims | grep -iE "$pat" || echo "(none)"
fi

echo
echo "== probe families hit (re-chase check: did we already run 17 probes on this?) =="
if [ -f RE_output/INDEX_claims.md ]; then
  sed -n '/## PROBE FAMILIES/,$p' RE_output/INDEX_claims.md | grep -iE "$pat" || echo "(none)"
fi
exit 0
