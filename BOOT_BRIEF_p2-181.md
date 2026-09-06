# BOOT_BRIEF_p2-181 — THE JOIN RELAY: GIVING THE PEER'S RECORD ITS BIRTHRIGHT

STATUS: live (2026-09-05, drafted post-20.309/20.310). Primary front:
peer-record-birthright. The transition + vptr scan ride as the pre-named
secondary (only if the primary's mask readout passes).

## PRIOR ART (required field)
q.sh terms: join_gate / 0x141769230 / reserve / birthright. Read in full:
establishment-decode.md (the writer map + the 3->4 gate), full-walk.md (the
idiom-lens walk + the theory), 20.309 (the ident decode: the record's identity
IS the peer's endpoint), 20.286 (the bit is stamped at record creation),
20.270 W2 (the missing type-13 grant - THIS BOOT IS ITS IMPLEMENTATION),
20.276 R5 (the hook A/B design this boot extends). The record-creation front
(20.286) was NAMED but never instrumented or behaviorally driven - no prior
boot has hooked the join gate/reserve (p2-164 hooked the NOTIFIER, a different
function, and it crashed the login - that hook is NOT reused).

## PURPOSE (ONE CONTRACT)
When the fork relays each client's join request to the other client
(relay_peer_join=true), the receiving client's host-side join gate creates the
peer's reservation record INSIDE a proper container - measurable as the peer
record's resv mask showing the container-stamped bit (0x40 on the rig / 0x80 on
the mac) instead of the containerless 0x20/0x00.

## THE CHANGE (server behavior + client instruments; the deliberate client deploy)
  - server 8a77a5b94c69fc9f: the join relay in peer_transport.cpp - on a
    type-0x0A join from one client, the whole join body (admission prefix +
    identity table + address/player tables) is re-enqueued into every OTHER
    peer's reliable outbound queue as a JoinId::request message. Settings key
    server/gameplay/relay_peer_join=true.
  - clients c2046914b3010932 BOTH: 4 new read-only enter hooks (the install
    table 51/51, verify_hook_rvas PASS 99 RVAs 0 bad). THE DELIBERATE CLIENT
    DEPLOY (preflight --record done; both machines hash-asserted).
  - the duty cycle stays on (30 s) - the sustained row is the backdrop this
    boot's mechanism needs.

## INSTRUMENTS (the wide net - every decision point on the chain)
  join_gate 0x14175C7C0 (the host-side join gate): enter args - DID THE JOIN
    ARRIVE at the client's host gate, and with what kind?
  join_reserve 0x141769230 (the reserve, kind 2): enter args - did the record
    get created, into which slot?
  join_handler 0x14178DE60 (the join-request handler): enter - the reserve's
    caller context (the container field read lives at its 0x14178EA80).
  join_msg 0x1417E5A10 (the registered plane handler): enter - the session-plane
    message vocabulary (also the ladder's last-rung readout for later).
  resv probe (already deployed): the peer record's mask/states - THE OUTCOME
    METER (mask 0x40/0x80 = the birthright fixed).
  stage=join_relay result=queued (server): the relay's own liveness.
  rig bootflow + the vptr dump (rig-side scan): the secondary phase.

## READOUT TRIGGER (required field)
  - stage=join_relay result=queued: fires on a join with the setting on.
    REPLAYED: RE_output/map/fixtures/join_relay_trigger.py over the p2-180
    archive = 2 fires (one per client), exit 0.
  - join_gate/join_reserve/join_handler/join_msg: NEVER-OBSERVED (first-fire
    risk) - these functions have never been hooked; their firing IS the
    question. Absence negatives pre-named below.
  - resv mask 0x40/0x80 on the peer's record: the resv probe emits on change
    (p2-180 archive: 12 lines, the state dumps cited in 20.308).

## PRE-NAMED OUTCOMES
  (a) relay queued + join_gate fires + reserve fires with the container field
      0/1 + the peer's record mask 0x40/0x80 -> THE BIRTHRIGHT WORKS. The
      ladder/(4,5), the guard, and the receiver vptr scan follow as the
      secondary phase of the same session.
  (b) relay queued but join_gate never fires -> the relayed join does not reach
      the client's host gate (the client's inbound routing drops or re-routes
      it) -> decode the client's inbound join routing (0x14175E520's message
      source) before any further relay shaping.
  (c) join_gate fires but bails before the reserve -> the gate's conditions
      (the activity-kind ranges at its head) name the blocker -> the fork must
      present the matching kind or the relay must ride a different plane.
  (d) reserve fires with the container field = -1 -> the container source is
      upstream of the gate -> decode the gate's caller context deeper.
  (e) no join_relay line at all -> no join arrived (check joincapture - it
      fires per join unconditionally) or the setting did not load.

## ABANDON OUTCOME (empty-mask #7)
If the relayed join IS processed by the host gate and the reserve runs, and the
record's mask is STILL born without a container stamp (outcome (d) across both
machines), the container-stamp theory DIES: the mask bit's set path is not the
join flow, and the front abandons the birthright lens - returning to the
receiver-construction question with hook B (0x1416BCFC0) + the resv widened
change-gate as the only remaining instrument. No further relay shaping after
that.

