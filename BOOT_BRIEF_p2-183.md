# BOOT_BRIEF_p2-183 — THE CONNECTION-LAYER JOIN: DELIVERING THE PEER'S JOIN TO THE RIGHT MAILBOX

STATUS: live (2026-09-06, drafted post connection-layer-join-delivery.md).
FRONT: connection-layer-join

## PRIOR ART (required field)
q.sh terms: join_relay / 0x1416E0460 / connection-layer / joincapture. Read in
full: RE_output/claims/connection-layer-join-delivery.md (THE decode - the two
relay defects: reliable-queue channel + declared size 6144 vs the client's own
1536; the switch is reachable only from the OOB consumer 0x1416E2A90);
adoption-condition.md (sessions live at state 6; peer-adoption walker runs);
FINDINGS 20.108 + DOOR (the join chain end-to-end); 20.310 (the relay's
session-plane refutation). NO boot has ever delivered a peer join on the OOB
container channel; join_type0a/join_processor have never fired.

## PURPOSE (ONE CONTRACT)
With relayPeerJoin on, the fork forwards each client's join container VERBATIM
as an OOB datagram to the other peer (the join's native channel), and the
receiving client's OWN join machinery runs: join_type0a fires, then (gates
permitting) join_processor and the reserve/admit flow - the first join traffic
this project has ever delivered.

## THE CHANGE

INSTRUMENTS: join_type0a, join_processor, admit, add_candidates, sess_state
- server sunrise-server.exe: relay_join_body RE-TARGETED - the captured join
  container goes out byte-verbatim on the OOB datagram channel
  (send_transport, the connect-response path) instead of the reliable queue;
  no re-framing (the sender's nonce/session key/declared size 1536 stay
  byte-correct). Same settings gate (relay_peer_join).
- clients: NO source change to instruments (the p2-182 build already ships
  join_type0a/join_processor/admit/add_candidates/sess_state + the 4 p2-181
  hooks; 56/56). The DLL is REDEPLOYED because the build tree moved
  (steam_api64.dll also compiles peer_transport.cpp) - a deliberate deploy,
  byte-different for the server code it contains, instrument-identical.
- duty cycle stays on (30 s).

## INSTRUMENTS (unchanged from p2-182, all deployed)
join_type0a 0x1416E0460 / join_processor 0x1417806C0 / admit 0x141777EC0 /
add_candidates 0x141792080 / sess_state (getter 0x140C26490 exit read,
change-gated) / join_gate / join_reserve / join_handler / join_msg / resv
probe. Server: stage=join_relay result=sent|none (NEW result word), stage=join
result=admit, joincapture.

## READOUT TRIGGER (required field)
- join_relay result=sent: REPLAYED - the relay fires on join-admit events;
  fixture RE_output/map/fixtures/joinrelay_oob_trigger.py over the p2-182
  server log (fires: >=1, the p2-182 relay queued at t=663344), exit 0.
- join_type0a/join_processor: NEVER-OBSERVED (first-fire risk) - their firing
  IS the question (same pre-named form as p2-182).
- resv mask/container fields on the peer's record: change-gated, existing.

## PRE-NAMED OUTCOMES
  (a) join_relay=sent + join_type0a fires + join_processor fires + admit fires
      -> THE JOIN FLOW RUNS. The record's adoption and the ladder follow as the
      secondary reads of the same archive (resv state lines).
  (b) join_relay=sent + join_type0a fires + join_processor never -> the nonce
      check or the session lookup died inside the handler (its refusal path) ->
      decode the OOB packet-record parse (the 0x141C9AD28-vtable object).
  (c) join_relay=sent + join_type0a silent on BOTH -> the registry gate (id 10
      descriptor absent) or the client's OOB parse dropped the datagram ->
      decode the registrar/bulk writer for the 10..29 family; also check the
      sender's join actually arrived (joincapture >= 1 first - input gate).
  (d) join_relay=none -> no peer had a link when the join arrived (peers=0) ->
      timing: the relay needs both links up; joins re-fire on channel rebuild
      (20.119) so a later join may still deliver - read the WHOLE boot.
  (e) machinery runs but the record still stalls (3,4)/mask=0 -> adoption
      ran but the establishment mirror failed -> NEG-A of adoption-condition.md.

## ABANDON OUTCOME (empty-mask #7)
If (c) reproduces on both machines with join_relay=sent >= 1, the OOB-channel
theory of delivery is COMPLETE but the registry gate is real: abandon the
"verbatim forward is enough" lens; the fork must inject the id-10 registry
descriptor's provenance (decode who registers 10..29) before any further
relay work. One boot, no retries.

## EFFECT CLAIM (empty-mask #5)
Delivery (join_relay=sent) is NOT the claim. The EFFECT: the receiving
client's OWN join machinery runs (join_type0a enter line) - the first time in
this project's history that join traffic crosses between two clients.

