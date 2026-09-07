# BOOT BRIEF p2-200 - THE TYPE-20 PUSH DECODES FOR CONTENT, AND THE VIEW ABANDON

STATUS: prepared 2026-09-07 (post 20.326). Front: **allocation-content** (new; streak 0).
Server-only: the built type-20 encoder fix (20.325) rides this deploy; the view
initiator is RETIRED (activity_view_initiate=false, the 20.326 abandon).

## PURPOSE (what this boot learns, win or lose)

The type-20 (allocate_entity_indices) push has been ARRIVAL-proven (p2-198: the
mask filled, entity creation stopped failing) but the body DECODED EMPTY (the
schema walker consumed 15 of 14584 bits). 20.325 fixed the encoder two ways
(two leading 1-bits; per-element five presence bits) and femu-validated the
fixed body BIT-IDENTICAL to the positive control. This boot is the first time
the client receives a type-20 body that decodes FOR CONTENT. Win: any
downstream movement in the entity path (new client lines past the p2-198
baseline). Lose (the pre-named negative): the mask stays exactly as p2-198
left it and NO new downstream line appears - the allocation CONTENT is then
confirmed inert for the peer path, and row 8's receiver-object job-gate
(20.326 R6b) becomes the sole front.

## GRAPHICS DELTA

Zero new rendered models expected. Server-only change; clients stay
be5807eca028ddea on both machines. No client hooks ship (HOOK COUNT 0).

## FALSIFIABLE CLAIM

