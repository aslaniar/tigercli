# STATE - living snapshot

STATUS: live (2026-09-06 ~15:10 PDT). Verdict + deployed + next only.
Full text: FINDINGS (the evening arc banked in
HANDOFF_2026-09-06_EVENING-CHANNEL.md - READ THAT FIRST; session failures:
docs/postmortems/POSTMORTEM_2026-09-06_THE-BLIND-GUARD.md - FOUR instrument
defects this session, all documented with rules R1-R8 in docs/ENFORCEMENT.md).

*** 2026-09-06 (STATIC + recorded logs, NO new boot): THE STATE LADDER IS
## DECODED AND ROW 5 IS CLOSED - THE QUESTION WAS WRONG AND ITS ANSWER WAS
## NEVER NEEDED. field_xref on +0x1AEF8: 497 accesses, 6 writes, only TWO that
## can write an arbitrary value - 0x14178CD98 (20.184's cluster) and
## 0x1417B37DE, which 20.184 never named and which IS the state-transition
## function: it formats old and new state through 0x14177A280 and LOGS them.
## THE CLIENT PRINTS ITS OWN LADDER, and p2-195's log carries every transition:
##   'none' -> 'host-established'                      (fireteam, posse)
##   'none' -> 'peer-creating' -> 'peer-joining' -> 'peer-established'  (the fork's)
## Cross-matched to sessstate: STATE 6 = 'host-established', STATE 4 =
## 'peer-established'. So the gate's 6..9 window is the HOST HALF OF THE LADDER:
## a type-0x0A join is a HOST-ONLY message and the receiving client is a PEER in
## the fork's session. NO key, channel, container or retarget value could ever
## have passed - the relay was delivering a host-only request to a peer.
## AND IT NEVER MATTERED: the membership plane has ALREADY been putting the rig
## into the mac's group session as peer #2 `_established` (peers valid 0x7 =
## three, players valid 0x3 = two, plus a direct mac<->rig channel established).
## CONTROL RUN: those counts are IDENTICAL in p2-193a, p2-193b and p2-195 - the
## membership plane has done this for at least three boots, through every relay
## experiment, so the refusals never blocked anything.
## THE RELAY ROAD p2-181..p2-195 IS CLOSED on its own question.
## THE REAL WALL IS ROW 7, NOT ROW 9 (correcting this session's first reading):
## in the FORK's group_target session NO peer ever reaches '_connected' - peers
## #0, #1 and #2 all sit at '_established' - while the LOCAL posse session DOES
## reach '_connected' on the same boot (the positive control, right beside the
## failure). Identical across the p2-190 baseline landing, p2-193a/b and p2-195.
## establishment-decode.md already named this and it was never resolved: the
## 3->4 site 0x141803F2B is guarded on [rsi+0x3040]==3 AND [rsi+0x1D18]==5 - it
## REQUIRES the ladder at CONNECTED(5) - and its own words are "the ladder must
## reach 5 - the connected-rung, MESSAGE-FED".
## SO ent_recv=0 IS A SYMPTOM OF ROW 7, not an independent row-9 problem: the
## receiver object is gated on ladder==5 and is never built. Sending an entity
## before the ladder connects is pushing on a door held shut upstream. The
## entity contract stays spec-complete and femu-validated (20.302-20.304, outer
## wire type still open, 20.303 R4) and waits on row 7.
## Full text: claims connection-layer-join-delivery.md section 14. ***

