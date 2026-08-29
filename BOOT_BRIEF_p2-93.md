# BOOT BRIEF p2-93 (2026-08-28) - slice set follows the reported region: does the
# public Tower transition finally take its switch task?

STATUS: live (2026-08-28 ~21:2x). Supersedes nothing; p2(90) region seed stays ON,
p2(91)/p2(92) member flags stay OFF (FINDINGS 20.152 - the flags are not the lever).

## PURPOSE
This boot tests p2(93): the slice set this host PUBLISHES now follows the region the
client REPORTED, instead of staying pinned to the destination's arrival bubble.

The p2(90) boot was misread as an asymmetry (rig renders, mac black-screens). It is
not. Both clients ran the identical world-controller ladder - both crossed the
managed-session-start gate, both reached `activity:in_world`, both citizen-joined
PUB56.56 successfully, both precached slice-set 56 - and then BOTH stopped at exactly
the same place, with no slice-set-switch task and no transition completion. Neither
client ever left its own private Tower.

Cause, measured: every `stage=roster` line in the whole p2(90) boot read
`region=56 slice=48`. `effective_region` lets the reported region win for the region
INDEX but leaves `region.arrival` on the destination's arrival bubble (48), and the
two places that publish a slice set both read the arrival - the roster's spawn
override and the global-activity-state body's `sliceSetIndex`. A PRIVATE or ORBIT
slice-set transition self-simulates its phase (`:simulator: advancing simulated phase
directly to 'switch-now'`), so PRV24/PRV48 complete with no server agreement at all.
The PUBLIC `normal_z_leg` transition has no simulator arm: it waits for the authority
to agree, and the authority kept saying 48.

WIN: after "Finished precaching slice-set 'PUB56.56'", each client logs
`Region 'PUB56.56 (HASH: 0x82ae25b4)' is being assigned the slice-set-switch task`
then `Stopping transition of type 'transitioning:normal_z_leg' due to completed` and
the rendered world becomes the shared public Tower.
LOSE: precache still finishes and no switch task is assigned - the slice set was
necessary but not sufficient, and the next lane is the transition PHASE carrier
itself (candidates already narrowed: the region record's 32-lane transition-token
array, and the host tail's teleport block - state 3b / token 8b / sliceSet 10b /
hash 32b - which this host has published as empty for every boot to date).

## GRAPHICS DELTA
No new rendered models are introduced by this change. The intended outcome is that
each client swaps the world it ALREADY has precached (slice-set 56, the standard
Tower) in place of slice-set 48. Both slice sets were already loaded and rendered in
p2(90), so L12 exposure is unchanged from the last boot. Clients may boot minimized
where possible; the win condition is readable from the logs alone.

## FALSIFIABLE CLAIM
With `activity_slice_set_follows_region=true`, every `ev=activity stage=roster` line
emitted after a client reports region 56 reads `region=56 slice=56` (not `slice=48`),
and each client's slice-set transition manager assigns the slice-set-switch task for
'PUB56.56' after its precache completes.

CONTENT NEGATIVE: if `stage=roster` lines still read `region=56 slice=48` after the
client has reported 56, the switch did not reach `effective_region` - the publish
path is not the one the roster reads, and the change tested nothing.
SECOND CONTENT NEGATIVE: if the roster lines DO read `region=56 slice=56` and the
client still never assigns the slice-set-switch task, then the published slice set is
not the phase input. That is a real result: it retires the slice-set hypothesis and
promotes the transition-token / teleport-block carrier named in PURPOSE.
THIRD CONTENT NEGATIVE (regression watch): if either client's citizen join breaks
('the session disappeared while we were joining', retry loop) the way p2(91)/p2(92)
broke it, the spawn override moving off the destination arrival is itself harmful -
flip the switch to false, no rebuild, and the boot still produced a result.

## ABSENCE NEGATIVE
- If `ev=gameplay stage=settings` does not echo `slice_follows_region=1`, the settings
  key failed to parse and this boot tested the OLD behaviour (U9). Treat as tested
  nothing, not as a negative result.
