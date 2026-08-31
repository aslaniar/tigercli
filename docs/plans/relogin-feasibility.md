# Plan: re-login without client restart (feasibility -> implementation)
Priority: QUEUED - behind boot-gate v3 (the deterministic enforcement layer,
which takes priority; see ~/.opencode/plan/boot-gate-v3.md). Do not start
this until that ships.

## THE PROBLEM
Every server rebuild + restart kicks the client to title. Re-login then hits
marionberry until the client is FULLY restarted - and the restart (cold
shader compile, full boot sequence) is the bulk of every boot test's cost.

KEY CLUE: a client restart ALWAYS fixes it. Whatever breaks re-login is
client-side, in-memory, and cleared by restart.

## CANDIDATE FAMILIES (to be discriminated, not assumed)
A. STALE CLIENT SESSION STATE: return-to-title keeps the old session key,
   sequence counters, member bindings in memory; re-login resumes with them;
   the fresh server cannot validate them -> marionberry.
B. IDENTITY MISMATCH: content/build identity cached client-side vs the
   restamped new binary -> fails before signon.

## PHASE 1 - DISCRIMINATOR (cheap; pen session owns server restarts)
Three restart variants, each with client-log + server-log capture
(loggrep the signon/ev= lines at the marionberry moment):
  1. same binary, same state.db, server restart only
  2. new binary, restamped, same state.db
  3. full deploy (new binary, new state) - known-fail baseline
Variant 1 working => Family B (identity). Variant 1 failing like variant 3
=> Family A (client session state). Either result names the subsystem.

## PHASE 2 - LOCATE
- Client log at the marionberry moment names the failing step (the SignOn
  flow is already mapped: svc-25/26 handshake, bootstrap tokens, schema).
- Static: beacons/funcq the error site; the signon handlers and the svc-25/26
  path are already-mapped territory (claims + femu/bapdecode work).

## PHASE 3 - FIX (two families, server-side preferred)
- SERVER-SIDE (pen owns server code): persist BAP session keys/nonces in
  state.db across restarts (TLS session-resumption style) so a client
  presenting its old session resyncs; or accept + force full re-handshake
  on login rather than failing.
- CLIENT-SIDE (DLL, ships like any DLL change): a return-to-title hook that
  clears stale signon state, forcing renegotiation. Needed if the client's
  re-login path only ever tries session-resume (phase 2 answers this).
- femu's role: replay the failing signon/apply functions against dump state
  to test fix hypotheses without boots.

## HONEST UNKNOWNS
- Which family owns it (phase 1's purpose).
- Whether the client's re-login path can re-run FULL signon or only
  session-resume (static question, phase 2).
- Whether the marionberry site is client-code or a Steam-layer pass-through.

## PARALLEL CHEAP WIN (independent)
Client-restart cost is mostly COLD SHADER COMPILE (no persistent
MoltenVK/DXMT cache on this Mac). Persisting the shader cache shrinks every
full restart regardless of this fix. Small, separate, worth doing anytime.

## ACCEPTANCE
- Phase 1 produces a named family with log evidence.
- The fix: server restart + re-login from title, client NOT restarted,
  reaches the Tower. Regression: a full client restart still works.
