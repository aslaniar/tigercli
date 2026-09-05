# Workspace - Destiny preservation RE project (router)

STATUS: live (2026-08-26, meta/workflow-harness-v1)

This file is the ROUTER: identity, doc map, conditional-load triggers, the
compressed rule table, the model spend map, and doc governance. ~150-line budget.
All deep content lives in the files it points to.

PROJECT: derive a full private server for the D2 Season-of-Arrivals build and
run D1-on-PC research; in-process Sunrise DLL + standalone fork replacement,
multi-account/multi-peer work in flight. Full strategy: GAME_PLAN_2026-08-14.md.

*** THE GOVERNING CONSTRAINT (user, 2026-09-02; it outranks any lane's convenience) ***
THE CLIENT IS NEVER MODIFIED. THE SERVER MUST ACCOMPLISH EVERYTHING. This was a retail
game: retail clients rendered peers against Bungie on server input alone, so every
missing behaviour IS reachable from the wire, and a client-side shortcut does not just
break scope - it destroys the evidence that the server-side answer exists. This forbids
.text patching AND client-side WRITES INTO GAME DATA (the p2-161 gate poke is the case
that forced the rule to be written down: it slipped past the narrower "no .text patching"
line). Client-side writes are admissible ONLY as a throwaway DIAGNOSTIC that answers
"does X matter", never as a delivered mechanism, and the switch reverts to 0 the moment
the boot ends. Instruments that only READ are unaffected.
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
| FRONT_e2e-stack.md | live front page | the END-TO-END map: the layers that WORK, and the appearance gap. NOTE: its region-B-as-appearance-candidate line is SUPERSEDED by 20.202 |
| NIGHT_RUNNER.md | live manual | running the function-map night lanes (reconcile/night_pull/funcq/beacons/femu) |
| HANDOFF_2026-09-03_CREATION.md | SUPERSEDED by 20.291 (front parked) | its PROVEN list (W1 closed, W3 down, cond5 a pure read, the walk skips self) stands and is still the right starting evidence; its QUESTION and its image/mask road are parked. Read FINDINGS 20.291 first |
| HANDOFF_2026-08-31_GATE-FEEDERS.md | SUPERSEDED by 2026-09-03_CREATION | ALWAYS when taking over. Its gate table + elimination list stand, but 20.246/20.250 spent its items 1-3 (static exhausted) and did item 4 (the p2-146 dump); STATE.md NEXT governs |
| FINDINGS 20.291 (in FINDINGS_2026-08-25.md) | NEWEST VERDICT - READ FIRST | ALWAYS when taking over. Parks the image/mask front (premise unevidenced + a 3.5x object-size contradiction); RETRACTS 20.288 R2/R3 and participant-image-format-spec 2/4/5; decodes the BAP queue-event wire format (a capability, not a road); names 20.53's remainder as the project's only positive control. Then 20.283-20.287 for the wall stack |
| HANDOFF_2026-08-31_POOL-PROTOCOL.md | SUPERSEDED by 20.219 | the pool-family STATIC MAP is still the reference; its hunt list and its "host mask empty" premise are dead |
| HANDOFF_2026-08-30_ENTITY-FRONT.md | superseded by 2026-08-31 | the entity-front hunt list (spent); its closed-fronts record stands |
| docs/handoffs/HANDOFF_2026-08-30_CONSUMER-HUNT.md | superseded by ENTITY-FRONT | the appearance-consumer hunt; its premise (the profile pipeline as the road to a rendered peer) is settled |
| docs/handoffs/HANDOFF_2026-08-29_STAGE-TRAY.md | HISTORICAL (retracted 20.191/20.192) | the staging-population lane. Its premise was false - NULL is the apply's normal third argument. Read only for that history |
| docs/handoffs/HANDOFF_2026-08-29_PROFILE-WRITER.md | superseded | the profile-block writer contract; its job shipped at 20.178 |
| docs/handoffs/HANDOFF_2026-08-29_ADMISSION.md | HISTORICAL (20.170) | the admission-forge lane, now CLOSED - its premise was false. Read only for that history |
| docs/handoffs/HANDOFF_2026-08-28_L9-RENDER.md | superseded by ADMISSION | historical: the L9 render front |
| docs/handoffs/HANDOFF_2026-08-27_ROAD-C.md | superseded by L9-RENDER | historical: how road C was opened and closed |
| docs/handoffs/HANDOFF_2026-08-27_LAYER-SHIFT.md | superseded by ROAD-C | historical context for the scope shift |
| RE_output/claims/lane-brief-template.md | lane contract | spawning any lane |
| INCIDENT_2026-08-25_false-loops.md | closed incident | failure/silence investigation |
| POSTMORTEM_2026-08-31_THE-EMPTY-MASK-LOOP.md | closed postmortem | HOW ~8 BOOTS WENT TO A NON-BLOCKER: a return code read as a state, and 8 more mechanisms. Written for a workflow-fixing session; read before briefing any multi-boot front |
| docs/postmortems/POSTMORTEM_2026-08-30_MY-ERRORS.md | closed postmortem | the 2026-08-30 error record: three rule violations, three "the tool already existed" misses, and the engineering faults that cost two boots and a crashed launch. Read before building a new instrument |
| docs/postmortems/POSTMORTEM_2026-09-01_THE-NIGHT-RUNNER.md | closed postmortem | the 0831/0901 ~30-lane night wave and the 3 boots it fed: one unexamined inherited premise under correct work; readiness language that conflated "the callee does X" with "the call happens"; a census written larger than its scan. Read before briefing a lane wave |
| docs/postmortems/POSTMORTEM_2026-09-01_INSTRUMENTATION.md | closed postmortem (+ 09-02 ADDENDUM) | every instrument of the 09-01 session: the probe that logged the answer and not the question (3 boots), budgets spent before the event, a control that could not fire, an instrument that overstated the wire, and the patterns that WORKED (first-seen-key gating, whole-array enter+leave dumps). ADDENDUM p2-160 (3 launch cycles, 2 spent on the instrument): a dump gated on an event its own hook placement excludes; a peer test with no anchor; a mitigation designed against a guessed mechanism; and the five defects a LINE-BY-LINE read found afterwards. THE RULE IT YIELDED: when a boot has already produced lines from an instrument, REPLAY the next version's trigger over those lines before deploying - a recorded run is a fixture, and shipping without it spends a launch to run a unit test. Read before writing or changing any probe |
| docs/postmortems/POSTMORTEM_2026-09-02_THE-WRONG-QUESTION.md | closed postmortem | THE STRATEGIC ONE - READ BEFORE OPENING OR CLOSING ANY FRONT. ~10 boots hunted a gate while 20.219 R4's own sentence said "the client NEVER ASKS. Creation is not reached." A front closed on a sub-question; a retraction (20.219 R5) that buried the project's only known SERVER-SIDE lever for provoking entity creation (20.208 R6 / 20.213 R1) without meeting its control; and the working case (the local player, failing the same gate, 603 samples a boot) never read as the control it is |
| docs/postmortems/POSTMORTEM_2026-09-03_READING-THE-INSTRUMENT.md | closed postmortem | THE INTERPRETATION ONE - READ BEFORE TRUSTING ANY PROBE OUTPUT. Seven errors in one session, five sharing one shape: a conclusion drawn from an instrument's field without first reading the code that produces it (a boot that never happened; a scan whose positive control failed and was reported anyway; a fix written before the census; `value=` read as a bit that was a counter). Also the record that EVERY mechanical gate fired correctly and caught real defects - the failures were all in the ungateable gap. Its rule: before a probe's output enters a conclusion, read what produces it |
| docs/postmortems/POSTMORTEM_2026-09-02_THE-WIRE-WATCH.md | closed postmortem | the DR watch's three abnormal host outcomes and its retirement (LESSONS U18): VEH/DR/suspend = behavioural; platform-mechanism validation; kill criteria; mitigation-vs-root-cause. Read before building any instrument that intercepts the host |

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
U17 no optional protocol types  | U18 invasive instruments (VEH/DR/suspend) = behavioural; postmortem 09-02 | ARH1-8 anti-rabbit-hole (lane execution)
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
docs/archive/GAME_PLAN_2026-08-07.md + GAME_PLAN_2026-08-14.md (root) strategies; FINDINGS_2026-08-07 background; RE_output/
claims/*.md specs (dispatch map, signon, deadorbit, family-4 wire layout).
Skills/context notes for the car-project analogy: keep THIS research's files in
THIS directory only (`../car-projects/` is separate).
