# Plan: deterministic enforcement layer (2026-08-30)

Premise (established by POSTMORTEM_2026-08-30_MY-ERRORS.md): 11 of 16 session
errors violated rules that were written down verbatim. Prose rules leak at
decision-time regardless of model tier. Deterministic enforcement = intercept
the ACTION with code at the moment it happens.

## THE FOUR INTERCEPTION POINTS

### 1. BEFORE BUILD - instrument construction (kills B2, B3, B4, C1, C2, C3)
gate_boot.py v2 additions - the brief TIES to the build:
- `HOOK COUNT: N` field == verify_hook_rvas.py match count (B4: the gate
  existed but had nothing to compare against)
- `INSTRUMENT LIVENESS: <literal>` must appear in the INSTRUMENT SOURCE
  files listed in the brief (B3: brief pre-named the ambiguity the
  instrument could not resolve - nothing tied them)
- `OBSERVER BUDGET: <event class>` required per instrument (B2: STATE
  verbatim rule, violated because no field forced it)
- derived-layout claims require a `landmark:` token citing captured bytes
  (B1: PREFER LANDMARKS OVER ARITHMETIC, mechanical form)
- detour feasibility: target function size from the spine (functions.csv)
  must exceed the detour footprint (C2: 36/37-byte targets mechanically
  rejected); `CALL FREQUENCY:` field required (C3: hot-path risk named)
- canonical trampoline template: RE_scripts/templates/hook_trampoline.*
  (C1: the profile_harvest pass-through shape becomes the only sanctioned
  starting point; hand-rolling = the deviation)

### 2. BEFORE BOOT - environment (kills A2, A6-residue, C5, A4c)
preflight.py - the WORLD gate, separate from the document gate:
- deployed hash == built hash (re-assert; deploy scripts already do)
- content-cache PE identity matches the deployed binary (A6: the server
  refuses, but preflight catches it BEFORE the launch attempt)
- client DLL export count == last-known-good manifest (C5: seconds,
  mechanical, fastest load-failure check)
- settings edited / backups exist / server state (A2's unmet preconditions)
- INSTRUMENT MANIFEST reconciliation: every instrument the brief claims is
  armed must be present in the deployed binary AND listed in
  RE_output/map/instruments.json (A4c: the ev=ingress hook was armed and
  logging, invisible to the session - the manifest makes deployed
  instruments enumerable)
"ready" is now DEFINED: gate_boot PASS + preflight PASS. Nothing else.

### 3. AT COMMIT - everything written (kills D5, NST residue, doc drift)
pre-commit hook v2 (INSTALL IT - core.hooksPath has been pending since
08-26; this postmortem makes activation mandatory):
- parse-checks .py/.sh (exists)
- FINDINGS entry timestamp lint (index --lint already knows how)
- STATE headline verdict-mark lint: the Updated: block must contain a
  verified-by-* token (D5: untested conclusions in the living snapshot)
- boot-brief lint: required fields of the v2 brief (HOOK COUNT, INSTRUMENT
  LIVENESS, OBSERVER BUDGET, CALL FREQUENCY)

### 4. AT THE DESTRUCTIVE ACTION (kills A3)
- idempotent destructive scripts: reset_lobby_claims (and every restart/
  reset) gains a state check - already-done = no-op + say so (the pen
  session owns these scripts; queued change with rationale)
- decision_log.py: state-changing actions pre-register
  hypothesis/action/expected outcome to RE_output/map/decisions.log
  (ARH1 mechanical)

### 5. THE A4 FIX - registry by capability + inventory (kills A4a/A4b)
- TOOLS.md rows gain `ANSWERS:` field - the QUESTION a tool answers, not
  its name ("tells a captured buffer's WIRE form from its STORED form")
- toolsq.sh <question words>: searches the ANSWERS field + claims corpus
- deployed-instrument manifest: instruments.json, written by deploy scripts,
  read by preflight; `instrument_list.sh` = what is armed right now

### 6. REPORTING FIELDS (kills A5, D6 - partially)
report-back/claims template gains two required fields:
- `WHAT THIS RULES OUT:` (forces negatives to be framed as information)
- `UNRESOLVED CONTRADICTIONS: none | list` (D6: noticing becomes mandatory)

## THE LEDGER - ENFORCEMENT.md
A generated+hand-maintained ledger: every hard rule (U1-17, ARH1-8, NST,
STATE rules like LANDMARKS/BUDGET-OBSERVERS) -> enforcement status:
  gated | linted | template | manifest | judgment-only
- conversion debt becomes visible (bloat = backlog, same as doc budgets)
- judgment-only rules (U15, U11, D4-class reading errors) route explicitly
  to the verify-agent rubric - deterministic about ASKING, honest about
  ANSWERING
- future incidents land as one ledger row each (incident -> notch), never a
  paragraph of prose - the adaptive-tightness mechanism

## HONEST LIMITS
- Gates add friction where a rule turns out not to matter (~20% of actions).
  Price of determinism; buys the 80%.
- Reading-comprehension errors (D4) and authority-scope judgment (U15) are
  interpretation acts - no interceptable action exists. They get the rubric.
- Gates only bind if used: the sanctioned path must be the lazy path
  (wrappers, templates, --force escape hatches that LOG).

## BUILD SEQUENCE (each independently shippable)
1. preflight.py + instruments.json (A2/A6/C5/A4c - the two wasted boots' class)
2. gate_boot v2 brief-tie fields + brief template v2 (B2/B3/B4/C2)
3. pre-commit v2 + INSTALL (D5 + the standing NST activation)
4. toolsq.sh + TOOLS.md ANSWERS fields (A4a/b)
5. decision_log.py + idempotent destructive scripts (A3, pen-owned)
6. ENFORCEMENT.md ledger (the map of what is and isn't enforced)
