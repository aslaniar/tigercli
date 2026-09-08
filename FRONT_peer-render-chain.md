# FRONT — THE PEER-RENDER CHAIN (pinned chart; update after every boot or static verdict)

## WHERE THE PROJECT STANDS (2026-09-08, after the 20.336 archive audit) - read this first

**THE ONE CONSTANT ACROSS EVERY BOOT EVER ARCHIVED:** the client logs
`networking:simulation:entity: failed to create 'player_broadcast' entity`
17-80 times per boot on BOTH machines - and it is the ONLY string the client's
whole simulation/entity subsystem ever emits. Traced end to end: `pb_create ->
ent_make -> idx_alloc (mgr_free=0) -> -1 -> retail site 214 (rva 0x16EE3F7)`.
The client's entity-index manager carries low=100/high=200 and sits at **0 for
essentially the whole boot** (rig p2-206: failures run t=51594..237031, i.e. 185
seconds after its single brief fill). The fork pushes `index_allocation` **three
times a boot, `members=1`, join-burst only** - and the call site's own comment
says *"the cross-member map is deferred"*, twelve lines under a comment that
says *"without it every player_broadcast creation returns -1"*. The encoder
already supports 64 participant rows; only the call site passed a span of one.
**The peer's index block has never been sent.**

WHY THIS DISPLACES THE CHECKSUM LANE: p2-206 is the best boot on record - sweep
off, ZERO checksum rejections, peers valid 0x7, players valid 0x3, both clients
in the tower, variant B absent - and it still failed 17x/79x. The checksum front,
finished perfectly, returns to a state that already does not render; it is
repairing a regression the sweep INSTRUMENT induced (p2-205/206 logged zero
rejections with the sweep off).

THE LIMIT, RECORDED SO IT IS NOT OVERSOLD: this does not prove that filling the
pool renders a peer. The local creation loop is self-only (20.301/20.260) and the
receive blocks are genuinely never constructed (20.336 R4, now correctly tested).
It is the best-evidenced open lead with a server-side lever already proven to
land (p2-198: mask 0 -> ~150).

WHAT WORKS TODAY (the fun part): both clients land in the tower (solo or paired),
the membership plane puts each player in the other's session (players valid 0x3),
entity creation succeeds for the local player, the fork delivers entity records on
two carriers with acknowledgements, and the identity machine is byte-correct end
to end.

## THE CHAIN — fork publishes peer → record → adoption → ladder → guard → receiver → entity → RENDER

STATUS: live (2026-09-07 - p2-208/209/210 banked: THE CHECKSUM GATE FOUND + THE PIN-DOWN ITERATION). **The peer-arrival black's mechanism is now measured end-to-end: the client rejects the fork's membership bodies ("session membership checksum failed" -> "no membership information, forcing disconnect") - and the rejections track EXACTLY ONE variable across six boots: the trailing 32-bit pair (stable bodies: zero rejections ever; cycling bodies: rejection on every republish).** The p2(42) "second variable" was the poison, not the render trigger; the crafted-self-row arm (p2-207) and the foreign-row+full+fresh arm (p2-208) both nulled on today's build (no clone, no peer body - the render question awaits the membership acceptance gate). PIN-DOWN ITERATION 1 (20.335): the fork's emission side is PROVABLY correct (line-verified lookup3 transcription + hash_bytes(dump)==logged Y SELF-CHECK), the base-shift hypothesis REFUTED by execution (client_base=1 = the documented client layout, still 415 rejections - the sessionStateClientBase 'fix' was never the fix), the residual = the pair's participation in the client's hashed replica; the site-269 verifier static read is the next lane. PLAYABILITY: sweep OFF (restored), clientBase TRUE kept (the stable+TRUE cell = the playable baseline, itself untested). INSTRUMENTS STANDING: the state_hash dumps + matcher (state_hash_matcher.py) + the client-log oracles.
Update protocol: after every boot or static finding, re-mark the rows and bump
the STATUS date. Each row's fact must carry its evidence token. The user reads
this instead of re-deriving session narratives.

