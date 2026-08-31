# Plan: universal log-query layer (safe parallel implementation)

Date: 2026-08-27. Context: active dev session holds the pen on the road-C front.
This work must not jeopardize it.

## SAFETY ENVELOPE (binding for the whole implementation)

- Work on branch `meta/logquery-v1` off main. The active session commits to main
  untouched; fold-in later. New-file-only by construction -> zero merge conflicts.
- ALLOWLIST (things I may create/modify):
  - NEW: RE_scripts/logindex.py, RE_scripts/logq.py, RE_scripts/loggrep.sh
  - NEW: RE_output/logindex/* (gitignored output dir; indexes are regenerable)
  - NEW: RE_output/scratch/logq_fixtures/* (synthetic test fixtures)
  - DEFERRED (pen-dependent, staged as branch edits, fold in later):
    TOOLS.md registry rows + AGENTS.md router trigger + a FINDINGS entry.
- FORBIDDEN while the other session runs:
  - no edits to fork code (RE_build/**), deploy scripts, settings, cache restamps
  - no boots, deploys, server/client restarts, port listeners
  - no writes into RE_output/boots/ or RE_output/captures/ (READ-ONLY there)
  - no edits to STATE.md / FINDINGS_*.md (active session owns the pen)
- All log access is read-only. Live logs: copy-snapshot before parsing so an
  in-flight append can never tear a read (an ingestion detail, NOT a
  freeze-specific design).

## DESIGN: universal, not capture-specific

Principle: ingest ANY sunrise.log-shaped file (live, frozen capture, merged
timeline output), any number of sources. The ev=/stage=/key=value grammar is
already the project's standard (U5); we index it generically, no per-family
hardcoding. Freezing/copying is just ingestion hygiene for live files.

## WORK ITEMS

1. VERIFY merge_timeline.py N-source support (before anything new):
   a. run `--selftest` (synthetic 3-source + ground truth) -> expect exit 0
   b. real dual-client verification: merge RE_output/boots/p2-78_mac_sunrise.log
      + p2-78_rig_sunrise.log + the s1 server log; check pair counts and
      drift report land, client<->client tape pairing actually fires on real
      data (the fixture proves the code; only real captures prove the wiring)
   c. if (b) fails: minimal fix in merge_timeline.py + extend the fixture to
      cover the failing shape. No rewrite; it is oracle-bearing code.
2. RE_scripts/logindex.py -- universal ingestion:
   - input: one or more log paths (+ optional LABEL= prefix, like merge_timeline)
   - output: RE_output/logindex/<name>.db (SQLite): table events(source, file,
     line, t_ms, ev, stage, kv_json, raw)
   - reuse boot_record's line grammar (import VERBATIM, same as merge_timeline
     does) -> one parser, zero fork debt
   - live-file ingestion = copy to logindex/scratch + stamp (size/mtime) in the
     db header; frozen files read in place
   - `--selftest`: synthetic 2-source fixture with known lines -> assert counts
     and field extraction; prints LIVENESS counts always
3. RE_scripts/logq.py -- the query surface (replaces sed-zoom guessing):
   - filters: --ev --stage --grep --source --range t1 t2 --tail N --line a,b
   - output: FULL-WIDTH lines, every hit cited as file:line (claim-ready)
   - cross-source mode: `--aligned` uses merge_timeline's drift data when
     present so t-ranges compare across machines correctly
   - exit codes: 0 hits / 1 no hits / 2 usage (liveness-printing on boring path)
4. RE_scripts/loggrep.sh -- zero-infra locate convention:
   - `loggrep.sh <file-or-capture-dir> <pattern>`: grep -n, FULL WIDTH,
     warns if given a live file (line numbers rot), suggests logq for indexed work
5. Verification pass (all on /usr/bin/python3; parse-check + smoke first,
   hooks not installed):
   - logindex+logq on the p2-58 reason-hook capture: reproduce the boot-#12
     finding (zero `value=` lines after install line) as ONE query
   - logindex+logq on a p2-78 dual-client capture: same query per source,
     then --aligned across both
   - a representative road-C question answered without opening sed once

## ACCEPTANCE

- All selftests exit 0; real dual-client merge verified (work item 1b)
- One-command answers to queries that today need grep+sed chains per machine
- `git status` shows ONLY allowlisted new paths; main untouched

## DEFERRED TO FOLD-IN (when the pen frees up)

- TOOLS.md rows (logindex/logq/loggrep + "check merge_timeline before writing
  any parser" note), AGENTS.md router trigger, FINDINGS entry, merge to main.
