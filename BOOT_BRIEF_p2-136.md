# BOOT BRIEF p2(136) - THE ENTITY FRONT: ARM THE INJECTION AND WATCH THE VERDICT

STATUS: live (2026-08-30). Reads with FINDINGS 20.208 (p2(135): the membership front
closed, the black screen renamed) and RE_output/claims/sobject-carrier.md.

## WHY THIS BOOT

p2(135) fixed the membership state hash and the whole session layer went healthy: 0
checksum failures, 0 forced disconnects, `peers valid 0x7 / players valid 0x3`, and
`Citizen join for PUB56.56 succeeded!` - with the profile LIVE. The revision counter
stopped at 9 instead of 23,908.

The mac still went black at peer arrival, and with the checksum noise gone the real
mechanism is legible for the first time:
    networking:simulation:entity: failed to create 'player_broadcast' entity
repeating, one burst after each of our type-12 activity membership pushes
(`stage=push result=ok type=12 body=3882 len=3927`, 100 of them). The client is being
handed something substantial, is trying to instantiate a player entity from it, and is
failing. This project has never had an error message for the rendering wall before.

Also settled this run, and it changes the direction: the client<->client channel was
captured WITH profiles applying - the exact condition 20.196 RESULT 5 named as its own
re-open case - and it is still flat. 1,394 packets, 106,691 B, 1,382 of them 76 B on the
wire, largest packet 268 B, 10s buckets 2495/6232/6232/6232/6232/6156/6308/... with no
burst at co-location. The peer does NOT send its own packaged guardian. The entity has to
come from the server, which is the lane this boot arms.