## STATE READERS (empty-mask #1)
- the relay's decision: DIRECT = stage=join_relay result=sent (the emitter).
- arrival at the client's switch: DIRECT = join_type0a enter line.
- the gate's internals: DIRECT = join_processor / admit enter lines.
- the record's outcome: DIRECT = resv probe state dumps.
No inferred-from-return-code claims.

## FIX SURFACE: server
The behavior change is server-only (the relay's channel). The client DLL
redeploy carries NO behavior change (same instrument set; the server-side
relay code inside the DLL is dormant in client-instrument mode). SERVER-SIDE
GAP (governing-constraint ledger): the fork cannot yet complete the join's
session-identity mapping if the receiver's session blobs differ from the
sender's join (outcome (b)-adjacent) - the session-key mapping is the named
wire item for the NEXT change if this boot's machinery stops at the lookup.

## WIDE NET (every decision point)
- the join's arrival at the fork: stage=joincapture (unconditional).
- admission: stage=join result=admit (the gate's own line).
- the relay's delivery: stage=join_relay result=sent (the emitter's line).
- the receiver's switch: join_type0a (deployed).
- the receiver's processor: join_processor (deployed).
- reserve/admit: deployed hooks.
- the record's state: resv probe + sess_state (change-gated).
- the landing/backdrop: bootflow (existing).

## CHAIN MARKS (L16)
  L1 both machines land                     verified-by-execution (p2-180)
  L2 clean transition completes             verified-by-execution (p2-180)
  L3 record identity compositions match     verified-by-dump (20.309)
  L4 record born containerless              verified-by-log (20.286/20.308)
  L5 hosted sessions exist in-fork          verified-by-execution (p2-182)
  L6 join delivered on the connection layer unknown (THIS BOOT - the contract)
  L7 the ladder climbs to (4,5)             unknown (establishment-decode gate)
  L8 guard/receiver/codec/entity            unknown (contract spec-complete)
  L9 the entity renders and moves           unknown

## OBSERVER BUDGET / CALL FREQUENCY
- all client hooks: unchanged from p2-182 (per-join class, change-gated
  sess_state; no per-tick fixed-N hooks).
- stage=join_relay: per join (~2/boot), server-side.

## HOOK COUNT: 56 (unchanged; verify_hook_rvas PASS re-run at deploy)
## INSTRUMENT SOURCES: RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks/milestone_trace/milestone_trace_observer.cpp
## INSTRUMENT LIVENESS
the names ("join_type0a", "join_processor", "admit", "add_candidates",
"sess_state") must appear in BOTH clients' attach lines (the p2-182 deploy
already satisfies this; assert at preflight).

## FALSIFIABLE CLAIM
With relay_peer_join on and both links up: stage=join_relay result=sent >= 1
AND a join_type0a enter line appears on at least ONE machine. REFUTED by (c):
sent >= 1 with zero join_type0a lines on both machines while bootflow shows
both landed and joincapture >= 1.

## ABSENCE NEGATIVES (both kinds)
- zero join_relay lines of ANY result: no join arrived (joincapture also
  absent -> VOID) or the setting did not load.
- join_relay=sent >= 1 but join_type0a == 0 on both: outcome (c) - the
  registry gate / OOB parse, NOT the channel.
- join_type0a fires but join_processor never: outcome (b) - the nonce or the
  session lookup inside the handler.

## GRAPHICS DELTA (U12)
Expected new rendered models: 0 (the contract is the join delivery). A second
guardian appearing would be the chain running end-to-end - a bonus, pre-named
as outcome (a) carried further, not the claim. Minimization: no visual change
is expected from a record-state change alone.

## SETUP
  1. Server deployed (the re-targeted relay) + restarted (reset_lobby_claims;
     backgrounded; hangs after succeeding).
  2. Clients REDEPLOYED (build-tree drift: the DLL contains the server source;
     preflight --record; hash assert both).
  3. rig ssh control socket up.
  4. Both clients land; NO in-game actions required (the relay needs only the
     joins clients already send at landing).

## ADVERSARIAL PASS: the replay fixture (joinrelay_oob_trigger) must fire over
## the p2-182 server log before deploy; the hook RVAs unchanged (56/56); the
## outcome tree covers the relay's own plumbing ((d)), the handler's internals
## ((b)), and the registry gate ((c)). The one unreviewed assumption: the
## client's OOB consumer accepts an unsolicited id-10 container mid-session -
## outcome (b)/(c) is its detector.

## DO NOT
  - do not read the receiver's machinery lines before join_relay=sent (input
    gate)
  - do not re-frame or edit the join body mid-boot (one variable: the channel)
  - do not tune the relay's transport (send_transport is the proven path)
  - do not launch the server from anywhere but the repo root
  - do not modify the client beyond the declared instruments
