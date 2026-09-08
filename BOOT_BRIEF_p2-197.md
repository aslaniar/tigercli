# BOOT BRIEF p2-197 - THE EXTERNAL BODY: the first entity packet the fork has ever sent

STATUS: prepared 2026-09-06 evening (post 20.321). Front: peer-entity-send (row 9,
the corrected front). Server-only change; no client modification.

## PURPOSE (what this boot learns, win or lose)

Whether the client's armed receive pipeline dispatches a server-sent external body
to the ent cluster. The fork's established packets gain an external body (the
four-channel wrapper, one channel-2 record: playerBroadcast CREATE, token slot 7,
baseline = the dump's descriptor-0 bytes) behind the `gameplay_external_body`
setting. WIN: the client's own log prints the receive and the entity enters the
manager - the peer-render road opens. LOSE: the client's RX view gate is closed or
the tail grammar disagrees - the RX tail diagnostic names which.

## GRAPHICS DELTA

Zero new rendered models expected by design. If the entity applies, a peer guardian
MAY appear - that is the goal, not a delta to minimize. No client build changes; the
client's rendered content is untouched by this boot's binary delta (server only).

## FALSIFIABLE CLAIM

With `gameplay_external_body=true`, the fork's next established packet to each
connected, applicationReady peer carries, after its two reliable queues: an
external-present bit =1, then a 105-bit four-channel wrapper
(`10 03 81 00 05 fb 0f 2e a0 42 1e 04 42 00`), then a filler-absent bit =0, then
zero padding. The wrapper's channel-2 record is a strict CREATE: token {slot 7,
incarnation 0}, type 2 (playerBroadcast), five-envelope flags [1,0,0,0,0],
lifecycle 0, baseline 8 bytes `fd 87 97 50 21 0f 02 21` (the paired-tower dump's
descriptor-0 kind-2 payload). CONTENT NEGATIVE: the same packet with the
`gameplay_external_body` gate off carries the two zero tail bits - byte-identical
to every packet the fork has ever sent (verified in the p2-196 archives: 2,277
stage=packet lines, all absent-form).

## ABSENCE NEGATIVE (L13: what ZERO instrument lines means)

If the fork logs `stage=external result=sent` (>=1) and the client shows NO
reaction (no "receiving sobject creation" line, no entity-create funnel line),
that means: the client's RX view gate is closed on this connection, or the client's
tail grammar reads different bits than our writer emits (the [ext-present] position),
or the receive tick's gate function (0x1416FC600: global byte 0x142037AF0 + session
context) refuses at the session level. The fork's RX tail diagnostic
(`stage=tail result=external-bits`) separates the first case from the others: if the
CLIENT's own upstream tails are large (>9 bits), its view gate is OPEN and a silent
RX means a grammar mismatch downstream of the gate. No fork-side `result=sent` at
all means the probe never armed - the service() conditions (connected +
applicationReady + gate on) never all held: read `stage=svc result=skip` lines.

## CHAIN MARKS (L16)

- fork arm: service() arms externalPending per applicationReady link .......... verified-by-reading (this session; peer_transport.cpp)
- fork encode: write_external_entity_frame 105-bit body ....................... verified-by-execution (standalone self-test PASS; round-trip byte-identical)
- fork tail: [ext=1][body][filler=0][padding] ................................. verified-by-execution (packet-level round trip: decode_established finds extOffset=94, body re-decodes byte-identical)
- transport: send_acknowledgement rides send_transport (dtls || association) ... verified-by-reading (existing path, unchanged)
- client receive tick armed: global byte 0x142037AF0 = 1 ...................... verified-by-execution (dump_p2146 read: byte = 0x01)
- client ent path: ent_recv -> ent_header -> ent_create ....................... verified-by-reading (callers.py single-caller chain; contract doc)
- client accepts fresh id: ent_create applies slot 7 without lease/descriptor . verified-by-femu (femu_ent_create_freshid: 5 arms, id=7 byte-identical to id=0/2)

## ADVERSARIAL PASS: self (this session) - three ways this boot could mislead me

1. The fork could log `result=sent` while the packet never left (send_transport
   fails silently) - countered: the acked readout is the delivery proof; an unacked
   probe gives up after 4 attempts and logs gaveup.
2. The client could consume the tail as FILLER (its view gate open but grammar
   reading a filler length from our first 14 bits) - the packet would drop, the
   peer's acks stop, the client rebuilds the link: VISIBLE as a reconnect storm,
   not silent. Pre-named as the grammar-mismatch signature.
3. The client could accept the entity and STILL not render (the id needs the
   second-stage registration the femu boundary named) - the readout is the receive
   line first; render is a later boot's claim. Not conflated here.

## PRIOR ART (09-05 FAILURE 5)

- sgrep 141718510 (ent_recv): the carrier census (carrier-type-table.md) - the four
  slot-10 handlers are vtable-fed; the activity router EXCLUDES types as the carrier.
  Verdict: the established packet's external body is the remaining carrier; this boot
  tests it.
