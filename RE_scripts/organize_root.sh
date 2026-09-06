#!/usr/bin/env bash
# organize_root.sh - PHASE B of the 2026-08-31 root reorganization.
# Moves FINDINGS_*.md into findings/ and finalizes the layout.
#
# SAFETY INTERLOCK (all checked before anything moves):
#   (a) no uncommitted changes to the files it moves;
#   (b) no file in the repo root was modified in the last 30 minutes (the pen
#       session must be idle - moving its active write target mid-session is
#       the damage we are avoiding);
#   (c) the generated index is FRESH (INDEX_findings.md newer than the newest
#       FINDINGS file) - moving files on top of a stale index would leave the
#       recall layer pointing at the old layout.
# --dry-run runs every check and prints what WOULD happen; it never moves.
# The tooling (reconcile/build_index/bootstrap_check) already accepts BOTH
# locations, so after this script nothing else needs to change.
set -eu
cd "$(dirname "$0")/.." || exit 2
dry=0
[ "${1:-}" = "--dry-run" ] && dry=1

now=$(date +%s)
recent=0
for f in *.md; do
  [ -f "$f" ] || continue
  m=$(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f")
  if [ $((now - m)) -lt 1800 ]; then recent=1; echo "recent: $f"; fi
done
if [ "$recent" -eq 1 ]; then
  echo "REFUSING: a root document was modified within 30 minutes -"
  echo "the pen session may be active. Run at a clean handoff."
  exit 1
fi
if [ -n "$(git status --porcelain FINDINGS_2026-*.md 2>/dev/null)" ]; then
  echo "REFUSING: FINDINGS files have uncommitted changes - commit first."
  exit 1
fi
newest=$(cat <(ls -t FINDINGS_2026-*.md 2>/dev/null) | head -1)
if [ -f RE_output/INDEX_findings.md ] && [ -n "$newest" ] \
   && [ RE_output/INDEX_findings.md -ot "$newest" ]; then
  echo "REFUSING: RE_output/INDEX_findings.md is OLDER than $newest -"
  echo "rebuild the index first (python3 RE_scripts/build_index.py) so the"
  echo "move does not leave the recall layer stale."
  exit 1
fi

count=$(ls FINDINGS_2026-*.md 2>/dev/null | wc -l | tr -d ' ')
if [ "$dry" -eq 1 ]; then
  echo "DRY-RUN OK: all interlocks clear; would move $count FINDINGS file(s)"
  echo "  -> findings/ (git mv), then fix the AGENTS.md router row, then"
  echo "  rebuild indexes (reconcile, build_index) and run bootstrap_check."
  exit 0
fi

mkdir -p findings
git mv FINDINGS_2026-*.md findings/ 2>/dev/null || mv FINDINGS_2026-*.md findings/
moved=$(ls findings | wc -l | tr -d ' ')
echo "moved $moved findings file(s) into findings/"

# finalize the router path (the FINDINGS row): the old pattern named
# FINDINGS_2026-\*.md which never matched the real FINDINGS_2026-08-*.md row,
# so the rewrite silently never landed (backlog 3.3). Match the month generically.
sed -i '' 's#^| FINDINGS_2026-[0-9][0-9]-\*\.md |#| findings/ (FINDINGS_2026-*.md) |#' AGENTS.md
if ! grep -q '^| findings/ (FINDINGS_2026-\*\.md) |' AGENTS.md; then
  echo "REFUSING to declare success: the AGENTS.md router row rewrite did not land" >&2
  echo "(check the row text - the sed targets '| FINDINGS_2026-MM-*.md |')" >&2
  exit 1
fi
echo "router row rewritten: findings/ (FINDINGS_2026-*.md)"

/usr/bin/python3 RE_scripts/reconcile.py | tail -1
/usr/bin/python3 RE_scripts/build_index.py | tail -2
bash RE_scripts/bootstrap_check.sh | tail -1
echo "PHASE B COMPLETE - root holds only live documents."
