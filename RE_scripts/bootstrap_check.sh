#!/usr/bin/env bash
# REGISTRY: caps: session-bootstrap, doc-budgets, search-proof, instrument-specs
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
for f in AGENTS.md LESSONS.md ENVIRONMENTS.md TOOLS.md docs/ENFORCEMENT.md HANDOFF_*.md; do
  [ -f "$f" ] || continue
  if head -5 "$f" | grep -q '^STATUS:'; then
    echo "ok      $f"
  else
    echo "MISSING $f (no STATUS line in first 5 lines)"
  fi
done

echo
echo "== SEARCH-TOOL PROOF (T1.1: a blind grep returns exit 0 EMPTY - prove the tool sees the corpus) =="
arch=$(ls -td RE_output/logs/*/ 2>/dev/null | head -1)
if [ -z "$arch" ]; then
  echo "LOUD    no boot archives under RE_output/logs - cannot prove the search tool; grep a known capture by hand"
else
  probe=""; probe_lit=""; probe_n=""
  for f in "$arch"*_sunrise.log; do
    [ -f "$f" ] || continue
    for lit in "Adding player" "ev=" "stage="; do
      n=$(/usr/bin/grep -ac -- "$lit" "$f")
      if [ "$n" -gt 0 ]; then probe="$f"; probe_lit="$lit"; probe_n="$n"; break 2; fi
    done
  done
  if [ -z "$probe" ]; then
    echo "LOUD    no known literal found in $arch - verify the search tool by hand before trusting any scan"
  else
    shadow_n=$(grep -ac -- "$probe_lit" "$probe" 2>/dev/null)
    [ -n "$shadow_n" ] || shadow_n=0
    if [ "$shadow_n" -eq "$probe_n" ]; then
      echo "ok      search tool clean: bare 'grep' sees $probe_n hits of \"$probe_lit\" in $(basename "$arch") (== /usr/bin/grep)"
    else
      echo "LOUD    SEARCH TOOL BLIND: bare 'grep' returned $shadow_n but /usr/bin/grep returns $probe_n for \"$probe_lit\""
      echo "        in $probe - the ugrep wrapper honours .gitignore/-I (TRAP 19). Use /usr/bin/grep or RE_scripts/sgrep.sh"
      echo "        for anything under RE_build/ or RE_output/, and treat every prior bare-grep NULL as unproven."
    fi
  fi
fi

echo
echo "== SPECIFIED INSTRUMENTS - CHECK IF BUILT (empty-mask #8: the definitive probe, named and never built) =="
spec=$(/usr/bin/grep -rn -iE "definitive instrument|the instrument that would|instrument that would" RE_output/claims/*.md 2>/dev/null)
if [ -n "$spec" ]; then
  echo "$spec" | sed 's/^/  SPECIFIED /'
  echo "  ^ these name an instrument in writing. Build it or retire the sentence before booting around it."
else
  echo "ok      no unbuilt-instrument sentences in the claims corpus"
fi

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
[ -n "$newest_findings" ] && /usr/bin/grep '^## [0-9]' "$newest_findings" | tail -6 | cut -c1-100

echo
echo "== STATE HEADER (first 12 lines; read the rest of STATE.md after) =="
head -12 STATE.md

echo
line
echo "BOOTSTRAP OK (all instruments emitted - absence would have printed LOUD)"
