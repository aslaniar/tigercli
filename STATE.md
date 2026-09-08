# STATE - living snapshot

STATUS: live (2026-09-08 - 20.348 CORRECTION BANKED: "runs in missions"
RETIRED. The gate is world-change x MANAGED-SESSION-LIVE (6..9) - the
tower qualifies in retail; in our boots the evaluated session sits at 4.
THE FORK-SIDE LEVER CANDIDATE = the session-state climb 4->6 (the parked
front, reopened). See HANDOFF_2026-09-08_GATE-MACHINE.md - NEWEST, READ
FIRST). Verdict + deployed + next.

*** 20.345-20.347 (THREE SUBAGENT LANES, all local, no boot): THE
## CONSOLIDATED FRONT COLLAPSED TO ONE TRIGGER: ACTIVITY ENTRY.
## - Lane D: no producer for the pending queue in ANY encoding (every
##   section, every form); the queue is a named schema field (mgr+0x206a0
##   = "i107" in runtime reflection tables) and is producer-silent BY
##   DESIGN until established. The manager family is named: the activity
##   singleton's message queue ("msgq %s: in...out...").
## - Lane E: the attachment event FOUND. mgr+0x8=1 written by 0x140B540C1
##   in FUN_0x140B53FC0 (VERIFIED; attachment object = the manager
##   singleton itself, r13+0x2A10 = 0x21DDC09C900). Mode 2/3 writer =
##   FUN_0x140B534A0 (startup/world-entry). The MODE-1 DRIVER = the
##   activity/world-change executor 0x140C090B0 ("Change world
##   (activity_name=...)"), gated on [r14+0x1AEF8] in 6..9 (the
##   managed-session live gate). The cascade hangs off the consumer's
##   fall-through 0x1416FCF95; its pump's byte gates read 0 (open).
## - Lane C: 0x142B0E210 was a TRANSCRIPTION ERROR for 0x14280E210 (the
##   record's KNOWN unmix global) - populated, same per-boot pad as the
##   sibling slot; the "global = 0" premise was measured at a dead
##   address. The activation class's ctor 0x140E3BD00 has ONE caller
##   chain: 0x140E3C0B0 <- 0x140B47B20 <- PHASE-INIT 0x140B37BF0 - a
##   ~40-call unconditional sequencer that NEVER STARTED (tail flag
##   0x141D4CD34 = 0xC2 verified; watch slot registered; zero class
##   instances x2 sweeps). Client-internal verdict INFERRED (medium-high).
## THE FORK-SIDE LEVER: drive the ACTIVITY/WORLD-CHANGE load while a
## managed session is live (6..9) - what the community's mission work
## does. NEXT BOOT: not tower-only; include an activity/world-change load;
## readout now SIX values (recv_root / af0 / f7da0 markers / fragment-list
## / vft-instance check / phase flag 0x141D4CD34). Full text: FINDINGS
## 20.345-20.347 + the three lane reports (RE_output/content/lane_[bcd]_report.md). ***

*** 20.343 (Lane B subagent + parent verification): f7da0 = virtual method
## +0x88 of class vftable 0x141C14F70 (relocated-qword storage - invisible
## to 20.341's u32 scan; method corrected). The class instance is built
## LAZILY by 0x140E3BD00 (decrypt global 0x142B0E210 -> obj=ptr+0x2F00 ->
## vft at obj+0xA0), from stage-init 0x140B37BF0. RUNTIME: the global is 0
## and the class has ZERO instances - the object that would receive the
## activation call never gets constructed. The class's vtable owns the
## whole gate-machine family (+0x88 activation, +0x90 teardown,
## +0x98 flag-clear, +0xA0 de-init). Job body 0x140B76F20 has FIVE static
## call sites (session-startup sequencers; reaches the manager via thunk
## 0x1416FC5E0) - correction to 20.342 R3. The chain-root registry's
## out-handles are ZERO (both address pairs) - the registration never
## completed its store; 20.338's heap-descriptor fact stands. mgr+0xC
## carries the MACHINE IDENTITY (the rig's account key). NEXT: (a) enumerate
## writers of 0x142B0E210 - the fork-side trigger candidate if
## server-reachable; (b) the p2-211 boot readout is FIVE values (adds: does
## vft 0x141C14F70 gain an instance). Full text: FINDINGS 20.343 + Lane B's
## report RE_output/content/lane_b_report.md. Lane A still running
## (free-list lifecycle + pool identity). ***

