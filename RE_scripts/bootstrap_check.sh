#!/usr/bin/env bash
# REGISTRY: caps: session-bootstrap, doc-budgets
# bootstrap_check.sh - session-start instrument (2026-08-26, DOC GOVERNANCE).
# Prints the doc-budget report, STATE header pointer, newest findings headlines,
# index liveness. Emits on the BORING path too (L13): a clean run prints
# "BOOTSTRAP OK" lines, never silence. Exit 0 always - this is visibility,
# not a gate.
set -u
cd "$(dirname "$0")/.." || exit 2

line() { printf '%s\n' "-------------------------------------------------------------"; }

echo "== DOC BUDGETS (target vs actual; over = visible debt to consolidate =="
agents_lines=$(wc -l < AGENTS.md | tr -d ' ')
state_lines=$(wc -l < STATE.md | tr -d ' ')
state_secs=$(grep -c '^## ' STATE.md)
lessons=$(wc -l < LESSONS.md | tr -d ' ' 2>/dev/null || echo MISSING)
envn=$(wc -l < ENVIRONMENTS.md | tr -d ' ' 2>/dev/null || echo MISSING)
printf 'AGENTS.md       target <=150  actual %s %s\n' "$agents_lines" \
  "$( [ "$agents_lines" -le 150 ] && echo OK || echo '** OVER **')"
printf 'STATE.md        target <=120* actual %s (sections: %s) %s\n' "$state_lines" "$state_secs" \
  "$( [ "$state_lines" -le 120 ] && echo 'OK (*transition cap)' || echo '** OVER (diet pending) **')"
printf 'LESSONS.md      uncapped additions, one-in-one-out   %s\n' "$lessons"
printf 'ENVIRONMENTS.md uncapped additions                   %s\n' "$envn"

echo
echo "== STATUS LINES (every dated doc opens with one; auditor verifies) =="
for f in AGENTS.md LESSONS.md ENVIRONMENTS.md TOOLS.md HANDOFF_*.md; do
  [ -f "$f" ] || continue
  if head -5 "$f" | grep -q '^STATUS:'; then
    echo "ok      $f"
  else
    echo "MISSING $f (no STATUS line in first 5 lines)"
  fi
done

echo
echo "== SCAN-NEGATIVE HYGIENE (20.209 R2 class: a scan's coverage limit is not a world-fact) =="
na_out=$(/usr/bin/python3 RE_scripts/negative_audit.py 2>/dev/null)
na_rc=$?
echo "$na_out" | grep -E "LIVENESS|NEGATIVE AUDIT FLAGS" | head -3
if [ "$na_rc" -ne 0 ]; then
  echo "DEGRADED: negative_audit flagged scan-negative claims (rc=$na_rc) - run: /usr/bin/python3 RE_scripts/negative_audit.py"
fi

echo
echo "== REGISTRY AUDIT (registry rows vs tool reality - 08-31 rig_dll_helper drift) =="
ra_out=$(/usr/bin/python3 RE_scripts/registry_audit.py 2>/dev/null)
ra_rc=$?
echo "$ra_out" | grep -E "REGISTRY AUDIT|caps-verified" | head -2
if [ "$ra_rc" -ne 0 ]; then
  echo "DEGRADED: registry_audit found drift (rc=$ra_rc) - run: /usr/bin/python3 RE_scripts/registry_audit.py"
fi

echo
echo "== INDEX LIVENESS (stale index is a soft warn; missing index is loud) =="
newest_findings=$(cat <(ls -t FINDINGS_2026-*.md 2>/dev/null) <(ls -t findings/FINDINGS_2026-*.md 2>/dev/null) 2>/dev/null | head -1)
if [ -f RE_output/INDEX_findings.md ]; then
  if [ "$newest_findings" ] && [ RE_output/INDEX_findings.md -ot "$newest_findings" ]; then
    echo "warn    INDEX_findings older than $newest_findings -> rerun build_index.py"
  else
    echo "ok      INDEX_findings fresh"
  fi
else
  echo "LOUD    no INDEX_findings.md -> python3 RE_scripts/build_index.py"
fi

echo
echo "== NEWEST FINDINGS HEADLINES ($newest_findings) =="
[ -n "$newest_findings" ] && grep -m 6 '^## [0-9]' "$newest_findings" | cut -c1-100

echo
echo "== STATE HEADER (first 12 lines; read the rest of STATE.md after) =="
head -12 STATE.md

echo
line
echo "BOOTSTRAP OK (all instruments emitted - absence would have printed LOUD)"