*** p2-195 (ONE PAIRED BOOT, 2026-09-06 ~16:29): ROW 5'S WALL IS MEASURED AND
## IT IS ONE STATE TRANSITION. The gate MATCHES the relayed join and refuses on
## its SECOND check - measured, not inferred:
##   walk_leave ret=0x4631748 bind=2 state=4 depth=1 outcome=FOUND-STATE-OUT
##   walk_map window=1 (FRESH states, same call): st0=6 st1=0 st2=6 st3=0
##                                                st4=0 st5=4
##   join_processor calls=0  |  the retail refusal fires immediately after.
## Every value was PRE-NAMED in the brief; the boot was a confirmation and it
## confirmed. depth=1 proves the walk is the GATE'S OWN, closing the p2-193b
## attribution ambiguity by construction. CLOSED BY MEASUREMENT: the channel,
## the key (verbatim), the container, the lookup, and the gate's decision path
## (exactly two conditions - claims section 11.1 - no third check exists).
## THE FORK'S SESSION IS BOUND AT SLOT5 AND CARRIES THE RIGHT IDENTITY. It sits
## at state 4; the gate requires 6..9. The client's own two sessions sit at 6 in
## the SAME container on the SAME boot, so 6 is reachable and observable.
## THE INSTRUMENT DEFECT IS ALSO FIXED: the mac LANDED (initial_slice_set x10,
## tower) on 44c400b985d60c7a, where d5ed2ae3 never reached the tower - the R8
## regression (the leave probe's budget checked against EMITS while the novelty
## gate returned before that counter moved) was found by READING, not by the two
## boots p2-194a/b spent on it. Third-branch streak on this front: 2 -> 0.
## THE ONE REMAINING QUESTION ON ROW 5: what drives a session slot from 4 to 6,
## and what must the fork send to drive the forkSession-named one there?
## Starting evidence (do NOT re-derive): 20.184 RESULT 3 - stage writers are
## 0x14178CD97's cluster driven by 0x140C05F80, which tries stages 0/1, 2/3, 4/5
## until the setter returns true; "THE CLIENT CYCLES STAGES 0..5 ONLY". p2-195
## matches it exactly - the fork's session is parked at the TOP of that range.
## Full text: RE_output/claims/connection-layer-join-delivery.md sections 11-13.
## PARKED DEBT - AND IT IS TWO DISTINCT FAILURES, NOT ONE (user, 2026-09-06):
##   VARIANT A (SOLO, never-spawn): the mac never spawns in at all; a subclass
##     swap does NOT fix it. Segment 2 reaches `region result=forced native=0
##     answer=1` and never fade_release; the client stays alive and keeps
##     logging. THIS BOOT (p2-195) was variant A.
##   VARIANT B (CO-PRESENCE, post-spawn): the mac is ALREADY spawned and moving
##     when the screen goes black, and it is triggered by the RIG launching to
##     the tower. This is the variant the rig-connection correlation belongs to,
##     and that correlation STANDS.
## Do not merge these two in any future note: they differ in when they strike
## (before vs after spawn), in whether a subclass swap helps, and in whether a
## second machine is required at all. ***

*** 2026-09-06 LATE (STATIC, NO BOOT): ROW 5'S WALL IS NAMED - THE MATCHED
## SLOT IS SLOT5 AND ITS STATE IS 4, NOT 6. The join gate was disassembled to
## exhaustion (0x1416E0460 + walker 0x14177A0B0 + helper 0x1417944C0): between
## the walker and the processor there are EXACTLY TWO conditions - rax != 0 and
## [rax+0x1AEF8]-6 <=u 3 - and no third check exists. Mapping p2-193a/b's
## RECORDED compares to slots by WALK ORDER (binds {0,-1,1,-1,-1,2}; an unbound
## slot is never compared; a bound slot spends one compare at +0x57C and at most
## one at +0x94E) puts the match on SLOT5 = 0x4631748 - and walk_map read that
## slot at state 2 then 4, never 6, in THREE runs. The client's own two sessions
## sit at 6. THE MATCH ALSO SITS INSIDE join_type0a's OWN enter/leave window, so
## the "was it the gate's walk or another consumer" ambiguity is answered from
## data already on disk. RETRACTED: p2-193b's "the matched slot is slot2, st=6"
## (inferred from which record held the blob rather than from the walk order).
## ALSO FOUND: walk_map's change gate hashes key^slots^binds and the states are
## read only when a line emits - so a STATE change cannot trigger a line, and
## every st<i>= ever logged is the state at some OTHER field's change. That is
## why "st2=6" was never evidence about the refusal walk.
## THE FRONT IS NOW ONE SERVER-SIDE QUESTION: what drives a session slot from
## state 4 to 6, and what must the fork send to drive the forkSession-named one
## there? The positive control is local and measured - the client's own sessions
## make the climb organically (p2-182, both machines).
## Full text: RE_output/claims/connection-layer-join-delivery.md sections 11-12.
## DEPLOYED FOR THE CONFIRMATION BOOT: client 44c400b985d60c7a on BOTH machines
## (preflight PASS). The walk-return probe is now ARMED BY THE JOIN WINDOW -
## join_type0a IS the gate (RVA 0x16E0460) and calls the walker once, so the
## probe costs one thread-local read outside the gate's own call and the
## attribution is by construction. That also fixes the R8 defect that broke the
## mac's landing: the old leave probe checked its budget against EMITS while the
## novelty gate returned before that counter moved, so two guarded reads and a
## sixteen-entry scan ran on EVERY walker return, forever. ***

