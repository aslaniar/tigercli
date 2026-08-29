# BOOT BRIEF p2-90 (2026-08-28) - region-churn seed: does the rig survive its own re-target?

## PURPOSE
This boot tests p2(90): when a client's activity session is re-created (the re-target
after a withdrawn membership, FINDINGS 20.146/20.147), the fresh record is now seeded
with the account's last client-reported region instead of falling back to the arrival
slice set (48). Win: the rig's session reaches region 56 after churn, its client sees
"PUB56.56 includes us", citizen-joins, opens its second BAP link (GAH), and completes
the Tower load into the SAME instance as the mac. Lose: the rig churns again and the
fix did not produce the region-56 self-record - the claim path needs the next lane.

## GRAPHICS DELTA
No new rendered models. Both clients load the standard Tower (slice_set 56); L12 does
not apply - nothing about rendering changes this boot. Clients may boot minimized
where possible.

## FALSIFIABLE CLAIM
The rig client completes the Tower load into the same public instance as the mac
(shared session description; rig roster naming the mac's xuid; boot_verdict section 2
PEER xuid count >= 1 on the rig) BECAUSE its post-churn session carries region 56.
CONTENT NEGATIVE: if the rig's post-churn session still reads region=48 in
`stage=roster` lines, the seed did not produce a 56 record - either no prior reported
region existed to seed from (see ABSENCE) or the claim path itself is the defect
(next lane: the client's one-time report).
SECOND CONTENT NEGATIVE: if the rig reaches the Tower but the instances differ
(boot-1 shape), the seed worked but the public-row join path is the next defect.

## ABSENCE NEGATIVE
`stage=session_seed` lines appear on EVERY own-session commit while the switch is on.
- If `result=seeded` never appears AND the rig churns a session, then no prior record
  held a client-reported region at churn time - i.e. the rig's FIRST session never
  reported 56 this boot, which moves the defect earlier (the first report) and the
  fix never had its precondition.
- If `stage=session_seed` lines are ENTIRELY absent (not even `result=none`), the
  instrument did not run / did not deploy - provenance failure, treat the boot as
  having tested nothing.
- If `stage=settings` does not echo `region_survives_churn=1`, the switch failed to
  parse and the boot tests the OLD behavior (U9).

## CHAIN MARKS
- Region-56 record present on the wire to the rig (224/224 bodies) - VERIFIED
  (RE_output/claims/gah-region-decode.md, byte 759 bit 4, per-record self-check).
- Rig's own region record stayed 48 across post-churn sessions - VERIFIED (decode +
  server roster lines region=48 for 20000A/20000B).
- Mac's client reported 56 ~5 s into its session; its binding flipped 48->56 -
  VERIFIED (server advertise line t=12781867, roster flip t=12816757).
- Rig's early session read as 56 to the mac before the churn - VERIFIED (mac's two
  earliest bodies, decode lane NOTED item).
- Withdrawal cap (membershipPeerRetryCap=2) latched peerWithdrawn on the mac's
  session - VERIFIED (log t=12785303), left UNFIXED this boot (one contract per boot).
- Fresh-session region seeding produces a client-visible self-record that triggers
  the citizen join - ASSUMED (this boot's test; the client's claim trigger on a seeded
  region has never been observed).
- Seed survives hash/replica interactions - VERIFIED non-blocking (l9-profile-layout
  ADDENDUM: session-state hash empirically not a gate).

## ADVERSARIAL PASS
ADVERSARIAL PASS: waived - solo main-session boot prep, no second reviewer available
in-session. The session-id rule is waived per the B-checkpoint exception; the
FALSIFIABLE CLAIM and both negatives above are the adversarial surface - the boot is
judged by the rig's roster region lines and boot_verdict section 2, not by absence of
errors.

## INSTRUMENTS
INSTRUMENTS: region_survives_churn, session_seed
Deployed exe byte-literals (provenance): the two strings above must exist in
RE_output/s1_accept/sunrise-server.exe.
Runtime liveness lines (server log):
- `ev=gameplay stage=settings ... region_survives_churn=1` at bind (must appear).
- `ev=activity stage=session_seed result=seeded|none` on every own-session commit.
- `stage=roster ... region=56` naming the rig's post-churn session soid (the win line).
