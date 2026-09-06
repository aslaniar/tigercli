# BOOT_BRIEF_p2-179 — THE RECEIVER QUESTION, MEASURED WITH THE DUMP THAT WAS NEVER TAKEN

STATUS: live (2026-09-05, drafted post-20.302)

Server ed43adf1d6152744 (UNCHANGED — no rebuild, no settings change; hash asserted
on disk 2026-09-05). Clients 3cc844c4cdd2fd63 BOTH (the p2-178 build; asserted at
setup). THE CLIENT IS NEVER MODIFIED.

## PRIOR ART (required field — TOOLING_AUDIT T2.2)
q.sh terms run this session: ent_recv / 0x141718510 / receiver (findings read
in full, not searched): 20.222, 20.224, 20.225, 20.251, 20.262-20.267,
20.270 (W1 ran: outcome (c)), 20.271-20.286 (connection-ladder arc, W1/W4
closed), 20.291 (image front parked), 20.296 (installer reframed: mask
lifecycle conversion), 20.297 (transition run = outcome (c); R6: THE RIG DUMP
WAS NEVER TAKEN), 20.301 (loop front retracted; front = server-side entity
replication), 20.302 (ent cluster decoded; contract doc). STATE NEXT governs.

## PURPOSE (ONE CONTRACT — U10)
Does a participant transition produce a receiver-bearing object? 20.296 R2
reframed the receive-interface installer as mask-lifecycle conversion; 20.297
ran the transition but measured only the hook census (ent_* = 0) because the
rig dump was never taken (20.297 R6 - tooling gap, named). This boot takes
the dump. The four receive vptrs (0x141C9ADD8/0x141C9AE50/0x141C9AEC8/
0x141C9AF40) in the transitioned machine's memory is the readout.

PRE-NAMED OUTCOMES (20.296 R3, unchanged):
  (a) vptrs present + ent_recv fires on the push -> THE PEER-ENTITY PATH OPENS
      (server-feedable; encoder work proceeds on a live target).
  (b) vptrs present, ent_recv silent -> the ring->receiver dispatch is the
      wall (20.302 R7's VMP/cross-function candidates become the measured
      question).
  (c) no vptrs -> conversion needs more than a mask transition; the sweep-
      state prerequisite (20.297 R2) becomes the measured quantity.

