# FRONT — THE PEER-RENDER CHAIN (pinned chart; update after every boot or static verdict)

STATUS: live (2026-09-06, after p2-194b + the evening decode). This is the project's tracking chart.
Update protocol: after every boot or static finding, re-mark the rows and bump
the STATUS date. Each row's fact must carry its evidence token. The user reads
this instead of re-deriving session narratives.

## THE CHAIN — fork publishes peer → record → adoption → ladder → guard → receiver → entity → RENDER

| # | Link | Status | Basis |
|---|------|--------|-------|
| 1 | Fork publishes the peer; both clients land + hold the row | DONE | verified-by-execution (p2-180) |
| 2 | Client builds the peer's record; identity byte-exact | DONE | verified-by-log/dump (20.309) |
| 3 | Live hosted session exists (machinery precondition) | DONE | verified-by-execution (p2-182: state 6, sids 0/1, BOTH machines) |
| 4 | Peer's records enter the session candidate list | RUNNING | verified-by-log (p2-182: add_candidates from 0x141769CFC, per session) |
| 5 | **JOIN REQUEST passes the connection-layer gate** | 🟡 **TWO OF THREE CHECKS PASS. (1) THE CHANNEL IS FIXED: the join gate (0x1416E0460) loads the walker's container from [ctx+0x28] of the packet's OWN connection (disasm-verified), so the relay must ride the association whose connection object holds the bound sessions - the ENGINE association, not the OOB datagram whose container is nearly empty. relay_join_engine_channel=true, SHIPPED, channel=engine wire-proven. (2) THE LOOKUP MATCHES: on the engine channel the relayed join's key (the verbatim fork sessionId) matched a walked slot's blob, match=1, MEASURED TWICE (p2-193a/b, gate-chain caller 0x17944FA). (3) THE GATE STILL REFUSES - and the found-path carries a SECOND check the decode had missed until 09-06: [found_slot+0x1AEF8] must be in {6,7,8,9} (the session-state window, 6 = LIVE HOSTED) or the SAME 'unknown session' refusal text fires (0x1416E04B6: add ecx,-6 / cmp ecx,3 / ja -> the not-found refuse block). THE AMBIGUITY: walk_map read the matched slot (slot2) at st=6 - INSIDE the passing window - while join_processor (hooked at the gate's own found-path callee 0x1417806C0) stayed at calls=0. Either (a) +0x1AEF8 differs at the refusal walk from the landing walk, or (b) the matched walks were another consumer of the shared walker and the gate's own walk missed. ONE INSTRUMENT SEPARATES THEM: the walker's LEAVE probe (its return value = the gate's own lookup decision, attributed)** | verified-by-execution (p2-192a, p2-193a/b) + verified-by-reading (the join gate's full disasm) |
| 6 | Reserve -> admit -> adoption completes for the peer | DECODED, waits on 5 | verified-by-reading (20.108 end-to-end) |
| 7 | Ladder climbs to connected (4,5) | DECODED, unproven | verified-by-reading (establishment-decode.md; gate = ladder==5) |
| 8 | Guard + receiver object | DECODED, unobserved | verified-by-reading (20.279/20.287; receiver zero in every measured state) |
| 9 | Entity message encodes + sends | SPEC-COMPLETE, 1 unknown | verified-by-femu (contract + payloads; outer wire type open, 20.303 R4) |
| 10 | Entity renders and moves | NOT YET | the last link; positive control = the local player (20.53) |

## HOW TO READ ROW 5 (after the evening of 2026-09-06)

The front moved further on 09-06 than in the prior week, and the remaining
wall is ONE READOUT wide. Read it as three checks in series:

  CHANNEL   the relayed join must arrive on the connection whose [ctx+0x28]
            container holds the bound sessions. DONE - the engine association
            (relay_join_engine_channel=true; channel=engine on the wire).
  LOOKUP    the walker must find a slot whose identity blob equals the join's
            sessionId. DONE - match=1, measured twice (p2-193a/b), verbatim
            key, gate-chain caller 0x17944FA.
  STATE     the found slot's [+0x1AEF8] must be 6..9. UNRESOLVED - the field
            read 6 on the matched slot at the LANDING walk, yet the processor
            never ran. This is the whole of row 5's remaining wall.

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

## WHAT THE LEAVE READOUT DECIDES (pre-named, all three branches)

  MISS             -> the gate's walk uses a DIFFERENT container than the rich
                      one; attribute via the container-id lines (live since
                      p2-191) and the fix moves back to delivery.
  FOUND-LIVE       -> the state check passes and the refusal comes from DEEPER
                      than the decode reaches; next decode = 0x1417806C0's own
                      body (capacity vs [pkt+8], flags [pkt+4]).
  FOUND-STATE-OUT  -> the fork-side fix is making the forkSession-named session
                      reach state 6+; p2-182 proved sessions reach 6 organically,
                      so this is a sequencing problem, not a missing mechanism.

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
- PARKED DEBT, now causally interesting: the mac's co-presence render-black
  (client stays alive, segment 2 reaches region-forced and never fade_release;
  the rig's connection event is its sharpest trigger correlation).

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