- sgrep "external" in the fork: external_entity_codec (complete, unwired),
  external_shadow (receive-only, unwired), established_packet tail (absent form
  only). Verdict: the send half was scaffolded and never wired - this boot wires it.
- sgrep 0x142037AF0: six refs, all readers in the network-extract/receive cluster;
  NO readable writer (VMP-set). Verdict: activation-side enable, out of scope.
- q.sh verdicts: q.sh returns false-null on hex terms (night handoff, twice-burned);
  sgrep.sh used throughout this front.

## DEAD-END AUDIT (required: PRIOR ART cites retracted work)

- The join relay road (p2-181..p2-195, CLOSED): this boot does not touch the join
  path; relay settings stay as-is and irrelevant.
- idx_alloc / row 7b (RETRACTED 20.321): this boot does not depend on the +0xC118
  pool; slot 7's lease-bit is proven unnecessary by femu (the validation is soft).
- CLAIM O / svc21 grant (REFUTED): no grant body is sent; svc21's catalogue reply
  is untouched.

## STATE READERS (a direct reader per asserted state)

- "the body left the fork" -> the fork's own log: `stage=external result=sent`
  (Level::info, per attempt) and `stage=external result=acked` (the peer's ack).
- "the client's view gate state" -> the fork's RX diagnostic: `stage=tail
  result=external-bits bits=%zu` on every client packet (large tails = open).
- "the client consumed the entity" -> the CLIENT's own log: the retail funnel line
  "receiving sobject creation" (key 0x141CA0EB0; the retail_log_enqueue_observer
  path captures game log lines into the client sunrise.log).
- "the probe armed at all" -> `stage=external_selftest result=pass` (once) +
  `stage=svc result=skip` lines when it did not.

## EFFECT CLAIM (distinct from delivery)

DELIVERY (this boot's claim): the body reaches the client's receive path and the
ent dispatch consumes it. EFFECT (pre-named, NOT claimed here): the peer entity
becomes addressable in the manager (the second-stage registration), and a peer
guardian renders. If delivery succeeds and the effect does not follow, the next
front is the second stage (0x14170F390/0x14171D4A0) - named, not chased here.

## ABANDON OUTCOME (pre-named)

Set `gameplay_external_body=false` in settings.json and relaunch: the fork's
packets return byte-identical to every pre-probe packet (the gate defaults off;
zero code path runs). The RX tail diagnostic stays live and harmless. The front
then waits on whichever the readout indicted (view gate / grammar / tick gate).

## WIDE NET (a probe at every decision point on the suspect chain)

- fork TX: result=sent / result=acked / result=gaveup / result=buildfail (all four
  terminal states of the probe).
- fork RX: stage=tail on every client packet (the client's own tail size).
- client: its own receive log lines (retail funnel) - no client hooks are added or
  changed this boot; the deployed client build stays be5807eca028ddea.
- the connection link: existing stage=packet / stage=svc / stage=keepalive lines
  unchanged, so a reconnect storm (grammar mismatch) is visible against baseline.

## FIX SURFACE: server

Server only: peer_transport.cpp (arm/attach/ack), external_send.{h,cpp} (new),
established_packet.{h,cpp} (tail writer + RX diagnostic field), state/gameplay/
definition.h (probe state fields), activation settings comment. No client change;
no SERVER-SIDE GAP section needed (this boot IS the server-side gap being filled:
the external body the server never sent).

## NEGATIVE TEST (the arm that fails on the bad state, and where it RAN)

RAN THIS SESSION, standalone (clang++ against the module + its middleware deps):
1. The codec's preflight REJECTS a remove record carrying a baseline (the malformed
   arm) - verified: encode_frame returns false.
2. The self-test caught a REAL bug pre-deploy: finish() returns whole BYTES and the
   first version stored it as bitCount - the tail writer would have truncated the
   105-bit body to its first 14 bits. Fixed (bitCount = writer.bit_count()); the
   self-test then PASSes and the packet-level round trip pins the tail bit order.
3. Packet round trip: write head+ack+queue+external-tail -> decode_established
   (expectExternal=true) -> extOffset/hasExternal correct, the 105 body bits
   re-decode byte-identical, filler-absent=0. (fixtures under the session's temp;
   the standing tests live in external_send.cpp self_test, run once at the first
   send and logged as stage=external_selftest).

## MODEL REVIEW (required: trailing third-branch streak on this front)

Front `peer-entity-send` is NEW (streak 0; the ledger's recent fronts were
session-lookup-identity (closed by 20.321's retraction of its premise) and
connected-rung (p2-196)). No third-branch debt applies. THE DEAD ASSUMPTION THIS
BOOT MUST NOT INHERIT (the review the retraction demands): "no index -> no entity"
- the row-7b chain retracted today. This boot's send carries a fresh id WITHOUT a
lease bit or descriptor, justified by the femu ent_create arms, not by the retracted
pool claim. Second assumption named: the client's RX view gate opens at activity
join - UNPROVEN; the RX tail diagnostic reads it directly this boot instead of
assuming it.
