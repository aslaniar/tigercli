# STATE - living snapshot

STATUS: live (2026-09-01). Verdict + deployed + next + reading order only.
FINDINGS holds the dated entry stack; front detail lives in FRONT_*.md and the
HANDOFF; operational facts live in ENVIRONMENTS.md.

Updated: 2026-09-02 12:1x PDT. *** 20.254 (offline): THE WRITE-BACK IS REAL - the p2-158
hit geometry (table+0x38 AND table+0x2AF8) proves a full-table RESTORE (dest=table) ran at
landing through an obfuscated thunk (0x1403CB790 -> jmp 0x1403CB340; source provenance
behind the second-.text wall). 20.246's client-side "no writer" is superseded in KIND:
the writer is a bulk SSE copy dispatched from obfuscated code. p2-159 probe DESIGNED:
hook 0x1403CB340 (clean pdata fn) logging dest/src + the SOURCE's per-record gate bytes
+ caller RVA; paired dwell shows whether the restore source ever carries bit4=1 on the
non-authority machine. Ship with wwatch capture-then-quiet. NO BOOT SPENT.
PRIOR: *** 20.253 (offline): THE IMAGE IS A STAGING SNAPSHOT -
pool ctor PUBLISHES the fresh table into a per-activity staging object (0x1403CB340:
table->X+0x80, flag X+0x70; direction CORRECTED from 20.252), gated by THE 20.220
authority predicate 0x1412AADF0 (pools built on its FALSE side). Snapshot manager
0x140C21FE0 is flattened (obfuscator wall - do not chase); 21 checkout sites: pool
query paths, ctor, and manager clusters 0x1416BC33E/0x141741130 (4 snapshots ->
0x140092D40). THE QUESTION: which consumer WRITES participant-record data back into
table/snapshot from OUTSIDE (authority/server) - (a) read 0x140092D40 + 0x1416BC33E
offline, or (b) one probe boot: hook 0x1403CB340 both machines + watch the SNAPSHOT's
gate byte (capture-then-quiet). Fork has NO participant-table model server-side - if
snapshot deltas ride the pool protocol, the fork must build it.
PRIOR: *** 20.252 (p2-158 canary): THE GATE-BYTE WRITER IS FOUND -
the participant records (gate bytes included) are copied as ONE WHOLESALE TABLE IMAGE
handed to the pool ctor 0x1404F77D0 ([rsp+0x70]) -> 0x1403CB340 (0x59290 stack backup +
image copy) -> 0x1404DF6A0 copier (0xB24 x 0x80 SSE loop, .pdata gap). NO client code
computes bit 4; the masks ride in the same image. NEW FRONT: who sources the image
(ctor caller 0x140BFE3F8, static tables 0x141C19A70/80 + manager array)? If the image is
server-fed pool state, the FORK controls cond5 - set bit4 in its participant records
(INFERRED, verify first). Watch status: rig pipeline PROVEN (selftest ok x3); the captures
landed (0x00->0x00 both windows); rig then died silently ~3k ticks later (AV, garbage
context, triage dump useless). DO NOT re-boot the watch as-is: next watch boot ships
capture-then-quiet disarm. Mac cannot watch (Wine/Rosetta, selftest FAIL permanent).
PRIOR: *** 20.251 (offline, no boot): OPEN QUESTION (3) ANSWERED -
THE cond5-GATED RECEIVER IS REQUIRED TO RENDER A PEER. The replication cluster has
exactly ONE entry (ent_recv <- ent_header <- ent_create; single caller at every hop,
oracle-validated E8/E9 + ptrs + moffs64) and that entry is the receiver object - which is
never constructed without cond5. The only other player-entity door, the creation loop
0x1413086E0, is self-only BY DESIGN: gate 2 is an ownership test and the owner field
carries each member's OWN identity (mac live: peer record owned by the rig's handle; rig
dump: rec0=RIG / rec1=MAC, symmetric). THE WRITE-WATCH ON record+0x38 IS VALIDATED.
PRIOR: *** 20.250 (p2-157): THE c4 FRONT IS DEAD. The peer's contactable byte is NEVER
queried (~6,100 reader calls, each client asks only about itself); 20.245 R3 and
20.246 R6 RETRACTED; tracking cluster fully EXONERATED.
cond5 IS THE ONE FRONT, AND IT IS VALIDATED (20.251). Standing verdicts behind it:
20.246 cond5 closed as a WIRE front (bit 4 of participant record+0x38 has NO
writer under any covered static encoding; 384/384 dump records + 500 live
samples, bit4=1 appeared ZERO times ever); 20.245 tracking-row/latch lifecycle
by-design, not a blocker; 20.242 the tracking feed exists (client self-heals the
row); 20.239 the same-region citizen advert ships and works; 20.219 slot supply
closed (145 free slots, never asked). THE USER'S FRAMING GOVERNS (20.238): the client
is unmodified retail and rendered peers against Bungie on server input alone, so a
writer EXISTS and is runtime-registered where static analysis cannot reach. Full
narrative: FINDINGS 20.238-20.251 (verdicts only here - GOVERNANCE).

## DEPLOYED (2026-09-01 23:4x - p2-158 WIRE-WATCH, mac ONLY - rig pending ControlMaster)
   clients        BOTH: 2952c2640147773e (2026-09-02 11:3x) - p2-159: pubrest hook
                  (0x1403CB340 publish/restore observer + one-shot source-image dump)
                  + wwatch capture-then-quiet + VEC consumption-rule fix (any #DB from
                  our DR addresses is consumed - closes the post-quiet unhandled-#DB
                  hole; adversarial review NOT-READY -> all 7 findings fixed).
                  BOOT_BRIEF_p2-159.md GATE PASS. Rollbacks: mac .bak_p2d7_20260901_233724
                  chain, rig .bak_p2d7_20260902_112956. Canary: rig solo first (selftest
                  ok + pubrest lines); mac wwatch stays FAIL-by-platform (Rosetta).
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
dynamic. QUESTION (3) ANSWERED (20.251): the construction path IS required - the
replication cluster's single entry is the receiver, and the local loop is
self-only by design. Peer rendering remains the wall. What is LEFT:
 (1) cond5's DYNAMIC front - the write-watch (see NEXT). Validated: no
     alternate door exists for a peer entity.
 (2) type-38 ack absence -> the withdraw-unacked-2 cycle (retry-cap switch).

## NEXT (per 20.250 + 20.251 - cond5 IS THE WHOLE PROBLEM, AND THE WATCH IS VALIDATED)
 THE INSTRUMENT: a write-watch on record+0x38 during a paired dwell. The address
 is already logged live every tick by ptable (table=0x1D3065B8 + i*0x2AC0 + 0x38),
 so the target needs no discovery - only a hardware/page watch or a hook on
 whatever writes the region. Design against the instrumentation postmortem's
 rules: log the KEY not just the value, gate on novelty not a budget, and pick a
 control that can actually fire.
 SETTINGS NOW: pool_c4_mark_push TRUE and HARMLESS (peer-only). DO NOT MARK SELF (20.249). DO NOT RAISE the retry cap (20.247 R8).
 TOOL DEBT: reset_lobby_claims.sh cries wolf; c4query derefs before dedupe (instrumentation postmortem).

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
