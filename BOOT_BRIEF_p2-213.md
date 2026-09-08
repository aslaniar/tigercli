# BOOT BRIEF p2-213 - THE POKE: FORCE THE LIVE GATE, MEASURE THE SECOND HALF

STATUS: prepared 2026-09-08 evening (session ses_f7d51b158ffe0zTn97f4s5dZGv).
FRONT: multiplayer-chain - the event-21 handoff's step 1 (HANDOFF_2026-09-08_EVENT-21.md:
"THE DIAGNOSTIC POKE - do this before building an emitter").
INSTRUMENTS: poke (P1) + state_set + tail_gate + obj_gate + cons_tick + attach_w +
mode23_w + activate + phase_init + br_fcc10 + br_bef0 + gatewatch.
Built client: 04a06084c542fa22 (steam_api64.dll, this Mac, make -j8; literals asserted
in the binary: stage=poke / stage=gatewatch / poke_state9 / state_set / tail_gate /
attach_w / phase_init all present). Server: UNCHANGED 45acf511c6021990 - no server arm.

## PURPOSE (what this boot learns, win or lose)

THE POKE (P1). 20.353 R6 measured that everything downstream of event 21 is
"willing": the executor evaluates OUR session (sid=2, 0x4631748), the C2 guard
returns TRUE 9/9 on it, and the executor idles 65,308x waiting for 6..9. The
inferred second half (attach -> establish -> queue producer -> activation ->
construction -> render) has NEVER RUN in any boot, and has NO working reference
to diff against (the local player renders through a disjoint self-only path -
the pasted-session correction, verified 20.260/20.321). This boot forces the
one missing input - the session's live state - and measures the cascade.