## EFFECT CLAIM (empty-mask #5)
Delivery (the relay queued, the join forwarded) is NOT the claim. The EFFECT:
the peer's reservation record carries a container-stamped mask bit (0x40/0x80)
from birth - visible in the resv dumps - which is the precondition for every
link after it (the sweep's claim, the ladder, the guard, the receiver).

## STATE READERS (empty-mask #1)
  - the relay's decision: DIRECT reader = the server's own stage=join_relay
    line (the emitter logs its decision).
  - the join's arrival at the client gate: DIRECT reader = the join_gate hook's
    enter line (the hooked function's own entry).
  - the reserve's execution + container: DIRECT reader = the join_reserve
    hook's enter line + the join_handler's context.
  - the record's mask/states: DIRECT reader = the resv probe's state dumps.
  No inferred-from-return-code claims.

## FIX SURFACE: server
The behavioral change is server-only (the relay). The client changes are
INSTRUMENTS ONLY (read-only enter hooks, the sanctioned detour class) - no
client behavior is modified.

## WIDE NET (user directive)
Every decision point on the chain carries a probe or a pre-named reason:
  - the join's arrival at the fork: stage=joincapture (unconditional).
  - the relay's decision: stage=join_relay (the gate's own line).
  - the client's gate: join_gate.
  - the reserve: join_reserve.
  - the handler's container read: join_handler (the field read is at its
    0x14178EA80; the enter context + the resv mask bracket it).
  - the session-plane messages: join_msg.
  - the record's state: the resv probe (mask/states, change-gated).
  - the landing: bootflow (existing).
  - the receiver: the rig-side vptr scan (the secondary phase).

## CHAIN MARKS (L16)
  L1 both machines land (duty-cycled row)      verified-by-execution (p2-180)
  L2 a clean transition completes              verified-by-execution (p2-180)
  L3 the record's identity compositions match  verified-by-dump (20.309)
  L4 the record is born containerless          verified-by-log (the resv masks,
                                                20.286/20.308)
  L5 the join gate creates the record in a container
                                               unknown (THIS BOOT - the contract)
  L6 the ladder climbs to (4,5)                unknown (the rung after L5)
  L7 the guard passes and the receiver exists  unknown (20.223/20.305/20.308:
                                                zero in every measured state)
  L8 the codec builds the entity               unknown (the contract complete,
                                                the encoder awaits the outer type)
  L9 the entity renders and moves              unknown (the 20.53 positive control
                                                only; appearance unmeasured)

## OBSERVER BUDGET / CALL FREQUENCY
  - the 4 new hooks: per-join events (rare: ~2/boot); emit budgets 24 each
    cover many boots. No per-tick hooks added.
  - the resv probe: change-gated (existing behavior).
  - stage=join_relay: per join (~2/boot).

## HOOK COUNT: 51 (the install table verified 51/51; verify_hook_rvas PASS -
## 99 RVAs, 0 bad, 10 known data addresses). INSTRUMENT LIVENESS: the new
## hook names ("join_gate", "join_reserve", "join_handler", "join_msg") must
## appear in BOTH clients' attach lines; INSTRUMENT SOURCES:
## RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks/milestone_trace/
## milestone_trace_observer.cpp (the Targets table this build ships).

## FALSIFIABLE CLAIM
With relay_peer_join on, the first paired boot shows: stage=join_relay
result=queued >= 1 per client, join_gate/join_reserve enter lines on BOTH
machines, and the peer's record resv mask = 0x40 (rig) / 0x80 (mac) at its
birth - instead of 0x20/0x00.
REFUTED by outcomes (b)/(c)/(d): the hooks fire but the mask stays
containerless, or the join never reaches the gate.

## ABSENCE NEGATIVES (both kinds)
  - zero join_relay lines: either no join arrived (joincapture also absent ->
    no client joined -> VOID) or the setting did not load (the settings grep
    assert at setup).
  - zero join_gate lines with relay queued: outcome (b) - the client's inbound
    routing is the wall, NOT the relay.
  - join_gate fires, join_reserve never: outcome (c) - the gate's conditions.
  - the resv mask never shows 0x40/0x80 with the reserve firing: outcome (d).

## GRAPHICS DELTA (U12)
Expected new rendered models: 0. The contract's readout is the record's mask
state (log-visible). A second guardian remains the unclaimed positive for the
render front and would be a bonus, not the contract. Minimization: no visual
change is expected from a record-state change.

## SETUP (my job; user only launches the games)
  1. Server deployed (8a77a5b94c69fc9f) + restarted; clients deployed
     (c2046914b3010932) BOTH - hashes asserted by preflight (PASS 13/0/0).
  2. Settings: relay_peer_join=true (parse-verified), duty cycle 30000.
  3. rig ssh control socket up.
  4. reset_lobby_claims before the launch (backgrounded; hangs after
     succeeding).

## ADVERSARIAL PASS: waived - the mechanism is decode-derived
## (establishment-decode.md + full-walk.md), the replay is green, the hook
## RVAs are verifier-passed, and the outcome tree covers the relay's own
## plumbing ((e)) and the gate's internals ((b)/(c)/(d)). The one unreviewed
## assumption: the client's host gate ACCEPTS a relayed join whose packet
## source is the fork (the identity/endpoint self-checks) - outcome (b)/(c)
## is its detector, and hook A's captured context names the check that
## fired.

## DO NOT
  - do not read the resv masks before checking join_relay/joincapture (input
    gates result)
  - do not tune the relay's framing mid-boot; one variable
  - do not hook the notifier 0x1417FFA20 (the p2-164 login-killer)
  - do not skip the transition dump if the primary passes (the receiver
    question has waited four boots for a valid measurement)
  - do not launch the server from anywhere but the repo root
  - do not modify the client beyond the declared instruments
