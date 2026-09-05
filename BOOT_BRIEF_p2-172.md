# BOOT_BRIEF_p2-172 — THE RESEED: CLAIM-PATH ACCUMULATION UNDER A LIVE CONTAINER

STATUS: NEVER RAN (2026-09-03 22:0x - the mac client was not closed before deploy and
froze in Tower at ~21:00:05 on the OLD build; the p2-172 client/server never executed
against each other; session died before relaunch). REVERTED to p2-171 clean - see
FINDINGS 20.289/20.290. Retry requires the 20.290 R3 no-live-client pre-deploy check.

## PURPOSE

20.287 corrected the mechanism: the guard's required bit is OR-ACCUMULATED at claim time
(`or word [rec+0x3112], 1<<edx` @ 0x1417c0ea6), not fixed at birth. The peer's record
carries only bit 5 (container -1) because only the -1 path ever claims it, while the guard
demands a live container's bit (6/7, pinned by gatebit on both machines in p2-171). A later
claim under a live container would ADD the bit - the blank records prove accumulation works
(mac rec=1 went 0x0080 -> 0x00C0 in p2-171).

THIS BOOT: the fork re-delivers the membership snapshot under a fresh revision every 2nd
keepalive on the private link (settings membership_reseed_interval=2, republish() defeats
the client's repeat-drop). The membership landing is the one observed trigger that re-enters
the claim path (20.280: membership t=328223 -> record birth t=328234). Two read-only
observers ride it: resv_claim (0x1417C3480 - names WHICH path stamps WHICH bit on WHICH
identity) and image_set (0x1403CB720 - fires only if an image is delivered; zero firings on
our fork is the pre-named negative).

## GRAPHICS DELTA

ZERO new rendered models expected. Entity construction is NOT reached by this boot
(20.285 R4: a passing guard constructs nothing; the claim is the side effect that matters).
A rendered peer would be a surprise to explain, not a success to bank.

## FALSIFIABLE CLAIM

After a server line `stage=membership_reseed result=republished`, a later `resv_claim`
line names a claim with bit 6 or 7, and a subsequent `resv_rec` line shows a record whose
mask GAINED bit 6/7 (0x0020 -> 0x0060 / 0x00A0 / 0x00E0, or 0x0040/0x0080 gaining the other
live-container bit) - on the PEER's record specifically if the peer's identity is the one
claimed, on any record if the path runs at all.

PRE-COMPUTED MASK TRANSITIONS (offline replay over 20.286 R3's recorded values - the
fixture for this boot's new column):
  peer mac  0x0020 + bit6 -> 0x0060 | + bit7 -> 0x00A0 | + both -> 0x00E0
  rig mac-rec 0x0040 + bit7 -> 0x00C0
  blank mac 0x00C0 is already saturated (bits 6+7) - no further gain possible there.

## CONTENT NEGATIVE

  (2) reseed fires (server line present) but EVERY resv_claim line shows bit=5 -> the
      claim path's bit source is fixed independent of timing; the sequencing lever is
      dead; the image route is the only road. The resv_claim caller_rva values say WHICH
      subsystem stamps (sweep ~0x1417024d2 vs join-family ~0x14176940c/0x141769816/
      0x141770e2e/0x1417b8ee2).
  (3) reseed delivers but zero resv_claim lines appear -> membership does not re-enter
      the claim path; the birth was one-shot at join; lever dead differently.
  (4) resv_claim shows bit 6/7 claims but NO mask ever gains them -> CONTRADICTION with
      the OR model - re-read 0x1417c0ea6's path before any conclusion (20.285 R4 shape).

## ABSENCE NEGATIVE

  - ZERO stage=resv_claim lines -> the claim never ran this boot OR the observer failed;
    the install census (attached=1 for resv_claim/image_set) distinguishes them.
    Instrument, not game.
  - ZERO stage=image_set lines -> EXPECTED on our fork ("the fork never delivers the
    image"). A firing is the headline, not the baseline.
  - ZERO stage=membership_reseed -> the setting did not arm or the interval was never
    reached; check the server's settings line and keepalive cadence before concluding.

## CHAIN MARKS

  L1 card in the guard's field .............. verified-by-execution (20.284)
  L2 gate forced open, guard runs ........... verified-by-execution (p2-170, 1190 calls)
  L3 claim sticks, record retained .......... verified (corrected 20.286 R0: the retained
      word is a DIFFERENT bit, not a guard-granted claim)
  L4 W2: the required bit ON THE PEER ....... THE LINK THIS BOOT TESTS (via accumulation)
  L5 entity construction .................... NOT THIS BOOT (out of scope; 20.285 R4)
  L6 movement ............................... UNSTARTED, out of scope

## ADVERSARIAL PASS

ADVERSARIAL PASS: waived:the new column's arg decode was VERIFIED-BY-READING the callee
(esi=edx flows unchanged to 0x1417C08F0's OR site at 0x1417c0ea6; r8 is the 86-byte blob
pointer the sweep passes at 0x1417024a2) and the mask transitions were pre-registered by an
offline replay over 20.286 R3's recorded p2-171 values (listed under FALSIFIABLE CLAIM).
Novelty gating is first-seen-key per (blob, bit) - the disown/re-claim flicker that repeats
one pair costs zero lines (p2-171's flicker would have flooded a plain budget). Both
observers are read-only: resv_claim dereferences NOTHING (register values only); image_set's
16-byte fingerprint read is SEH-guarded.

## INSTRUMENTS

INSTRUMENTS: "stage=resv_claim fn=%s call=%llu caller_rva=0x%llX bit=%u blob=0x%llX
first_seen=1", "stage=image_set fn=%s call=%llu obj=0x%llX image=0x%llX fp=",
"stage=membership_reseed result=republished interval=%u session=%llu"

LITERAL TARGETS:
    Game/bin/x64/steam_api64.dll: "stage=resv_claim", "stage=image_set"
    (both asserted in the deployed file at 210048/210056)

## DEPLOYED

  server   949ba4b10966071f - NEW build (reseed + settings key); deploy asserted
           deployed==built; server restarted, listeners 3/3, nat ok, claims reset 0.
  clients  BOTH 4aa099b6105745e6 - hash + 2 literals asserted in each deployed file
           (mac 210048 / rig 210056).
  gate     verify_hook_rvas PASS (95 RVAs, 0 bad) - includes the two new hook sites.
  rollbacks: settings.json.bak_reseed_preboot; client DLLs .bak_p2d7_20260903_210048 (mac)
           / .bak_p2d7_20260903_210056 (rig); fork commit 2e91f94 (revert = full rollback).

## SETTINGS / HYGIENE

  server   membership_peer_transport_identity=true, roster_peer_participation=true,
           membership_reseed_interval=2  (NEW - the arm for this boot)
  clients  gate_poke=0 BOTH (NOT armed this boot - the poke is retired for this question)
  server reset DONE between runs (the standing rule).
  *** PHASE 1 = SOLO CONTROL (mac only, ~3 min in Tower): confirm reseed lines fire on
      schedule, resv_claim lines appear for the SELF identity, no client crash. Then
      phase 2 = paired. ***
  RELAUNCH BOTH CLIENTS for phase 2.

## PRE-NAMED OUTCOMES

  1. WIN: peer record gains bit 6/7 (mask 0x0060/0x00A0/0x00E0) after a reseed -> the
     guard's requirement is satisfiable by fork timing alone; next boot scopes L5.
  2. bit=5 only -> sequencing lever dead; image route confirmed as the only road; the
     resv_claim caller_rva values feed the image-format lane.
  3. no claims fire on reseed -> membership is not the trigger; hunt the real one with
     the observer already in place.
  4. contradiction (bit 6/7 claimed, mask unmoved) -> instrument/model defect; re-read
     the OR site; NO further boot on this question until resolved.