With entity_index_allocation=true and the 20.325 encoder, every type-20 push
body is 1854 bytes (the femu lane's predicted size) with the two leading 1-bits
and five presence bits per populated element. CONTENT NEGATIVE: the deployed
server (8dd6284736d1aa44, p2-199) sent 1823-byte bodies that the client's
schema walker consumed 15 bits of; this boot's bodies must differ byte-wise and
decode in the femu harness. The client-side effect claim is DELIBERATELY
SEPARATE (below).

## EFFECT CLAIM (distinct from delivery)

DELIVERY: the server emits 1854-byte type-20 pushes (the push path is
unchanged; only the body differs). EFFECT (pre-named, not claimed): the
4096x0x20 table the content feeds changes state for the first time; any
downstream entity-path movement is the win. NO specific new client line is
EXPECTED - a clean null on every downstream observable is a VALID outcome that
closes the "allocation content" question and concentrates the front on row 8.

## ABSENCE NEGATIVE (L13: what ZERO new lines means)

If no downstream line moves vs the p2-198 baseline (mask fill identical,
failures stay stopped, no tag-0x14/0x15 traffic appears): the allocation
content does not drive the peer path - recorded, not a mystery. The
mask-fill-absent case (mgr_free stays 0) would mean the push path itself
regressed - a DIFFERENT failure, named separately.

## CHAIN MARKS (L16)

- encoder fix (two leading 1-bits; five presence bits/element) ........... verified-by-femu (20.325 R3/R4: bit-identical to the positive control)
- the push path (settings-gated append_entity_index_allocation_notification) verified-by-reading (activity_message_push.cpp; the p2-198 boot: 4 pushes, mask filled)
- the view initiator RETIRED (activity_view_initiate=false) ............... verified-by-reading (20.326 R6c: the client drops id 40 at the switch - sending it is dead weight)
- the client's receive pipeline ARMED ..................................... verified-by-dump (20.322 R2: gate global 0x142037AF0 = 1)

## ADVERSARIAL PASS: self (this session) - three ways this boot could mislead me

1. The mask fill is ARRIVAL-driven (20.325 R2) - a boot where the mask fills
   proves nothing about content. The readout must therefore key on DOWNSTREAM
   movement, not on the mask.
2. The view-initiate flip changes the reliable-stream CONTENT of every packet
   after the first publish (one fewer message). Any client-side delta this boot
   could in principle be that removal - but the view was already dropped
   client-side (20.326 R3), so its removal changes nothing the client sees.
   Pre-named: no client-side delta is attributable to the view flip.
3. 1854 vs 1823 bytes: if the push FRAMING (not body) has a size field, a
   stale declared-size could truncate. The p2-198 push path shipped
   declaredSize separately (kParameterUpdateSize pattern); the allocation
   append uses the same mechanism. If pushes go out and decode empty AGAIN,
   the first suspect is the declared-size path, not the encoder.

## PRIOR ART (09-05 FAILURE 5)

- q.sh "allocation content" / sgrep type-20: 20.324 (p2-198, the arrival boot),
  20.325 (the femu fix). Verdict: no boot has ever carried the fixed body;
  this is the first.
- 20.326 R3: the view drop verdict - the reason the view initiator is retired
  rather than iterated. Not relied on for any effect claim.

## DEAD-END AUDIT (required: PRIOR ART cites retracted work)

- Row 7b idx_alloc framing (RETRACTED 20.321): not relied on.
- The type-21 grant (no applier slot, 20.324): stays OFF (entityIndexGrant
  false); not part of this boot.
- The view handshake (20.326: structurally dropped): NOT re-armed; the
  initiator is retired. No token/kind iteration.

## STATE READERS (a direct reader per asserted state)

- "the push went out" -> the server's push lines (the p2-198 pattern).
- "the body is the fixed one" -> push body size 1854 in the server log/the
  upstream dump lane (lane 1's svc8 dump lines if the client echoes).
- "the mask state" -> mgr_fill/mgr_free samples (existing instrument).
- "downstream movement" -> any NEW client line past the p2-198 baseline
  (ent lines, tag-0x14/0x15 traffic, peer-path lines) - boot_verdict +
  logq over the archive.

## FIX SURFACE: server

Server only: the built exe (e50c1a8bf65ffbc4, includes the 20.325 encoder) +
settings (entity_index_allocation=true unchanged; activity_view_initiate
true->false). Client untouched. No SERVER-SIDE GAP section - the wire item
(the content-correct allocation) is what this boot sends.

## WIDE NET (a probe at every decision point on the suspect chain)

All existing instruments (HOOK COUNT 0; no new client hooks ship):

- server TX: the push lines (size + count) - the p2-198 pattern.
- the body: 1854-byte bodies on the wire (the svc8 upstream dump lane, lane 1,
  if the client echoes; otherwise the server-side append log).
- the mask: mgr_fill/mgr_free samples (existing).
- downstream: the client's existing ent/receive lines + boot_verdict's
  both-machine comparison vs the p2-198 archive (the per-arm discriminator).

## ABANDON OUTCOME (pre-named)

entity_index_allocation=false returns the join burst to the pre-20.213 shape.
activity_view_initiate is already false = the 20.326 abandon state
(byte-identical to pre-p2-199 on the view surface).

## NEGATIVE TEST (the arm that fails on the bad state, and where it RAN)

1. THE BODY: ran in the femu lane (RE_output/scratch/femu_type20_body_validation.md,
   2026-09-06/07) - the fixed body decodes BIT-IDENTICAL to the positive control
   (14640/14832 consumed); the OLD body's arms never matched under any leading-bit
   alignment. The failing arm = the old encoder, which FAILS the harness.
2. THE PUSH PATH: ran in boot p2-198 (verified-by-execution: 4 pushes, the mask
   filled, all 48 creation failures stopped) - the path is proven; only the body
   bytes differ.
3. THE VIEW FLIP: activity_view_initiate=false is the p2-199 brief's own
   pre-named abandon (byte-identical to every boot before p2-199); the flip is
   verified-by-reading the settings diff at deploy.

## MODEL REVIEW (required: front history)

Front allocation-content is NEW (streak 0; p2-198's allocation-dispatch closed
hypothesis-survived). THE DEAD ASSUMPTION NAMED: "mask fill = the client
believes its allocation" - p2-198 proved ARRIVAL fills the mask; the CONTENT
was never once validated (it decoded empty in p2-198). This boot tests content
for the first time. The view-registration front (p2-199, streak 1) is CLOSED
by 20.326's static verdict, not by this boot.
