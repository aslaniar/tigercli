# STATE - living snapshot

STATUS: live (2026-09-01). Verdict + deployed + next + reading order only.
FINDINGS holds the dated entry stack; front detail lives in FRONT_*.md and the
HANDOFF; operational facts live in ENVIRONMENTS.md.

Updated: 2026-09-01 22:04 PDT. *** 20.250 (p2-157): THE c4 FRONT IS DEAD. ~6,100
reader calls through a sustained paired dwell and the peer's contactable byte is
NEVER queried - each client asks only about itself - while that byte sat at 1 on
both machines. 20.245 R3 and 20.246 R6 RETRACTED; the tracking cluster fully
EXONERATED; crash discriminator resolved (self-marking caused p2-156, the
c4query probe is clean).
THE PROJECT IS NOW ONE FRONT: cond5, dynamic. Standing verdicts behind it:
20.246 cond5 closed as a WIRE front (bit 4 of participant record+0x38 has NO
writer under any covered static encoding; 384/384 dump records + 500 live
samples, bit4=1 appeared ZERO times ever); 20.245 tracking-row/latch lifecycle
by-design, not a blocker; 20.242 the tracking feed exists (client self-heals the
row); 20.239 the same-region citizen advert ships and works; 20.219 slot supply
closed (145 free slots, never asked). THE USER'S FRAMING GOVERNS (20.238): the
client is unmodified retail and rendered peers against Bungie on server input
alone, so a writer EXISTS and is runtime-registered where static analysis cannot
reach. Full narrative: FINDINGS 20.238-20.250 (verdicts only here - GOVERNANCE).

