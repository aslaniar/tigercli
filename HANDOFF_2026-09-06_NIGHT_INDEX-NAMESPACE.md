# HANDOFF 2026-09-06 (NIGHT) — ROWS 1-7 FALL, AND THE FRONT MOVES TO THE INDEX NAMESPACE

STATUS: live (2026-09-06, end of the Claude Code session). Written for the
opencode session taking over. Read STATE.md's header first, then this.
Companions: FRONT_peer-render-chain.md (the pinned chart, current);
RE_output/claims/connection-layer-join-delivery.md §11-14 (the row-5 closure);
RE_output/claims/entity-index-allocation-schema.md (last section = the CLAIM O
refutation); RE_output/claims/establishment-decode.md (thread 2).

## THE ONE-PARAGRAPH STATE OF THE WORLD

Row 5 is CLOSED (the connection-layer join gate is host-only; the receiving
client is a peer and can never pass it — and it never mattered, because the
membership plane had already delivered the peer). Row 7 is PASSING (the peer's
connection ladder reaches 5 and holds; the "(3,4) stall" was a dead sampler's
last reading). Row 6 is NOT A DEPENDENCY (the participant mask has 7 accesses in
the whole binary and none is in the entity cluster). What actually blocks the
project is one rung lower than any of those: **idx_alloc 0x141711D10 returns -1,
23+ times a boot, and the local entity-index mask comes up empty.** No entity can
exist without an index, so ent_recv has read calls=0 in 97 of 97 archives.

## WHAT CHANGED TODAY (five things, ranked by how much they change the map)

1. **ROW 5 CLOSED, ON ITS OWN QUESTION.** The join gate's 6..9 window is the HOST
   half of the session ladder (state 6 = 'host-established', 4 =
   'peer-established' — the client prints these names itself). A type-0x0A join
   is a host-only message; the receiving client is a peer. No key, channel,
   container or retarget value could ever have passed. The p2-181..p2-195 relay
   road (~14 boots) is closed. Claims §11-14.
2. **ROW 7 IS PASSING, AND ITS WALL WAS AN INSTRUMENT ARTIFACT.** p2-196: the
   rig's connection went ladder 4 → 5 and held 90+ seconds. The (3,4) stall
   carried since p2-164 and "reproduced" in p2-180/p2-195 was resv_rec's last
   sample from a probe whose host function had stopped being called (resv ran 10
   times all boot, last 93 seconds before the log ended).
3. **20.277 R2 CONFIRMED, MY COUNTER-HYPOTHESIS REFUTED.** disown rec=1 bit=5
   before=0x0020 after=0x0000 **wasset=1** — the peer's participant bit IS set
   and IS cleared. resv_rec's mask=0x0000 is the aftermath, not the origin.
4. **TWO OF MY OWN CLAIMS, DISPROVED BY ME, LATER THE SAME SESSION.** "The fork
   has no entity encoder" — wrong, I grepped the wrong names; it has
   activity_entity_slots_encoder, activity_entity_index_allocation_encoder,
   activity_entity_index_grant_encoder, entity_baseline. "Nothing has ever been
   sent" — wrong; 20.218 (p2-143) verified "OUR MESSAGES ROUTE (flags=0x00),
   ASSIGNMENT+ORDERING ALL CONFIRMED WORKING". If you read the middle of this
   session's commits without reading the end, you will inherit both errors.
5. **CLAIM O IS PROBABLY WRONG — DO NOT BUILD ON IT.** See below.

## THE TRAP TO NOT WALK INTO (this is the most valuable paragraph here)

entity-index-allocation-schema.md CLAIM O says the client's entity-index request
rides BAP svc21 and the fork answers it EMPTY, and it calls the request shape
"still unread". The shape has been captured in ~130 archived server logs,
including tonight's, and it decodes to:

    0x12 -> protobuf field 2, wiretype 2 ; 0x3a -> 58 bytes ; packed repeated
    varints: 1090090..1090096, 1090150..1090152, 1090170..1090171,
    1090200..1090202, ... — sorted runs with gaps, all in a 1.09-million band.

Entity indices are SMALL INTEGERS, live set 0..6 (20.302). This is a catalogue
query — which is precisely what the fork's own routing already calls it
(RequestService::purchasedOffers) — and an EMPTY svc22 reply is a CORRECT answer
to it. CLAIM O's "exactly once per join" is contradicted as well (p2-196: three
occurrences; 20260906_155138: eleven).

