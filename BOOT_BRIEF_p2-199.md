# BOOT BRIEF p2-199 - THE VIEW HANDSHAKE, INITIATED: the fork speaks first

STATUS: prepared 2026-09-07 (post p2-198). Front: view-registration (row 6c).
Server-only change (the view initiator + the probe bookkeeping fix) + settings.

## PURPOSE (what this boot learns, win or lose)

Whether a client that RECEIVES a host view establishment (id 40, sent by the
fork at its first publish) ANSWERS with its own view - the fork's dormant
bind_view fires for the first time in project history - and whether the
handshake opens the client's external-body registration (stage=tail lines) and
ultimately the entity consume path (row 7). Win: the handshake completes, the
client's answer reveals its view's content, and the registration opens. Lose:
the client ignores/refuses our view - and the answer/no-answer split (its own
reply vs silence) names which requirement we missed.

## GRAPHICS DELTA

Zero new rendered models expected. No client change.

## FALSIFIABLE CLAIM

With activity_view_initiate=true, the fork sends one view establishment per
admitted peer at its first published snapshot: a 69-bit body
(`07 65 1d 3c f4 9f f9 1d c8` for session token 0xECA3A79E93FF23B9; kind=0,
optional absent, no list, token = the group session id) as reliable message
id 40. The client's own decoder/validator (0x1416DD920, femu-validated THIS
session: returned rax=1, consumed 69, errflag 0, decoded kind=0/optional=-1/
hasList=0/token intact) ACCEPTS this body. The client then answers with its
own view establishment upstream, which the fork's bind_view binds and echoes
(stage=view result=bound fires for the first time ever). CONTENT NEGATIVE:
with the gate off (every boot before this), no id-40 exists in either
direction - the all-archive census (zero stage=view lines anywhere) is the
negative arm.

## ABSENCE NEGATIVE (L13: what ZERO instrument lines means)

If the fork logs stage=view result=initiated (sent) and the client NEVER
answers (no stage=view result=bound): the client's apply declined our view
despite the decoder accepting it - the decode passed but the apply's own
checks (the token comparison? the kind semantics? a session-state requirement?)
failed. The next decode is then the client's group-dispatch apply site (the
decoder's caller context), NOT the format. If result=initiate-fail: the fork's
own send refused (the queue) - a fork-side bug, pre-named. If neither line
appears at all: the publish never released (the may_publish gate) - read
stage=publish result=held lines.

## CHAIN MARKS (L16)

