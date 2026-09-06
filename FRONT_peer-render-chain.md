# FRONT — THE PEER-RENDER CHAIN (pinned chart; update after every boot or static verdict)

STATUS: live (2026-09-06, after p2-189). This is the project's tracking chart.
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
| 5 | **JOIN REQUEST arrives on the connection layer** | 🟡 **everything up to the lookup DONE (delivery ✓, version gate ✓, record ✓, walker decoded ✓, retarget mechanism ✓). p2-189 MEASURED (both machines): the gate's walked six slots are bound to SMALL-INDEX sessions {0,-1,1,-1,-1,2}, one NAMED BY THE MACHINE'S OWN JOINID (binder2's stack args = the joinId; binder ctx pointers = the walked slots; cof chain captured). The relayed join's key must equal the RECIPIENT'S JOINID = retarget ARM 3 (the fork holds the live value; the rewrite machinery is built). The session-apply is NOT the landing blob's writer (open site). sesscmp caller-discrimination works; per-caller budgets = the one instrument fix. Parameters road closed; connect-family = pure transport (id 8 dropped OOB). Next: arm 3 boot + the binder-trigger correlation** | verified-by-execution (p2-183..189) + verified-by-reading (20.319/20.320) |
| 6 | Reserve -> admit -> adoption completes for the peer | DECODED, waits on 5 | verified-by-reading (20.108 end-to-end) |
| 7 | Ladder climbs to connected (4,5) | DECODED, unproven | verified-by-reading (establishment-decode.md; gate = ladder==5) |
| 8 | Guard + receiver object | DECODED, unobserved | verified-by-reading (20.279/20.287; receiver zero in every measured state) |
| 9 | Entity message encodes + sends | SPEC-COMPLETE, 1 unknown | verified-by-femu (contract + payloads; outer wire type open, 20.303 R4) |
| 10 | Entity renders and moves | NOT YET | the last link; positive control = the local player (20.53) |

## HOW TO READ ROW 5 (the front, after p2-189)

p2-183 delivered the join bytes OOB (the join's native channel) and the
client's own join gate RAN. p2-184 measured the gate's first check (the
"nonce" = the PROTOCOL VERSION — passes). p2-186's identity fix at +152 is
hash-valid and stays. p2-187 measured the lookup's one-qword compare LIVE.
20.319 (static) decoded the gate's walker completely and CLOSED the
parameters road (OOB id 38 = the default stub = silent drop). p2-188/188b
proved the retarget mechanism live (arm 1's value refuted; the identity
decoder fixed and proven). 20.320's decode identified the BINDERS as the
binding chokepoints; p2-189's six new instruments captured them live on
BOTH machines: the gate's walked six slots are bound to small-index
sessions {0, -1, 1, -1, -1, 2}, one named by THE MACHINE'S OWN JOINID
(binder2's stack args, byte-exact vs each machine's admit line), and the
binder context pointers match the walked slots exactly. THE CONSEQUENCE:
the relayed join's sessionId must equal the RECIPIENT'S CURRENT JOINID —
retarget arm 3, the first arm whose key value is proven inside the gate's
walked records on both machines.

## WHAT EACH ROW 5+ SUCCESS LOOKS LIKE (updated at p2-189 close)

  join_type0a enter line                 = DONE (p2-183, mac)
  nonce gate passes                      = DONE (p2-184: 0xA4F8 == 0xA4F8)
  identity published hash-valid          = DONE (p2-186: +152, both joins completed)
  the lookup's compare measured live     = DONE (p2-187: key = sessionId)
  the gate's walked map measured         = DONE (p2-189: walk_map, both
                                           machines: {0,-1,1,-1,-1,2})
  the binding events attributed          = DONE (p2-189: binder ctx = the
                                           walked slots; the key = the
                                           machine's own joinId)
  caller-discriminated sess_cmp          = DONE (works; per-caller sub-
                                           budgets = the one instrument fix)
  the relayed join matches a walked slot = THE CURRENT BLOCKER -> arm 3
                                           (sessionId := recipient's
                                           current joinId; one server value
                                           change, machinery built)
  join_processor enter                   = the lookup must pass first
  join_reserve from 0x14178EA73 (NOT the self-reserve sites) = the join flow
  admit enter from the join-handler caller                    = the flow runs
  resv mask gains the container bit + rec leaves (3,4)        = ADOPTION
  ladder reaches (4,5)                                        = establishment
  receiver vptr non-zero / ent_recv fires                     = the entity road

## THE CURRENT BLOCKER (p2-189's measured facts)

- The gate's walked six slots are bound to SMALL-INDEX sessions {0,-1,1,
  -1,-1,2} — walk_map captured at the relayed join's refusal, identical on
  both machines.
- One of the walked records is NAMED BY THE MACHINE'S OWN JOINID: binder2's
  stack args carry it verbatim on both machines (mac 0x59ED107102C1F335 /
  rig 0x587CDBAF44D4D2AB — each matching its own admit line exactly), and
  cof_soid granted the index (2) for that key. p2-187's census separately
  measured a record whose blob = the machine's joinId (key=joinId vs
  blob=joinId, match=1).
- THEREFORE: retarget arm 3 — the relayed join's sessionId := the
  recipient's current joinId (the fork holds the live value on every
  admitted row; the membership machinery refuses updates that do not echo
  it). Arm 1 (machine id) dead; arm 2 (the real account key) fallback.
- The connect-family handshake (ids 5/6/7/9) is PURE TRANSPORT (a 62-slot
  connection table, 0x41F0 stride, address-matched; channel/sequence
  negotiation only) — no session binding rides it, and OOB id 8 (establish)
  is silently dropped. The binding happens in the two BINDER functions;
  the runtime trigger is inside the VM-obfuscated ring (the correlation
  question for the next capture).
- The session-apply is NOT the landing-session blob's writer (apply_stamp
  fired once, early, into a static config object) — the copier walk is the
  remaining suspect for that open site.
- The mac's parked render-black recurrence: the client stays alive,
  segment 2 reaches region-forced and never fade_release (sharper marker
  than previously recorded); the rig spawned fine on the identical build.
- The game's own refusal is greppable in every future boot:
  "networking:messages:join-request: received message for an unknown session
  ... sending back a refusal" (the session field renders as two reversed
  dword groups — decode before comparing).
- THE NEXT DECODE: the connect-family handlers (OOB ids 5/6/7/9 ->
  0x1417D3010/0x1417D4590/0x1417D27B0/0x1417D1A90) — what binds sessions
  into the receiving connection's context. Arm 2 (the real account key as
  the retarget value) is the fallback fix, not the next move.

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