- `ev=activity stage=roster` lines carry `region=` and `slice=` on every keepalive and
  are the entire instrument for this boot; p2(90) produced 494 of them. If ZERO
  `stage=roster` lines appear, the roster path did not run - provenance failure (L13),
  the boot tested nothing, and the deploy is suspect before the change is.
- If `stage=roster` lines appear but `region=` is never 56 on either client, the
  clients never reported the public region this run, so the change never had its
  precondition. That is an earlier defect (the region report), not evidence about the
  slice set.

## CHAIN MARKS
- Both clients reached `activity:in_world` and citizen-joined PUB56 in p2(90) -
  verified-by-reading (both client logs, state_manager ladder identical, mac t=106469
  / rig t=87390; citizen join succeeded mac t=107757 / rig t=88187).
- Neither client was ever assigned a slice-set-switch task for PUB56 -
  verified-by-reading (grep of slice_set_transition_manager across both logs: the
  switch task appears for PRV24 and PRV48 only).
- Private and orbit transitions self-simulate the switch-now phase; the public one
  does not - verified-by-reading (`:simulator:` lines present for PRV24/PRV48 on both
  clients, absent for PUB56 on both).
- The server published `region=56 slice=48` for the whole run - verified-by-reading
  (494 `stage=roster` lines, both accounts, p2(90) index).
- `region.arrival` is the value both publish paths read, and the reported region never
  moves it - verified-by-reading (activity_roster_snapshot.cpp effective_region;
  activity_global_state_push.cpp resolve_state; the only two arrival_slice_set callers).
- A reported region is DOCUMENTED as beating the arrival slice set "wherever the host
  must say where the player is" - verified-by-reading
  (state/activity/membership/activity_membership_query.h, reported_region doc block).
- Region index and slice-set index share one numbering here (bubble x 8) -
  verified-by-reading (region_reader.h region_index + its static_asserts; PUB56.56 /
  PRV48.48 name form; client `bootflow stage=region ... slice_set=56`).
- Publishing the reported region as the slice set makes the client take the switch -
  assumed (this boot's test; never observed).
- The spawn override moving off the destination's arrival bubble is harmless -
  assumed (it is the one behaviour change with a plausible bad path; the THIRD
  CONTENT NEGATIVE above is its watch, and the switch reverts it without a rebuild).
- The peer machine-id window mismatch (`blob[0..7]` vs `blob[5..12]`) is non-blocking -
  verified-by-reading (recorded in p2(89) and BOOT_BRIEF_p2-87; both clients logged
  'Could not find tracking data for peer 1', released the reservation and continued
  in p2(90)). NOT touched this boot - one contract per boot.

## ADVERSARIAL PASS: waived: solo main-session boot prep, no second reviewer available
in-session (B-checkpoint exception). The FALSIFIABLE CLAIM and the three content
negatives are the adversarial surface: this boot returns a usable result in every
branch, including the branch where the slice set turns out not to be the phase input.

## INSTRUMENTS: slice_follows_region=%u

## SWITCH POSITIONS FOR THIS BOOT
  activity_slice_set_follows_region  TRUE   <- the one contract under test
  activity_region_survives_churn     TRUE   (p2(90), required, unchanged)
  activity_host_region_bound         TRUE   (unchanged)
  activity_public_row_membership_bodies 65535 (unchanged)
  activity_member_setup_flags        FALSE  (p2(91)/p2(92), stays off - 20.152)
  join_roster_observer               FALSE  both clients (unchanged)
  slice_set                          56     both clients (unchanged)

## ROLLBACK
Flip `activity_slice_set_follows_region` to false in
RE_output/s1_accept/Sunrise/settings.json - no rebuild, restores p2(90) behaviour
exactly. Settings backup: settings.json.bak_p2d93_preboot_20260828.
Server rollback binary: p2(86) `4b2bff83c05f4bb9`. DO NOT BOOT p2(71).