THE POKE'S MECHANISM (governance-clean): when the executor's own resolver
(exec_sess 0x140C03F70, already shipped) returns our session parked at
gate-state 4, the observer calls the REAL session-state setter 0x1417B3600
ONCE with (session, 9, 0x30) - byte-for-byte what 20.350 R1's chain-3 last hop
does, edge-detection bookkeeping included. Settings-gated client.poke_state9
(default false), one atomic one-shot guard, logged before and after. THE
GOVERNING CONSTRAINT: this is a throwaway DIAGNOSTIC per the AGENTS.md
allowance - it answers "does the cascade work when the gate passes"; it is
never a delivered mechanism; a relaunch without the setting is the revert.
(The p2-161 gate_poke precedent and its incident are the reason this is
settings-gated and one-shot; 20.268 records that poke's measured effect.)

Everything the cascade could touch is instrumented BEFORE the poke fires:

| stage | instrument | pre-named "fired" reading |
|---|---|---|
| attach | attach_w (0x140B53FC0, the mode-1 writer) | calls rise; mgr+0x8 -> 1 |
| attach (distinguish) | mode23_w (0x140B534A0) | separates attach from world-entry writes |
| establish/queue | (no direct hook - producer-silent BY DESIGN until attached; the attach verdict is the design-proof) | - |
| activation | activate (f7da0 0x1416F7DA0) | calls rise; gatewatch b09 falls 1->0 (f7da0 clears it), b05/b07 clear, af3/B00/AF8 arm |
| activation (class) | phase_init (0x140B37BF0) | calls rise; the vft-0x141C14F70 class finally constructs |
| construction | recv_root (already shipped counter) + tail_gate/obj_gate/br_fcc10/br_bef0 | tail_gate flips true; recv_root's calls continue but a DEEPER branch passes; ent ctor has no hook (pdata gap - pre-named) |
| render | the boot's own eyes + the site-214 failure count | a guardian carrying the PEER's identity, moving when they move |

gatewatch (new, every census) dumps af0/af3/b00/af8/b04..b0a + recv_root's
encrypted pointer global - the corrected 20.354 flag set, so the cascade's
progress is visible even where no hook exists.

## GRAPHICS DELTA

None by design. The poke changes one session-state byte through the game's own
setter; no rendered content is added or removed by the instrument. IF a peer
guardian renders, that is THE GOAL arriving (the row-10 acceptance), not a
delta to minimize. The acceptance test: the rendered entity carries the PEER's
account and character and moves when they move - NOT a repeat of 20.53's "You".

## FALSIFIABLE CLAIM

CLIENT (04a06084c542fa22): the DLL installs 81 targets (kTargetsSize 81 ==
initializer count, verify_hook_rvas PASS 131 RVAs / 0 bad / 11 not-code);
with client.poke_state9=true the first exec_sess leave that returns our
session at state 4 emits `stage=poke ... armed=1` then `verdict=executed
state_after=9` (the setter's own edge-detection makes the field read 9
immediately after the call); within the same boot attach_w's calls rise from
its boot-long baseline (0 expected pre-poke) and gatewatch shows b09 fall.

CONTENT NEGATIVE (the revert): with poke_state9 absent/false the poke emits
NOTHING (the setting gates before the one-shot check), and the client's
game-visible behavior is otherwise byte-identical to 2f45faa's - 10 new
counter rows, 2 retwatch rows, 1 sampler line per census.

## ABSENCE NEGATIVE (L13: what ZERO instrument lines means)

- poke lines MISSING ENTIRELY (with the setting on) -> exec_sess never
  returned our session at state 4 post-landing (the trigger never armed) OR
  the deploy is stale. First check `attached=1` on the exec_sess census and
  the settings literal in the deployed file; then read exec_sess's
  sessstate lines for the state sequence (1->2->4 must appear first).
- poke `armed=1` but NO `verdict=executed` -> the setter call crashed the
  detour thread - the last line IS the finding; the 38-byte primary's detour
  is the suspect (pre-named in the CHAIN MARKS).
- poke executed, state_after=9, and attach_w NEVER rises -> the executor's
  SECOND conjunct (the world-change half) did not hold at the poke moment -
  the cascade answer is "state alone is not enough"; retry design moves to
  poking during an actual world-change tick (pre-named follow-up, not a
  third branch improvised).
- attach_w rose and gatewatch b09 never fell -> the arm sequence
  (f7da0) did not run despite attach - the queue-producer/establishment step
  is the wall; br_fcc10/br_bef0/recv_root readouts locate it.
- EVERYTHING fired but no guardian -> construction consumed but render
  refused: the row-10 acceptance failed on identity (20.53's "You" class) -
  the acceptance test's pre-named failure.
- ARCHIVE GUARD (20.336 R1): before reading ANY null, all three archives
  (server/mac/rig) must exceed the startup-only stub decisively; verify the
  server log GREW past startup before the boot ends.

## CHAIN MARKS (L16)

- executor evaluates OUR session (sid=2), climbs 1->2->4, stops ..... verified-by-execution (20.353 R1, exec_sess, both machines)
- the C2 guard returns TRUE on our session 9/9 ....................... verified-by-execution (20.353 R2; LIMIT: C2b/C2c read the packet - other events' bodies only)
- the event-21 handler chain ends in set_session_state(sess,9,0x30) .. verified-by-reading (20.350 R1/R2, unconditional once entered)
- the setter's signature (session, new_state, reason) ................ verified-by-reading (20.349 R6)
- the poke replicates chain-3's exact call ........................... this boot's instrument (the call IS the claim)
- the tail gate 0x1416FC6D0 = 5 gate-cluster bytes + 0x1412A8C70 ..... verified-by-reading (p2213prep_notes.md; disasm this session)
- all five tail-gate bytes satisfied in every archived dump .......... verified-by-execution (20.354 R1, 4 dumps, 0x143051FA8 oracle)
- af0=1 everywhere; 20.339 R6's af0/AF8 transposed ................... verified-by-execution (20.354, banked correction)
- recv_root dispatched and bailing ................................... verified-by-execution (20.353 R4, 12,258 calls)
- WHAT THE POKE CASCADE ACTUALLY DOES ................................ unknown (this boot measures - the whole point)

## ADVERSARIAL PASS: three ways this boot could mislead me

1. THE POKE FIRES TOO EARLY. exec_sess runs 65,308x a boot; the FIRST leave
   with our session at state 4 may precede the landing (the session climbs
   1->2->4 during join, before the tower world-change). A poke before the
   world-change context exists tests nothing. Mitigation as designed: the
   one-shot fires on the FIRST state-4 return - if the cascade reads null,
   the poke timestamp vs the landing timestamp is the FIRST thing to read,
   and the re-poke-during-world-change follow-up is pre-named above.
2. THE SETTER CALL FROM THE DETOUR THREAD. 0x1417B3600's primary is 38
   bytes + chained fragments; the detour is on ITS start, and the poke CALLS
   it - re-entrancy through our own detour. The setter's first store
   (0x1417B37DE) is in a fragment, so the call runs game code under our
   hook. If the client dies, the last line (`stage=poke ... armed=1`) names
   it; the fallback design is a raw field write (state_after=9 via
   [slot+0x1AEF8]=9) which skips the bookkeeping - pre-named as P1-raw.
3. ATTACH ATTRIBUTION. attach_w rising could be mode-2/3's world-entry
   write, not the poke's attach - that is what mode23_w is for. Read the
   two counters TOGETHER; attach_w without mode23_w is the poke's signature.

## PRIOR ART (09-05 FAILURE 5)

- q.sh poke: 20.268 - "THE POKE DID CHANGE SOMETHING. ent_gate went from 0
  calls in nine boots to..." - the p2-161 gate poke's measured-effect record.
  THIS boot's poke is a different mechanism (a setter CALL, not a gate-byte
  write) and is the SANCTIONED use of the diagnostic allowance that incident
  forced into writing. Cited, not re-chased.
- q.sh state_set: no hits - a new probe family on an existing chain.
- The cascade's static map: 20.349 (the setter + reachability), 20.350 (the
  three chains, chain-3 = state 9, unconditional), 20.351 (the pump), 20.353
  (the measurements), 20.354 (the corrected flag set).

## DEAD-END AUDIT (required: prior art touches retracted work)

- The p2-161 poke incident: NOT repeated - that poke wrote a gate byte as a
  mechanism-shaped change; this one is a declared one-shot diagnostic that
  reverts at relaunch, and the brief says so (the governing constraint's text).
- 0x1416CA0B0 (the p2-147a frozen-client suspect) is NOT re-added as a hook -
  recv_root's existing counter + the deep-branch rows carry the construction
  question from the clean-code side.
- The ent ctor 0x1416BB1E0 is NOT hooked (pdata gap - refused by the tool,
  recorded). Its firing would have been nice; its absence from the table is
  pre-named here so a construction is not read as "no hook fired = nothing
  happened".
- 20.53 is NOT cited as a render control (retracted): the acceptance test is
  the peer's identity and movement, not the local player's render.

## STATE READERS (a direct reader per asserted state)

- "the poke fired" -> `stage=poke ... armed=1` + `verdict=executed state_after=9`
- "the session went live" -> state_set enter lines (rcx=our session rdx=9)
  and gatewatch (af3/B00/AF8 arming IF the cascade reaches the transition)
- "the attach happened" -> attach_w calls>0 WITHOUT mode23_w; gatewatch has
  no mgr+0x8 read (the manager's +0x8 is behind the per-boot-encrypted
  global - pre-named uninstrumented this boot; attach_w's firing is the
  attach evidence, not a byte read)
- "the activation ran" -> activate calls>0 + gatewatch b09 1->0
- "the sequencer started" -> phase_init calls>0
- "construction crossed the tail" -> tail_gate flips true; br_fcc10/br_bef0
  enter lines name WHICH deep branch passed or refused
- "the archive is complete" -> all three logs past the startup-only stub

## EFFECT CLAIM (distinct from delivery)

DELIVERY (claimed by this boot): the poke executes once at state 4; state
reads 9 after; every cascade instrument above reports; the gatewatch line
family exists per census. EFFECT (pre-named, NOT claimed here): the full
second-half cascade to a rendered peer. If delivery succeeds and the effect
does not follow, the instrument table names WHICH link stopped - that is the
boot's product either way. No new front is opened from this boot's data
without that separation.

## ABANDON OUTCOME (pre-named)

Set client.poke_state9 back to false (or delete the key) and relaunch: no
write of any kind - the revert is the settings flip, no rebuild. If the
cascade does not fire: the emitter work (event 21) was never the answer and
the front moves per the tree above (executor's second conjunct / the
queue-producer step / the deep branches) - each destination pre-named, no
third branch improvised from a null.

## WIDE NET (probes at every decision point on the suspect chain)

- The full census (81 targets, zeros included) every ~15s: any unexpected
  riser beside the pre-named set is visible without a new instrument.
- gatewatch per census: the flag set's timeline, including the constants
  (af0=1) whose constancy is itself checked.
- Existing shipped instruments untouched: evt_sub (complete enumeration -
  does event 21 arrive once the session is LIVE? the poke boot doubles as
  that test for free), sess_guard, exec_sess, resv, recv_root.
- The site-214 `failed to create 'player_broadcast'` count on both machines
  (the C2-attributed canary; also the only string the entity subsystem
  emits - it MUST move if construction starts consuming).

## FIX SURFACE: client | server

CLIENT (instrument + diagnostic only): milestone_trace_observer.cpp (10 new
rows, gatewatch, the poke), settings client/definition.h + parser
(poke_state9). No .text patching; the poke is a settings-gated one-shot
through the game's own setter.

SERVER: NOTHING. 45acf511c6021990 unchanged. (The event-21 emitter is boot
2's server-side work and is deliberately NOT built before this boot - the
poke can invalidate it, which is why it goes first.)

## NEGATIVE TEST (the arm that fails on the bad state, and where it RAN)

1. verify_hook_rvas (this session, rc=0): 131 RVAs checked, 0 bad, 11
   not-code (the labelled data class); install table 81 == initializer
   count; static_assert guards the size match.
2. probe_audit (the 09-06 BLIND-GUARD gate, rc=0 after the fix): PASS -
   the audit FOUND a real defect first (sess_guard's leave coverage was
   missing from the p2-212 build; fixed with first_seen_leave + the
   no-leave citation) - the gate worked, recorded.
3. Build clean (llvm-mingw, make -j8); instrument literals grep-verified in
   the BUILT binary (stage=poke / stage=gatewatch / poke_state9 / state_set
   / tail_gate / attach_w / phase_init, all >=1).
4. The poke's own negative: settings-gated before the one-shot; slot
   null/misalignment refused before any dereference; state!=4 refused
   before any call.
5. Settings staged with backup: Game/bin/x64/Sunrise/
   settings.json.bak_p2213_prepoke; client.poke_state9=true staged on the
   MAC. THE RIG's settings staging + both client deploys are pre-flight
   steps (below).

## INSTRUMENTS

- poke (P1): the one-shot setter call, exec_sess-triggered.
- state_set / tail_gate / obj_gate / cons_tick / attach_w / mode23_w /
  activate / phase_init / br_fcc10 / br_bef0: the cascade rows.
- gatewatch: the corrected flag set, per census.

### READOUT TRIGGER

- poke: on the first exec_sess leave returning a state-4 slot (settings on).
- enter lines: per-call up to each row's budget (state_set 64 - the
  working sessions' transitions share it; if the budget exhausts early the
  pre-named reading is "read the census counts, not the missing lines").
- retwatch (tail_gate/obj_gate): on VALUE CHANGE only.
- gatewatch: every census (~15s wall-clock floor).
- cons_tick: counter-only (hot path; budget 0 = census counts only).

PER-INSTRUMENT TRIGGER PROVENANCE (T2.1):
- evt_sub / recv_root / sess_guard / exec_sess / state_set-adjacent shipped
  rows: EMITTED UNDER THESE TRIGGERS in RE_output/logs/20260908_132021_p2-212
  (mac t=113477 first evt_sub enter; recv_root census calls=13437; sess_guard
  enter+ret lines x9) and 20260907_205125_p2-211.
- poke: NEVER-OBSERVED (first-fire risk) - new instrument. Mitigations: the
  trigger is an ALREADY-FIRING hook's leave path (exec_sess emitted under
  exactly this trigger in p2-212); the one-shot is atomic; both lines log
  before and after the call.