## THE CHAIN — fork publishes peer → record → adoption → ladder → guard → receiver → entity → RENDER

| # | Link | Status | What it means in plain English | Basis |
|---|------|--------|---|---|
| 1 | Fork publishes the peer; both clients land + hold the row | DONE | Our server tells each client the other player exists, and both accept it and keep it. | verified-by-execution (p2-180) |
| 2 | Client builds the peer's record, identity byte-exact | DONE | Each client turns that announcement into a real internal record with the correct identity bytes. | verified-by-log (20.309) |
| 3 | Live hosted session exists | DONE | The client has a genuine session object alive in the state the rest of the machinery requires. | verified-by-execution (p2-182) |
| 4 | Peer's records enter the candidate list | DONE | The other player shows up in the list the session machinery actually considers. | verified-by-log (p2-182) |
| 5 | Join request passes the connection-layer gate | CLOSED - wrong question | We spent ~14 boots trying to make one client "admit" the other with a join packet. That can never work: only a session's HOST answers joins, and both clients are peers in our server's session. It also never mattered - the membership plane had already put each player in the other's session. | verified-by-execution (p2-195) + claims 11-14 |
| 6 | Reserve -> admit -> adoption | NOT A DEPENDENCY | The reservation/claim bookkeeping sits on a different path. The participant mask it maintains has 7 accesses in the whole binary and none of them is in the entity code. | verified-by-reading (field_xref, 7/7 accesses) |
| 6b | The ID-allocation message reaches its real handler | ✅ **DONE (p2-198)** | Turning the allocation push on (it had been off in every recent boot) worked end to end: the client's applier applied it, the local ID pool filled for the first time ever (0 -> ~150 free), all 48 creation failures stopped mid-boot, and the client's entity creation silently succeeded for the rest of the boot. BONUS: the handler table holds 15 types and the grant type (21) is NOT among them - the old failed-grant experiments were structurally doomed; the allocation was always the right message. | p2-198: mask 0 -> 144-150 across 13.7k samples; failures stop at t=99960 |
| 6c | The client becomes a replication participant (view + receiver registration) | ❌ **TWO ROADS DEAD (20.326 + p2-201/202)** | (a) The view message: the client decodes it fine, then drops it - the receive switch has NO case 40 (a bare `ret`) and no h0 apply slot. No consumer exists on any plane. (b) The type-9 host designation: delivered 4x burst (p2-201) then 45x duty-cycled (p2-202) with correct bodies - zero client response. The client accepts every message the fork can send on this plane and never becomes a participant. Both roads closed by measurement, not argument. What remains of 6c is the receiver-object construction question, static-located: it hangs off a transport JOB. | 20.326 (jump tables + live registry block); p2-201/p2-202 boot_outcome records |
| | 7 | Ladder climbs to connected (4->5) | PASSES | The client's connection to the other player climbs all the way to "connected" and stays there. The wall we thought was here was a probe that had quietly stopped reporting. | verified-by-execution (p2-196) |
| 7b | Entity INDEX allocation (idx_alloc) | ❌ **RETRACTED (20.321) - NOT THE BLOCKER** | idx_alloc 0x141711D10 returns -1 54x/boot - TRUE, identity CONFIRMED (a real free-slot allocator over the session object's +0xC118 8192-bit pool). But it has exactly ONE caller (ent_make 0x14170F190 <- 0x1416EE180, the LOCAL creation loop; the create is never attempted for a foreign record, 20.300), the receive cluster structurally cannot reach it, ent_create's lease/descriptor validation is SOFT (bit0-payload decodes from the wire regardless), and the local player renders every boot while it fails. A peer's index arrives ON THE WIRE. Do not build the allocator probe. | verified-by-reading + callers.py + disasm (20.321, this repo's FINDINGS) |
| 8 | Guard + receiver object | ❌ **CLOSED BY MEASUREMENT (p2-205) - THE BLOCKER IS CLIENT-INTERNAL-ONLY** | One question remained: does a VERIFIED-CORRECT type-51 echo construct the receive blocks? p2-205 answered it: 8 echoes delivered with correct attribution (v3 svc25-echo keying - the FOURTH keying axis, the only durable per-client value), the sent bytes MATCH the client's own identity row byte-exact (dump-verified x5), and the ent slot-10 handlers still have ZERO heap instances - the receive blocks were never constructed. The type-51 apply half is inert BY MEASUREMENT. Combined with lane #4 (apply = ring-push/telemetry recorder; the only construct gate is the VMP byte [unmixed+0xCD5]), NO fork-sendable wire message can construct the receive blocks. Row 8's answer is architectural: the blocks are created by client-internal state (a transport JOB under the VMP gate) that no message reaches. | p2-205: 8x result=stored + identity_dumpcheck MATCH x5 (0x7FF69984DD38) + **[CENSUS RE-DONE 20.336: the original needle searched HANDLER ADDRESSES, which can only ever match the .rdata slot-10 words. Bases proven via ctor 0x1416BB1E0's four LEAs (0x1C9ADD8/0xAE50/0xAEC8/0xAF40, handler at +0x50); re-run on p2-206 = 0 heap, control 4 image hits. THE VERDICT STANDS AND IS NOW ACTUALLY TESTED.]** + lane #4 claims 6f/6g + 20.331 (gate1 = VMP-oracle comparator with no wire inputs; gate cluster byte-identical across all artifacts) |
| 9 | Entity message encodes + sends | ✅ DELIVERY PROVEN (p2-197) | The carrier is NAMED: the established packet's external body (four-channel wrapper; channel 2 = the entity record). The fork now SENDS it behind `gameplay_external_body`: a strict CREATE, token {slot 7, incarnation 0}, type 2 playerBroadcast, baseline = the dump's REAL kind-2 bytes. The clients RECEIVED every probe packet (acks climbed through the probe sequences; no drops, no reconnect storm). Consumption was silent - because of row 8, not the wire. Probe bookkeeping race (gaveup before ack credit) fixed for the next boot. | p2-197: result=sent x8; client base climbed through seq 6; self-test + packet round trip |
| 10 | Entity renders and moves | NOT YET | The actual goal: another player's guardian visible and moving on your screen. | positive control = the local player (20.53) |

## HOW TO READ ROW 5 (after the evening of 2026-09-06)

The front moved further on 09-06 than in the prior week, and the remaining
wall is ONE READOUT wide. Read it as three checks in series:

  CHANNEL   the relayed join must arrive on the connection whose [ctx+0x28]
            container holds the bound sessions. DONE - the engine association
            (relay_join_engine_channel=true; channel=engine on the wire).
  LOOKUP    the walker must find a slot whose identity blob equals the join's
            sessionId. DONE - match=1, measured twice (p2-193a/b), verbatim
            key, gate-chain caller 0x17944FA.
  STATE     the found slot's [+0x1AEF8] must be 6..9. THE WALL, MEASURED at
            the refusal walk itself (p2-195): the matched slot is slot5
            (0x4631748, bind 2 - the session carrying the fork's identity) and
            it is at 4. The two sessions at 6 are the client's own, in the SAME
            container, on the SAME boot - so 6 is reachable and observable.

DO NOT RE-WALK (each was closed by measurement, not by argument):
  - the retarget VALUE arms (1 = join machine id, 2 = real account key,
    3 = recipient's joinId) - all three refused, and p2-190c refuted arm 3 by
    DIRECT measurement of the walked blobs, not just by the refusal line. The
    verbatim fork sessionId is the key that MATCHES; the value question is
    settled.
  - the blob-stamp timing theory (retracted - the container was the variable,
    not the stamp).
  - the connect-family handshake (ids 5/6/7/9): PURE TRANSPORT, a 62-slot
    address-matched connection table; no session binding rides it.
  - the parameters/OOB-plane road (id 38 = a bare `ret`, a silent drop).
  - the +0x818 / +0x38-bit-4 hunts and the creation-loop framing (all dead).

THE INSTRUMENT DEBT THAT GATES THE READOUT: the walk-return probe has been
shipped three times and broken a client twice (duplicate-RVA install froze the
rig; hot-path read cost stalled the mac's landing). Its four defects and the
rules they yielded (R1-R8) are in POSTMORTEM_2026-09-06_THE-BLIND-GUARD.md and
docs/ENFORCEMENT.md. The next version must cost the walker's hot path nothing
outside the join window.

## WHAT EACH ROW 5+ SUCCESS LOOKS LIKE (updated 2026-09-06, after p2-194b)

  join_type0a enter line                 = DONE (p2-183, mac)
  nonce gate passes (it is the protocol
    version check, not a nonce)          = DONE (p2-184: 0xA4F8 == 0xA4F8)
  identity published hash-valid          = DONE (p2-186: offset +152, both
                                            joins completed)
  the lookup's compare measured live     = DONE (p2-187: the key IS the
                                            join's sessionId)
  the gate's walked map measured         = DONE (p2-189: {0,-1,1,-1,-1,2},
                                            identical on both machines)
  the gate's own compare chain visible   = DONE (p2-190c: the alignment fix -
                                            callers 0x17944FA / 0x1794520)
  the relay lands on the right channel   = DONE (p2-192a: channel=engine)
  the relayed join MATCHES a walked slot = DONE (p2-193a/b: match=1, twice)
  --------------------------------------------------------------------
  (row 5 CLOSED here by p2-195/196 - the gate is host-only and the receiving
   client is a peer; the membership plane had already delivered the peer.)
  receiver vptr non-zero / ent_recv fires = the entity road opens (rows 8-9)
  THE FRONT'S OWN READOUT (post-20.321)   = the outer wire type named (static),
                                            femu's accept/reject verdict on a
                                            wire id without lease/descriptor,
                                            then the fork's first peer-entity
                                            send and "receiving sobject
                                            creation" in the client log.

## THE CORRECTED FRONT (20.321, 2026-09-06 evening - replaces the row-5 sections)

Row 5 is CLOSED (host-only gate; never mattered). Row 7b is RETRACTED. The
front is ROW 9: **send a peer entity on the sobject system (system B).**

- SYSTEM B = ent_recv (0x141718510 family) -> ent_create (0x141718080): small-
  int ids 0..6, lease bitmap +0xC520, table A descriptors (runtime-built),
  world manager. THIS is the peer-render path. Contract spec-complete
  (femu-validated) except the OUTER WIRE TYPE.
- SYSTEM A = the session entity-slot pool (+0xC118, 8192 slots, idx_alloc,
  tags 0x14/0x15 request/donate, in-activity init leaves the local mask
  empty). REAL and open - no tag-0x14 request exists in any archive - but NO
  verdict depends on it. Parked; do not spend a boot on it.
- THE ID QUESTION IS OPEN-SOFT: ent_create's lease-bit and descriptor checks
  bail to a NON-fatal path; with header bit0 set the record decodes from the
  wire regardless. If femu confirms the apply path accepts a fresh wire id,
  NO grant message is needed at all.
- NEXT (STATE.md): 1) name the outer wire type (static; carrier chain
  0x1416EACB0 -> 0x1417115D0 -> 0x1417117D0, router census 44 handlers);
  2) femu ent_create with a bit0-set kind-2 body and a fresh id;
  3) fork-side send on the identified carrier; 4) ONE boot.
