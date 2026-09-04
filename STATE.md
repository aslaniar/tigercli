# STATE - living snapshot

STATUS: live (2026-09-03). Verdict + deployed + next + reading order only.
FINDINGS holds the dated entry stack; front detail lives in FRONT_*.md and the
HANDOFF; operational facts live in ENVIRONMENTS.md.

Updated: 2026-09-03 19:3x PDT. *** 20.286: W2 IS ANSWERED AND IT IS NOT A BIT THAT CAN BE
SET. The guard's required bit is STAMPED AT RECORD CREATION from the container the record is
born into. Records carrying it never climb the state ladder; records that climb never carry
it - and on the rig the SAME peer identity sits in BOTH populations at once (one with the
bit, stuck at the bottom; one climbing, without it). p2-170 ran the guard 1,190 times
against a correct card and the peer's bit never moved off 0. No claim, climb or poke can
grant it. THE FRONT IS RECORD CREATION: what determines the container a peer's reservation
record is created in, and can the server influence it. Whether that is the same question as
entity construction is NOT asserted - both are creation questions; scope the next session as
CREATION (record + entity) rather than assume a boundary.
EARLIER TODAY: W1 CLOSED and W3 DOWN (20.284). Three real server defects fixed - the peer
card was sourced from the region's activity-host descriptor (same address both directions),
landed one 86-byte array early, and a race meant one of two players never got sent one.
VERDICT TRAIL (full text in FINDINGS):
  20.286 W2 birth-set, front = record creation; retracts my p2-170 "the claim sticks"
  (the field read as `mask` IS the guard's word - a different bit was retained, not a claim).
  20.285 cond5 is a pure data read with no second path; the walk SKIPS SELF; a passing gate
  CONSTRUCTS NOTHING (its return feeds a diagnostic string) - it claims as a side effect.
  20.284 W1 closed: the guard's field holds the peer's real endpoint, 1,559 samples.
  20.283 the card reaches the slot one array early; RETRACTS the "compose hop drops it"
  reading and the phantom 16:44 boot. 20.238 USER'S FRAMING GOVERNS.

## DEPLOYED (2026-09-03 - p2-171 ran on these; nothing is owed to the next run)
   clients        BOTH a96a6a70f578fc40 - resv_rec answers W2 on one line
                  (reqA/setA/reqB/setB). Rollbacks .bak_p2d7_20260903_1911*.
   server         6f018fcd42d309a4 - 8/8 harness gates rc=0.
   settings       server membership_peer_transport_identity=true,
                  roster_peer_participation=true. Clients gate_poke=0 BOTH (armed only for
                  p2-170/p2-171, reverted and read back after each). gate_wwatch
                  DR/VEH/suspend retired at COMPILE TIME.
   archives       p2-170 .../20260903_190455_p2-170, p2-171 .../20260903_191821_p2-171
                  (logindex p2170.db / p2171.db). Briefs p2-166/167/168/170/171, all GATE PASS.

## WHERE WE ARE
Session/membership/identity/transport all DONE. Of the four-wall stack: W1 CLOSED, W3 DOWN,
W4 instruments proven, and W2 DISSOLVED rather than passed - it was never a settable bit.
Everything fixed to date concerns a peer record's CONTENTS. Nothing yet touches how that
record is CREATED, which is where the remaining blocker lives.

## NEXT (handoff: HANDOFF_2026-09-03_CREATION.md)
  THE ONE QUESTION: what determines the container a peer's reservation record is created in?
  The guard's bit is birth-set from that container, so this is the only reachable lever.
  Start from 20.286 R3's two-population evidence, then the record creator.
  DO NOT: spend boots poking cond5 (20.286 R4 - nothing downstream of cond5 reaches a
  birth-set bit); or plan "make the guard claim it so the bit follows" (p2-170 tested that).
  THEN/ALONGSIDE: entity construction. Levers 20.208 R6 (world_population -> type-7 sobject
  + type-52 epoch) and 20.213 R1 (lease size fired the attempt on type-12 pushes), both
  untested. Treat creation as ONE front until evidence splits it.
  PARKED: the gate-byte provenance (20.285 R6 / 20.286 R4) - the copier is ruled out as its
  source by direct instrumentation over three boots.

 pool_c4_mark_push TRUE and HARMLESS.
 DO NOT MARK SELF (20.249). DO NOT RAISE the retry cap (20.247 R8).
 TOOL DEBT: reset_lobby_claims.sh cries wolf; c4query derefs before dedupe.

## SUPERSEDED (20.221 gate-2 framing; dump pointer lives in DEPLOYED)
 Scenario-scoped, not time-scoped (20.221 R5): Tier-1 code/tables reusable until
 the GAME binary changes; Tier-2 roster/manager state only valid for THIS scenario.

## HARD RULES (earned; each cost a boot or a day)
  - RESET THE SERVER BETWEEN RUNS (reset_lobby_claims.sh, backgrounded).
  - THE CLIENT IS NEVER MODIFIED - THE SERVER MUST ACCOMPLISH EVERYTHING (user,
    2026-09-02; full statement in AGENTS.md). No .text patching AND no client-side
    writes into game data. Client writes are throwaway DIAGNOSTICS only, reverted at
    the end of the boot. NO guessed interface ordinals. Census FIRST.
  - EVERY hook RVA through verify_hook_rvas.py before a boot (it catches
    added/dropped digits - both have happened).
  - Bundle OBSERVATION freely; BEHAVIOUR only behind a settings switch.
  - CENSUS BEFORE FILTER. BUDGET OBSERVERS PER EVENT CLASS.
  - SCAN AFTER THE WRITE. PREFER LANDMARKS OVER ARITHMETIC.
  - Wire fields: raw fields keep byte order, VALUE fields are MSB-first.
  - One long-running/ssh action per shell call; it hangs AFTER succeeding.
  - Solo control boot before any two-machine run.
  - Boot-test scope is fixed at brief approval; instrument tweaks wait.

## DEAD ENDS - DO NOT RESUME (mechanism in FINDINGS)
 RETIRED: tracking-feed dispatch naming (20.241) | +0x38 writer encodings (20.234) |
    slot SUPPLY as scarcity (20.220) | router-flags gate (20.218) | type-20 teardown +
    assignment VALUE semantics (20.217) | PEER CHANNEL as appearance/bulk carrier
    (20.196/20.208 R5 - NOT for continuous position/state) | region A appearance
    fields (20.202) | admission-forge (20.170) | road C (20.113-144) | staging
    population (20.191/2) | svc21=pool request. Full list: FINDINGS dead-end blocks.
 RE-OPENED (postmortem THE-WRONG-QUESTION): 20.219 entity front - the client NEVER
    ASKS; creation not reached. The only known server-side lever on entity creation =
    20.208 R6 (world_population -> type-7 sobject + type-52 epoch) + 20.213 R1 (lease
    size setting fired the attempt on type-12 pushes). THAT IS THE FRONT after the
    walls fall. UN-RETIRED 20.221: entity-replication cluster RECEIVER candidate.
 PARKED: mac black screen | rx-decode | reason hunts | posse fabrication.

## READ FIRST (any session taking over)
  0. FINDINGS 20.283-20.284 FIRST (W1 closed, the two retractions, the front's move to
     cond5), then 20.238-20.257 for the verdict stack it rests on (20.252-20.256 =
     gate-byte writer, staging layer, type-12 lever). Postmortem 09-02 (U18).
  1. AGENTS.md conditional triggers; boot work loads LESSONS pre-boot checklist
     and runs gate_boot.py on the brief.
  2. ENVIRONMENTS.md before ANY deploy/capture/settings edit (trap 18: settings
     edits are format-sensitive; RIG<->MAC transfers = tar-over-ssh, never scp).
  3. Log evidence: RE_output/logindex/p2150.db; logq.py --aligned. Captures have
     NUL bytes (grep -a); logindex/logq over grep chains.
