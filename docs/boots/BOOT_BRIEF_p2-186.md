# BOOT_BRIEF_p2-186 — THE CORRECTED IDENTITY FIX: idB AT THE WALK-DERIVED OFFSET (+152)

STATUS: live (2026-09-06). FRONT: session-lookup-identity
(ledger: 1 third-branch on this front - this boot's evidence burden is
explicit: the mechanism AND the offset must both land.)

INSTRUMENTS: join_type0a (pktdump), inst_nonce, join_processor, sess_state

## PRIOR ART (required field)
q.sh terms: idB / 0x1416E2350 / kMemberIdBOffset / 0x141A83C00. Read in full:
connection-layer-join-delivery.md (the whole chain + THE COPIER WALK section
- this session's decode); p2-185's outcome (the mechanism verified live: the
record's key = sessionId byte-exact, constant across join retries = the
admit log's session id; the +144 model offset diverged the hash - outcome
(c) as pre-named - and was REVERTED byte-exact). The walk this session:
field address = walker + entry[8] + entry[9](signed), advancing by size;
walker starts at entry+8; the walk lands f1@+8 (NetAddr 96B incl. its length
prefix), f2@+112 (machineId 16B), f3@+136 (joinId), **f8 (idB)@+152**, f9@+160,
f10 (playerSlot)@+168, f11/f12@+180/+182 - EVERY hash-validated model offset
matched AND the stride sums to 184 exactly. p2-185's +144 was 8 bytes low
(the NetAddr's length prefix lives inside its 96-byte field).

## PURPOSE (ONE CONTRACT)
Same contract as p2-185 at the corrected offset: the relayed join's sessionId
matches the receiver's identity blob (the apply copies member0's idB at
+152), the session lookup PASSES, and join_processor fires for the first
time.

## THE CHANGE
- server: session_messages.cpp publishes field 8 (idB) = the member's
  sessionId (session-wide, every row); session_state.cpp's replica model
  writes idB at member-entry **+152** (the walk-derived offset).
- clients: redeployed DLL (middleware rebuild); instruments unchanged (57/57).

## THE HASH RISK (pre-named, as in p2-185 - with the difference stated)
The +152 offset is now WALK-DERIVED (validated against every hash-validated
model offset and the stride) rather than descriptor-order-inferred (p2-185's
error). If the walk's element-base anchor is still wrong, outcome (c)
repeats: no result=completed + the retry storm, and a SECOND third-branch on
this front forces the model review before any further boot.

## INSTRUMENTS (unchanged, all deployed)
join_type0a (pktdump) / join_processor / admit / add_candidates / sess_state
/ inst_nonce / join_gate / join_reserve / join_handler / join_msg / resv /
server: join_relay result=sent, joincapture, stage=join admit/completed.

## READOUT TRIGGER (required field)
- join_processor enter: NEVER-OBSERVED (the contract).
- join_relay result=sent: replayed over p2-184's server log (the admit-line
  fixture fires; exit 0).
- everything else: existing, proven in p2-183/184/185.

## PRE-NAMED OUTCOMES
  (a) join_processor fires + the join-flow reserve/admit fire -> THE LOOKUP
      PASSES. The record's adoption (resv mask/container) and the ladder
      follow in the same archive.
  (b) join_type0a fires + join_processor never + the join COMPLETES (no hash
      divergence) -> the lookup still fails with a valid hash: the compare's
      bit-4 selector picked the +0x94E variant blob, or the identity copy
      into the live session (sess+0x57C) rides a different path than the
      replica export -> decode the live blob's writer (the parameters apply).
  (c) the join completion breaks again (no result=completed + retries) ->
      the +152 offset is ALSO wrong -> STOP. The offset derivation from the
      static walk is insufficient; the runtime registry/base anchoring needs
      a measurement - the model review before any further attempt.

## ABANDON OUTCOME (empty-mask #7)
(c) = the static walk is insufficient for the offset; the front's remaining
road is a runtime observation of the applied member rows (an instrument boot
with the client's decode dump) - a deliberate decision after the model
review, not a retry loop.

## EFFECT CLAIM (empty-mask #5)
The session lookup PASSES (join_processor enter line) - the first advance
past the gate for a peer's join.

## STATE READERS (empty-mask #1)
- the lookup: DIRECT = join_processor enter.
- the gate: DIRECT = join_type0a enter + pktdump (the record's fields).
- the relay: DIRECT = join_relay result=sent.
- the completion: DIRECT = stage=join result=completed (the hash outcome).

## FIX SURFACE: server
The membership wire + the state model (both server-side); the client DLL
redeploy carries the same middleware (no instrument/behavior change).
SERVER-SIDE GAP: none named - the publishing fix is server-side.

## WIDE NET
joincapture / join admit / join completed (server) / join_relay result=sent /
join_type0a + pktdump / join_processor / admit / add_candidates / resv probe
/ sess_state / bootflow.

## CHAIN MARKS (L16)
  L1-L6: as banked (p2-180/182/183/184)
  L7 the nonce gate passes                  verified-by-execution (p2-184)
  L8 the session lookup matches             unknown (THIS BOOT - the contract)
  L9 the ladder climbs to (4,5)             unknown
  L10 guard/receiver/codec/entity/render    unknown

## OBSERVER BUDGET / CALL FREQUENCY
- unchanged from p2-184 (all change-gated or per-join; no new hooks).

## HOOK COUNT: 57 (unchanged; verify_hook_rvas PASS re-run at deploy)
## INSTRUMENT SOURCES: RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks/milestone_trace/milestone_trace_observer.cpp
## INSTRUMENT LIVENESS
the names ("inst_nonce", "join_type0a", "join_processor", "sess_state") must
appear in BOTH clients' attach lines.

## FALSIFIABLE CLAIM
With relay_peer_join on and both links up: join_processor enter fires on at
least ONE machine, AND stage=join result=completed appears (the hash risk's
readout - the landing/join flow must stay healthy). REFUTED if join_processor
never fires while join_type0a does (outcome (b)/(c)).

## ABSENCE NEGATIVES (both kinds)
- zero join_type0a: the relay didn't deliver (check join_relay/joincapture -
  input gate).
- zero result=completed with joins flowing: outcome (c) - the hash diverged.

## GRAPHICS DELTA (U12)
Expected new rendered models: 0. A second guardian = the chain end-to-end (a
bonus, not the claim).

## SETUP
  1. Server deployed (af414e390a97808b) + restarted (reset_lobby_claims;
     backgrounded; hangs after succeeding).
  2. Clients redeployed BOTH (the middleware rebuild; preflight --record).
  3. rig ssh control socket up.
  4. Both clients land; NO in-game actions.

## ADVERSARIAL PASS: the offset is WALK-DERIVED with the full arithmetic in
## the claim (every hash-validated offset matched; the stride sums exactly);
## the hash risk is pre-named with its revert; the hook set is unchanged.

## DO NOT
  - do not read the machinery lines before join_relay=sent (input gate)
  - do not ship a second identity change this boot (one variable)
  - do not launch the server from anywhere but the repo root
  - do not modify the client beyond the declared instruments