- PARKED DEBT - TWO DISTINCT RENDER-BLACK FAILURES (user, 2026-09-06), never
  to be merged into one note. CORRECTED 2026-09-07 (p2-204): variant A's
  "solo never spawns" was, in p2-204 v1, THE CASCADE BUG (the v1 keying made
  the type-51 arm fail closed, `encoded=false` rolled back every join burst,
  the session starved) - fixed by the arm decouple (p2-204 v2), and the mac
  landed SOLO. The variant families stay distinct; the p2-204 correction
  applies to A's mechanism, not B's.
    VARIANT A - SOLO, PRE-SPAWN: the mac never spawns in at all, and a
      subclass swap does NOT fix it. Segment 2 reaches `region result=forced
      native=0 answer=1` and never fade_release; the client stays alive.
      p2-195 was this variant, with the rig not yet up. p2-203's transient
      `Failed to find the Orbit slice-set name` (t=66505) is the same family
      (it fell back to orbit, later landed - bursts survived there).
    VARIANT B - CO-PRESENCE, POST-SPAWN: the mac is ALREADY spawned and
      moving when the screen goes black; the trigger is the RIG launching to
      the tower. The rig-connection correlation belongs to B and STANDS.
  They differ in when they strike (before vs after spawn), in whether a
  subclass swap helps, and in whether a second machine is needed at all.

