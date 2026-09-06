# ENFORCEMENT - the rule -> mechanism ledger (2026-09-06, FINDINGS 20.307-20.309)

STATUS: live (2026-09-06). The map of what is and is not enforced. Companion:
docs/plans/enforcement-layer.md (the design), AGENTS.md (the rule table),
.opencode/agent/verify.md (the rubric judgment-only rules route to).

## HOW TO READ THIS

Premise (POSTMORTEM_2026-08-30): 11 of 16 session errors violated rules that
were written down verbatim - prose rules leak at decision time regardless of
model tier. Every hard rule below carries exactly one status:

  gated        a script refuses/blocks/flags at the moment it matters
               (exit 1, negative-first tested - a guard never observed
               failing is an assumption with syntax, 09-05 FAILURE 2)
  linted       the pre-commit hook blocks it at commit
  template     the brief/lane template FORCES the naming; content quality is
               the reviewer's (forced judgment - boot-gate-v3's honest class)
  manifest     the registry/manifest makes the thing enumerable and compared
  rubric       judgment-only: no interceptable action exists; routes to
               .opencode/agent/verify.md, which is deterministic about
               ASKING and honest about ANSWERING

Honest limits (enforcement-layer plan): gates add friction where a rule turns
out not to matter (~20% of actions); gates only bind if used, so the
sanctioned path must be the lazy path (wrappers, defaults, --force that logs);
reading-comprehension and authority-scope errors are interpretation acts and
get the rubric, not a pretend gate.

Conversion debt rule: a rule marked rubric with a plausible mechanism is
BACKLOG, not protection. This ledger is where that debt is visible.

## TABLE 1 - UNIVERSAL LESSONS (U1-U18)