- fork initiator built: publish_snapshot's queued path, gated, once per record . verified-by-reading (this session; group_host.cpp)
- the body: 69 bits, kind 0, optional absent, no list, token=group session ..... verified-by-execution (standalone encode: 07 65 1d 3c f4 9f f9 1d c8)
- the client's decoder/validator ACCEPTS it .................................... verified-by-femu (this session: rax=1, consumed 69, errflag 0, fields decoded intact)
- the client's validator rules (kind<=5, optional>-2, list<=16, clean end) ..... verified-by-reading (0x1416DD920 whole; the clean-end check 0x14034E9B0 = over-read/errflag only)
- the fork's answer half: bind_view binds + echoes ............................. verified-by-reading (group_host.cpp:601; never once executed)
- the transport: send_reliable -> peer::enqueue_reliable (the echo's own path) . verified-by-reading (the echo uses the identical call)
- the client's upstream answer arrives as an established-packet queue record ... verified-by-reading (the group registry framing; the fork drains it today for ids 4-39)

## ADVERSARIAL PASS: self (this session) - three ways this boot could mislead me

1. The client might answer the handshake but the REGISTRATION still not open -
   the view and the external handler may be two separate switches. The readout
   separates them: stage=view result=bound (the handshake) vs stage=tail
   (the registration) are independent lines.
2. The client's answer might arrive at bind_view with a MISMATCHED token/kind
   (its view names a different session) - bind_view binds and echoes anyway;
   the compatible() check exists but nothing enforces it on the fork's path.
   A bound-but-incompatible view would log bound WITHOUT opening anything -
   the log carries kind/token, so the mismatch is visible.
3. Our view could arrive BEFORE the client's session state is ready (the
   publish release boundary is the client's own application-ready marker, but
   the client's view state may init later) - if the answer never comes but a
   LATER retry would work, the once-per-record flag hides it. Pre-named: if
   result=bound never fires this boot, one re-send-on-timer variant is the
   follow-up, not a conclusion.

## PRIOR ART (09-05 FAILURE 5)

- sgrep "view" in the claims corpus: the fork's bind_view/echo (group_host),
  view_message.{h,cpp} (the grammar, built from the client's registry), and
  the client strings ("failed to create view for '%s'" - the view-create
  failure path exists in the client). Verdict: the format is known, the
  handshake has never run, the initiator is the missing half - this boot.
- sgrep kViewMessageId: id 40, declared 40 bytes; the live registry block read
  from dump_p2146 (present=1, name 'view-establishment', max=40, handlers
  0x1416DEE90 encode / 0x1416DD920 decode). Verdict: consistent.
- q.sh verdicts: hex-term false-null known; sgrep used.

## DEAD-END AUDIT (required: PRIOR ART cites retracted work)

- The idx_alloc/row-7b framing (RETRACTED 20.321): not relied on.
- The type-21 grant (no applier slot, 20.324): stays off; not part of this boot.
- The p2-197 external-body probe: not reopened - it stays on (proven harmless)
  and is the DOWNSTREAM consumer this boot's registration would activate.

## STATE READERS (a direct reader per asserted state)

- "our view left" -> stage=view result=initiated (new line, once per peer).
- "the client answered" -> stage=view result=bound (bind_view's existing line,
  firing for the first time; it carries the client's kind/token/list).
- "the registration opened" -> stage=tail result=external-bits lines (the
  client's own external bodies) + the external probe finally acking.
- "the entity consume path opened" -> the client's "receiving sobject creation"
  line (the p2-197 instrument set) / ent_recv deltas.

## EFFECT CLAIM (distinct from delivery)

DELIVERY: our view is sent, the client's decoder accepts it (femu-proven), and
the client's answer lands. EFFECT (pre-named, not claimed): the view binds both
sides, the external handler registers, and the entity body is consumed - any
prefix of that chain is progress and names the next lane.

## ABANDON OUTCOME (pre-named)

activity_view_initiate=false: the fork returns to answer-only (byte-identical
to every prior boot; the initiator line disappears). The dump gate and the
external probe are independently revertible.

## WIDE NET (a probe at every decision point on the suspect chain)

- fork TX: stage=view result=initiated / initiate-fail (new).
- fork RX: stage=view result=bound (the answer; carries the client's fields) +
  the reliable-queue delivered-id census (a NEW id, e.g. 40 upstream, is the
  answer's arrival signature even if bind_view's staging fails).
- the registration: stage=tail lines (the client's own external bodies).
- the entity consume: the client's receive lines / ent deltas (existing).

## FIX SURFACE: server

Server only: group_host.cpp (the initiator + the Admitted flag),
peer_transport.cpp (the bookkeeping fix), gameplay settings (the gate).
Client untouched (be5807eca028ddea). No SERVER-SIDE GAP section - the missing
wire item (the host's view) is what this boot sends.

## NEGATIVE TEST (the arm that fails on the bad state, and where it RAN)

1. THE VIEW BODY against the client's own decoder: femu (this session,
   RE_output scratch femu_view_decode run) - the ACCEPT arm returned rax=1
   with consumed=69/errflag=0 and every field decoded intact; the REJECT arm
   (rc=1 on any violated rule) is the validator's own code at 0x1416DD9B1
   (kind>5 / optional<=-2 / list>16 / dirty reader each set al=0 - read
   directly, not assumed).
2. THE ENCODER round trip: the fork's write_view output fed through the
   standalone harness (whole-bytes=9, exact-bits=69, the byte dump cited in
   FALSIFIABLE CLAIM) - ran this session.
3. THE PROBE BOOKKEEPING fix: the sequence is stamped once (verified-by-
   reading the diff; the p2-197 gaveup-before-ack race is the failure it
   removes).

## MODEL REVIEW (required: trailing third-branch streak on this front)

Front `view-registration` is NEW (streak 0; p2-198's allocation-dispatch closed
hypothesis-survived). THE DEAD ASSUMPTION NAMED: "the client will speak first"
- five hundred boots of answer-only evidence say it will not; the initiator
half has never existed until this boot. Second assumption: "the token is the
group session id" - the decoder does not validate it; the APPLY might. If the
answer never comes, the token identity is the first suspect, and the client's
apply decode is the next lane.