*** p2-192/193/194 (the evening's front): THE SESSION-TO-CONNECTION
## BINDING SOLVED TO THE SECOND CHECK. VERIFIED CHAIN: (1) the join gate walks
## the container of the packet's OWN connection ([ctx+0x28], disasm-verified)
## - the fork's relays now go on the ENGINE association
## (relay_join_engine_channel=true, wire-proven channel=engine); (2) the gate's
## LOOKUP MATCHES (key=forkSession vs blob=forkSession, match=1, measured
## twice, p2-193a/b); (3) the gate STILL refused - the found-path carries a
## SECOND check: [found_slot+0x1AEF8] must be 6..9 (the session-state window;
## 6=LIVE HOSTED) or the identical "unknown session" refusal text fires
## (the join gate's disasm). THE REMAINING AMBIGUITY: the matched slot's
## +0x1AEF8 value vs the sessstate probe's state=6 reading - one instrument
## (the walker's leave-probe) from resolution. NEXT: the bisect (572ca7c2 on
## both machines = the proven-landing pair), then the walk-return readout ONE
## verified change at a time. THE MAC'S LANDING BROKE ON 3d95a375/d5ed2ae3
## (the last two builds) - the mac has 572ca7c2 restored; the rig is on
## d5ed2ae3. THE SESSION'S OWN DEBT: four instrument defects shipped under
## boot pressure (guard / hash / dual detour / hot-path cost) - all documented
## in the postmortem; the user took the machine back ("the dog doesn't clean
## up its own mess" - restore the playable state first, debug with gates).

Full text: FINDINGS (20.309 is newest; 20.292-20.308 under it). Session failures:
docs/postmortems/POSTMORTEM_2026-09-05_THE-REBUILD.md (4 launches lost, 3 to my defects).
Ops facts (network move, grep hazard, BOM trap) in ENVIRONMENTS.md. Instrument
defects: docs/TOOLING_AUDIT_2026-09-05.md.

*** 20.311 (p2-182, ONE BOOT, the adoption-condition baseline): THE HOSTED-SESSION
## PREMISE WAS WRONG - THE SESSIONS ALREADY EXIST. During a plain fork landing BOTH
## machines put TWO session slots into state 6 (LIVE HOSTED SESSION, sids 0/1), and
## the PEER-ADOPTION walker ran per session (add_candidates from 0x141769CFC upserts
## the peer's records into session +0xC8). What never happens: the CONNECTION-LAYER
## join - join_type0a (0x1416E0460) = 0, join_processor = 0, join_handler = 0 on both
## machines. The p2-181 relay failed because it delivered the join as a SESSION-PLANE
## JoinId::request (the F3 space) - the connection layer (receive switch 0x1416E0940,
## types 0..0x2A; type 10 -> 0x1416E0460) is a DIFFERENT space the relay never touched.
## THE FRONT: deliver the peer's join body as a connection-layer type-10 packet on the
## existing fork->client channel (the fork already RECEIVES clients' own type-0x0A
## joins - joincapture). The handler's nonce check (word[+0] == 0x1416C1260()) makes
## the PACKET FRAMING the work. Full text: RE_output/claims/adoption-condition.md
## (MEASURED + THE RELOCATED MISSING LINK). Road 3's client-host premise is moot; the
## roster/invite plane stays parked fork-side work for the retail UI path only. ***

 *** 20.320 (p2-189, ONE BOOT, the wide binding capture): THE BINDING
## ARCHITECTURE IS MEASURED END TO END - THE FIX KEY IS THE RECIPIENT'S JOINID.
## +6 client hooks (58->64: binder1/binder2/cof_index/cof_soid/walk_map/
## apply_stamp) + sess_cmp WIDENED to (caller_rva,key,blob) triples - all fired
## on BOTH machines. MEASURED: the join gate's walked six slots are bound to
## SMALL-INDEX sessions {0,-1,1,-1,-1,2} (walk_map, identical both machines);
## binder2's stack args name the binding key = THE MACHINE'S OWN JOINID (a6,
## both machines); binder ctx pointers = the walked slots (attribution proven);
## cof_index granted indexes 0/1, cof_soid index 2 (the joinId-keyed record);
## apply_stamp fired ONCE (early, static dst) - the session-apply is NOT the
## landing blob's writer (open site). sesscmp widening WORKS but the flat
## 64-triple budget was spent by the landing noise before the relayed join
## (per-caller sub-budgets = the instrument fix). The relayed join refused
## byte-verbatim (retarget OFF) - baseline reproduced. The mac hit the parked
## co-presence render-black (alive client, no fade_release in segment 2; the
## rig fine on the identical build). THE CONSEQUENCE: the gate's walked slots
## hold the client's OWN joinId-named session (p2-187's blob census: a record
## whose blob = the joinId, match=1) - SO THE RELAYED JOIN'S SESSIONID MUST
## EQUAL THE RECIPIENT'S CURRENT JOINID = retarget ARM 3 (the fork already
## holds the live value; arm 1 dead, arm 2 fallback; the rewrite machinery is
## built - one value change). Full text: connection-layer-join-delivery.md
## section 10. ***


## 20.319 (STATIC + SHIP, no boot): THE PARAMETERS ROAD IS CLOSED ON THE OOB
## PLANE - THE FIX MOVED TO THE RELAY RETARGET. The client's message registry
## decoded: descriptor blocks 0x40 wide (present/name/min/max/4 handler slots),
## parameters-update at reg+0x980 (max 0xAC20 = kParameterUpdateSize exactly).
## THE OOB SWITCH byte map re-read slot-indexed: id 0x26 (38) = slot 16 =
## the default stub 0x1416E0A40 = a bare `ret` - SILENT DROP (join-complete
## id 12 too). The client's reliable-plane receive is the VM-OBFUSCATED ring
## (0x1472B4425/0x146260781 prologue) - parameter-value publishing cannot
## reach the client. VINDICATED: the apply 0x1416C5280's TAIL (disasm_fn
## TRUNCATED it at 0x1416C5B89 - tool debt, 09-03 class) copies source
## +0xC8/+0xD0 → blob +0x57C/+0x584: the claim's +0xC8 window was right.
## The gate walk DECODED: 0x14177A0B0 walks 6 slots, per slot [slot+0x1C7C0]
## → record via 0x14179AF00; helper 0x1417944C0 compares the key vs
## [rec+0x57C] FIRST (bit 4 of [rec+4] set), else [rec+0x94E]; both blobs
## tried, one-qword equality. peer-connect (id 11, 0x1416E0E10) is the SAME
## GATE - every connection-layer message naming the fork's session dies at
## the one wall. TWO IDENTITY FORMS distinguished (logs): the REAL account
## key (field6!=0: mac 0xD3DABDA3AF16F99E, rig 0x846C8338F7D022E6, stable;
## appeared as live blobs) vs the join machine id (field6=0, per-boot,
## machineId>>40 == memberKey&0xFFFFFF; appeared as a blob NOWHERE). The
## mac's own-join comparisons (t=131-132xxx, PRE-refusal) included match=1
## vs the fork's sessionId - the landing's session, outside the gate's
## slots; the refusal's walk emitted no new pairs (novelty-gate hazard).
## NEXT DECODE (clean code): the connect-family handlers 0x1417D3010/
## 0x1417D4590/0x1417D27B0/0x1417D1A90 - what binds sessions into the
## receiving connection's context. SHIPPED: relay_join_target_identity
## (default OFF) - the relay's per-recipient sessionId retarget at absolute
## bit 109 (byte-verified vs the p2-182 admit decode; fixture replay: only
## the 64 sessionId bits change), value = the recipient's join machine id
## (arm 1; arm 2 = the real account key; the boot readout decides).
## Full text: RE_output/claims/connection-layer-join-delivery.md (20.319). ***

 *** 20.318 (p2-185..187, THREE BOOTS + the no-boot decode arc): THE LOOKUP IS MEASURED
## LIVE - THE BLOCKER IS THE SESSION-TO-CONNECTION BINDING. Chain verified: the record =
## the DECODED JoinRequest struct (proto/minBuild/maxBuild/sessionId/joinId - byte-exact vs
## the fork's own admit decode in THREE boots); the nonce gate = the PROTOCOL VERSION check
## and it PASSES (0x1416C1260 returns 0xA4F8 both machines; p2-183's nonce diagnosis
## RETRACTED); the session lookup = a ONE-QWORD compare (0x141A83C00: cmp [key],[blob]) =
## the join's sessionId vs the receiver session's identity blob. p2-185: idB published at
## model-entry +144 -> the state hash DIVERGED (no result=completed, retry storm, outcome
## (c) as pre-named) -> reverted byte-exact. p2-186: the copier walk (0x1416E2350: field
## address = walker + entry[8] + entry[9] signed, advancing by size; walker at entry+8)
## derives the true offset +152 - HASH-VALID (both joins completed). p2-187 (the live-blob
## instrument, sess_cmp on the equality helper): THE JOIN'S LOOKUP FIRES AND COMPARES THE
## JOIN'S SESSIONID (10 firings, byte-exact) - and the blobs hold THE MAC'S OWN IDENTITY
## (account key 0xD3DABDA3..., joinId 0xACBE7AA8...), NOT the fork's sessionId. THE GAME'S
## OWN REFUSAL IS NOW VISIBLE IN OUR LOGS: "networking:messages:join-request: received
## message for an unknown session ... sending back a refusal". A session whose blob DOES
## hold the sessionId exists (match=1 during the landing) - outside the gate's ctx+0x28
## container. THE NEXT DECODE: the session-to-connection binding - what populates the
## ctx+0x28 container's sessions' identity blobs; the fork must publish that binding.
## THIRD-BRANCH LEDGER: session-lookup-identity carries 2 (p2-185, p2-186) - the model
## review for that front is BANKED in the p2-187 brief (the dead assumption: the state's
## idB flows into the live blob via the membership machinery - it does not; the live
## writer is the session-to-connection binding path). Full text: RE_output/claims/
## connection-layer-join-delivery.md + FRONT_peer-render-chain.md (the pinned chart). ***

TOOLING 20.307 (2026-09-05, no boot): enforcement waves 0-1 SHIPPED - pre-commit hook
INSTALLED; gate_boot v3 brief-tie fields ENFORCED (the next boot brief MUST carry
PRIOR ART / STATE READERS / READOUT TRIGGER / EFFECT CLAIM / ABANDON+WIDE-NET / FIX
SURFACE; instrument briefs also OBSERVER BUDGET / CALL FREQUENCY / HOOK COUNT /
INSTRUMENT LIVENESS - template updated); record each boot's outcome at boot close via
RE_scripts/boot_outcome.py (>=2 third-branches on a front refuse the next boot without
MODEL REVIEW). WAVE 2 SHIPPED (20.308): replay_trigger.py (the encoder's ship gate is
runnable - replay its trigger over a recorded log), preflight.py + instruments.json
(the world gate; "ready" = gate PASS + preflight PASS; run --record after every
deploy), boot_verdict --sigtable (per-arm discriminator), hook_targets + the
verify_hook_rvas T1.4 fix, field_xref T1.3, needle_scan T1.2. WAVE 3 SHIPPED
(20.309): logq v2 (--bare/--fn/--help/--aligned-loud/truncation-marker),
build_index corpus expansion + dedupe, organize_root --dry-run + fixed sed,
negative_audit two-tier, disasm_fn gap-refusal, decision_log.py, reset_
lobby_claims idempotent + port-SET + --check (real restart path untested -
pen live; run at the next boot boundary). Remaining backlog: toolsq.sh,
negative_audit tool-blindness flag (T2.3), the T3.1 client-side budget
marker (pen's lane), ENFORCEMENT.md ledger (Tier 4).

*** 20.302 (STATIC + FEMU, NO BOOT): THE ENT_* RECEIVE CLUSTER IS DECODED. Four
receive interfaces (0x141718510 ent_recv / 0x141718AE0 / 0x1417183C0 /
0x141718CB0), all at vtable slot 10 of the four blocks the ctor 0x1416BB1E0
installs; one 0x84-byte record shape; the header grammar (ent_header
0x141717EB0) femu-validated bit-exact; the anchor codec 0x1404C16C0 fully
decoded (index13+salt4[+high2], 22-bit handle); wire = MSB-first bits in
big-endian u64 words (femu-proven). Descriptor tables read from the p2-146
dump: entity indices are SMALL INTEGERS (live set 0..6), descriptor 0 carries
kind=2 - the creation loop's own kind. THE CONTRACT IS WRITTEN:
RE_output/claims/ent-receive-contract.md - the fork encoder's source of truth.
Dispatch-INTO the cluster (who calls slot 10) = complete-encoding scan done,
only VMP/cross-function-register candidates remain; the contract does not
need it. 20.303 (lane): THE CARRIER LAYER IS NAMED - the "network extract"
pair (0x1416C8250/0x1416C8240) feeds a decode chain (0x1416EACB0 -> 0x1417115D0
-> 0x1417117D0) operating the SAME entity storage as ent_create; router census
complete (93 wire bytes, 44 handlers; type 17 excluded, type 22 = the receive
tick's own gate fn). 20.304 (lane): PAYLOAD BODIES DECODED + FEMU-VALIDATED -
kind 2 (the player/guardian) = RAW 8 BYTES (64 bits, no presence, no
transforms; bit-exact vs the real dump codec object); kind 1 = 55 bits, kind 3
= 0 bits; 23 per-kind keys from the dump; two decode dialects (W1 walker + a
NEW 0x1404BA530 dialect, table 0x141F95980, extended types 18-46 carry the
wire). THE ENCODER'S PAYLOAD HALF IS SPEC-COMPLETE FOR THE GUARDIAN KIND. ***

*** 20.301 (STATIC, NO BOOT - READ THIS BEFORE ANY LOOP WORK): THE COND5 BIT IS NOT THE
CREATION GATE. The creation loop 0x1413086E0 never calls the cond5 reader at all - that
reader's only callers are the reconcile/RELEASE sweep. Verified: the constants are sound
(stride 0x2AC0, +0x38, bit 4), no stride-indexing site WRITES +0x38, and the loop's real
bail is GATE 2: member[+0x818] == gate1's out-value.
*** AND THAT WAS ALREADY SETTLED. *** 20.260 (2026-09-02, no boot) measured gate 2 on both
machines across three boots: gate1's out-value is THE OBSERVING MACHINE'S OWN identity and
each record's +0x818 is that member's own. "The loop is not the peer path and never could
be." 20.221 R2 said it first. I re-measured it across 20.298-20.300 and built a front page
on it. Those findings' DATA stands; their framing as "the wall" is RETRACTED.
THE REAL FRONT, unchanged since 20.221 R3: peers must ARRIVE by SERVER-MEDIATED
replication on the gameplay plane (UDP 30976). The receive cluster logs zero because
NOTHING EVER SENDS IT A PEER ENTITY - and the fork has never sent one. Client<->client is
refuted as the carrier (20.208 R5, pcap). This is fork-side work in code we own. ***

*** 20.300 (p2-178): the create is never ATTEMPTED for a foreign record (loop 15,745
passes, memidx_alloc 2). Data stands; its "wall" framing is superseded by 20.301.
First gate-byte reading at a creation call (f38=0x00). DELIVERY VOLUME ELIMINATED (11
peer bodies vs 2, identical outcome). Attribution now DIRECT. Rig hang PRE-EXISTING.
My re-arm did NOT fire - threshold 8 unreachable; ack-counting cannot drive it. ***
*** 20.299 (p2-177 solo): husk NOT reproducible on 3 triggers; H4 negative. ent_recv=0
across 3,774 local creates. publish_player_profile=false = leading black-screen suspect.
My probe was gated on an event its own placement excluded (pgate is table-driven). ***
*** 20.298 (p2-176): first ATTRIBUTED foreign-peer measurement; row CONTENT exonerated.
20.297 R2 reopened (starved: 104/128 snapshots sent nothing). ***

VERDICT TRAIL (one line each; full text in FINDINGS):
  20.298 run A: extras exonerated, wall = claim state; 2 retractions; grep-wrapper
    defect; stale variant comment; retry-cap permanence named.
  20.297 transition run - R2 REOPENED (starved); R3's never-sticks framing stands.
  20.296 receiver = converted, not constructed; C3 retired (user).
  20.295 p2-174: the client READS the row's character field; knob is SOLO-ONLY.
  20.294 eventType not the routing key; wire->image CLOSED at the queue interior.

## DEPLOYED (2026-09-06 ~15:10 - the banked state after the evening arc)
   NETWORK   mac 192.168.1.7 (ethernet; identity caches the stale .164 -
             the decoder accepts either); rig 192.168.1.136.
   server    acbb62af4a3ca133 RUNNING (settings relay_join_engine_channel=true,
             relay_peer_join=true, relay_join_target_identity=false (the
             verbatim key is the measured match), retry_cap=10, duty 30000;
             backup .bak_p2-192_dtls).
   clients   mac 572ca7c2fc02ada3 RESTORED (the proven-landing build;
             d5ed2ae3f12e42fb saved as .bak_d5ed2ae3_150906).
             rig d5ed2ae3f12e42fb (backs: .bak_p2d7_20260906_144204=5313eb03).
             BISECT FIRST: 572ca7c2 on both = the proven-landing pair.
   server bak .bak_p2d6_<14:0x stamp>; client baks on both machines hold the
             evening's builds (572ca7c2/3d95a375/0687f/5313eb03 lineage).
   logs      RE_output/logs/<today's stamps>; the auto-archives + the p2-190
             baseline archive (RE_output/logs/20260906_114917).


## NEXT - ROW 7: THE CONNECTED RUNG (established(4) -> connected(5))
##  Row 5 is CLOSED. Do NOT resume the join relay, the retarget, the state
##  ladder, or any "drive the session to 6" idea - the client is a peer and the
##  peer is already established by the membership plane.
  1. (STATIC, first) What MESSAGE feeds the connected rung? The positive
      control is on every boot: the local posse session's peers reach
      '_connected' while the fork session's never do. Diff what the posse
      peers receive against what the group_target peers receive - same log,
      same boot, same client. Start from establishment-decode.md's transition
      sites and [rsi+0x1D18].
  2. (FORK) Publish whatever that is. Row 7 is the gate on row 8's receiver.
  3. READOUT: peer #2 reaching '_connected' in the group_target dumps, then
      a non-zero receiver vptr, then ent_recv calls>0.
  4. The ENTITY contract is ready and waits (20.302-20.304; outer wire type
      open, 20.303 R4). Do not spend it before row 7 opens.
  4. The membership/session plane is DONE and must not be re-litigated: the
      rig arrives as peer #2 `_established`, 3 peers / 2 players, direct
      channel up, reproducible across p2-193a/b and p2-195.
  5. OPEN DEBT: the mac's TWO render-black variants (see the parked-debt block
      above - do not merge them); the image_set hang; logq/logindex broken at
      merge_timeline.py:286; reset_lobby_claims' real-restart path untested
      (the manual pkill + mac-port/launch-server-macos.sh path works and was
      used for p2-195); q.sh false-null on hex addresses (it returned EMPTY for
      1AEF8 while /usr/bin/grep found 10 hits - Tier-2 row, now twice-burned).
## HARD RULES (earned; full text in LESSONS/AGENTS)
  - THE CLIENT IS NEVER MODIFIED - the server must accomplish everything.
  - Reset the server between runs (backgrounded; it hangs AFTER succeeding).
  - Check the INPUT GATE before reading any result (withdrawals, peer bodies actually
    sent) - 20.297 R2 died of this.
  - Before a probe's field enters a conclusion, read the code that PRODUCES it.
  - ANCHOR EVERY DISASSEMBLY; census before filter; solo control before paired.
  - logindex/logq need /usr/bin/python3; launch the server from the REPO ROOT.
