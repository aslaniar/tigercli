# BOOT BRIEF p2-211 - THREE ARMS: THE DISPATCH COUNTER, THE SESSION-CHURN WITNESS, THE CROSS-MEMBER MAP

STATUS: prepared 2026-09-08 (session ses_f81347b92ffeJbYtejcBKgVOp5).
FRONT: multiplayer-chain
INSTRUMENTS: recv_root, stage=session_release
Front: the live chart FRONT_multiplayer-chain.md; no prior boot on
this front, ledger streak 0). Built from the staged worktree
.claude/worktrees/fork-p2211 (HEAD 3578d98 + the 13 deployed files + this
boot's three arms). Built artifacts: client 3ee1a38bc19f1c53, server
45acf511c6021990. HOOK COUNT: 69 (119 RVA constants checked, 0 bad; targets table 69/69; kTargetsSize 69 == initializer
count).

## PURPOSE (what this boot learns, win or lose)

One paired boot, three independent readouts, every one informative either way.

1. STAGE D (the structural wall): does anything ever DISPATCH the construction
   chain's root? 20.338 measured the subsystem REGISTERED AND LIVE (descriptor
   object on the heap, the root's address in nine heap records) while the
   constructor has zero heap refs and the receive blocks are absent in six
   dumps - but a dump cannot separate "never dispatched" from "runs and bails".
   The staged read-only call counter settles it in one boot: calls=0 -> nothing
   dispatches entry 0; the question moves to what owns/dispatches the table
   (static read). calls>0 -> it runs and bails, and the 12 budgeted enter lines
   carry caller_rva - WHO dispatches it comes free.
2. STAGE B (the churn): WHY the mac's activity sessions die young (6-9 wire
   snapshots each, then replaced) while the rig's carries 456 - the asymmetry
   that feeds the mac almost no peer rows. The new server line fires on the
   single teardown path with a result field, so the churn is finally
   attributable (released vs kept vs who-called-and-when).
3. STAGE C (C2): does filling the cross-member allocation map (one row per
   joined MACHINE, not just the joiner) reach the client's pool - the
   "failed to create 'player_broadcast' entity" count falls from 17-80 toward
   0, or the client provably does not consume cross-member rows.

## GRAPHICS DELTA

No new rendered models expected by design. The client change is a READ-ONLY
call counter (one relaxed atomic increment per call on the watched function;
zero behavior change). C2 may change rendered content in one direction only:
entities that previously failed allocation could now succeed - if a peer
guardian renders, that is THE GOAL arriving, not a delta to minimize. No
rendered content is removed or substituted.

## FALSIFIABLE CLAIM

CLIENT: the deployed DLL (3ee1a38bc19f1c53) installs a read-only counter at
the construction chain's root entry - a clean .pdata function start verified
this session (bounds 0x140B5ECD0..0x140B5F16D, size 1181, offset 0) - and its
census line `ev=mtrace stage=census fn=recv_root rva=0xB5ECD0 attached=1
calls=N` appears within seconds of DLL load (why=install) and at least every
~15s thereafter (why=periodic), ZEROS INCLUDED. calls is monotonically
nondecreasing across censuses. Budgeted enter lines (<=12) carry caller_rva.
CONTENT NEGATIVE: the counter changes no behavior - with the DLL live the
client's game-visible behavior is byte-identical to be5807eca028ddea's
(the table grew by one read-only target; verify_hook_rvas PASS, static_assert
guards the size/initializer match).

SERVER: every release_session call with a real session id logs exactly once
`ev=activity stage=session_release session=0x<id> result=released|kept`
(locked section first decides, the line prints AFTER the lock drops; the
absent-id early return logs nothing).

C2: with `gameplay.entity_index_allocation_cross_member=true`, each
index_allocation push carries one row per joined machine, caller first
(base 0 never moves) - members=N where N = joined machine count (>=2 during
co-presence). CONTENT NEGATIVE: with the flip OFF (default), pushes are v1's
single row byte-exact (the patch's own default-off design; wire form
re-checked against the first push line this boot).

## ABSENCE NEGATIVE (L13: what ZERO instrument lines means)

