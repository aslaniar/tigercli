# BOOT_BRIEF_p2-177 - THE HUSK: INSTRUMENT A SUCCESSFUL BODY CREATION, SOLO
STATUS: live (2026-09-04, drafted after 20.298 + the 20.135 fold-in)

Server 3f0496a9ebcf744c UNCHANGED. Client p2-171 a96a6a70f578fc40 (MAC ONLY).
NO REBUILD, NO NEW INSTRUMENT, NO CLIENT CHANGE, NO RIG.

## PURPOSE
The husk sequence (black screen -> recover -> a second guardian, the player controlling
the NEW body, the old one left inert) is the ONLY known case of this client rendering a
character body that nothing is driving - and per 20.135 IT FIRES SOLO, with the rig not
booted. That makes it the project's first reusable POSITIVE CONTROL for body creation.
This boot watches a body creation that SUCCEEDS, with the same probes that watch the
peer record fail 11,491 times (20.298 R1), so the two paths can be diffed.

WIN OR LOSE, THIS BOOT LEARNS:
  - f38 nonzero on any record across the event -> cond5 IS on the render path, the gate
    byte IS writable in practice, and the state that writes it is named. The +0x38
    writer hunt becomes "which path did that", not "does anything ever do it".
  - f38 stays 0x00 while a body renders -> COND5 IS NOT ON THE RENDER PATH.
    FRONT_chain-to-a-moving-guardian.md's central premise is wrong and gets rewritten
    BEFORE another boot is spent hunting the writer. This is the cheaper failure.
  - no husk at all -> the sequence is not reproducible on this build/settings; the delta
    from the historical condition is itself the finding.

## THE CHANGE (server settings only; NO rebuild)
Restore the two run-A peer-row knobs to the historical baseline. They are peer-row
experiments and MEANINGLESS SOLO, and publish_player_profile=false is the one run-A knob
NOT yet excluded as a contributor to the 2026-09-04 black screen. Removing an
experimental variable is not a second experiment (U10 intact).
  membership_peer_transport_identity  FALSE -> TRUE
  publish_player_profile              FALSE -> TRUE
UNCHANGED: peer_retry_cap=10 (harmless solo), same_region_advert=true,
self_peer_row=false, sweep=false/pin 0, world_population=true, c4_mark_push=false.
*** gate_poke MUST REMAIN 0. *** The pgate probe carries a poke - the only write this
DLL can make into game memory. THE CLIENT IS NEVER MODIFIED; a poke here would destroy
the evidence that the server-side answer exists. Assert it 0 pre-launch.

## INSTRUMENTS: pgate/ptable, pb_create, ent_make, create_loop, memidx_alloc,
## idx_publish, mgr_init/mgr_fill/mgr_sync, member_get
## (ALL EXISTING in the deployed p2-171 client. No new literals. Nothing for
##  verify_hook_rvas.py - no RVA is new or changed.)
## LITERAL TARGETS: none new

## SETUP (my job; user only launches ONE game)
  1. Apply the two settings flips; echo them back and assert.
  2. reset_lobby_claims.sh (server restart; claims cleared).
  3. Assert mac client hash a96a6a70f578fc40 and gate_poke=0.
  4. Rotate the mac client log to zero so the event is unambiguous.
  5. RIG STAYS OFF. Confirm no rig session server-side before launch.
  6. log_archive.sh --label p2-177-husk afterwards.

## THE RUN
SOLO mac. Launch, sign in, go to the Tower, and LAND. Then STAND STILL and observe.
Do not switch characters, do not go to orbit. Dwell ~4 minutes after landing whether or
not the sequence fires. If the screen goes black, WAIT - do not alt-tab, do not quit;
the recovery is part of the sequence and killing the client destroys the measurement.

