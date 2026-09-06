# BOOT_BRIEF_p2-182 — ROAD-3 ORACLE PASS: DOES A CLIENT HOST A SESSION AGAINST THE FORK?

STATUS: live (2026-09-05, drafted post-adoption-condition decode). Primary
front: adoption-condition. One contract: the native host-side join/admit flow
is observed firing (or its first precondition named) during a paired boot in
which BOTH clients ATTEMPT to form a fireteam and launch an activity.

## PRIOR ART (required field)
q.sh terms: 0x1417806C0 / 0x141777EC0 / 0x14178CCA0 / adoption-condition /
join_gate. Read in full: RE_output/claims/adoption-condition.md (THE NEW DECODE
- the condition is the host-side join flow, precondition session state 6..9);
FINDINGS 20.108 (the host-side join gate end-to-end) + the DOOR finding
(candidate table, session objects, the refusal reason 4);
establishment-decode.md (the (3,4) stall); 20.310 (relay refuted - relay stays
INERT, settings unchanged). NO prior boot has observed the join processor
0x1417806C0, the admit 0x141777EC0, the add-candidates 0x141792080, the
type-0x0A handler 0x1416E0460, or any session state dword. p2-181's hooks
(join_gate/join_reserve/join_handler/join_msg) are already deployed and carry
over unchanged.

## PURPOSE (ONE CONTRACT)
Determine whether the client-side host machinery can run in our environment at
all: during a paired boot with a deliberate fireteam + activity-launch ATTEMPT,
does (i) any session slot reach state 6..9, (ii) the type-0x0A join processor
fire, (iii) reserve+admit fire, (iv) the peer's record adopt (mask/container
readout). This is the Road-3 viability gate and, on NEG-B, the Road-1 decode
pointer (which session-state input the fork must learn to provoke).

## THE CHANGE (server: NONE. clients: instruments only - the deliberate deploy)

INSTRUMENTS: join_type0a 0x1416E0460, join_processor 0x1417806C0, admit 0x141777EC0, add_candidates 0x141792080, sess_state getter-0x140C26490-exit-read

- server 8a77a5b94c69fc9f UNCHANGED (duty cycle + relay stay as deployed; the
  relay is inert by 20.310 - it is part of the wide net, not the mechanism).
- clients BOTH: +5 read-only hooks (51 -> 56, verify_hook_rvas must PASS):
  join_type0a 0x1416E0460 (enter args + return)
  join_processor 0x1417806C0 (enter args: sess, conn, pkt)
  admit 0x141777EC0 (enter args)
  add_candidates 0x141792080 (enter args: session_id, count)
  sess_state: the session-slot getter 0x140C26490 (rcx = idx, rax = slot) -
  LEAVE-side read of [slot+0x1AEF8] (state), [slot+0x850]/[slot+0x854]
  (container), [slot+0x1C7C0] (session id), CHANGE-GATED per slot pointer
  on the whole tuple, first observation forced (baseline).
