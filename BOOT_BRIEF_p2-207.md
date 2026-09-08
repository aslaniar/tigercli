# BOOT BRIEF p2-207 - THE CRAFTED SELF-PEER ROW: RECREATE THE 20.53 RENDER
# CONDITION ON TODAY'S FORK (membership_self_peer_row=true)

STATUS: prepared 2026-09-07 (post p2-206; the 20.53 record re-read). Server-
only SETTINGS change - NO rebuild: the crafted-row path is in the deployed
binary (activity_membership_push.cpp C3 path). The character override was
already staged (membership_row_character_override=0x9EAA300100100101 = the
mac's own character); the master switch was off. Clients unchanged
(be5807eca028ddea both). HOOK COUNT 0.

front: self-peer-row

## WHY THIS BOOT (the milestone's surviving proof, re-run on today's fork)

FINDINGS 20.53's RETRACTION preserved one verified fact: **"the client WILL
render a body from a membership row"** - the p2(42) run (server
d5d9c823fe4163e1): a SECOND GUARDIAN rendered in the tower, a clone of the
local player named "You", with ZERO peer connection (15 steamnet lines, all
sign-in scaffolding; no send_rendezvous). The retraction was about the row's
IDENTITY (it was the local player via a sibling-session bug, not a peer) -
and the client's behavior when handed a full fresh row was real: the roster
creates the slot, the row fills it. The C3 knob (membershipSelfPeerRow) now
recreates that exact condition DELIBERATELY on today's fork: a full row naming
the local player, same_client/same_account refusals bypassed by construction.
The p2(42) confound is already neutralized: the p2(42) table (full row + fresh
revision = render; anything less = nothing) - today's fork publishes the full
row with a fresh revision on the sweep-off path by default.

## PURPOSE (what this boot learns, win or lose)