*** 20.342 (STATIC + dump, NO BOOT): THE MANAGER OBJECT FOUND (STRUCTURAL
## SIGNATURE) - IT IS NOT IDLE: STATE 4, ARMED, +0x8=2, FREE LIST EMPTY.
## The singleton = 0x21DDC09C900 (unique 32-slot init signature). The
## machine ran via the job body; two gates hold the final stage. ***

*** 20.340 (STATIC + full Ghidra analysis of the carved image, 556s/106812
## fns): THE ARM CHAIN IS MEASURED END TO END. The master flag af0 has TWO
## writers: FUN_1416f7da0 = THE ACTIVATION JOB (init sequence, then IF
## FUN_1416cbdd0() (the singleton lazy-ensure: FUN_1416bd610 kind 7 +
## decrypt + validate) passes -> af0 = 1; FUN_1416f7870 = de-init (af0=0).
## _DAT_143051FA8 is NONZERO-ENCRYPTED in the dumps => the manager object
## EXISTS - the 20.338 "ctor 0 heap refs" census was NEEDLE-BLIND to
## encrypted references. Since af0=0 every boot: THE ACTIVATION JOB NEVER
## RAN. Dispatch = static fragment-pair {piece,next-piece} u32-RVA rows in
## .rdata (consumer/clearer/walker/arm1 all registered); f7da0's own rows
## NOT found - that registration is the open item. The consumer's address
## is a 32-BIT RVA (why the imm64 needle missed it). CORRECTED 20.339:
## "af0 has no writer" and "the consumer has no references" both wrong.
## NEXT: (a) f7da0's dispatch registration (.data + text2 dword scan + the
## walker-row pump); (b) FUN_14034d1c0(p) validation + FUN_1416bd610's kind-7
## registration; (c) the p2-211 counter boot now has a THREE-value readout:
## recv_root calls / af0 / f7da0's init markers (obj+0x59820, b05/b07/b09
## clears). Full text: FINDINGS 20.340 (plain-english section included). ***

*** 20.339 (STATIC, NO BOOT - READ FIRST ON THE ROW-8 FRONT): THE GATE CLUSTER
## IS A READABLE ARMED-STATE MACHINE AND THE MASTER FLAG NEVER ARMS. The
## on-disk exe is encrypted at EVERY code site; the dump memory is the truth -
## carve_runtime_image.py rebuilt it (oracles PASS) and Ghidra decompiled the
## 116-function neighborhood directly. Findings: (1) VMProtect virtualization
## exists (168 verified .vmp0 entries image-wide) but ZERO near the
## construction chain; .vmp0 at rest = 69.5% zeros + plain RVA table, not
## active bytecode. (2) The gate cluster (0x142037AF0..B40): af0=master switch
## (read everywhere, WRITTEN NOWHERE in any form - .text/.vmp0/absolute all
## scanned), af3=1 + B00=7 + AF8=ts = "transition armed" (set by
## FUN_1416fd0a0 / FUN_1416fbb40(5), both called only from the consumer tick
## 0x1416FCE01), b07/b08/b09/b0a/b04 = consumed-then-cleared sub-flags,
## b18 = 0x100-byte data buffer. (3) THE "VM-OBFUSCATED" RING SITES ARE
## POINTER-DECRYPTION HELPERS (global -> XOR chain -> real object pointer;
## terminal constant 0xab1f3b47; pointer globals per-boot-encrypted) - logic
## is plain; pointers are hidden. (4) RUNTIME: af0=0 in EVERY archived dump
## (byte-identical cross-artifact; b04=1, b09=1, b0a=1 idle). THE ARMING
## INPUT IS CLIENT-INTERNAL = the transport-JOB dispatch row 8 parked, now
## with a named flag and a hunt path (WHO re-encrypts _DAT_143051fa8).
## Full text: FINDINGS 20.339; artifacts RE_output/content/carve_*.txt +
## gate_census_p2-206.txt. Composes with the staged p2-211 counter boot. ***

*** 20.337/20.338 (2026-09-07 evening, STATIC + p2-206 artifacts, NO BOOT): THE
## CONSTRUCTION CHAIN IS REGISTERED AND LIVE, C2 IS BUILT AS A PATCH, AND STAGE
## B'S ASYMMETRY IS SESSION CHURN. (1) THE VTABLE READ: the receive-block
## construction chain's root 0x140B5ECD0 is entry 0 of a 14-entry handler table
## registered by one readable VMP call (header{count=1,6 fns}@0x141C16660,
## table@0x141C166A0) - and the registration RAN: in the p2-206 dump the
## descriptor object is live on the heap carrying the exact registration
## arguments, the root's address sits in NINE byte-identical heap records, the
## ent ctor 0x1416BB1E0 has ZERO heap refs (blocks absent, consistent), control
## needle 0 (scan sound). So "architecturally unreachable" is NOT what the
## artifact says - what is measured is ONLY that the CONSTRUCTOR never ran;
## whether the root executes-and-bails or is never dispatched is NOT settled and
## must not be asserted either way. The settling instrument: a READ-ONLY call
## counter on 0x140B5ECD0 - one boot, one number. (2) STAGE B: the 48
## same_account refusals are a CONTIGUOUS JOIN TRANSIENT on ONE session (~1.2k
## ticks after commit, ends after ~4 min; then 456 of 482 snapshots carry a
## peer) - the guards are FINE, nothing to loosen. The 65:3 asymmetry is NOT the
## duty cycle and NOT join timing - it is SESSION LIFETIME: the rig's session is
## long-lived (456 snapshots) while the mac's churn at 6-9 each, then replaced.
## WHY the mac's activity sessions churn is the open Stage-B question,
## server-side in the fork. (3) C2 BUILT, NOT DEPLOYED:
## 0001-c2-cross-member-allocation.patch - member_identities(): one row per
## joined MACHINE, caller first (base 0 never moves), behind
## gameplay.entity_index_allocation_cross_member (default OFF = v1 byte-exact);
## empty walk falls back to v1's single row (can never publish an empty
## allocation). C1 WITHDRAWN: the cadence is fine (17 pushes spread across the
## whole boot). (4) 20.336's corrections stand beneath this: startup-only server
## logs for 3 of the last 4 boots, p2-207's ledger record VOIDED, the row-8
## census needle fixed (vtable bases, not handler addresses) - verdict re-tested.
## Full text: FINDINGS 20.336-20.338; the live chart is FRONT_multiplayer-chain.md. ***

*** 20.336 (STATIC, NO BOOT - READ BEFORE ACTING ON ANY p2-207..p2-210 CLAIM):
## THREE CORRECTIONS AND A NEW FRONT.
## (1) THE ARCHIVE IS STARTUP-ONLY FOR THREE OF THE LAST FOUR BOOTS - server
##   logs of 24/41/24 lines for p2-207, the 165911 auto, and the p2-208-210
##   window; p2-207 lost the MAC too (47 lines, ends t=1834, never left hook
##   install). p2-207's "EFFECT NULL ON BOTH MACHINES" has no mac behind it and
##   cites `stage=crafted_peer` lines that occur ZERO times in the archived
##   server log; the arm is also SOLO-ONLY (20.295 R3) and was run PAIRED. The
##   p2(42) question is OPEN, not answered.
## (2) 20.335 R4's "the trailing pair is the ONLY variable" DOES NOT SURVIVE THE
##   ARCHIVE: p2-207's rig logged 246 checksum lines, and p2-185 (2026-09-05,
##   BEFORE the sweep existed) logged 206/46 on both machines.
## (3) THE ROW-8 CENSUS NEEDLE WAS WRONG - it searched for HANDLER ADDRESSES;
##   an object stores its VTABLE BASE. Bases now PROVEN (ctor 0x1416BB1E0 LEAs
##   all four: 0x1C9ADD8/0xAE50/0xAEC8/0xAF40, handler at +0x50). Re-run on
##   p2-206: 0 heap, control 4 image hits. ROW 8'S VERDICT STANDS - and is now
##   actually tested. Tool fixed (4a instance test / 4b control).
## THE INVARIANT AND THE NEW FRONT: `networking:simulation:entity: failed to
##   create 'player_broadcast' entity` fires in EVERY boot, BOTH machines (17-80),
##   and is the ONLY string the client's simulation/entity subsystem emits.
##   Traced: pb_create -> ent_make -> idx_alloc(mgr_free=0) -> -1 -> site 214.
##   The manager is low=100/high=200 and sits at 0 all boot (rig: failures to
##   t=237031, 185s after its one fill). The fork pushes index_allocation 17x a
##   boot, EVERY ONE members=1, join-burst only - and its own call-site comment
##   says "the cross-member map is deferred" while the comment above it says
##   "without it every player_broadcast creation returns -1". The encoder already
##   supports 64 members; only the call site passes one. p2-206 - the best boot on
##   record (players valid 0x3, both in tower, no black, zero checksum lines) -
##   still failed 17x/79x. THE CHECKSUM FRONT REPAIRS A SWEEP-INSTRUMENT
##   REGRESSION AND RETURNS TO A STATE THAT ALREADY DOES NOT RENDER.
## LIMIT (do not oversell later): this does NOT prove filling the pool renders a
##   peer - the local creation loop is self-only (20.301/20.260) and the receive
##   blocks are genuinely unconstructed. It is the best-evidenced open lead.
## Full text: FINDINGS 20.336. ***

*** 20.335/20.333 (p2-206..210 arc + THE PIN-DOWN) - PARTLY CORRECTED BY 20.336
## (R4's single-variable claim + p2-207's verdict; read 20.336 FIRST): THE MEMBERSHIP CHECKSUM
## GATE IS FOUND AND THE PEER-ARRIVAL BLACK'S MECHANISM IS MEASURED END TO
## END. The client rejects the fork's membership bodies ("session membership
## checksum failed" -> forcing disconnect -> the black when the rig arrives);
## the rejections track EXACTLY ONE variable across six boots - the trailing
## 32-bit pair (stable bodies: zero rejections ever; cycling: rejected every
## republish). The p2(42) pair was the POISON, not the render trigger; the
## crafted-self row (p2-207) and foreign-row+fresh (p2-208) both nulled on
## today's build. PIN-DOWN ITERATION 1: the fork's emission side is PROVABLY
## correct (state_hash_matcher.py: line-verified lookup3 + SELF-CHECK
## hash_bytes(dump)==logged Y); the base-shift hypothesis REFUTED by
## execution (client_base=1 = the documented client layout, still 415
## rejections); the residual = the pair's participation in the client's
## hashed replica; the site-269 verifier static read is the next lane.
## CORRECTED RECORDS (this session): p2-206's 'setup flags' attribution VOID
## (settings load once; the flips never reached the wire until the restarts);
## 20.331's 'unarmed at idle' VOID (the raw-global read is not the unmixed
## base). PLAYABILITY: sweep OFF, clientBase TRUE (the stable+TRUE cell is
## the playable baseline). DEPLOYED: server 55bfc8d8732fcb32 (the state-hash
## instrument, gated on membership_sweep), clients be5807eca028ddea both. ***

*** 20.322 (STATIC + FEMU + STANDALONE TESTS, NO BOOT): THE CARRIER IS NAMED AND
## THE SEND IS BUILT. The ent cluster's only entry is the [[vptr]+0x50] vtable
## dispatch - the carrier is the ESTABLISHED PACKET's EXTERNAL BODY:
## [ext-present 1][body][filler-absent 1][padding] after the two reliable queues.
## The fork's packets declared it ABSENT forever (write_absent_filler); the
## client's receive pipeline is ARMED (gate global 0x142037AF0 = 1 in dump_p2146;
## no readable writer - VMP-set). femu: ent_create APPLIES a fresh descriptorless
## id (7) byte-identically to id 0/2 - NO grant message needed. The send is wired
## server-only behind gameplay_external_body (activation settings): one-record
## playerBroadcast CREATE, token {7,0}, baseline = dump descriptor-0's real kind-2
## bytes fd 87 97 50 21 0f 02 21; the peer's ACK OF THE PACKET SEQUENCE proves
## delivery (the body is not reliable-queue protected; 4-attempt cap); self-test
## runs once and FAILS CLOSED - and caught a real truncation bug pre-deploy
## (finish() bytes stored as bits). BOOT p2-197 STAGED: brief GATE PASS, settings
## staged (.bak_p2-197_pre_external), D-044, front peer-entity-send (streak 0).
## READOUT: fork stage=external result=sent/acked; client's own receive line;
## stage=tail (RX diagnostic) separates view-gate-closed from grammar mismatch.
## ABANDON: gate off = byte-identical to pre-probe. Full: FINDINGS 20.322 +
## BOOT_BRIEF_p2-197.md. ***
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
## THE (3,4) STALL, RE-MEASURED ON p2-195 by the resv_rec probe - same boot,
## two records, the positive control sitting beside the failure:
##   rec=0 (the FORK's connection, ident ...0701A8C0): s30e8=4 s1dc0=5 - the
##         ladder reaches CONNECTED, touch=a real timestamp, mask 0x0020.
##   rec=1 (THE RIG's record, ident ...8801A8C0): s1dc0=3 -> 4 and STOPS,
##         mask=0x0000, touch=-1 (never touched).
## Identical to p2-180's measurement, so the stall survived W4, the duty-cycle
## fix AND the entire p2-181..p2-195 relay arc. establishment-decode CLAIM 2:
## the 3->4 site 0x141803F2B is guarded on [rsi+0x3040]==3 AND [rsi+0x1D18]==5
## - establishment REQUIRES the ladder at CONNECTED(5). The connected rung is
## MESSAGE-FED (0x1417E5A10 -> pump -> 0x1416D56C0, event type 4 subtype != 8
## -> 0x1416BCFC0). The fork's own connection gets that event; the peer's
## record never does. THAT is the question.
## ent_recv=0 IS A SYMPTOM of this, not an independent row-9 problem: the
## receiver is gated on establishment. The entity contract stays spec-complete
## (20.302-20.304, outer wire type open) and WAITS.
## INSTRUMENT WARNING (cost me two wrong readings today): the membership dump's
## `s=_established` / `s=_connected` STRING IS NOT THIS FIELD. It is not even
## monotonic - `_connected` appears BEFORE `_joining` in the same session's
## sequence. Read s30e8/s1dc0 via resv_rec; never infer the ladder from the
## dump string.
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

*** p2-196 + THE LATE-SESSION CORRECTION (2026-09-06). READ THE CORRECTION, NOT
## JUST THE BOOT.
## p2-196's TWO results:
##  (1) MY HYPOTHESIS REFUTED CLEANLY - disown rec=1 bit=5 before=0x0020
##      after=0x0000 wasset=1 ident=0xFF000C198801A8C0, twice: the RIG's
##      participant bit IS set and IS cleared. 20.277 R2's set-then-disowned
##      reading STANDS. resv_rec's mask=0x0000 is the aftermath.
##  (2) THE (3,4) STALL IS NOT A STALL. The rig's connection 0x41D49B8 (= rec=1
##      by the 0xA8 base arithmetic) went ladder 4 -> 5 at t=266218 after
##      rung_adv fired at t=266149, and HELD at 5 through t=358252. The stall
##      carried since p2-164 and "reproduced" in p2-180/p2-195 was A DEAD
##      SAMPLER'S LAST READING: resv ran 10 times all boot, last at t=264682,
##      93 seconds before the log ends. ROWS 1-7 ARE DONE OR PASSING.
##
## *** THE CORRECTION - TWO CLAIMS I MADE THIS SESSION AND THEN DISPROVED ***
##  (a) "The fork has no entity encoder" is WRONG. I grepped the wrong names.
##      The fork HAS activity_entity_slots_encoder, activity_entity_index_
##      allocation_encoder, activity_entity_index_grant_encoder and
##      entity_baseline - the top two ranked carrier candidates - wired behind
##      the gameplay settings entity_index_allocation / _assignment / _grant.
##  (b) "Nothing has ever been sent" is WRONG. 20.218 (p2-143, verified-by-log):
##      "THE ROUTER GATE THEORY IS DEAD - OUR MESSAGES ROUTE (flags=0x00).
##      ASSIGNMENT+ORDERING ALL CONFIRMED WORKING." The fork's activity messages
##      reach the client's router and the assignment->recreate->sync chain runs.
##  The ent_recv=0-in-97-of-97 count is REAL and still the headline symptom, but
##  its cause is NOT an absent sender. It is downstream of index allocation.
##
## RETRACTED 2026-09-06 EVENING (20.321, STATIC): ROW 7B IS A POISONED CLAIM -
## IDX_ALLOC IS NOT THE PEER-RENDER BLOCKER. The user challenged the identity;
## verifying it killed the causal chain. Identity CONFIRMED (a real free-slot
## allocator over the session object's +0xC118 8192-bit pool), but it has
## exactly ONE caller (ent_make 0x14170F190 <- 0x1416EE180, the LOCAL creation
## loop; the create is never attempted for a foreign record, 20.300), the
## receive cluster structurally cannot reach it (+0xC118's only writers are
## init/alloc/release, CLAIM G), ent_create's lease/descriptor validation is
## SOFT (bit0-payload decodes FROM THE WIRE regardless; disasm 0x141718080),
## and the local player renders every boot while idx_alloc fails 54x. The -1
## is real and belongs to SYSTEM A (the session entity-slot pool, the
## tag-0x14/0x15 request/donate protocol, open) - NOT SYSTEM B (ent_recv/
## ent_create, small-int ids 0..6, lease bitmap +0xC520) which IS the peer
## path. THE ALLOCATOR-PROBE SPEC IS RETIRED (wrong subject; bootstrap #8
## silenced). Wire check: NO tag-0x14/svc20 request exists in any archive.
## Full text: entity-index-allocation-schema.md final section. ***
##
## THE REAL FRONT (restored, sharper): the fork must SEND a peer entity on the
## sobject system. The contract (20.302-20.304) is spec-complete except ONE
## unknown: the OUTER WIRE TYPE (dispatch into vtable slot 10; carrier chain
## 0x1416EACB0 -> 0x1417115D0 -> 0x1417117D0, same entity storage). The id is
## OPEN-SOFT: bit0-payload decodes without lease bit or descriptor, so a grant
## may not be needed - ent_create's step-5 gate 0x1417114C0 and the apply path
## decide. FEMU CAN ANSWER THAT WITH NO BOOT.
##
## AND THE RECORDED ROOT CAUSE FOR IT IS PROBABLY WRONG: CLAIM O of
## entity-index-allocation-schema.md says the client's index request rides BAP
## svc21 and the fork answers it empty. The request body - which the claim calls
## "still unread" - has been captured in ~130 archives and decodes to protobuf
## field 2, a PACKED REPEATED VARINT list 1090090..1090202 (sorted runs, 1.09M
## band). Entity indices are SMALL INTEGERS 0..6 (20.302). That is a catalogue
## query, which is what the fork's own routing already calls it
## (RequestService::purchasedOffers), and an EMPTY reply is correct for it.
## CLAIM O's "exactly once per join" is contradicted too (p2-196: 3; another
## boot: 11). DO NOT build an entity-index grant body onto svc21 - the
## scaffolding exists (BodyCodec::entityIndexGrantResponse) which is exactly why
## that mistake is cheap to make. Full text: the claim doc's last section. ***


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

## DEPLOYED (as recorded by the p2-206..210 session, 2026-09-07; verified only
##    against the 20.335 headline record - the pre-boot checklist still applies)
   NETWORK   mac 192.168.1.7 (ethernet; identity caches the stale .164 -
             the decoder accepts either); rig 192.168.1.136.
   server    55bfc8d8732fcb32 (the state-hash instrument, gated on
             membership_sweep; still includes the p2-203 type-51
             bubble-startup echo behind activity_bubble_startup and the
             20.325 type-20 fix).
   clients   be5807eca028ddea on BOTH machines (the audited platform; the
             tree client build is unshipped work - the preflight client pair
             FAILS knowingly, D-049).
   settings  PLAYABILITY: sweep OFF, clientBase TRUE (the stable+TRUE cell,
             20.335).
   logs      RE_output/logs/<today's stamps>; ARCHIVE WARNING (20.336 R1):
             server logs were startup-only (24/41/24 lines) for 3 of the
             last 4 boots - verify the archive is complete before reading
             any null.


## NEXT - THE PAIRED p2-211 BOOT (Stage D counter + Stage B lifetime + C2), STAGED NEVER RAN
##  The Claude session died at its limit AFTER writing the staging, BEFORE
##  running it. Staging worktree .claude/worktrees/fork-p2211 (nested fork repo
##  at HEAD 3578d98 + the 13 uncommitted deployed files carried over) holds
##  apply_p2211.py - WRITTEN, VERIFIED UNAPPLIED (0 hits for both edits). It
##  adds: (a) CLIENT the recv_root read-only call counter (RVA 0xB5ECD0, exact
##  .pdata bounds offset 0, budget caps EMITS only, kTargetsSize 68->69);
##  (b) SERVER release_session teardown logging (ev=activity
##  stage=session_release). SEPARATELY WAITING: 0001-c2-cross-member-allocation.patch
##  (the 20.337 C2 arm, also unapplied). PRE-NAMED READOUT, readable either way:
##  - recv_root calls=0 -> nothing dispatches entry 0; the question moves to what
##    owns/dispatches the table. calls>0 -> it runs and bails, and the bail is a
##    static read of a readable 1181-byte function - likely server-satisfiable.
##  - server: session_release lines name WHO tears the mac's sessions down
##    (20.338 R4's churn question).
##  - C2 arm (if applied): mgr_free stays >0 past landing; site-214
##    `failed to create 'player_broadcast' entity` falls from 17-80 toward 0;
##    `index_allocation push members=N` with N = session members.
##  ABSENCE NEGATIVES: members=N ships and mgr_free still reads 0 -> the client
##    is not consuming cross-member rows (real verdict, not a null). Guard the
##    server log ARCHIVE (20.336 R1: 3 of the last 4 boots logged startup-only).
##  DO NOT: assert the root is never dispatched (unmeasured either way); loosen
##    same_account (a join transient, 20.338 R4); raise the 30s duty cycle
##    (`paced` is not a failure, 20.337 R3); deploy C2 without testing the
##    default-OFF settings flip; run the p2(42) arm PAIRED (solo-only,
##    20.295 R3); cite 20.53 as a render control (retracted); re-census ent
##    instances with handler-address needles (vtable bases only, 20.336 R4).
## HARD RULES (earned; full text in LESSONS/AGENTS)
  - THE CLIENT IS NEVER MODIFIED - the server must accomplish everything.
  - Reset the server between runs (backgrounded; it hangs AFTER succeeding).
  - Check the INPUT GATE before reading any result (withdrawals, peer bodies actually
    sent) - 20.297 R2 died of this.
  - Before a probe's field enters a conclusion, read the code that PRODUCES it.
  - ANCHOR EVERY DISASSEMBLY; census before filter; solo control before paired.
  - logindex/logq need /usr/bin/python3; launch the server from the REPO ROOT.