- CLIENT-SIDE GAP (governing-constraint ledger): the fork cannot yet PROVOKE a
  hosted session (state 6..9) - that wire item is unnamed (the session-state
  machine's drivers are undecoded). This boot measures whether the HUMAN-DRIVEN
  attempt reaches it; it does not modify client behavior.

## THE STIMULUS (revised 09-06: the fireteam-invite script was NOT executable)
The original action script ("A invites B to fireteam, launch an activity")
assumed roster visibility the fork does not provide (no presence/roster plane
has ever been built; the clients cannot see each other in-game - the user
caught this before the launch). REVISED: LANDING-ONLY BASELINE.
  1. Both clients land (duty-cycled row; p2-180 backdrop). No further actions.
  2. The sess_state reader measures, for the first time ever, the session
     slots' states (+0x1AEF8), the container fields (+0x850/+0x854) and the
     session ids during a normal fork landing.
  3. Any fireteam/invite stimulus is DEFERRED until the roster/invite plane
     is decoded and built (new front, fork-side; the L3 vocabulary -
     player-add 0x22, membership-update 0x1E, boot-machine 0x21,
     delegate-leadership 0x20 - is the candidate carrier family).

## READOUT TRIGGER (required field)
  - sess_state change lines: NEVER-OBSERVED (new instrument). REPLAYED: the
    change-gate logic replayed over the recorded resv_rec transitions (the
    recorded run is the fixture) - RE_output/map/fixtures/
    sessstate_change_trigger.py over the p2-181 archive (197,982 lines) and
    the p2-180 archive (269,415 lines): fires on BOTH (exit 0; sample mac
    t=198432/205417, rig t=68547/68610). The fixture's first two runs
    returned ZERO - both were FIXTURE defects (wrong stage name; wrong ctx
    layer), not instrument facts - each was fixed before the replay passed.
  - join_type0a/join_processor/admit/add_candidates: NEVER-OBSERVED - their
    firing IS the question (first-fire risk, pre-named).
  - join_gate (deployed): fires ~13k/boot (per-tick class - its output is only
    "the pump ran"; NOT an outcome line this boot).
  - resv probe (deployed): change-gated state dumps - the outcome meter.

## PRE-NAMED OUTCOMES (re-read for the landing-only stimulus)
  (a) a session slot reaches state 6..9 during landing alone -> the fork CAN
      provoke a hosted session; capture what triggered it and Road 3 (or a
      direct Road-1 replay of that trigger) opens immediately.
  (b) slots leave 0/-1 but stop below 6 -> the state machine RUNS and the
      transition that stalls names the missing input - the decode target.
  (c) slots never leave 0/-1 during landing -> NEG-B CONFIRMED (expected):
      baseline fact, session-state machine's drivers become the Road-1 decode.
  (d) no sess_state lines at all with landing confirmed -> the session system
      is inert in our environment (the getters never called) - itself a fact
      about how far the landing gets.
  (e) container fields +0x850/+0x854 show non-(-1) values on any slot -> the
      container the reservation disown reads exists in-session; its writer is
      then decodable.

## ABANDON OUTCOME (empty-mask #7)
If (c) or (d) reproduces, the "clients can host against the fork" question is
settled for the landing state; Road 3's fireteam stimulus is blocked by the
missing roster/invite plane (fork-side work, a NEW front) AND the session-state
machine decode becomes the Road-1 target. The boot does not retry.

## EFFECT CLAIM (empty-mask #5)
The claim is not "a guardian rendered". The EFFECT: the first DIRECT
measurement of the client's session-slot states in the fork environment - at
least one sess_state line emitted during landing (state, container fields,
session id), whatever the values.

## STATE READERS (empty-mask #1)
  - session state: DIRECT = the sess_state change-gated dumps (read from the
    getter's own return slot).
  - the join's arrival/processing: DIRECT = the type-0x0A/processor enter
    lines.
  - reserve/admit execution: DIRECT = the deployed + new hooks' enter lines.
  - record state: DIRECT = the resv probe.
  No return-code-inferred claims.

## FIX SURFACE: server
No behavior change this boot. The instruments are read-only hooks + a
change-gated state reader (sanctioned detour class) - no client behavior is
modified. (Server-side gap named above.)

## WIDE NET (every decision point)
  - landing/bootflow (existing) - backdrop liveness.
  - the launch attempt: bootflow stage lines + the human-noted refusal point.
  - the session state: sess_state (new).
  - the join arrival at the client: join_type0a (new).
  - the processor/capacity: join_processor (new).
  - the gate: join_gate (deployed; per-tick class, context only).
  - reserve/admit: deployed + new hooks.
  - adoption: add_candidates (new) + resv probe (outcome meter).
  - the relay: stage=join_relay (deployed, inert - context only).

## CHAIN MARKS (L16)
  L1 both machines land                 verified-by-execution (p2-180)
  L2 clean transition completes         verified-by-execution (p2-180)
  L3 record identity compositions match verified-by-dump (20.309)
  L4 record born containerless          verified-by-log (20.286/20.308)
  L5 adoption condition decoded         verified-by-reading
                                        (adoption-condition.md, THIS FRONT)
  L6 a hosted session exists in-fork    unknown (THIS BOOT - the contract)
  L7 the ladder climbs to (4,5)         unknown (establishment-decode gate)
  L8 the guard/receiver/codec/entity    unknown (contract spec-complete)
  L9 the entity renders and moves       unknown

## OBSERVER BUDGET / CALL FREQUENCY
  - join_type0a/join_processor/admit/add_candidates: per-join class (rare,
    ~0-2/boot expected); emit budget 24 each.
  - sess_state: getter MAY be per-tick class - emit is CHANGE-GATED per slot
    (state-transition events only, expected <20/boot). NO fixed-N enter
    budget on any per-tick function (the p2-181 lesson).
  - join_gate (deployed): per-tick, already budgeted; context only.
  - resv probe: change-gated (existing).

## HOOK COUNT: 56 (51 deployed + 5 new; hook_targets declares=56 initializers=56;
## verify_hook_rvas PASS - 104 RVAs, 0 bad, 10 known data addresses)

## INSTRUMENT SOURCES: RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks/milestone_trace/milestone_trace_observer.cpp

## INSTRUMENT LIVENESS
the names ("join_type0a", "join_processor", "admit", "add_candidates",
"sess_state") must appear in BOTH clients' attach lines.

## FALSIFIABLE CLAIM
During the paired landing boot, at least ONE sess_state line is emitted on
either machine (any state value - the claim is the first direct measurement
of the session slots, not any particular state). REFUTED if zero sess_state
lines appear while bootflow shows both machines landed (=> outcome (d): the
session system is inert).

## ABSENCE NEGATIVES (both kinds)
  - zero sess_state lines: the change-gate never fired => either no getter
    calls (VOID/d: the session system is inert) or states never change from
    the attach-time baseline (the forced first emit distinguishes: one
    baseline line per slot proves the reader lives).
  - any join machinery lines during landing (join_processor/admit on real
    traffic): unexpected-but-decisive -> a hosted session exists at landing.
  - resv mask still 0x00/0x20 with the deployed hooks' normal behavior:
    expected (the relay is inert; adoption needs the host flow).

## GRAPHICS DELTA (U12)
Expected new rendered models: 0 (instruments only; landing-only stimulus,
no activity attempt).

## SETUP
  1. Server unchanged + restarted before the boot (reset_lobby_claims;
     backgrounded; hangs after succeeding).
  2. Clients: BUILD + deploy the +4-hook build on BOTH machines
     (deliberate deploy; preflight --record; hash assert both).
  3. rig ssh control socket up.
  4. The action script above is executed by the players AFTER both land.

## ADVERSARIAL PASS: the replay arm for sess_state's change-gate must run
## before deploy (replay_trigger exit 1 on zero fires = no deploy); the four
## new hooks are first-fire instruments whose firing IS the claim (their
## absence is an outcome, not an instrument defect - pre-named above).

## DO NOT
  - do not read resv masks before the sess_state baseline (input gate)
  - do not attempt fireteam/invite actions in-game (the roster plane does not
    exist; the stimulus is landing-only this boot)
  - do not ship a client build without verify_hook_rvas PASS on the new table
  - do not shape the relay (inert by 20.310)
  - do not launch the server from anywhere but the repo root
  - do not modify the client beyond the declared instruments