## DEPLOYED (2026-09-01 15:0x - p2-154 ARMED)
   clients        d3809e97f927b228 (mac, 2026-08-31 23:29) - the p2-153 build:
                  track_add/track_fixup/track_set/track_c4 + trackadd/retwatch
                  probes. Rig hash unverified since (ssh needs a password); its
                  p2-153 instruments are evidenced by its own log lines.
   server exe     4f51581cbd3561c7 - RUNNING (p2-154 deploy, built==deployed,
                  lobby+ladder empty). The type-45 PEER-CONTACT push behind
                  pool_c4_mark_push. Bind line proves both switches: `c4_mark_push=1
                  peer_retry_cap=65535`. Rollback: settings .bak_p2d8_c4mark_20260901_145236;
                  exe+cache .bak_p2d6_*.
   dumps          p2-146 (rig, femu's verified graft-dump target - KEEP) and p2-150
                  (rig, verified-paired reference, PROVENANCE.txt inside), in
                  RE_output/dumps/. p2-149 DELETED (superseded, analysis banked).
   index          RE_output/logindex/p2150.db + p2150.drift.json (the p2-150
                  evidence); p2-152+ logs get their own index after the boot.
   capture        RE_scripts/capture_gameplay_plane.sh (UDP 3097/3074/3075/30976,
                  en0+en13+lo0, route resolve + liveness probe; smoke-tested).
   BOOT HYGIENE: deploy client DLLs BEFORE the user boots (a running process never
   re-reads its image; cost a boot). Restart the server with reset_lobby_claims.sh
   backgrounded (it hangs after succeeding). Use logindex/logq, not grep chains.

## WHERE WE ARE
Session/membership/identity: DONE. Entity-index/slot supply: CLOSED (20.219).
Tracking-row/latch lifecycle: CLOSED (20.245). Contactable byte: DEAD (20.250).
Construction gate cond5: CLOSED AS A WIRE FRONT (20.246) - static is exhausted
(R1-R4, incl. the record-handle encoding no prior scan covered); the fix is
dynamic. Peer rendering remains the wall. What is LEFT:
 (1) cond5's DYNAMIC front - the write-watch (see NEXT).
 (2) type-38 ack absence -> the withdraw-unacked-2 cycle (retry-cap switch).
 (3) UNTESTED SINCE 20.208: whether the construction path is required to render a
     peer at all (the local guardian renders with ent_recv/ent_create at ZERO).
     Now the cheapest open question in the project.

## NEXT (per 20.250 - THE c4 FRONT IS DEAD; cond5 IS THE WHOLE PROBLEM)
 THE INSTRUMENT: a write-watch on record+0x38 during a paired dwell. The address
 is already logged live every tick by ptable (table=0x1D3065B8 + i*0x2AC0 + 0x38),
 so the target needs no discovery - only a hardware/page watch or a hook on
 whatever writes the region. Design against the instrumentation postmortem's
 rules: log the KEY not just the value, gate on novelty not a budget, and pick a
 control that can actually fire.
 SEQUENCING NOTE (2026-09-01 review): open question (3) is cheaper than the
 watch and could invalidate its premise (a peer rendered without the
 construction path makes the watch a non-blocker hunt). Run the (3)
 discriminator - partly offline via the p2-146 dump - BEFORE arming the watch.
 SETTINGS NOW: pool_c4_mark_push TRUE and HARMLESS (peer-only; keep or disable).
 DO NOT MARK SELF (20.249). DO NOT RAISE the retry cap (20.247 R8).
 TOOL DEBT: reset_lobby_claims.sh cries wolf every run; c4query derefs before its dedupe check (instrumentation postmortem). STATE diet debt: cleared 2026-09-01.

## SUPERSEDED (20.221 gate-2 framing; dump pointer lives in DEPLOYED)
 Scenario-scoped, not time-scoped (20.221 R5): Tier-1 code/tables reusable until
 the GAME binary changes; Tier-2 roster/manager state only valid for THIS scenario.

## HARD RULES (earned; each cost a boot or a day)
  - RESET THE SERVER BETWEEN RUNS (reset_lobby_claims.sh, backgrounded).
  - NO .text patching; NO guessed interface ordinals. Census FIRST.
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
 RETIRED 20.241 R4: static naming of the tracking-feed dispatch type - the
    dynamic discriminator is the 20.241 R5 probe (add-site caller RVA).
 RETIRED 20.234: the +0x38 writer under every covered static encoding - accessor
    family all readers; disp8/SIB/decomposed-base x participant fns = 0; 59 stride
    sites; second-.text SIB unattributable (bounded, not proven).
 RETIRED 20.220: slot SUPPLY as the blocker (loop stops at its GATES; two real
    allocators, different jobs).
 RETIRED 20.219: the whole entity-index/slot-supply front (also dead: type-28 as
    the missing message, assignment-unlocks-fill, ordering/race reading).
 UN-RETIRED 20.221: entity-replication cluster - RECEIVER candidate, see above.
 RETIRED: router-flags gate (20.218) | type-20 teardown (20.217 am2) |
    assignment VALUE semantics (20.217) | PEER CHANNEL as appearance carrier
    (pcap-refuted 20.196, 20.208 R5 - HARD, still constrains 20.221 reading (a))
    | region A appearance fields (20.202) | admission-forge (20.170) |
    road C (20.113-20.144) | staging population (20.191/2) | svc21=pool request.
    Full list: FINDINGS dead-end blocks.
 PARKED: mac black screen (Ubuntu server move is the clean test) | rx-decode |
    reason hunts | posse fabrication.

## READ FIRST (any session taking over)
  0. FINDINGS 20.238-20.241 (corrected framing + admission front) then
     20.242-20.250 (tracking cluster closure + the c4 retraction). BOOT BRIEFS
     p2-149/p2-150/p2-151 carry the verified-paired discipline.
  1. AGENTS.md conditional triggers; boot work loads LESSONS pre-boot checklist
     and runs gate_boot.py on the brief.
  2. ENVIRONMENTS.md before ANY deploy/capture/settings edit (trap 18: settings
     are format-sensitive text edits; NIC is not a constant; server recovery;
     RIG<->MAC FILE TRANSFER = tar-over-ssh, NEVER scp/sftp, SHA256 both ends).
  3. Log evidence: RE_output/logindex/p2150.db (+ drift json) - query with
     logq.py --aligned.
  4. Captures contain NUL bytes (grep -a); logindex/logq over grep chains.
