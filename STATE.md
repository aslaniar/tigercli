# STATE - living snapshot

STATUS: live (2026-09-03). Verdict + deployed + next + reading order only.
FINDINGS holds the dated entry stack; front detail lives in FRONT_*.md and the
HANDOFF; operational facts live in ENVIRONMENTS.md.

Updated: 2026-09-03 18:0x PDT. *** 20.284 (p2-167): W1 IS CLOSED. The admission guard's
86-byte field now holds the peer's real endpoint - 1,559 samples carrying the RIG's
address inside the MAC's participant slot, which the mac has no local way to compose, so
the bytes are conclusively ours. It was an off-by-one FIELD INDEX, never a dropped
payload: the card had been landing one 86-byte array early (slot+0xEC), and moving the
presence index 10->11 shifted the whole blob by exactly one array with its internal
geometry preserved (+8 into the array, second copy +0x1E). W3 is DOWN (peer reservation
record reached 4/5 by resv call 11). The race fix works: the rig's card published after
3/8 bounded waits, where the old accounting would have withdrawn the peer row for good.
*** W2 IS UNMEASURED, NOT "THE LAST WALL" ***: ent_gate=0 - the guard was never invoked,
so nothing read the card and the cascade thesis remains untested end to end. THE FRONT IS
NOW UPSTREAM OF W2: what makes cond5 pass on the SERVER's terms (20.230's question, never
answered; the only known opener is the client-side poke, which cannot ship). After that:
W2, then entity construction - never tested, and the 09-02 postmortem argues that is where
the front actually lives.
VERDICT TRAIL (full text in FINDINGS):
  20.284 W1 closed, W3 down, W2 unmeasured; rig drop = transport reset (10054), NOT our
  body (888 bodies accepted, zero decode failures); the peer key changing to a machine-id
  form is a SYMPTOM of a dying session (one boot only) and the fail-closed refusal is
  correct - a widening was written and reverted (R7). 20.283 the card DOES reach the
  slot, one array early; the server had been sourcing it from the region's activity-host
  descriptor (same address both directions) - fixed to echo the peer's own connect-time
  bytes. RETRACTED in 20.283 R0: there was no boot at 2026-09-03 16:44 (that archive is
  p2-165 still running; the widened DLL was staged 6 s after it), and 20.282's "compose hop
  does not carry it" - it always carried them, into the neighbouring field.
  20.280 the three 86-byte arrays + full mask machinery. 20.238 USER'S FRAMING GOVERNS.

## DEPLOYED (2026-09-03 - p2-167 ran on these; R7 fix built but NOT deployed)
   clients        BOTH 0ff6911ff5a654ae - slot_dump widened + liveness line. Rollbacks
                  *.bak_p2d7_20260903_174656 (mac) / _174709 (rig).
   server         d7a7dc9be138b412 RAN p2-167 and its BEHAVIOUR IS CURRENT - the R7
                  widening was reverted, so the rebuilt exe is behaviourally identical.
                  Nothing is owed to the next run.
   settings       server membership_peer_transport_identity=true,
                  roster_peer_participation=true, peer_retry_cap=2 (the wait cap is
                  separate by design). Clients gate_poke=0 BOTH (verified on disk);
                  gate_wwatch DR/VEH/suspend retired at COMPILE TIME.
   archives       p2-167 RE_output/logs/20260903_175317_p2-167 (all three logs);
                  p2-166 .../20260903_173450_p2-166. Briefs BOOT_BRIEF_p2-166/167 (both
                  GATE PASS).

## WHERE WE ARE
Session/membership/identity DONE; slot supply, row lifecycle, contactable byte,
gate-byte writer, staging publish lever all CLOSED (mechanism in FINDINGS). Of the
four-wall stack: W1 CLOSED and W3 DOWN (20.284), W4 instruments proven. W2 is
UNMEASURED behind cond5, which is now the front - see NEXT.

## NEXT
  THE FRONT: make cond5 pass WITHOUT a client write. 20.285 read the whole chain: cond5 is
  a PURE DATA READ (six instructions, no second path), so only the byte can change the
  outcome, and nothing computes it - it arrives in a wholesale image copy. THE ONE UNRUN
  EXPERIMENT: hook the copier 0x1403CB340 and log the restore SOURCE's gate bytes
  (designed at 20.254 R3; cancelled with p2-159 only because the DR watch riding along
  crashed both machines - that watch is retired at compile time now, and this probe is a
  plain detour). Build that next.
  KNOW BEFORE RESUMING (20.285 R4): a passing gate CONSTRUCTS NOTHING. Its return feeds one
  AND-accumulator whose only consumer is a diagnostic string builder. The goal survives
  because the guard CLAIMS as a side effect (card -> find-or-create -> stops the disown
  sweep). The probe's old "would-construct" label was never verified and is corrected.
  Also: the walk SKIPS SELF, so the local player is not a control for it.
  THEN: W2 (the peer's mask bit) becomes measurable, and the cascade thesis of 20.280
  gets its first end-to-end test.
  THEN: entity construction - untested; levers are 20.208 R6 (world_population -> type-7
  sobject + type-52 epoch) and 20.213 R1 (lease size fired the attempt on type-12 pushes).
  OPEN (do NOT close by loosening the key test): why does the published peer identity
  change to a machine-id form while a session is failing? Read the roster/foreign-member
  path (20.284 R7).
  BEFORE THE NEXT PAIRED RUN: relaunch BOTH clients (a staged DLL that is never loaded
  cost a whole cycle - 20.283 R0).

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
