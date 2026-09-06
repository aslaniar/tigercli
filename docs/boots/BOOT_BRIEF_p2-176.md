# BOOT_BRIEF_p2-176 — RUN A: THE 20.53 ROW BISECTION, MINIMAL ROW, PAIRED
STATUS: live (2026-09-04, drafted post-20.297)

Server 3f0496a9ebcf744c (UNCHANGED — settings-only run, no rebuild, no redeploy).
Clients p2-171 a96a6a70f578fc40 BOTH (unchanged; THE CLIENT IS NEVER MODIFIED).

## PURPOSE
Name, or exonerate, the field added since 20.53 that prevents a peer record's
entity from PERSISTING. 20.53 is the project's only positive control: a full row
under a fresh revision made the client render a body. Everything added to the peer
row since is settings-gated. Run A strips the post-20.53 extras and asks whether
the creation loop completes.

WIN OR LOSE, THIS BOOT LEARNS:
  - sticks + clone renders -> the extras contain the breaking field; bisect ON one
    at a time until the churn returns -> THE FIELD IS NAMED.
  - sticks, no clone -> persistence is fixed, the gap is presentation.
  - churns with the row SUSTAINED -> the extras are exonerated as the breaking
    field; the wall is the record's claim state, not the row's content.

## THE CHANGE (server settings only — no rebuild, no client change)
  membership_peer_transport_identity   true  -> FALSE   (post-20.53 extra #1)
  publish_player_profile               true  -> FALSE   (post-20.53 extra #2)
  membership_peer_retry_cap            2     -> 10      (starvation fix, see below)
KEPT DELIBERATELY:
  membership_peer_same_region_advert   true  (the CITIZEN — a 20.53 INGREDIENT, not
                                        an extra; 20.295 R2 named citizen-less-ness
                                        as why the V-2 run rendered nothing)
  membership_sweep=false, membership_sweep_pin=0
      NOTE: the pin is NOT gated on membership_sweep (verified in source,
      activity_membership_push.cpp:360-368 — it is read unconditionally). Index 0 =
      TrailingVariant::packedMasks, which is byte-identical to the default
      initializer, so the live config is uncontaminated. p2-175 logged
      variant=packed_masks, confirming this empirically.
      TRAP: definition.h:117's variant-order comment is STALE (it lists the p2(42)-era
      names). Today pin=4 is all_mask — "The historical reading, and it froze."
  membership_self_peer_row=false, membership_row_character_override (inert: it is
      nested inside `if (craftedSelfPeer)`, verified by reading)
  pool_c4_mark_push=false, world_population=true, reseed=0, row_flags=0

## WHY THE RETRY CAP MOVED (the defect p2-175 hid)
p2-175's peer row was PERMANENTLY WITHDRAWN on all four sessions after 2
unacknowledged bodies. `peerWithdrawn` is never cleared. On the main session
(...107) only 2 of 102 peer-available snapshots preceded withdrawal — 98 came
AFTER, sending no peer row at all. Across all sessions 104 of 128 peer-available
snapshots (81%) sent nothing.
CONSEQUENCE: 20.297 R2's outcome-(c) verdict was measured against a wire carrying
no peer row. It is a STARVED measurement, not a negative result, and is reopened.
Cap 10 (not 0) is bounded: ~10 bodies x 4 sessions ~= 40, well under the 127/146
storm that blocked the Tower load in p2(111), while giving 5x today's exposure.

## INSTRUMENTS: wire_snapshot, membership_peer, peer_advert, member_get, pb_create
## (all EXISTING — p2-171's observers and the deployed server's own lines.
##  NO new literals, NO new hook, NO rebuild. Nothing to verify_hook_rvas.)
## LITERAL TARGETS: none new (existing lines already present in the deployed exe)

## SETUP (my job; user only launches the two games)
  1. reset_lobby_claims.sh (clears the in-memory lobby-claim table + restarts the
     server — REQUIRED, the running server still holds cap=2 from 19:36).
  2. Echo the deployed settings back and assert the three flips landed.
  3. Assert client hashes on both machines: a96a6a70f578fc40.
  4. Launch the server FROM THE REPO ROOT (relative paths — 20.297 R5's lesson).
  5. ssh control socket for rig log pull:
     ssh -M -S ~/.ssh/cm-rig -o ControlPersist=8h -N -f rasla@192.168.1.136
  6. log_archive.sh --label p2-176-runA afterwards; logindex both clients + server.

## THE RUN
Paired Tower, FIRST ENTRY ONLY. No transition rider (p2-175 already spent one, and
a transition is only interpretable once the row is known to be sustained). Both
players reach the Tower and dwell ~5 minutes. No character switches, no orbit.

## GRAPHICS DELTA (THE TEST ITSELF)
Expected new rendered models: 0 or 1. A SECOND GUARDIAN in the Tower on either
machine is the positive. Baseline is one guardian per machine (own player).
Minimization: no client change, no new instrument, one settings-only server delta;
the graphics delta IS the deliverable, so it cannot be minimized further.

## FALSIFIABLE CLAIM
With the two post-20.53 extras OFF and the peer row SUSTAINED (>= 6 peer rows
actually published per session, no `result=withdrawn`), the client's creation loop
COMPLETES a peer-owned record: pb_create stops repeating on the same slot with
identical args, and the already-created check turns true.

CONTENT NEGATIVE (what refutes it): the peer row is delivered sustained AND
pb_create still repeats identical-arg creates on a PEER-OWNED record (owner != the
local machine's member key). That exonerates transport-identity and the profile
block as the breaking field and moves the wall to the record's claim state.

## ABSENCE NEGATIVE (L13 — what zero lines MEAN)
  - zero pb_create enter lines for a PEER-OWNED record: NOT "the extras are
    innocent". It means the record never reached the loop; the wall is upstream
    (claim/admission), pointing back at the 20.219 front.
  - ANY `result=withdrawn` line: THE RUN IS STARVED AND THE RESULT IS VOID.
    This is a first-class ABORT condition, not a footnote — it is exactly what
    invalidated p2-175. Check it FIRST, before reading pb_create.
  - zero `stage=member` lines from member_get: the ownership join is unavailable
    and NO attribution claim may be made from pb_create alone.
  - zero wire_snapshot lines: no membership body was due — a different finding
    from a refused one (the fork's own comment at the emit site).

## READOUT (in this order — the input check GATES the result)
  1. INPUT CHECK: `result=withdrawn` count MUST be 0. Then per session, count
     wire_snapshot peer=1 and confirm they precede no withdrawal.
     NOTE: `peer=1` logs havePeer ("a peer was AVAILABLE"), NOT publishPeer.
     It is not proof a row was sent. This misreading is what cost p2-175.
  2. OWNERSHIP JOIN: member_get `stage=member rec=<addr> owner=<member key>` gives
     the owner; pb_create/memidx_alloc/idx_publish share a stable per-record rcx
     (pb_create rcx=X, memidx_alloc rcx=X+0xC, pb_create r8 == idx_publish rcx).
     The rig's member key is 0x846C8338F7D022E6 (stable since the 20.53 capture);
     anything else on the mac is the mac's own.
  3. VERDICT: does pb_create stick (creates stop) or churn (identical args repeat
     every ~16 ticks) on a PEER-OWNED record.
  4. Visual: second guardian, yes/no, on which machine.

## CHAIN MARKS (L16)
  L1 server publishes a peer row              verified-by-execution (p2-175: 128
       peer-available snapshots, peer_advert result=built)
  L2 the row is SUSTAINED, not withdrawn      unknown (THIS BOOT — cap 2->10 is
       the change under test; p2-175 failed this link and nobody checked)
  L3 client accepts the row, creates a record verified-by-execution (20.295 R0)
  L4 creation loop engages the record         verified-by-execution (20.297 R1)
  L5 the built entity PERSISTS in the pool    unknown (THE WALL — this boot)
  L6 a second guardian renders                unknown (20.53, self-clone only)
  L7 the peer's appearance is theirs, not a   assumed (peer-authored; out of scope)
       clone

## ADVERSARIAL PASS: waived: no adversarial reviewer run this session. RECOMMENDED
before launch given that p2-175's verdict fell to an unchecked input assumption —
the specific thing an adversarial pass catches. The starvation defect this brief
fixes was found by reading the emitter, not by review, so review has not yet been
applied to THIS brief's own assumptions.

## DO NOT
  - do not read pb_create before checking `result=withdrawn` (input gates result)
  - do not read `peer=1` as "a peer row was sent" (it logs havePeer)
  - do not set membership_sweep_pin from definition.h's comment (stale; pin=4 froze
    the client)
  - do not re-enable membership_self_peer_row (displaces real peer rows, 20.295 R3)
  - do not add a transition rider to this run (first entry only)
  - do not modify the client, in any form, for any reason
  - do not launch the server from anywhere but the repo root