## SETTINGS (NO CHANGES - the seeding stack is already deployed and ON; road 1's
## ladder learnings are folded in: extras exonerated 20.298, cap=10 anti-
## starvation, publish_player_profile=TRUE per the 20.299 black-screen suspect)
  roster_peer_participation=True (W1, 20.270: digests cleanly)
  membership_peer_transport_identity=True (W4 re-pin, 20.284: card lands on
      the guard's 86-byte field, 1,559 samples)
  membership_peer_retry_cap=10, rearm_after_acks=8 (inert by construction,
      20.300 R5 - left as-is to avoid a settings variable)
  publish_player_profile=True, world_population=True (carrier 17),
  same_region_advert=True, self_peer_row=FALSE (C3 retired, user),
  sweep=false pin=0, c4_mark_push=false
Disk-verified 2026-09-05 against RE_output/s1_accept/Sunrise/settings.json.

## THE RUN
  1. reset_lobby_claims.sh (server restart from the REPO ROOT - 20.297 R5).
  2. Paired Tower, first entry: MAC lands first and STAYS put (no orbit, no
     character switch - the mac is the CONTROL that holds the session).
  3. RIG transitions: rig leaves to orbit and re-enters the Tower. This is
     the conversion input on the machine we can dump.
  4. RIG DUMP regardless of re-entry state: if the re-entry hangs
     (initial_slice_set_loading is pre-existing, 20.300 R6), the dump is
     taken anyway - the vptrs, if installed, were installed before any hang,
     and a hung process's memory still answers the question.
     `bash RE_scripts/rig_full_dump.sh p2-179-transition`
  5. Dwell ~3 min post-re-entry, then archive + index
     (log_archive.sh --label p2-179-transition; logindex all three).

## INSTRUMENTS (all existing; NO new hooks, NO client change)
  - ent_recv 0x141718510 / ent_header 0x141717EB0 / ent_create 0x141718080
    enter hooks (deployed p2-178 clients, 24/12/12 arg slots).
  - sobj_decode 0xE739D0 / queue_evt 0x16F0F60 (the decode arms - 20.297 R1's
    "ring-only" consumption lines).
  - Server: wire_snapshot / membership_peer / membership_ack (the input gate).
  - THE VPTR SCAN (validated this session): dump_search.py over the fresh
    rig dump, --u64 <base+0x1C9ADD8|AE50|AEC8|AF40>. Smoke on p2-146: 0 hits
    (the known negative, 20.223) with --selftest PASS (positive control,
    base+0x1CA1518) - a real null. Compute the NEW boot's module base via
    minidump_reader Minidump.module('destiny2').

## READOUT TRIGGER (required field — TOOLING_AUDIT T2.1)
  - ent_recv/ent_header/ent_create: emit on function ENTRY; trigger = a
    received entity reaching the codec. NEVER-OBSERVED (first-fire risk):
    zero in every instrumented boot (20.263 R1). The absence negative is the
    pre-named outcome (c) - zero lines is a FINDING here, not instrument
    silence, because the vptr scan independently distinguishes (b) from (c).
  - sobj_decode: emitted on fresh pushes in p2-175 (20.297 R1: rig 1, mac 2)
    - the transition's fresh type-7 push is the trigger that makes it emit.
    ZERO sobj_decode lines at re-entry = the transition did not happen =>
    THE RUN IS VOID (input gate; same class as p2-175's starvation).
  - vptr scan: trigger = the dump file; liveness = --selftest PASS on the
    same dump + the known-present string hit inside the module.

## READOUT (in order - input gates result)
  1. INPUT: rig sobj_decode fires at re-entry (fresh push consumed). If 0,
      VOID.
  2. ent_recv/ent_header/ent_create census, both clients, full dwell.
  3. THE VPTR SCAN on the post-transition rig dump (the decisive readout).
  4. Graphics: second guardian on the mac (does the rig's return render?).

## GRAPHICS DELTA (U12)
The test itself is memory-state, not pixels, but the visual readout is still
recorded: expected NEW rendered models beyond the baseline (one guardian per
machine, own player only) = 0 or 1. A second guardian on the MAC after the
rig's re-entry is the positive (L6). Minimization: no client change, no new
hook, no settings change; the graphics delta is a secondary readout to the
vptr scan and cannot be reduced further.

## FALSIFIABLE CLAIM
A participant transition (leave + re-enter) on a machine holding a peer row
installs the four receive-interface vptrs on at least one object (outcome (a)
or (b)). REFUTED by outcome (c): post-transition dump contains zero instances
of all four vptrs while sobj_decode/queue_evt show the transition's push was
consumed.

## ABSENCE NEGATIVES (both kinds, L6+L13)
  - zero sobj_decode at re-entry: the run is VOID (no transition input).
  - zero ent_* lines AND zero vptrs: outcome (c) - conversion needs more
    than a mask transition; the front moves to the sweep-state prerequisite.
  - zero ent_* lines WITH vptrs present: outcome (b) - the dispatch is the
    wall; 20.302 R7's remaining candidates (VMP 0x140484EE0, cross-function
    register passing) become measurable against a live object.
  - vptr scan 0-hits is only trusted with --selftest PASS on the SAME dump.

## CHAIN MARKS (L16)
  L1 paired Tower co-location            verified-by-execution (20.140)
  L2 a participant transition occurs      verified-by-execution (p2-175)
  L3 the transition's push is consumed    verified-by-execution (sobj_decode,
                                           20.297 R1 - re-asserted THIS boot)
  L4 a receiver-bearing object exists     unknown (THIS BOOT - the dump)
  L5 ent_recv fires                       unknown (THIS BOOT; NEVER-OBSERVED)
  L6 the peer entity is created           unknown (blocked on the fork encoder,
                                           20.302 contract; lanes in flight)
  L7 a second guardian renders            unknown (20.53 positive control only)

## SETUP (my job; user launches the games)
  1. reset_lobby_claims.sh from the repo root; echo back the deployed
     settings and assert the states above; assert server hash ed43adf1...
  2. Assert client hashes 3cc844c4cdd2fd63 on BOTH machines.
  3. ssh control socket: ssh -M -S ~/.ssh/cm-rig -o ControlPersist=8h -N -f
     rasla@192.168.1.136 (log pull + the rig dump both need it).
  4. Server restart backgrounded - it hangs AFTER succeeding (STATE hard rule).

## ADVERSARIAL PASS: the pre-named outcome tree is 20.296 R3's own, already
## stress-tested by 20.297's execution. The new element (the dump) has a
## validated positive control. Waived with the reviewer's consent recorded
## here; the one unreviewed assumption: "the conversion input exists on the
## machine that transitions" - if the rig's dump shows no vptrs, check the
## MAC's state before concluding (c) (the mac's conversion may be the live
## one; no mac dump tooling exists - noted gap, 20.297 R6).

## DO NOT
  - do not read the ent_* census before the sobj_decode input check
  - do not take the dump BEFORE the transition (scenario-scoping, TOOLS.md
    dump_search trap: a dump answers only states the process entered)
  - do not restart the server mid-run; do not launch from outside the repo root
  - do not modify the client, in any form, for any reason
  - do not enable membership_self_peer_row (C3 retired, user, 20.296 R0)
  - do not treat a rig re-entry hang as a new finding (pre-existing,
    20.300 R6; the dump answers regardless)