| Rule | One line | Status | Mechanism |
|---|---|---|---|
| U1 | the reference is the FRESH-FETCH oracle | rubric | no mechanism; name the fetch in the claim |
| U2 | instrument before intervention | rubric | no gateable action; verify pass reviews the order |
| U3 | complete the map before moving | rubric | funcq/registry support it; the choice is judgment |
| U4 | the reply envelope IS the contract | rubric+template | verify rubric #1; FALSIFIABLE CLAIM field |
| U5 | log routing, not activity | tool-supported | logq/logindex are the sanctioned path; grep chains stay debt (no gate) |
| U6 | pre-name the negative (both kinds) | gated | gate_boot: FALSIFIABLE CLAIM + ABSENCE NEGATIVE sections; rubric #2 |
| U7 | escalate after 2 failures | rubric | explicitly un-automated (AGENTS JUDGMENT list) |
| U8 | the disk is the truth | rubric | report-backs are pointers by convention |
| U9 | document every gate's expected value | template | brief pre-naming (OBSERVER BUDGET, EFFECT CLAIM); pricing the modal negative stays rubric (p2-160 err 3) |
| U10 | one contract per boot | gated-presence | gate sections per brief; composition is JUDGMENT (AGENTS: "U10-composition") |
| U11 | exoneration only in the direction tested | rubric | verify rubric #2 |
| U12 | every brief states its graphics delta | gated | gate_boot: GRAPHICS DELTA section |
| U13 | a null result indicts the instrument first | gated-assist+judgment | replay_trigger exits 1 on ZERO fires; READOUT TRIGGER field; interpreting a live null stays judgment |
| U14 | prove the artifact is the artifact built | gated | preflight deployed==built hashes + --literals in DEPLOYED binaries + instruments.json; rubric #4 |
| U15 | every source has a scope of authority | rubric | verify rubric #6; on the AGENTS JUDGMENT list |
| U16 | mark EVERY chain link | gated-presence | gate_boot CHAIN MARKS + evidence tokens; mark CONTENT is rubric (#3) |
| U17 | nothing in a shipped protocol is optional | rubric | no mechanism |
| U18 | invasive instruments (VEH/DR/suspend) = behavioural | template+judgment | CALL FREQUENCY field required; platform validation + kill criteria + one-line retirement stay judgment (wire-watch postmortem; the watch's own retirement is the worked example) |

## TABLE 2 - PROJECT/STATE HARD RULES

| Rule | Status | Mechanism |
|---|---|---|
| THE CLIENT IS NEVER MODIFIED (governing constraint) | gated | FIX SURFACE: client forces a SERVER-SIDE GAP section naming the missing wire item (gate_boot, U18-gate) |
| reset the server between runs | gated-assist | reset_lobby_claims: idempotent no-op (server up + claims=0 + port set = says so), --check read-only preview; the DECISION to reset stays judgment |
| check the INPUT GATE before reading any result (20.297 R2) | rubric | named negative in every brief; no gate can verify a delivery actually arrived |
| before a probe's field enters a conclusion, read its PRODUCER (09-03) | rubric | the one rule this session earned; the gates now honor it for their own fields (09-03's asymmetry) |
| ANCHOR EVERY DISASSEMBLY | gated | disasm_fn REFUSES a .pdata gap (rc=1 + linear-disassembler handoff); verify_hook_rvas/preflight pdata-check every RVA |
| census before filter | template | lane-brief rule (applies to LOG LINES too - 09-03 E4) |
| solo control before paired | gated | boot_verdict --sigtable: a signature in BOTH arms is mechanically NOT peer-attributable |
| logindex needs /usr/bin/python3; launch from the REPO ROOT | rubric | ENVIRONMENTS facts; no gate |

## TABLE 3 - POSTMORTEM-DERIVED RULES (08-31 -> 09-05)

| Rule | Source | Status | Mechanism |
|---|---|---|---|
| run q.sh on a front's central address+noun BEFORE opening/re-opening it | 09-05 FAILURE 5 (the costliest class: ~18 boots) | gated | gate_boot PRIOR ART: queries + verdicts required, or 'none: <why>'; closed/dead citations force a DEAD-END AUDIT |
| >=2 consecutive third-branches = a model indictment | empty-mask #6 | gated | boot_outcome.jsonl ledger; gate_boot refuses the next boot without a real MODEL REVIEW section (a mention does not pass - caught in testing) |
| a front is closed by answering ITS question, not a sub-question | wrong-question PM | rubric | candidate conversion: the closing verdict restates the original question - no mechanism yet |
| a retraction must meet the evidence it retracts | wrong-question PM | rubric | negative_audit's quoting auto-waiver makes retraction text visible |
| the working case is a control, read every boot | wrong-question PM | template | solo-arm discriminator (boot_verdict); reading pgate's own output stays judgment |
| replay EVERY new trigger over recorded data before deploy | 09-01 addendum + 09-05 FAILURE 3 | gated-assist+template | replay_trigger.py (exit 1 on zero fires; the re-arm N=8 acceptance proven on p2-175/176 data); lane-brief rule; the HABIT is rubric |
| a change ships without its own negative test = an assumption with syntax | 09-05 | rubric+convention | followed in 20.307-20.309 acceptance sections; no gate can force it |
| the search tool must be PROVEN each session | T1.1 (2 false claims) | gated | bootstrap_check SEARCH-TOOL PROOF (bare grep vs /usr/bin/grep on the newest archive); sgrep.sh is the un-blindable path |
| probe design: log the key / novelty-gate / control-fires / derived-lines | 09-01 DEFECTS 1-4 | template | lane-brief PROBE DESIGN RULES (each names its defect); content is rubric |
| callee-proven != route-proven; census denominators; relative observables; falsify-the-front lane first; disputes block synthesis | night-runner PM | template | lane-brief NIGHT-WAVE RULES |
| a guard added in the same edit is not independent | 09-05 FAILURE 2 | rubric | compile-time guards exist in source; showing the guard FAIL pre-fix is convention |
| a probe's pointer guard must match the SUBJECT field's actual alignment; a probe's reject path must be visible (first-reject line) | 09-06 BLIND-GUARD (emit_sesscmp's qword guard refused the gate's own misaligned blob pointers for ~5 boots; found by disasm, not by a boot) | template+gated-assist | R1: lane-brief PROBE DESIGN rule (alignment from the struct decode); R2: replay of a probe whose subject was never logged cannot substitute a STATIC placement proof (R3) - the p2-190c brief carries it |
| a novelty signature over XOR of fields collides to zero exactly on MATCHES (fields equal); a probe whose readout is one event's compare set resets its seen-set per event | 09-06 BLIND-GUARD ADDENDUM (the same-day fix's own hash erased every match; found via the call-gap re-derivation after the user's challenge, no boot) | template | R4: probe-design rule - hash fields jointly (rotl one into the other) + a synthetic collision arm ((k,k) must not alias (0,0)); R5: novelty per event (the join packet's own hook resets the seen-set) - both shipped in 8252f1dad6e8a0c1 |
| a LOOKUP function gets BOTH hooks (enter: the key asked; leave: the decision returned); a caller's post-lookup check between the lookup and the consumer is part of the contract - decode it before calling the path clean | 09-06 BLIND-GUARD ADDENDUM 2 (the walker had enter-only coverage; the gate's found-path state-window (+0x1AEF8 in 6..9) was unread since 20.319; the session's own "nothing between match and processor" claim contradicted the disasm already in the transcript) | template+rubric | R6: lane-brief probe-design rule (lookups hook on both sides); R7: producer-read applied to CALLER code (the printed disasm is the evidence, not its summary) - shipped as the walk_leave leave-probe (0687f90187e3dd97, 65 targets) |
| ONE detour per function start: a leave-probe rides the SAME target row as its enter probe - a second row on the same RVA is an unsupported install and freezes the client on the hot path; the install-table check must reject duplicate RVAs | 09-06 p2-194a (the walk_leave second row froze the rig's client at the loading loop; log ends mid-line t=198282; rig restored from backup) | gated (gap) | the fix: leave-probe routed onto the walk_map row's leave dispatch (3d95a375dc164972); GATE GAP: hook_targets/verify_hook_rvas checked table arithmetic but not duplicate RVAs - the duplicate-RVA reject is tooling debt for the fix session |
| hot-path probes pay the original read count - new reads go behind the change gate, not into the loop | 09-06 p2-194b (6 extra guarded reads on the walker's hot path stalled the mac's landing transition; states moved post-gate, d5ed2ae3f12e42fb) | template | R8: lane-brief probe-design rule (new reads behind the gate, never into the loop); the session's four instrument defects (guard, hash, dual detour, hot-path cost) all shared one shape: shipped without their negative test - the postmortem's closing lesson is that instrument changes need the same gates as shipped code |

## TABLE 4 - WORKFLOW / DOC / REGISTRY

| Rule | Status | Mechanism |
|---|---|---|
| NST: parse (and smoke) before run | gated-parse | pre-commit hook blocks unparseable .py/.sh at commit; the smoke half is rubric |
| METHOD: contract-first, census before port | template | lane-brief Step 1 (divergence census before implementation) |
| doc budgets + STATUS lines + index freshness | gated | bootstrap_check prints budgets, STATUS presence, INDEX staleness every session |
| the registry vouches BOTH directions + the router's files exist | gated | registry_audit: caps exact-match both ways (ROW-MISSING drift), ROUTER MISSING FILE fail, untracked warn |
| check-before-you-fork (TOOLS first) | manifest+judgment | TOOLS.md rows with caps; toolsq.sh (ANSWERS-field search) is BACKLOG |
| state-changing actions pre-register hypothesis/expected | gated-assist | decision_log.py (register/complete/show; OPEN decisions visible) - the HABIT is rubric |
| HOOK COUNT == install-table arithmetic | gated | gate_boot ties the brief to verify_hook_rvas' TARGETS TABLE line (the true hooks-installed count; rva==0 skipped entries surface as a mismatch) |

## THE VERIFY RUBRIC (where rubric rows go)

.opencode/agent/verify.md, fixed shape, <=30 lines: completion semantics,
both negatives, chain marks, provenance, liveness, scope of authority,
graphics delta, regression (ARH2), and the re-chase check (q.sh on the core
terms). Cite exact lines; UNKNOWN-FROM-ARTIFACT rather than assuming; never
soften a FAIL.

## INCIDENT -> NOTCH (the adaptive-tightness mechanism)

A future incident lands as ONE row here (rule, source, status, mechanism or
"rubric - conversion candidate"), never a new paragraph of prose elsewhere.
When a rubric row converts to a gate: update the row, cite the incident, run
the negative test that proves the gate FAILS on the pre-fix state (09-05
FAILURE 2 applied to the tooling itself), and register the tool in TOOLS.md
(REGISTRY caps) so registry_audit can vouch for it.

## OPEN CONVERSION CANDIDATES (debt, not protection)

- "front closed by answering its question" - could gate on the verdict
  restating the brief's PURPOSE question. Rubric today.
- toolsq.sh (ANSWERS-field capability search) - kills the 08-30 A4 class
  mechanically; backlog.
- negative_audit tool-blindness flag (T2.3) - flag scan-negatives citing
  bare grep over RE_build//RE_output; backlog.
- T3.1 budget-exhausted marker - CLIENT-side log format; ships with the
  pen's next client build, not by a tooling session.
- ARH1-8 (lane anti-rabbit-hole) - only ARH1 (one-motion) has a mechanical
  form (decision_log) and ARH2 (regression) a rubric line; the group needs
  its own pass before individual rows can be honest.
