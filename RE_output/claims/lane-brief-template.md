# LANE BRIEF TEMPLATE (contract-first, 2026-08-15)

Every implementation lane's brief follows this shape. Step 1 is mandatory — the
divergence census comes BEFORE any code. (The METHOD: the in-process Sunrise DLL is
the only proven-working server implementation; its behavior is the spec; divergence
is a bug until proven otherwise.)

## Step 1 — DIVERGENCE CENSUS (always, before implementation)
- Grep the fork for every mode-gated branch touching this subsystem:
  `core::settings::get().client.externalServer` + any other settings-dependent
  condition in the flow's code (hooks, routes, state, encoders).
- Build the divergence table: | site | in-process behavior | external behavior | status
  (ported / this-lane / latent) |.
- Diff the response/delivery semantics for every network touch (the headers, the
  framing, the synchronous-completion vs real-HTTP difference).
- Output: RE_output/claims/<subsystem>-census.md with the table + the verdict
  (what must be ported, in order).

## Step 2 — implement the ported behavior
- Each table row = one change. Mirror the in-process semantics exactly (including
  the empty-success routes, the ordering, the defaults when a key is absent).
- The acceptance for each = the in-process behavior reproduced on the standalone
  (the byte-level or the semantic equality per the row).

## Step 3 — gates
- Build + smoke + the probes that prove the ported behavior (curl/python, zero
  game boots wherever possible).
- A game boot happens ONLY when the census says "nothing left" or "here is the
  specific candidate" — never as a theory test.

## DEATH SAFETY (2026-08-16, hard — the lane-survival contract)
The observed lane deaths (the cuid TBD-shell case, the silent-cap pattern) all
died the same way: the analysis ran, the SYNTHESIS never landed. The rules:
1. **Per-phase claims, never end-of-run.** Write each claim into the deliverable
   the moment its phase's evidence lands — the raw first (crash-safe, flush per
   write), the claim text right after. A claim never waits for the FINAL.
2. **Near-limit = stop-and-write.** When the budget tightens: finish the current
   claim, list the remaining targets as OPEN items with their evidence pointers,
   stop. A partial deliverable + the raw = fully recoverable; a TBD shell = the
   main session does the lane's job.
3. **The priority order: raw > per-phase claims > log > report-back.** The
   report-back is OPTIONAL; the files are not. Spend the last budget on the files.
4. **The collector fallback is assumed.** If the lane dies mid-synthesis, the
   MAIN SESSION completes the deliverable from the raw — the lane's job is the
   evidence + the per-phase claims, never "write everything at the end."
5. **No sleep/poll loops; submit-and-release.** Long tool runs = background mode;
   one spawn, one report, end the turn. The main session harvests via the
   artifact mtimes + the completion notification, never the lane's own polling.

Report-back stays <=3 lines per ARH4.

## SCAN-NEGATIVE HYGIENE (2026-08-31 - a coverage limit is not a world-fact)
Every zero/none finding ("0 refs", "no writers", "statically unreachable")
MUST record an `ENCODEDS:` line in the claim stating exactly what forms and
encodings the scan searched. A tool's coverage limit promoted to a structural
claim is the 20.209 R2 class - three incidents: xref_scan form-filter,
field_xref disp32-only, image-encoded-pointer scans against
RUNTIME_BASE-relocated .data. Pointer scans over .data/.rdata use
xref_scan.py --ptrs (dual-encoding: image + relocated). The corpus carries a
flagger: RE_scripts/negative_audit.py.

## DEAD-END AUDIT (required when the lane works to escape a recorded dead end)
Before building any instrument to escape a dead end, answer in one line:
`DEAD-END AUDIT: <the cheap check that would falsify the dead end's premise>`
If the premise dies to a cheap re-check (existing tool, known encoding fact),
do that instead of building. Precedent: 20.209 R2's "statically unreachable"
died to a 5-minute relocated-pointer scan - after a 6.5GB dump tool was built.

## PROBE DESIGN RULES (2026-09-05 - from POSTMORTEM_2026-09-01/09-03; each
## rule names the defect it kills)
- LOOKUP PROBES LOG THE KEY (09-01 DEFECT 1, three boots): a probe on a
  lookup function emits pool + queried id + result, never the result alone.
  "Returns 0" is not a measurement until you know what was asked.
- NOVELTY GATING, NOT COUNTS (09-01 DEFECT 2): when the event is late in a
  hot path, gate on first-seen key (the pooldisp seen-bitmap shape), not a
  line budget. A budget measures the beginning of a boot; novelty measures
  the boot. Budgets still apply per event class.
- CONTROL FIRES VERIFICATION (09-01 DEFECT 3): before shipping a positive
  control, confirm from a PRIOR boot's logs that the control event occurs in
  the scenario under test. A control chosen without that check is decoration.
- DERIVED-LINES RULE (09-01 DEFECT 4): a log line reporting what was sent is
  derived from what was SENT, never from what was INTENDED. An instrument
  that overstates the wire is the defect class that burns boots later.
- FIXTURE REPLAY BEFORE DEPLOY (09-01 addendum + 09-05 FAILURE 3): replay
  EVERY new trigger in a build over a recorded boot's lines before it ships
  - `RE_scripts/replay_trigger.py <archive> --pred <fixture.py>`. A
  recorded run is a fixture; shipping without the replay spends a launch to
  run a unit test. EVERY change, not the one that feels riskiest.
- LOG THE GATE'S OPERANDS (09-01 attempt 1): a probe that logs the context
  of its own decision (every input to its dump predicate, on every call) is
  debuggable from ONE run; log outcomes only and you guess again.

## NIGHT-WAVE RULES (POSTMORTEM_2026-09-01_THE-NIGHT-RUNNER)
- One lane per wave is spawned FIRST whose deliverable is the evidence that
  the current front is real - and it is allowed to come back "it is not"
  (falsify-the-front).
- Readiness language separates CALLEE-PROVEN (a femu proof is about a
  function) from ROUTE-PROVEN (the call happens). "femu-verified end to end"
  says nothing about whether a fork-sent message reaches the handler.
- Census claims carry their DENOMINATOR: "6 tables x 4 of 32 records", never
  "6 tables, all records".
- Observables are expressed RELATIVELY ("the other client's first-registered
  identity key") unless proven stable across boots.
- A red-team dispute BLOCKS the synthesis line it touches; contradictions
  between the wave's own artifacts are resolved before synthesis, never
  averaged into a recommendation.

## Standing rules (unchanged)
- READ-ONLY on the fork unless the brief says otherwise; no git commits; the edit
  scope from the brief; stop stale sunrise-server.exe before smokes; the cache
  re-stamp after every rebuild; claims schema (## CLAIM / - addr / - claim /
  - evidence / - confidence); write early and often; FINAL section.
- New traps discovered → RE_scripts/domain_brief.md trap list.