The obvious next step CLAIM O implies — build an entity-index grant body and
answer svc21 with it — would be answering a question nobody asked. **And the
scaffolding to do it already exists in the fork** (BodyCodec::
entityIndexGrantResponse, settings entity_index_grant / entity_index_grant_flat,
currently false / true). That is exactly what makes this mistake cheap to make
and expensive to discover. Do not make it.

## THE NEXT MOVE

**Build the allocator probe.** It is specified verbatim in
entity-index-allocation-schema.md and has never been built, and
bootstrap_check.sh has printed the unbuilt-instrument warning at the top of
EVERY session since it was written (empty-mask #8):

    "a client-side probe on the allocator 0x141711D10 / the case-21 consumer
     0x14170CFB0 reading the +0xC118 popcount at call time."

Why this one and not another front: **its subject is a call that actually happens
and actually fails.** idx_alloc runs and returns -1 twenty-three-plus times every
boot. Every front of the last ~50 boots has instead been reading an ABSENCE
(ent_recv=0, receiver=0, mask empty, ladder "stuck"), and absence cannot separate
"the world is blocked" from "my instrument is blind or dead" — which is why three
walls in a row dissolved into instrument artifacts (the blind guard; st2=6; the
(3,4) stall). A live failing call is a categorically better subject.

Second, free, static: re-identify the REAL index request — find the message whose
body carries small integers in the 0..6 namespace, or establish that the client
never asks and the pool is meant to be filled by a push.

## THE INSTRUMENT PATTERN THAT WORKED TODAY (reuse it)

The join-window arm: `thread_local unsigned t_joinWindow`, incremented on the
gate's own enter and decremented on its leave, with every expensive probe
returning immediately when it is zero. It made the walk-return probe CHEAPER than
the build that lands, and it made attribution structural rather than inferential
— a line can only be emitted inside the gate's own call, on the same thread. It
also fixed the R8 regression that had broken the mac's landing for two boots.
Four probes shipped this way in p2-196 (disown / pump_lad / evt_sub / rung_adv);
all four fired, and pump_lad cost 1133 calls for 78 lines.

## GATE NOTES FOR WHOEVER SHIPS NEXT

- probe_audit.py (the workflow session's, uncommitted at handoff time) is now the
  deploy gate and it WORKS — it caught a missing zero-guard in my own new probe.
  Its arm B reads STRIPPED source, so only a real guard or per-operand transform
  satisfies it; a `collision:` comment cannot (the docstring overpromises).
- hook_targets caught a real 09-05 FAILURE 2: four rows added without bumping
  kTargetsSize would have detoured RVA 0. Bump kTargetsSize with any row change.
- verify_hook_rvas.py had a dead store that made it the only one of the three
  tools unable to honor a DUAL-OK waiver; fixed (one deleted line).
- q.sh returns EMPTY for hex terms (1AEF8, 1D18) while /usr/bin/grep finds ten
  hits. It has now cost this project twice in one day. Treat q.sh silence on a
  hex term as a tool fact, never a world fact, until that Tier-2 row is fixed.

## A RULE THIS SESSION EARNED (conversion candidate for ENFORCEMENT.md)

**An "unchanged" or "stalled" claim requires a LIVE sampler.** The (3,4) stall
was believed for ~30 boots because resv_rec's last sample was read as a steady
state; the sampler had stopped running 93 seconds before the log ended. Mechanism:
any brief asserting a stalled/unchanged state must cite the sampler's
END-OF-BOOT call count, not just the value. That single check would have killed
the (3,4) stall before p2-180, p2-195 and p2-196 each re-confirmed a ghost.

## DEPLOYED AT HANDOFF

  client  be5807eca028ddea on BOTH machines (68 install rows, preflight PASS)
  server  acbb62af4a3ca133 (relay settings unchanged and now irrelevant:
          relay_join_engine_channel=true, relay_join_target_identity=false)
  boots   p2-195 (hypothesis-survived), p2-196 (hypothesis-wrong) — both banked
          in RE_output/map/boot_outcomes.jsonl; decisions D-040/D-042 closed.
  logs    RE_output/logs/20260906_162912_p2-195, .../20260906_172618_p2-196