- state_set: NEVER-OBSERVED (first-fire risk) - new row, but the enter-line
  shape is the framework's generic (emitted by every row in every boot);
  risk = the setter is never called (that null IS the finding, per the
  absence tree: the working sessions' climbs must pass through it - if
  state_set never fires while the client's own sessions still reach 6, the
  38-byte primary's detour is the suspect, pre-named).
- tail_gate / obj_gate: NEVER-OBSERVED (first-fire risk) - retwatch
  change-gates them; risk = called at 12,258x rate with a hot first line.
  Budget 16 caps the enter lines; the census counts uncapped.
- cons_tick / attach_w / mode23_w / activate / phase_init / br_fcc10 /
  br_bef0: NEVER-OBSERVED (first-fire risk) - new counter rows on pdata-
  verified starts; the census's attached=1 line is their liveness proof
  (the p2-211 pattern: attached=0 is a deploy defect, not a verdict).
- gatewatch: NEVER-OBSERVED (first-fire risk) - new sampler INSIDE the
  existing census path (emit_summary emitted per census in every prior
  boot); risk = an offset error in the flag reads. Mitigation: the af0 byte
  has a KNOWN value in every archived dump (0x01 per 20.354) - the first
  gatewatch line self-oracles: af0=0 in the output means the read path is
  wrong, DISCARD the line, not the boot.

## SERVER-SIDE GAP (U18: what the server was missing)

NAMED, NOT FIXED THIS BOOT - deliberately. The wire item the server is
missing is EVENT 21 on the connected-gate event pump: 20.353 R3's complete
enumeration shows only 8/30/38 arriving; id 21 is the only dispatch id
reaching the handler (0x1416E0250) whose chain ends in
set_session_state(session, 9, 0x30) - the live-state write the executor
waits on. That emitter is BOOT 2's server-side work (behind a default-OFF
gameplay setting, from the fork's own 8/30/38 emission sites), and it is
deliberately NOT built before this boot: the poke can invalidate it, which
is why the poke goes first. THIS boot has no server arm and no server
change: 45acf511c6021990 runs unchanged, and the boot's single variable is
the client-side diagnostic.

### OBSERVER BUDGET

- Per-row budgets cap EMITS only; the census reads g_calls uncapped.
- The poke: one fire per boot by atomic exchange.
- gatewatch: one line per census (80 bytes read + one line).

### CALL FREQUENCY

- cons_tick: hot (per tick) - counter-only, one relaxed increment.
- attach_w/mode23_w/activate/phase_init: rare by function contract.
- state_set: rare (state transitions) - budget 64 is generous.
- tail_gate/obj_gate: recv_root's call rate (12,258/boot) - retwatch
  change-gates the detail lines; cost = one call + compare.

### HOOK COUNT

81 == verify_hook_rvas' TARGETS TABLE count on this boot's tree (run this
session; 131 RVAs checked across both observers, 0 bad).

### INSTRUMENT LIVENESS: poke, state_set, tail_gate, obj_gate, cons_tick,
attach_w, mode23_w, activate, phase_init, br_fcc10, br_bef0, gatewatch

### INSTRUMENT SOURCES
  RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks/milestone_trace/milestone_trace_observer.cpp
  RE_build/Sunrise-fork-inventory/Sunrise/src/core/settings/client/definition.h
  RE_build/Sunrise-fork-inventory/Sunrise/src/core/settings/client/client_settings_parser.cpp

## SETTINGS DELTA (the boot's only settings change)

- ADD: client.poke_state9 = true (mac STAGED this session, backup
  settings.json.bak_p2213_prepoke; rig stages at deploy). Default false =
  no write of any kind.
- UNCHANGED: the playable baseline (sweep OFF, clientBase TRUE,
  entity_index_allocation TRUE, duty cycle 30000, self-peer-row FALSE,
  cross_member as deployed on 45acf511c6021990); NETWORK stays
  192.168.1.164 (WiFi - verified current).