- recv_root census line MISSING ENTIRELY -> the observer did not load or the
  deploy is stale: check `attached=` on any census line; attached=0 means the
  install failed (the p2(112) class - treat as a deploy defect, NOT a verdict
  about the chain). attached=1 AND calls=0 across every census -> NOTHING
  dispatches entry 0: a real verdict, the question moves to the table's owner.
- session_release lines MISSING while sessions churn anyway -> the teardown
  does NOT go through release_session: read the group-host binding paths
  (the two callers) and the churn road moves to session CREATION (why the
  mac's sessions are born short-lived).
- C2 members=N ships but mgr_free stays 0 and site-214 failures continue ->
  the client is not consuming cross-member rows: a REAL verdict, not a null.
- ARCHIVE GUARD (20.336 R1 - the rule this brief exists to enforce): server
  logs were STARTUP-ONLY (24/41/24 lines) for 3 of the last 4 boots. Before
  reading ANY null: all three archives (server/mac/rig) must exceed the
  startup-only stub decisively (boot_outcome.py --logdir refuses <500-line
  server stubs); verify the server log GREW past startup before the boot ends.

## CHAIN MARKS (L16)

- D chain root registered and live at runtime ........................ verified-by-execution (20.338: p2-206 dump, descriptor object live, nine byte-identical heap records)
- D constructor never ran (receive blocks absent) .................... verified-by-execution (six dumps, corrected vtable-base needle, 20.336 R4)
- root is entry 0 of the 14-entry table; no direct callers ........... verified-by-reading (20.338 R1; the VMP registration call)
- root .pdata bounds, offset 0, size 1181 ............................ verified-by-execution (pdata_bounds.py this session)
- install table 69 entries == declared size; 119 RVAs ok ............. verified-by-execution (verify_hook_rvas this session, worktree tree)
- census prints every target's calls, ZEROS INCLUDED ................. verified-by-reading (emit_summary: loops kTargets, no budget gate) + verified-by-execution (p2-206 mac log t=6833: `stage=census why=install fn=ent_recv ... calls=0`)
- release_session is the single session-record teardown path ......... verified-by-reading (the only free site; callers: group_host_sessions x2)
- C2: one row per joined machine, caller first, default OFF = v1 ..... verified-by-reading (the patch; the encoder already accepts 64 rows, 20.336 R6)
- client CONSUMES cross-member rows .................................. unknown (this boot measures - the arm's whole point)
- churn = WHO tears the mac's sessions down .......................... unknown (this boot measures)

## ADVERSARIAL PASS: ses_f81347b92ffeJbYtejcBKgVOp5 - three ways this boot could mislead me

1. attached=0 silently reading as "never dispatched": the counter's verdict
   REQUIRES attached=1 on the recv_root census line first. An install failure
   is a deploy defect, not a Stage-D answer. Check attached BEFORE reading
   calls, every time.
2. session_release fires at SERVER SHUTDOWN too (the server is restarted
   between runs and hangs after succeeding): churn-during-play lines and
   shutdown lines will look identical. Separate by timestamp against the
   clients' activity windows, never by presence alone.
3. C2's failure-count collapse could be credited to the map when the pool
   (C1) is the real variable: read mgr_free lines ALONGSIDE the failure count.
   The collapse claim is only sound with the pool fed (members=N pushes) AND
   failures falling together.

## PRIOR ART (09-05 FAILURE 5)

- q.sh recv_root: no hits in FINDINGS/claims/probe families - a new instrument
  watching an existing chain. Verdict: nothing to re-chase; the chain's prior
  art is 20.338.
- q.sh session_release: no hits - the teardown path has NEVER been observed;
  that absence is the point of the server arm.
- q.sh cross-member: 20.337 - C2 built as a patch, NOT applied; C1 (cadence)
  withdrawn (17 pushes spread across the whole boot). Verdict: this boot
  applies and tests it.
- The construction chain's dispatch question itself: 20.338 R3 - runs-and-bails
  vs never-dispatched UNMEASURED; the counter is the settling instrument named
  there.

## DEAD-END AUDIT (required: prior art touches retracted work)

- ROW 8's "architecturally unreachable" framing (superseded by 20.338): this
  boot does not re-derive it and does not assert either dispatch state - it
  measures. The corrected record (registered and live; constructor absent) is
  the only premise used.
- The join-relay road (p2-181..p2-195, CLOSED on its own question): untouched;
  no relay settings change.
- CLAIM O / svc21 grant (REFUTED): C2 does not build any grant body onto
  svc21; the catalogue reply is untouched.

## STATE READERS (a direct reader per asserted state)

- "the counter is live and its count" -> the CLIENT's own log:
  `stage=census fn=recv_root attached=? calls=N` (zeros included; the census
  printer emit_summary loops every target with no budget gate).
- "who dispatches the root" (only if calls>0) -> `stage=enter fn=recv_root
  call=N caller_rva=0x...` (budget 12, first 12 calls sampled).
- "who tears a session down" -> the SERVER's log:
  `stage=session_release session=0x... result=released|kept`, attributed by
  timestamp against the surrounding `ev=activity` / group lines.
- "cross-member rows ship" -> `index_allocation push members=N` (N = session
  members during co-presence, >=2).
- "the pool and the failures" -> the existing per-boot lines: manager
  free-count reads and the site-214 `failed to create 'player_broadcast'
  entity` count on BOTH machines.

## EFFECT CLAIM (distinct from delivery)

DELIVERY (claimed by this boot): the census numbers exist with attached=1;
the release lines name every teardown with a result; members=N pushes ship
when the flip is on. EFFECT (pre-named, NOT claimed delivered here): filling
the map reduces the creation-failure count toward 0 (requires the client to
consume cross-member rows - C1's drain rate may still outpace supply), and
naming the churner enables the Stage-B server fix. If delivery succeeds and
an effect does not follow, the readout names which link failed; no new front
is opened from this boot's data without that separation.

## ABANDON OUTCOME (pre-named)

Set `gameplay.entity_index_allocation_cross_member=false` and relaunch: pushes
return to v1's single row byte-exact, no rebuild (the flip is the whole arm).
The counter and the release line stay live and harmless (read-only logging).
If calls=0 AND the churn stays unattributed after the lines are read: the
dispatch road abandons to the static question (what owns/dispatches the
table) and the churn road abandons to session CREATION (why the mac's
sessions are born short-lived) - both destinations named in the chart, no
third branch improvised from a null.

## WIDE NET (probes at every decision point on the suspect chain)

- The census prints EVERY target's calls, zeros included - so the full
  receive-cluster picture (ent_recv / ent_header / ent_create and the other
  66 targets) returns for free each ~15s; a calls>0 on any of them beside
  recv_root is visible without a new instrument.
- Existing index_allocation push lines + mgr_free reads + site-214 failure
  counts (both machines) - unchanged format, so the C2 readout compares
  against every prior boot's baseline.
- Existing membership_peer / same_account / wire_snapshot lines - the churn
  context, read via chain_status.py (the tool that refuses to summarize the
  three line families, the 20.337 regression's countermeasure).
- Server shutdown/restart lines - so shutdown-time release lines are
  separable from play-time churn (adversarial pass item 2).

## FIX SURFACE: server | client

CLIENT (instrument only): milestone_trace_observer.cpp - one read-only
target row + kTargetsSize 68->69. No behavior change; fills no wire gap.

SERVER (behavior + observation): activity_session_release.cpp (the teardown
line), the C2 cross-member allocation (definition.h + parser + push call
site + the member-identity map).

### SERVER-SIDE GAP (U18: what the server was missing)

1. The cross-member allocation rows: the fork's own call-site comment says
   "the cross-member map is deferred" while the comment above it records the
   consequence - "without it every player_broadcast creation returns -1" -
   and every archived boot shows 17-80 of those on both machines. The
   encoder has always accepted 64 rows; only the call site passed one. This
   boot supplies the rows behind a default-OFF flip.
2. The teardown path was UNLOGGED: release_session decided silently, so the
   churn (20.338 R4) could never be attributed. This boot adds the line.

## NEGATIVE TEST (the arm that fails on the bad state, and where it RAN)

Ran this session, each arm naming its fixture and result:
1. verify_hook_rvas on the worktree hook tree (rc=0, fixture
   RE_scripts/verify_hook_rvas.py + RE_scripts/hook_targets.py): 119 RVAs
   checked, 0 bad, 11 not-code (the labelled data-constant class), install-table
   arithmetic
   clean at kTargetsSize 69 == initializer count. The negative form is the
   09-05 crash class: a {nullptr,0} tail target detouring RVA 0 is caught by
   the compile-time static_assert (all_targets_populated) and the table
   check - it cannot reach a boot.
2. probe_audit (the 09-06 BLIND-GUARD gate, rc=0, record in
   RE_output/map/probe_audit.json): PASS, 0 findings, 111 hook files.
3. The staging script's own anchor asserts (fixture apply_p2211.py, run in
   the worktree this session): the original draft targeted
   activity_session_lookup.cpp where release_session does NOT exist - the
   missing-anchor class caught it BY READING (no boot spent); rewritten to
   the real path (transactions/activity_session_release.cpp,
   tail anchor after the lock release).
4. Literal presence grepped in the BUILT binaries (rc>=1 per literal):
   recv_root x1 (client dll), stage=session_release x1 (server exe), the
   cross-member key x1 (both). Deploy scripts re-assert hash + literals on
   the DEPLOYED files.
5. C2 default-off = v1 byte-exact: verified-by-reading (the patch's
   off-branch publishes v1's single row); the wire form is re-checked
   against the first push line this boot before the flip is trusted.

## INSTRUMENTS

- recv_root (client): the read-only call counter on the construction chain's
  root entry.
- session_release (server): the teardown witness line.

### READOUT TRIGGER

- recv_root census: emitted at install (why=install) and every kCensusInterval
  (64 calls) or kCensusMinIntervalMs (15s) thereafter, zeros included - cited
  from the p2-206 mac archive (RE_output/logs/20260907_161050_p2-206/
  mac_sunrise.log t=6833: `ev=mtrace stage=census why=install fn=ent_recv
  rva=0x1718510 attached=1 calls=0`).
- recv_root enter lines: every call up to budget 12 (first-12 sampling).
- session_release: every release_session call with a non-absent id; release
  attempts are rare (session teardown), so absence for a whole boot is
  meaningful (see ABSENCE NEGATIVE).

### OBSERVER BUDGET

- recv_root: budget 12 caps ONLY the per-call enter lines; the census
  counter (g_calls) counts every call uncapped and prints in full. The
  watched function is the dispatch root - per-load/per-message frequency is
  UNKNOWN BY DESIGN (that is the measurement), cost = one relaxed atomic
  increment per call, no reads added inside any loop.
- session_release: n/a (server-side only) - one line per teardown attempt,
  rare by the function's own contract (teardown only).

### CALL FREQUENCY

- recv_root: unknown per-load/per-tick BY DESIGN - the counter IS the
  measurement; the increment is the only per-call cost (one relaxed
  fetch_add, no guards, no reads). Comparable per-call cost to the existing
  ent_recv row (budget 24) which has run in every recent boot.
- session_release: n/a (server-side only), teardown-only (rare).

### HOOK COUNT

69 == verify_hook_rvas' TARGETS TABLE count on this boot's tree (worktree,
run this session: TARGETS TABLE 69/69 entries verified, 0 bad; 119 RVA
constants checked, 0 bad).

### INSTRUMENT LIVENESS: recv_root, stage=session_release

### INSTRUMENT SOURCES
  .claude/worktrees/fork-p2211/Sunrise/src/client/hooks/milestone_trace/milestone_trace_observer.cpp
  .claude/worktrees/fork-p2211/Sunrise/src/state/activity/transactions/activity_session_release.cpp
Sources (worktree): the observer carries `recv_root` (present x1 in the BUILT
client DLL); the transactions file carries `stage=session_release` (present x1
in the BUILT server exe). Preflight --brief verifies the same literals in
the DEPLOYED binaries after staging.

## SETTINGS DELTA (the boot's only settings change)

- ADD: gameplay.entity_index_allocation_cross_member = true (the C2 flip;
  the key ships default false in this build). Applied to
  RE_output/s1_accept/Sunrise/settings.json BEFORE the server starts
  (settings load once at startup - the p2-206 correction), reverted after
  the boot.
- UNCHANGED (the playable baseline, verified this session): sweep OFF,
  session_state_client_base TRUE, entity_index_allocation TRUE (v1 pushes),
  duty cycle 30000, self-peer-row FALSE.
