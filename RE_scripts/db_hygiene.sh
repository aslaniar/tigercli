#!/usr/bin/env bash
# REGISTRY: caps: db-maintenance, vacuum-guard
# db_hygiene.sh - opencode session-DB maintenance (2026-08-26).
# DRY-RUN by default: prints size/free-page report and a verdict.
# --vacuum performs the actual VACUUM, but ONLY when safe:
#   - refuses if the -shm/-wal files were touched in the last 5 minutes
#     (an opencode session is live; VACUUM would block it or fail on locks)
#   - refuses unless run with no active opencode process
# Reclaims the freelist (~492 MB measured 2026-08-26 after months of
# churn-and-delete); does NOT touch content. Legacy pre-migration tables
# (session, session_message rows from before 08-13 coexisting with v2 tables)
# are intentionally KEPT: dropping them inside a live app DB is exactly the
# kind of cleverness this project gave up for Lent.
set -u
DB="${OPENCODE_DB:-$HOME/.local/share/opencode/opencode.db}"
[ -f "$DB" ] || { echo "no DB at $DB"; exit 2; }

now=$(date +%s)
wal="$DB-wal"; shm="$DB-shm"
fresh=0
for f in "$wal" "$shm"; do
  [ -f "$f" ] || continue
  m=$(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f")
  if [ $((now - m)) -lt 300 ]; then fresh=1; fi
done

size=$(du -h "$DB" | cut -f1)
read total free < <(sqlite3 "file:$DB?mode=ro" \
  "SELECT printf('%d %d', page_count*page_size/1048576, freelist_count*page_size/1048576) FROM pragma_page_count(), pragma_page_size(), pragma_freelist_count();" 2>/dev/null)
echo "db: $size | pages: ${total:-?} MB total, ${free:-?} MB reclaimable"

if [ "${1:-}" != "--vacuum" ]; then
  echo "dry run. with --vacuum: sqlite3 \"$DB\" 'VACUUM;' (after closing sessions)"
  exit 0
fi

if command -v pgrep >/dev/null && pgrep -fl "opencode" >/dev/null 2>&1; then
  echo "REFUSING: an opencode process appears to be running (pgrep)."
  echo "Close sessions first - a vacuum against a live writer is how db work goes wrong."
  exit 1
fi
if [ "$fresh" -eq 1 ]; then
  echo "REFUSING: $wal/$shm modified within 5 min - a session was active very recently."
  exit 1
fi
echo "backup copy first (cheap insurance)..."
cp "$DB" "$DB.pre-vacuum-$(date +%Y%m%d-%H%M%S)" || exit 1
echo "vacuuming (minutes on a ~800 MB file; do not interrupt)..."
sqlite3 "$DB" "VACUUM;" || { echo "VACUUM FAILED - original untouched (sqlite fails clean)"; exit 1; }
ls -lh "$DB" | awk '{print "done:", $9, $5}'
