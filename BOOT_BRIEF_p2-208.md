# BOOT BRIEF p2-208 - THE TRAILING-PAIR SWEEP AGAINST A GENUINELY FOREIGN ROW:
# THE RE-RUN 20.53 PRESCRIBED AND NO ONE EVER EXECUTED
# (membership_self_peer_row=false, membership_sweep=true)

STATUS: prepared 2026-09-07 (post p2-207: the crafted self row is null on
today's build, and 20.53's own follow-up - "sweep OFF, full row, fresh" -
has now been RUN and answered: the full row alone does NOT render). This
boot is the OTHER half of p2(42)'s confound, under the condition 20.53's
retraction demanded ("the whole trailing sweep must be re-run once the peer
is genuinely foreign") and no boot has ever met: a GENUINELY FOREIGN row in
the roster WITH the trailing 32-bit pair cycling. Server-only SETTINGS
change - NO rebuild (the sweep machinery is in the deployed binary:
activity_membership_push.cpp sweep_slot/sweep_decide). Clients unchanged
(be5807eca028ddea both). HOOK COUNT 0.

front: trailing-pair-sweep

## WHY THIS BOOT (the confound, finally split)

p2(42)'s render changed TWO things (always-full row + the trailing 32-bit
pair sweep). The sweep-off half has now been answered null (p2-207 + the
p2(42)-era follow-up was never run until today). The sweep-ON half was
never isolatable: the retraction voided every sweep-era verdict because the
row was SELF ("the client's refusal of a roster naming itself twice says
nothing about counts versus masks"). TODAY, for the first time in the
project's history, the foreign condition is available: the p2-182 adoption
machinery puts the RIG's genuinely-foreign row in the mac's roster, and the
crafted-self arm is OFF. So this boot runs the p2(42) configuration with
the one variable the retraction demanded: a real peer's row, with the
trailing pair cycling across republications (membership_sweep=true). The
sweep is itself a free test harness: the client withholds acknowledgements
of peer-carrying bodies (20.48) while the fork republishes - so the ACK
per shape discriminates which trailing shapes the client accepts, and the
USER'S EYES say whether any shape renders a body.

## PURPOSE (what this boot learns, win or lose)

Win: a SECOND GUARDIAN - THIS TIME THE RIG'S GUARDIAN (the genuinely
foreign row - the milestone's actual goal, not a clone) - or at minimum an
ack/rejection pattern that names the trailing shape the client accepts.
Lose (pre-named): no render + no ack discrimination - the trailing pair is
not the trigger either, and with the full row, the fresh revision, the
genuine peer AND the pair all present, the milestone's surviving candidates
shrink to the CLIENT BUILD (p2(42) ran eb893d2b; today be5807eca028ddea)
or a client-side state we have never produced - an honest, stated ceiling.

## GRAPHICS DELTA

One extra rendered guardian (the rig's) if the arm hits. Server-only
settings flip. No hooks.

## FALSIFIABLE CLAIM

1. The mac's roster carries the RIG's row (genuinely foreign - member key
   0x846C8338F7D022E6 on the mac, 0xE4DDDA60E08629C3 on the rig), with
   full row content and fresh revisions.
2. The trailing 32-bit pair CYCLES across republications (the sweep's
   variants: count_masks, packed_masks_seq, count_masks_seq, all_mask,
   solo per the sweep test's own vocabulary) while the client withholds
   or acks.
3. CONTENT NEGATIVE: foreign row + cycling pair + fresh = still no body
   -> the trailing pair is exonerated by execution and the milestone's
   candidates are the client build / the unproduced client state.

## EFFECT CLAIM (distinct from delivery)

DELIVERY: the cycling foreign row rides the proven membership keepalive
path, republished while unacknowledged. EFFECT (pre-named, not claimed):
a body renders for the rig's row on the mac (and vice versa). If a render
appears it SHOULD be stationary (the peer link is absent - appearance is
peer-authored per 20.53's split).

## ABSENCE NEGATIVE (L13)

Foreign row + fresh + cycling pair + no render: the trailing pair is
exonerated (the p2(42) confound is fully split by measurement); the
milestone's remaining named difference is the CLIENT BUILD (the p2(42)
render fact was never re-verified on be5807eca028ddea) and the
appearance-layer inputs the fork has never produced (the c4-contactable
mark, the image/descriptor content). The front does not re-iterate row
shapes without a new static discovery.

## CHAIN MARKS (L16)

- the genuine peer row (the foreign condition) ....... verified-by-execution (p2-182: the peer-adoption walker upserts the rig's record; the p2-206/207 boot logs show both machines' memberships)
- the trailing-pair sweep ............................. in-tree (activity_membership_push.cpp sweep_slot/sweep_decide; the harness's sweep_test vocabulary - the same code paths)
- the p2(42) render + its confound ..................... verified-by-log (20.53: two variables changed; the follow-up prescribed; the retraction voided the sweep-era verdicts on self rows)
- the p2-207 null (sweep OFF, full row, fresh) ......... verified-by-execution (this session: crafted rows live on both machines, no clone on either)
- the ACK harness ...................................... verified-by-log (20.48: the client withholds acks of peer bodies; the republish loop is the harness)

## ADVERSARIAL PASS: self - four ways this boot could mislead me

1. THE SWEEP PIN: membershipSweepPin >= 0 would pin ONE variant instead of
   cycling - the setting is NOT set (default -1 = cycle). Verify no pin in
   the deployed settings before reading the ack pattern.
2. THE SELF-ROW LEFTOVER: the crafted arm must be OFF (this boot's flip)
   so the roster carries the real peer - the server was RESTARTED after
   the flip (the 2026-09-07 settings-loading lesson: settings load once at
   startup - the launch prints member_setup_flags=1; the sweep/selpeer
   don't print, so the READOUT is the sweep's own lines + the row content).
3. THE ACK SIGNAL MAY BE AMBIGUOUS: the client withholds acks of ALL
   peer-carrying bodies (20.48) - the discriminator is the sweep's per-
   variant line + ANY commit of a variant (accepted = acked), and the
   render is the user's eyes. No render + no ack = the acceptance gate is
   above the row (the client build / the unproduced state).
4. THE MILESTONE'S POSITIVE CONTROL IS THE LOCAL PLAYER (20.53): a
   stationary second guardian is the pre-named render signature; a MOVING
   one would be unprecedented (impossible without a peer link) - attri-
   bute any motion to the local loop, not the row.

## PRIOR ART (09-05 FAILURE 5 - q.sh each central term)

- q.sh "trailing | sweep | mask_mask": 20.53 (the confound + the retraction
  + "the whole trailing sweep must be re-run once the peer is genuinely
  foreign") + the sweep instrument doc (member slot 1 shape cycling).
- q.sh "self peer row": the C3 knob + 20.294 R5 + p2-207 (this session's
  null - the input-gate lines stage=crafted_peer on both machines).
- q.sh "peer row | roster": 20.44 (slot 1 = the peer), 20.38/20.51/20.53
  (the roster-creates-slot split).

## DEAD-END AUDIT

- The crafted self row (p2-207): null on both machines with the input gate
  verified - CLOSED; the knob returns to false this boot.
- The full-row-alone trigger (the p2(42) follow-up): null (p2-207's
  configuration WAS that follow-up) - CLOSED by execution.
- The receive-block construction (row 8): five artifacts, one constant
  (20.330-20.333) - NOT this boot's contract; the render path here is the
  roster/image side.

## STATE READERS (a direct reader per asserted state)

- "the foreign row is on the wire" -> the membership body carries the rig's
  key on the mac (and vice versa) - the keepalive/membership lines.
- "the sweep is cycling" -> the sweep's own lines (ev=membership
  stage=sweep-ish / the variant lines the harness vocabulary matches).
- "the client accepted a shape" -> an acknowledgement commits a variant
  (vs the withheld baseline, 20.48).
- "the render happened" -> THE USER'S EYES (a stationary second guardian,
  the RIG's character on the mac / the mac's on the rig).
- "row 8 moved" -> the boot-end dump (transition_readout) if taken.

## WIDE NET (probes at every decision point)

All existing instruments (HOOK COUNT 0): the membership push lines, the
sweep variant lines, the client census diff vs p2-206, the ent/mgr/pool
instruments, boot_verdict.

## FIX SURFACE: server (settings only)

membership_self_peer_row=true -> false (the crafted arm off; the genuine
peer row restored; backup .bak_p2-207_pre_selfpeer) and
membership_sweep=true (the trailing pair cycles; backup
.bak_p2-208_pre_sweep). Both in the deployed binary. Server RESTARTED with
the new config (the settings-load-once lesson). NO SERVER-SIDE GAP: this
boot publishes what the milestone's confound-split requires; THE CLIENT IS
NEVER MODIFIED.

## ABANDON OUTCOME (pre-named)

membership_sweep=false: the bodies return to the p2-206/p2-207 single-shape
row (full, no cycling). membership_self_peer_row stays false. No rebuild.

## NEGATIVE TEST (the arm that fails on the bad state, and where it RAN)

1. THE SWEEP MACHINERY: ran in the deploy harness (--membership-sweep-test
   rc=0: the variant vocabulary count_masks/packed_masks_seq/count_masks_seq/
   all_mask/solo + the advances) - the live server runs the same code path.
2. THE INPUT GATE (foreign row): the p2-182 execution record (the walker
   upserts the rig's record; both machines' memberships in the p2-206/207
   logs); the p2-207 log's membership lines show both machines present.
3. THE NULL BASELINE (sweep OFF): p2-207's run (crafted rows live, no
   clone) - this boot's comparison point for the render question.
4. THE BOOT'S OWN NEGATIVE: foreign row + cycling + fresh + still nothing
   = the confound fully split (the pair exonerated) and the milestone
   ceiling named - pre-named, decisive.

## MODEL REVIEW (required: the milestone framing + the corrected records)

THE DEAD ASSUMPTION NAMED (this session): "the p2(42) render's trigger was
the full row" - REFUTED by p2-207 (full row + fresh, no render). The
retraction's prescription ("re-run the sweep once the peer is genuinely
foreign") is the subject of this boot and has never been executed in
history. Also corrected this session: the p2-206 'setup flags necessary'
reading was VOID (settings load once; the flips never reached the wire;
the server was restarted for THIS boot with the corrected config - the
launch print is the reader). IF THIS BOOT NULLS, the milestone's stated
ceiling is: the client build (the render fact dates to eb893d2b) and the
appearance-layer inputs never produced - the render question closes by
measurement on this build, with the confound split complete. IF IT HITS,
the genuinely-foreign render is the milestone's first true peer-visibility
event with the full input chain named.