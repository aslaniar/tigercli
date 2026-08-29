# Workspace - Destiny preservation RE project (router)

STATUS: live (2026-08-26, meta/workflow-harness-v1)

This file is the ROUTER: identity, doc map, conditional-load triggers, the
compressed rule table, the model spend map, and doc governance. ~150-line budget.
All deep content lives in the files it points to.

PROJECT: derive a full private server for the D2 Season-of-Arrivals build and
run D1-on-PC research; in-process Sunrise DLL + standalone fork replacement,
multi-account/multi-peer work in flight. Full strategy: GAME_PLAN_2026-08-14.md.
Keep project knowledge ONLY in this repo's plain files (STATE.md, FINDINGS_*.md,
AGENTS.md) - never in any tool-private memory store. That rule never drifts.

## READ FIRST - THE DOC MAP (what exists, when to load what)

| File | Status | Load when |
|---|---|---|
| STATE.md | live snapshot; header only | ALWAYS at session start (or run bootstrap_check.sh) |
| LESSONS.md | deep layer | conditional, see triggers below |
| TOOLS.md | instrument registry | before writing a new scanner/parser/probe (forks are debt) |
| ENVIRONMENTS.md | deep env layer | touching deploys/tooling/Ghidra/cross-machine ops |
| FINDINGS_2026-08-*.md | append-only archive | when cited by STATE/lessons/index |
| FRONT_public-host-chain.md | live front page | working road C (server as group host) - the chain L1-L9 with marks |
| HANDOFF_2026-08-29_ADMISSION.md | newest handoff | ALWAYS when taking over. 20.104 closed (roster names the peer); a forged peer breaks setup:orbit; NOTE the two clients are on DIFFERENT builds |
| HANDOFF_2026-08-28_L9-RENDER.md | superseded by ADMISSION | historical: the L9 render front |
| HANDOFF_2026-08-27_ROAD-C.md | superseded by L9-RENDER | historical: how road C was opened and closed |
| HANDOFF_2026-08-27_LAYER-SHIFT.md | superseded by ROAD-C | historical context for the scope shift |
| RE_output/claims/lane-brief-template.md | lane contract | spawning any lane |
| INCIDENT_2026-08-25_false-loops.md | closed incident | failure/silence investigation |

Older HANDOFF_* / *_bak files = historical, superseded-by the table above.
Every dated doc opens with a `STATUS:` line; auditor verifies (DOC GOVERNANCE).
Indexes: `bash RE_scripts/q.sh <term>` queries supersession chains + claims;
RE_output/INDEX_findings.md / INDEX_claims.md are generated, never hand-edited.

## CONDITIONAL LOAD TRIGGERS (the expensive stuff loads by need, not by default)

- About to run or deploy ANY game boot -> LESSONS.md "PRE-BOOT CHECKLIST" +
  `python3 RE_scripts/gate_boot.py <boot-brief.md>` (exit 1 = no boot) +
  ENVIRONMENTS.md deploy section. Boot brief required sections are enforced.
- Investigating a failure / silence / null result -> LESSONS.md #13 #14 #11 +
  INCIDENT_2026-08-25_false-loops.md.
- Spawning or briefing a lane -> lane-brief-template.md (OUTPUT-FIRST shape).
- Claiming something about upstream/community code -> LESSONS.md #1 and #15.
- Writing/editing project docs -> DOC GOVERNANCE below.
- About to write ANY new script for a lane -> TOOLS.md first; generalize an
  existing tool rather than fork it.
- Digging through logs -> logq.py over a logindex.py index (loggrep.sh for
  one-line peeks). Any raw sed/grep CHAIN beyond that = conversion debt.
- Platform/tooling specifics (Windows rig, Ghidra invocation, shell layers) ->
  ENVIRONMENTS.md.

## COMPRESSED RULE TABLE (full text + stories: LESSONS.md)

U1 reference=fresh-fetch oracle | U2 instrument before intervention
U3 complete map before moving   | U4 reply envelope IS the contract
U5 log routing not activity     | U6 pre-name the negative (both kinds)
U7 escalate after 2 failures    | U8 disk is the truth
U9 document gate expected value | U10 one contract per boot
U11 exoneration only as tested  | U12 boot brief states graphics delta
U13 null result indicts instrument first | U14 assert artifact provenance
U15 source scope of authority   | U16 mark EVERY chain link
U17 no optional protocol types  | ARH1-8 anti-rabbit-hole (lane execution)
NST parse/smoke before run      | METHOD contract-first, census before port

JUDGMENT RULES (not automatable; review-time attention here): U15, U10-composition.

## SPEND MAP (model routing - flips the ladder for judgment nodes)

| Work class | Route |
|---|---|
| Mechanical: greps, boilerplate extraction, running known scripts, formatting | cheapest tier (flash); never for judgment |
| Decomposition: censuses, specs, summaries, lane briefs, plan drafts | default tier (sonnet / V4 Pro) |
| JUDGMENT NODES (preemptive, not after-failure): interpreting ambiguous data (wire bodies, disassembly semantics), deciding what an unexplained silence means, any conclusion that will spend a boot or close an open question | strongest available tier (GLM/kimi opencode; sonnet->opus on explicit request in Claude Code) |

Cost discipline unchanged: budget checks before spawns stay human-visible;
subagent tier mapping per harness lives in CLAUDE.md shim + parent AGENTS.md.
Rationale: cheap models do expensive damage precisely at judgment nodes -
a misread becomes a boot (which costs more than tokens). Everything converted
to gates/scripts runs model-free and belongs on the cheapest lane.

## DOC GOVERNANCE (2026-08-26 - why this file stopped growing)

Measured, not remembered: `bash RE_scripts/bootstrap_check.sh` prints every
budget vs actual each session start. Violation = visible debt, obligation to
consolidate before next milestone, never a blocker mid-work.

| Doc | Budget | Enforced shape |
|---|---|---|
| AGENTS.md (this) | 150 lines | router content only |
| STATE.md | headline verdict + deployed hashes + next gate + reading order (~40 lines); NO incident narratives (FINDINGS owns those); front detail -> FRONT_<name>.md pages | structural containment |
| LESSONS.md / ENVIRONMENTS.md | uncapped ADDITIONS but one-in-one-out | see RULE LIFECYCLE |

Mechanisms:
1. **Hard budgets checked by script** (dumb counters survive model churn).
2. **Rule lifecycle**: incident -> prose lesson -> converted to gate/brief-field/
   rubric line -> prose redundancy resolved same commit. Prose rules are debt,
   either awaiting conversion or labeled JUDGMENT. bloat = backlog.
3. **One-in-one-out** for lessons: adding N requires naming what it replaces.
4. **STATUS lines** on every dated doc (live / superseded-by X / historical);
   handoff author writes once, auditor verifies.
5. **Roving auditor** (flash-tier spawn, ~every 10th session): resolve every path
   referenced by the router (dead-pointer check), print budgets, sample index
   freshness (index mtime vs findings mtime), list live-marked docs >60d stale.
   Emits a liveness line even when clean - silence means it did not run (L13).

## CONVENTIONS (pointers)
Timestamps (exact time, never bare date): LESSONS.md. VERIFIED vs INFERRED
labeling: LESSONS.md. Deliverable/report-back rules: LESSONS.md + template.

## Where to start (historical context)
GAME_PLAN_2026-08-07/14 strategies; FINDINGS_2026-08-07 background; RE_output/
claims/*.md specs (dispatch map, signon, deadorbit, family-4 wire layout).
Skills/context notes for the car-project analogy: keep THIS research's files in
THIS directory only (`../car-projects/` is separate).