Win: the clone renders (a second guardian, the mac's character, named "You")
- the 20.53 surviving fact reproduced on today's build, with the render path
attributed in the census (creation-loop counters vs the roster-slot/image
machinery). Lose (pre-named): no clone - the C3 row is not sufficient for
the body-builder on today's fork (the row content/shape or the character
override is ignored), and the milestone's next probe is the trailing-field
re-run (the 20.53 retraction's voided verdicts) or the genuine-peer row.

## GRAPHICS DELTA

ONE extra rendered guardin (clone, expected stationary) if the arm hits.
Server-only settings flip. No hooks.

## FALSIFIABLE CLAIM

1. The membership push carries a full row naming the LOCAL identity in member
   slot 1 with a fresh revision (the C3 path; the override names character
   0x9EAA300100100101).
2. The client renders a body for that row: the user sees a second guardian
   (the mac's character) in the tower; the client census shows the creation
   machinery firing for a SECOND entity (pb_create/ent_make/idx_alloc counts
   up past the p2-206 baseline; the boot-end dump's mgr/pool census).
3. CONTENT NEGATIVE: full fresh row published + NO clone = the row shape or
   the character-override field is not sufficient for the body-builder on
   today's fork (pre-named; the next probe is the trailing-field re-run).

## EFFECT CLAIM (distinct from delivery)

DELIVERY: the crafted row rides the proven membership keepalive path.
EFFECT (pre-named, not claimed): the row renders a clone. The clone, if it
renders, is expected STATIONARY (20.53's correct split: "the ROSTER creates
the slot; the PEER LINK supplies who occupies it. Appearance, position and
animation are still peer-authored"). Row 8 (the ent receive blocks) is NOT
in this boot's contract unless the dump surprises.

## ABSENCE NEGATIVE (L13)

Full row + fresh revision + no clone: the body-builder's gate is beyond the
row content we control (or the override field is ignored - the C3 doc's own
unknown: "what the client's body-builder does with a row whose CHARACTER
field is overridden" is precisely the boot's question). The milestone then
re-runs the voided trailing-field probes (20.53 retraction) against a REAL
foreign row - which the self-row test does not enable. No boot is spent
re-iterating self row shapes without a new static discovery.

## CHAIN MARKS (L16)

- the row value (local identity + override) ........ in-tree (activity_membership_push.cpp C3 path; settings-gated)
- the render precondition (full row + fresh rev) ... verified-by-log (the p2(42) table: full+fresh = render; today's sweep-off path = full+fresh)
- the 20.53 render fact ............................. verified-by-execution (p2(42): clone rendered, zero peer link; capture archived)
- the identity of the row (self, deliberate) ........ the boot's subject - the same_client guard bypassed BY DESIGN (the C3 doc)

## ADVERSARIAL PASS: self - four ways this boot could mislead me

1. THE SOLO-CONTROL RULE (20.53's method note - "a single-client boot is
   now the cheapest falsifier available for anything peer-shaped, and it
   should be run FIRST"): the clone's attribution is cleanest SOLO (no rig
   noise). PRIMARY ARM: mac solo. If co-presence is preferred anyway
   (variant-B-era black is gone since p2-206), the clone must be
   distinguished from any rig-side render - the census (creation counters)
   discriminates.
2. THE OVERRIDE MAY BE IGNORED: the C3 doc's own open question is whether
   the body-builder honors the character field override. The readout: the
   clone (if any) either names the mac's character or the row's default -
   both are a render; the override question is secondary to "does a body
   exist".
3. THE RENDER MAY BE PER-MACHINE: 20.53 rendered on the mac only (the rig
   blacked). Today's fork has the rig landing cleanly - both machines may
   render clones (each from its own crafted row - each client receives ITS
   own self row). Either is a win.
4. CREATION-LOOP CONFOUND: the self row names the LOCAL identity - the
   creation loop's gate2 (member[+0x818] == local identity) PASSES for this
   row - so the clone may be created by the LOCAL creation machinery (a real
   mechanism now fully explained, NOT a bug - this is the p2(42) fact).
   The census must not attribute it to the receive blocks (row 8 stays
   closed unless the dump says otherwise).

## PRIOR ART (09-05 FAILURE 5 - q.sh each central term)

- q.sh "self peer | crafted row | C3": the C3 knob doc + 20.294 R5 + p2(42)/
  20.53 (the render fact + the retraction) + p2(45) (the same_client fix
  this test bypasses BY DESIGN) - re-read this session, the brief above.
- q.sh "membership row | roster slot": 20.44 (slot 1 = peer identity), the
  20.51/20.38 split (roster creates, peer link occupies).
- q.sh "receiving": the ent cluster contract (20.302-304) - NOT in this
  boot's contract.

## DEAD-END AUDIT

- The peer-arrival black (variant B): absent since p2-206 (the setup flags)
  - the co-presence arm is no longer risky.
- The receive-block construction: 5 artifacts, one constant (20.330-20.333)
  - NOT the subject; the clone's render path is the roster/creation side.
- The p2(42) confound (trailing pair sweep): the sweep is OFF and stays OFF
  (it would re-introduce the confound mid-boot).

## STATE READERS (a direct reader per asserted state)

- "the crafted row went out" -> the membership push lines (the C3 path is
  in the deployed binary; the body carries the local identity in slot 1).
- "the client created a second body" -> pb_create/ent_make/idx_alloc census
  counters UP past the p2-206 baseline (client census diff).
- "the render happened" -> THE USER'S EYES (a second guardian, the mac's
  character, named "You") - the milestone's primary reader.
- "row 8 moved" -> the boot-end dump (transition_readout: ent slot-10
  instances) - expected unchanged.

## WIDE NET (probes at every decision point)

All existing instruments (HOOK COUNT 0): the membership push lines, the
client census diff vs p2-206, the ent/mgr/pool instruments, the boot-end
dump (transition_readout) if taken.

## FIX SURFACE: server (settings only)

membership_self_peer_row=false -> true (backup .bak_p2-207_pre_selfpeer).
The C3 path + the already-staged character override were in the deployed
binary. NO SERVER-SIDE GAP: this boot publishes the row the milestone's
surviving proof depends on; THE CLIENT IS NEVER MODIFIED.

## ABANDON OUTCOME (pre-named)

membership_self_peer_row=false: the membership bodies return to the p2-206
byte shape (the same_client guard re-engaged, byte-identical - the off path
is untouched by design). No rebuild.

## NEGATIVE TEST (the arm that fails on the bad state, and where it RAN)

1. THE RENDER PRECONDITION (full row + fresh revision): ran in the p2(42)
   archive - full+fresh rendered; the p2(38) stale-revision and p2(41)
   minimal-row arms FAILED (nothing rendered) - the recorded table.
2. THE C3 PATH (bypass + override): ran nowhere before - first run of the
   master switch (the override was already staged); the boot's own negative
   is pre-named (no clone = row shape/override insufficient).
3. THE READOUTS: transition_readout proven on four artifacts; the census
   baseline (p2-206's counters) is the diff reference.

## MODEL REVIEW (required: the milestone framing)

The 20.53 retraction is the history this boot leans on: the milestone was
called wrong because the row named SELF - and its surviving fact ("the
client will render a body from a membership row") is exactly what the C3
knob now recreates ON PURPOSE, on today's binary, with the mechanism of the
p2(42) render now EXPLAINABLE (the self row passes the creation loop's
gate2 - 20.260's self-only check - so the clone is machined, not magic).
THE DEAD ASSUMPTION NAMED: "the clone render was a bug to avoid" - WRONG;
it is the milestone's positive control, deliberately re-armed. If the clone
renders, the next milestone question is the GENUINE-PEER row (the same
path with a foreign identity, which gate2 currently refuses - the gate2
question becomes the front). If it does not, the row shape/override
question absorbs the voided trailing-field probes.