# FRONT — THE PEER-RENDER CHAIN (pinned chart; update after every boot or static verdict)

STATUS: live (2026-09-06, after p2-196). ROWS 1-7 ARE DONE OR PASSING. THE FRONT IS ROW 9,
and it has never once been attempted: the fork has no entity encoder and ent_recv reads
calls=0 in 97 of 97 archives. This is the project's tracking chart.
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
| 7 | Ladder climbs to connected (4->5) | PASSES | The client's connection to the other player climbs all the way to "connected" and stays there. The wall we thought was here was a probe that had quietly stopped reporting. | verified-by-execution (p2-196) |
| 7b | **Entity INDEX allocation** | 🔴 **THE BLOCKER** | Every entity needs an index number from a small pool (the live set is 0..6). The client asks for one, and the request FAILS - idx_alloc returns -1, 23+ times every boot, and the pool mask stays empty. No index means no entity can exist at all. | verified-by-log (20.218 R2), reproduced every boot |
| 8 | Guard + receiver object | BLOCKED, not judgeable | The object that would receive entity data is never built. We cannot tell whether that is broken or simply idle, because nothing has ever had an index to send it. | receiver=0 in every boot |
| 9 | Entity message encodes + sends | READY, waiting on 7b | We know the exact byte format (femu-validated; a guardian's body is RAW 8 BYTES) and the server can already send activity messages that reach the client's router. There is just nothing valid to put in them yet. | verified-by-femu (20.302-20.304) + 20.218 |
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
  the walker's RETURN attributed         = THE CURRENT BLOCKER - the leave
    (MISS / FOUND-LIVE / FOUND-STATE-OUT)  probe on 0x14177A0B0, armed by the
                                            join packet so the hot path pays
                                            nothing outside the window
  join_processor enter                   = the state check must pass first
  join_reserve from 0x14178EA73
    (NOT the self-reserve sites)         = the join flow is running
  admit enter from the join-handler      = the flow completes
  resv mask gains the container bit
    and the record leaves (3,4)          = ADOPTION (row 6)
  ladder reaches (4,5)                   = ESTABLISHMENT (row 7)
  receiver vptr non-zero / ent_recv fires = the entity road opens (rows 8-9)

## THE ONE REMAINING QUESTION ON ROW 5

  **What drives a session slot from state 4 to state 6, and what must the fork
  send to drive the forkSession-named one there?**

Everything else on row 5 is closed by measurement: the channel (p2-192a), the
key (verbatim, p2-193a/b), the container (p2-193a), the lookup (match=1), and
the gate's own decision path (exactly two conditions, claims 11.1).

STARTING EVIDENCE - do not re-derive: 20.184 RESULT 3 (2026-08-29) already
decoded the stage writers as 0x14178CD97's cluster, driven by 0x140C05F80,
which tries stages 0/1, 2/3, 4/5 across 0x1C8A0-stride object pairs until the
setter returns true - "THE CLIENT CYCLES STAGES 0..5 ONLY". p2-195 matches that
exactly: the fork's session is parked at the TOP of the client-driven range.
Something else carries a session to 6, and the positive control is in the same
log - slot0 and slot2 are at 6 on the same boot, same container.

TENSION TO RESOLVE (not a blocker): 20.184 calls 6..9 "a DIFFERENT object
family" from the 0..5 cycling one, but slot0, slot2 and slot5 all live in the
one walked container. Its addresses stand; its framing needs a pass.

## THE CURRENT BLOCKER (measured facts, 2026-09-06 evening)

- The join gate 0x1416E0460, read line by line: (1) word[pkt+0] vs
  0x1416C1260() - the protocol version, PASSES; (2) call 0x14177A0B0 with
  rcx = [rdi+0x28] (mov rcx,[rdi+0x28] at 0x1416E04A4, call at 0x1416E04AC) -
  the walker over the ARRIVING CONNECTION's six session slots; (3) on a hit,
  0x1416E04B6: add ecx,-6 / cmp ecx,3 / ja 0x1416E04D7 - the state window,
  branching into the SAME refuse block as not-found, which is why both
  failures print identical text; (4) otherwise call 0x1417806C0, the processor.
- The walker's 35 consumers all sit in the connection-layer receive region
  (0x1416CD300..0x1416E13DA) plus 0x14175B8F0; the receive pump climbs into the
  VM-obfuscated ring, which is where the framing/reachability question ends.
- The gate's identity blobs are at [rec+0x57C] (bit 4 of [rec+4] set) or
  [rec+0x94E] - DELIBERATELY UNALIGNED fields, which is what blinded the
  observer for five boots.
- The session binders bind slot objects' [+0x1C7C0] through the init-time
  context manager 0x14175E520 plus the VMP ring; container objects are
  per-connection and DIFFER between the client's associations - that fact is
  the whole reason the channel mattered.
- The landing-session blob's writer is still an OPEN SITE: apply_stamp proved
  the session apply is NOT it (one firing, early, into a static config
  object); the copier walk 0x1416E2350 is the remaining suspect.
- The game prints its own refusal, greppable in every boot:
  "networking:messages:join-request: received message for an unknown session
  ... sending back a refusal" - the session field renders as two reversed
  dword groups, so decode before comparing.
- PARKED DEBT - TWO DISTINCT RENDER-BLACK FAILURES (user, 2026-09-06), never to
  be merged into one note:
    VARIANT A - SOLO, PRE-SPAWN: the mac never spawns in at all, and a subclass
      swap does NOT fix it. Segment 2 reaches `region result=forced native=0
      answer=1` and never fade_release; the client stays alive and keeps logging.
      p2-195 was this variant, with the rig not yet up.
    VARIANT B - CO-PRESENCE, POST-SPAWN: the mac is ALREADY spawned and moving
      when the screen goes black, and the trigger is the RIG launching to the
      tower. The rig-connection correlation belongs to B and STANDS.
  They differ in when they strike (before vs after spawn), in whether a subclass
  swap helps, and in whether a second machine is needed at all.

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
