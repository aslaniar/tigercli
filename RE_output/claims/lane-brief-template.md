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

## Standing rules (unchanged)
- READ-ONLY on the fork unless the brief says otherwise; no git commits; the edit
  scope from the brief; stop stale sunrise-server.exe before smokes; the cache
  re-stamp after every rebuild; claims schema (## CLAIM / - addr / - claim /
  - evidence / - confidence); write early and often; FINAL section.
- New traps discovered → RE_scripts/domain_brief.md trap list.
