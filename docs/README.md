# docs/ - directory layout (after the 2026-08-31 organization)

WHAT LIVES WHERE. The repo root holds only LIVE documents; everything
historical is here, one level down.

## This directory
- `handoffs/`      - all superseded HANDOFF_*.md (the newest stays at root;
                     the router doc map in AGENTS.md always names it)
- `postmortems/`   - closed POSTMORTEM_*.md
- `boots/`         - BOOT_BRIEF_p2-*.md work products (one per boot)
- `archive/`       - superseded strategies, map-status snapshots, one-off
                     analyses (GAME_PLAN_2026-08-07, RE_MAP_STATUS, ...)
- `plans/`         - workflow/implementation plans (boot-gate v3, femu v2,
                     night-runner, re-login feasibility, enforcement layer)

## Repo root (unchanged, all live)
- AGENTS.md (router) / STATE.md / LESSONS.md / ENVIRONMENTS.md / TOOLS.md
- CLAUDE.md / NIGHT_RUNNER.md / GAME_PLAN_2026-08-14.md
- FINDINGS_2026-*.md - the append-only archive. PLANNED MOVE: `findings/`
  (phase B of the 2026-08-31 organization - the tooling already accepts
  both locations; run RE_scripts/organize_root.sh at a clean pen boundary)
- FRONT_*.md (live front pages), INCIDENT_2026-08-25_false-loops.md,
  POSTMORTEM_2026-08-31 (closed but recently referenced)

## Data (never versioned)
- RE_output/reference/ - bubble CSVs, reference PDFs moved out of root
- RE_output/{map,logindex,boots,captures,incidents,...} - machine output
