# BOOT_BRIEF_p2-185 — THE IDENTITY FIX: idB CARRIES THE SESSION ID (THE LOOKUP'S MISSING HALF)

STATUS: live (2026-09-06, drafted post the no-boot blob decode).
FRONT: session-lookup-identity

## PRIOR ART (required field)
q.sh terms: idB / kMemberIdEmpty / 0x141A83C00 / blob / identity. Read in
full: connection-layer-join-delivery.md (THE decode chain, all four links
verified this session: record = the decoded JoinRequest struct [verified
byte-exact vs the fork's own admit log]; the lookup = a ONE-QWORD compare
0x141A83C00 `cmp [key],[blob]` = the join's sessionId vs the session blob;
the blob = the session apply 0x1416C5280 copying member0.entry+144.. from
the applied state; the fork wrote field 8 idB = kMemberIdEmpty = 0, leaving
the blob zero -> every join refused at the lookup). p2-183/184: the OOB
channel works, the nonce/protocol-version gate passes, join_type0a fires.

## PURPOSE (ONE CONTRACT)
The fork's membership rows now carry the session's id as each member's second
identity (protobuf field 8) — the value the session apply copies into the
identity blob. The relayed join's sessionId then matches the receiver's blob
and the join gate's session lookup PASSES: join_processor fires for the first
time, followed by reserve/admit from the join flow.

## THE CHANGE
- server: session_messages.cpp write_member publishes field 8 with the
  member's idB (= the fork's sessionId, session-wide, every row) instead of
  the empty constant; snapshot_builder threads the sessionId in;
  session_state.cpp's replica model writes idB at member-entry +144 so the
  published state hash stays consistent with what the client decodes.
- clients: redeployed DLL (the group middleware compiles into it too);
  instruments UNCHANGED (57/57, join_type0a/join_processor/admit/
  add_candidates/sess_state/inst_nonce all live).
- duty cycle stays on.

## THE HASH RISK (pre-named as its own outcome)
The state hash covers the whole replica. The fork's model previously left
member-entry +144..+167 ZERO and the hash validated in real boots - so the
client's state also held zero there, consistent with the empty parameters.
With idB now published AND modeled, both sides change together. IF the
client's field-8 offset is NOT entry+144 (a mis-mapped descriptor field),
the client's hash diverges from the published one and the peer's join
completion breaks - visible as the join never completing (stage=join
result=completed absent) instead of the landing breaking.

## INSTRUMENTS (unchanged, all deployed)
join_type0a (pktdump) / join_processor / admit / add_candidates / sess_state
/ inst_nonce / join_gate / join_reserve / join_handler / join_msg / resv /
server: join_relay result=sent, joincapture, stage=join admit/completed.

## READOUT TRIGGER (required field)
- join_processor enter: NEVER-OBSERVED (the contract - the lookup has never
  passed). The gate entry IS proven (p2-183/184: join_type0a fires) and the
  nonce gate passes (p2-184).
- join_relay result=sent: replayed over p2-184's server log (fires at the
  admit lines; same fixture class as p2-183 - exit 0, 2 fires).
- resv probe / sess_state / pktdump: change-gated, existing behavior.

## PRE-NAMED OUTCOMES
  (a) join_processor fires + admit/join_reserve (the 0x14178EA73 caller) fire
      -> THE JOIN FLOW RUNS. The record's adoption (resv mask/container) and
      the ladder follow as the same archive's secondary reads.
  (b) join_type0a fires + join_processor never -> the lookup still fails:
      either the field-8 offset is wrong (the hash outcome above) or the
      compare's bit-4 selector picked the +0x94E variant blob (never
      populated) -> next decode = the variant blob's writer.
  (c) the state hash diverges -> the peer's join completion breaks (no
      stage=join result=completed) -> the field-8 offset is wrong; revert
      idB to empty and re-derive the offset from the client's member decoder.
  (d) join_relay=none -> timing (read the whole boot; joins re-fire).

## ABANDON OUTCOME (empty-mask #7)
If (c) (hash divergence), the idB-at-entry+144 mapping is WRONG: revert the
membership field to empty (the byte-exact previous behavior) and re-derive
the offset from the client's member decode path before any further identity
work. If (b) reproduces, the +0x57C arm is not the compared arm - decode the
+0x94E writer. No retry loops.

## EFFECT CLAIM (empty-mask #5)
The session lookup PASSES (join_processor enter line) - the first time the
client's join machinery advances past the gate for a peer's join. Delivery is
not the claim.

## STATE READERS (empty-mask #1)
- the lookup's outcome: DIRECT = join_processor enter (fired/not).
- the join's arrival: DIRECT = join_type0a enter (existing, proven).
- the relay's delivery: DIRECT = join_relay result=sent.
- the record's outcome: DIRECT = resv probe state dumps.

## FIX SURFACE: server
The behavior change is server-only (the membership wire + the state model).
The client DLL redeploy carries the same middleware source (no instrument
change, no client behavior change). SERVER-SIDE GAP: none named - the fix is
server-side publishing.

## WIDE NET
- joincapture / join admit / join completed (server) - the join's full path.
- join_relay result=sent - the delivery.
- join_type0a + pktdump - the gate entry + the record's contents.
- join_processor / admit / add_candidates - the flow.
- resv probe + sess_state - the record and the sessions.

## CHAIN MARKS (L16)
  L1 both machines land                     verified-by-execution (p2-180)
  L2 clean transition completes             verified-by-execution (p2-180)
  L3 record identity compositions match     verified-by-dump (20.309)
  L4 record born containerless              verified-by-log (20.286/20.308)
  L5 hosted sessions exist in-fork          verified-by-execution (p2-182)
  L6 join delivered on the connection layer verified-by-execution (p2-183)
  L7 the join gate's nonce gate passes      verified-by-execution (p2-184)
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
least ONE machine during the boot. REFUTED if join_type0a fires and
join_processor does not (outcome (b)), or if the join completion breaks
(outcome (c)).

## ABSENCE NEGATIVES (both kinds)
- zero join_type0a: the relay didn't deliver (check join_relay/joincapture
  first - input gate).
- join_processor fires but admit never: the processor's own gates (capacity)
  - the pktdump's count field names it.

## GRAPHICS DELTA (U12)
Expected new rendered models: 0. A second guardian appearing = the chain
running end-to-end - a bonus, not the claim.

## SETUP
  1. Server deployed (1c2a2950ea591a90) + restarted (reset_lobby_claims;
     backgrounded; hangs after succeeding).
  2. Clients redeployed BOTH (build-tree drift: the DLL carries the changed
     group middleware; preflight --record; hash assert both).
  3. rig ssh control socket up.
  4. Both clients land; NO in-game actions.

## ADVERSARIAL PASS: the change is decode-derived end-to-end (all four links
## carry this session's evidence tokens); the state-hash risk is PRE-NAMED
## with its own outcome ((c)) and its revert path; the hook set is unchanged
## and verifier-passed.

## DO NOT
  - do not read the machinery lines before join_relay=sent (input gate)
  - do not ship a second identity change this boot (one variable)
  - do not launch the server from anywhere but the repo root
  - do not modify the client beyond the declared instruments