## FAIL MODES BANKED (all resolved, with their resolutions)

  p2-183 (b): handler internals -> RESOLVED by p2-184's instruments (nonce
       passes; the lookup is the blocker)
  p2-183 (c): framing/nonce -> RESOLVED (the OOB framing works; the "nonce"
       gate is the protocol version)
  (d) processor fires, reserve/admit never -> the candidate/gate conditions
       (still pre-named for the next boot)
  p2-188: arm-1 inert (relay verbatim) -> RESOLVED: the mac's identity table
       carries a stale cached address in its first NetAddr pair; the decoder
       now accepts either pair (SHIPPED, p2-188b proven)
  p2-188b: arm-1 refuted (the gate's slots don't hold the join machine id)
       -> BANKED: the retarget mechanism stays; the value arm is closed for
       the join-id form; the connect-family decode is next

## THE LAYER STACK (bird's eye; top = closest to the player, bottom = closest to the wire)

| Layer | What it is | Fork status |
|---|---|---|
| RENDER | models, animation, the world you see | the last link; untouched until entities flow |
| APPEARANCE/POOL | participant records, entity-index pool, image/descriptor machinery (types 28/30/45) | decoded; waits on a real entity |
| ENTITY | entity messages: receive cluster, kinds/codec, carrier 17 | contract spec-complete (femu-validated); 1 unknown (outer wire type) |
| ESTABLISHMENT | per-record connection ladder: established(4) -> connected(5), the (3,4) stall | decoded; waits on ADMISSION |
| SESSION MACHINERY (in-client, per-tick) | session slots state 0..9, candidate table, join_gate, reserve/admit, peer-adoption walker | RUNNING (p2-182: sessions live at 6, candidates fed) - blocked only by the join delivery |
| SESSION-PLANE MESSAGES (F3, ids 0x1E..0x25) | registered family: membership-update, player-add, boot-machine, delegate-leadership (runtime registry, own dispatch space) | fork publishes membership here; the RELAY WRONGLY delivered the join here (p2-181's mistake) |
| CONNECTION LAYER (receive switch 0x1416E0940, types 0..0x2A) | machine-to-machine packets: connect 5/6/7/8, ping/pong, type 0x0A = THE JOIN, membership rows (type 12) | fork RECEIVES joins here (joincapture); sending type 10 back = THE FRONT (p2-183) |
| TRANSPORT | sockets, DTLS peer channel, NAT/rendezvous | DONE |

Reading rule: a join body is BORN on the connection layer (a client sends its
type-0x0A to its join target). The relay moved it UP two layers and re-sent it
on a different layer - which is why no machine ever consumed it.