## THE OBSERVATION THAT COSTS NOTHING AND IS STILL UNCOLLECTED (20.135, open since
## 2026-08-28) - THIS IS AS IMPORTANT AS THE LOGS:
  *** WHERE DOES THE HUSK STAND? ***
    (a) at the position you held BEFORE the screen went black -> WORLD-CONTAINER REBIND
    (b) at the SPAWN POINT (where you normally arrive)         -> DOUBLE SPAWN
  One look eliminates one reading. Report it in words; no instrument can get it.

## GRAPHICS DELTA (THE TEST ITSELF)
Expected new rendered models: 0 or 1. Baseline is ONE guardian (the player). The husk is
a SECOND, INERT body. This is the deliverable and cannot be minimised further: no client
change, no new probe, one settings revert.

## FALSIFIABLE CLAIM
When the husk renders, the participant/entity machinery reaches a state it never reaches
for a peer record: a create COMPLETES (pb_create's census count advances and the loop
stops re-engaging the same slot), and the gate byte at participant_record+0x38 becomes
NONZERO on at least one record.

CONTENT NEGATIVE (what refutes it): the husk renders while every pgate sample still reads
f38=0x00 and no create completes. That refutes cond5 as a render-path precondition and
falsifies theory T1 in FRONT_chain-to-a-moving-guardian.md.

## ABSENCE NEGATIVE (L13 - what zero lines MEAN)
  - NO husk and NO black screen: the sequence did not fire. NOT evidence about cond5.
    Record the settings/build delta vs the historical condition and stop - do not read
    the f38 samples as a result about rendering.
  - BLACK SCREEN THAT NEVER RECOVERS (the 2026-09-04 shape): the husk half never
    happened. This EXCLUDES publish_player_profile=false as the black screen's cause
    (it is TRUE this run) and promotes the black screen to its own lane. Still a result.
  - zero pgate lines: the participant table was never walked - the probe's precondition
    (a live table) was absent, so f38 says nothing this run.
  - PROBE BUDGET LIMIT, NAMED IN ADVANCE: pb_create logs only its first 32 enter/leave
    pairs (budget 32); tonight's census reached 55 calls. If the husk's create is past
    #32 there will be NO per-call line for it. MITIGATION: the periodic census counter
    still advances, so read the calls= DELTA across the event. Do not read "no pb_create
    line at the husk" as "no create happened" - that is the census/budget trap.

## CHAIN MARKS (L16)
  H1 the husk sequence exists                  verified-by-execution (20.135; user
       report + full sequence reproduced)
  H2 it fires SOLO, rig not booted             verified-by-execution (20.135, p2(88)
       run 3; server-side addresses confirm the rig's absence)
  H3 it is the player's OWN previous body      verified-by-execution (user: control is
       in the NEW body; 20.127's co-presence framing FALSIFIED)
  H4 it is reproducible ON DEMAND              unknown - THE RUN'S FIRST RISK. "It's
       always been like that" is a user report over many boots, not a demonstrated
       trigger. 2026-09-04 went black WITHOUT recovering.
  H5 a create COMPLETES during the husk        unknown (THIS BOOT)
  H6 f38 becomes nonzero during the husk       unknown (THIS BOOT - the decisive read)
  H7 the husk path and the peer path differ    assumed (the diff is the whole point;
       H5/H6 are what make it measurable)

## ADVERSARIAL PASS: waived: no adversarial reviewer run. LOWEST-RISK BOOT OF THE
RECENT SET - solo, one machine, no rig, no network coupling, no rebuild, no new hook,
no client write (gate_poke=0), and a pure settings revert to a historical baseline.
The 2026-09-04 session lost four of five launches to environment coupling that a solo
boot structurally cannot hit. Flagging the waiver rather than hiding it.

## DO NOT
  - do not boot the rig (H2 is the whole reason this is cheap; a second machine
    reintroduces every failure mode that cost 2026-09-04)
  - do not enable gate_poke - THE CLIENT IS NEVER MODIFIED
  - do not quit or alt-tab during the black screen; the recovery IS the event
  - do not read "no pb_create line" as "no create" (budget 32; use the census delta)
  - do not read f38 as a render verdict if the husk never fired
  - do not switch characters or visit orbit during the run