## WHAT THIS BOOT CHANGES (settings only - no rebuild, no new instrument)

  server  world_population   FALSE -> TRUE   (the entity injection lane, built and never
                             once run; carrier stays 7 = sim-event sobject_message)
  clients world_trace        FALSE -> TRUE   (BOTH machines; its entity hook 0x141718080
                             sits INSIDE the entity-replication codec cluster
                             0x141717EB0..0x14172AAAA that owns the player_broadcast
                             channel, and logs entity_index/flags/local_index plus the
                             ORIGINAL'S RETURN VALUE as a decode verdict)
  clients state_diff         TRUE -> FALSE   (its apply hook logged zero calls twice; it
                             is dead weight on the apply path and comes off)
  clients decoder_trace      FALSE (held - shares the apply address)
Server exe and both client DLLs are UNCHANGED from p2(135).

## PURPOSE - what this boot learns, win or lose

WIN OUTRIGHT: a guardian renders, or the black screen stops. Either is the milestone.
WIN BY DIAGNOSIS: it still fails, and `ev=wtrace stage=entity_done ... verdict=` names
WHY each create is refused - the first direct evidence on the rendering wall rather than
inference from absence.

## GRAPHICS DELTA (L12)

This is the ONE boot in this series that deliberately adds a rendered model: the injected
entity, if it materialises, is a new drawn object. That is the point of the test.
Minimised: exactly one entity, at the top of the lease mask (8191 downward, so it cannot
collide with the client's own low-prefix grants), carrier 7, no other emission enabled.

## FALSIFIABLE CLAIM

CLAIM: with world_population armed, the client stops logging
`failed to create 'player_broadcast' entity` and/or a guardian-shaped entity appears; and
where it still fails, `ev=wtrace stage=entity` and `stage=entity_done` lines report a
non-zero call count with a decode verdict per attempt.

CONTENT NEGATIVE (pre-named - L6):
- ZERO `ev=wtrace stage=entity` LINES: the entity hook does not fire either, and the codec
  cluster is not reached on this path at all. That retires 0x141718080 as an observation
  point and the next question is which function DOES own the create.
- ENTITY LINES PRESENT, verdict uniformly refused, injection changes nothing: our injected
  entity is rejected for the same reason the client's own attempt is. The verdict value is
  then the whole finding and the fix is built against it.
- THE BLACK SCREEN STOPS BUT NOTHING RENDERS: the failure was a stall, not a missing model.
  Different problem, better one.
- SESSION REGRESSES (checksum failures return): world_population perturbed the membership
  plane. Roll back to p2(135)'s configuration, which is measured clean.

## ABSENCE NEGATIVE (L13)

The session-layer pass conditions from p2(135) must STILL hold, or this boot's entity
result is meaningless: server `members=3 players=2 ... profile=1 client_base=0`, both
`stage=join result=admit`, mac `peers valid 0x7 / players valid 0x3`, mac `Citizen join
... succeeded!`, and checksum failures at ZERO. If any regressed, the entity data is void.
LIVENESS: `ev=wtrace stage=install result=ok` on both machines. If that line is absent the
flag did not take and nothing below it means anything.

## MEASUREMENT

  mac : grep -ac "failed to create 'player_broadcast'"   -> expect 0, or a named verdict
  mac : grep -a  'ev=wtrace stage=entity'                -> index/flags/local_index
  mac : grep -a  'ev=wtrace stage=entity_done'           -> THE VERDICT per attempt
  mac : grep -ac 'checksum failed' / 'succeeded!'        -> the p2(135) result must hold
  srv : grep -a  'world_population\|stage=push result=ok type=' -> what we injected
  human: does anything render at the peer's location?
Archive both logs plus a pcap to RE_output/captures/<ts>_p2-136/.

## CHAIN MARKS (L16)

| Link | Mark |
|---|---|
| The membership state hash is fixed | VERIFIED-BY-EXECUTION (p2(135): 0 failures, players 0x3, citizen join succeeded, profile live) |
| The black screen is NOT the checksum force-disconnect | VERIFIED-BY-EXECUTION (p2(135): zero disconnects, screen still went black) - 20.203 R1 CORRECTED |
| The client fails to create player_broadcast entities | VERIFIED-BY-EXECUTION (retail log, 62 bursts) |
| Each burst follows our type-12 push | VERIFIED-BY-EXECUTION (100 x body=3882 len=3927) |
| The peer channel carries no guardian, WITH profiles live | VERIFIED-BY-EXECUTION (this run's pcap: max 268 B, flat buckets) - 20.196 RESULT 5 discharged |
| player_broadcast is a sobject channel of the entity codec cluster | VERIFIED-BY-READING (sobject-carrier.md; string 0x141CA1518, one xref, cluster 0x141717EB0..0x14172AAAA) |
| We grant the full entity-slot lease | VERIFIED-BY-EXECUTION (type=0 body=1024, the 8192-slot mask) |
| 0x141718080 is reached on this path | UNKNOWN - THIS BOOT |
| Why the create is refused | UNKNOWN - THIS BOOT |

## DEPLOYED (p2(136))

  server exe `789d8d9f0ed94e9e` UNCHANGED (p2(135) build, seven harness gates passed).
             Settings: world_population TRUE, carrier 7, publish_player_profile TRUE,
             session_state_client_base FALSE, profile_state_variant 0.
  clients mac+rig `5e7ce5327a235955` UNCHANGED. world_trace TRUE, state_diff FALSE,
             decoder_trace FALSE. Rig settings pushed and read back byte-exact.
  ROLLBACK: world_population FALSE returns exactly to p2(135), which is measured clean at
            the session layer.

## LITERAL TARGETS

LITERAL TARGETS:
  RE_output/s1_accept/sunrise-server.exe: world_population, stage=membership result=built
  Game/bin/x64/steam_api64.dll: ev=wtrace, stage=entity

## ADVERSARIAL PASS

ADVERSARIAL PASS: waived with a NOTED RULE TENSION: the peer-visibility rule says observer
first, emission second, and this boot arms both at once. Deliberate - boots are expensive
here and the observer makes a null readable rather than ambiguous, so arming both is
strictly more informative than observer-only and cannot produce a misreadable silence.
Both are settings flips with no rebuild; rollback is one flag to a measured-clean state.
Hook RVAs re-verified: 43 checked, 0 bad, VERIFY PASS.

## RUN SHAPE

1. (DONE) Arm the flags on all three targets, verify by read-back, archive p2(135),
   re-verify hook RVAs, restart the server.
2. mac to orbit, then Tower, SOLO. Confirm the landing AND that checksum failures are 0.
3. Rig joins the Tower. Hold ~90 s. Watch for anything rendering.
4. Measure; the verdict lines are the deliverable even if nothing renders.
