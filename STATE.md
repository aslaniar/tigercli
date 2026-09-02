# STATE - living snapshot

STATUS: live (2026-09-01 14:4x). Verdict + deployed + next + reading order only.
FINDINGS holds the dated entry stack; front detail lives in FRONT_*.md and the
HANDOFF; operational facts live in ENVIRONMENTS.md.

Updated: 2026-09-01 19:4x. *** 20.250 (p2-157): THE c4 FRONT IS DEAD. ~6,100 reader calls
through a sustained paired dwell and the peer's contactable byte is NEVER queried - each
client asks only about itself - while that byte sat at 1 on both machines. 20.245 R3 and
20.246 R6 RETRACTED; the tracking cluster is fully exonerated. Crash discriminator
resolved: self-marking caused p2-156, the probe is clean. THE PROJECT IS NOW ONE FRONT:
cond5, dynamic. PRIOR: *** 20.249 (p2-156): MARKING THE CLIENT'S OWN MACHINE ID
CRASHED THE MAC AND KEPT THE RIG OUT. Reverted; push disabled (c4_mark_push=0 verified).
AND THE PREMISE IS SUSPECT: the new probe shows each client's +0x602C4 reader asks only
about ITS OWN id, so 20.245 R3's "evaluator blocked by c4=0" is likely the self entry
being skipped correctly. PRIOR: *** 20.248 (p2-155): THE CONTACTABLE BYTE IS SETTABLE FROM
THE WIRE - peer row c4 0x00 -> 0x01 on BOTH machines across the type-45 handler call, the
first nonzero +0x602C4 in this project. It changed NOTHING downstream: the reader still
returns 0 (wrong row/pool), no evaluator activation, cond5 unmoved over 300 paired
samples. p2-156 is BEHAVIOURAL - mark every known machine id, not just the peer's.
PRIOR: *** 20.247 (p2-154): THE c4 PUSH SHIPPED AND THE CLIENT
DID NOT TAKE IT. Body delivered + accepted on both clients (after the peer's row
existed) and +0x602C4 never moved: the encoding, transport and row are EXONERATED,
the DISPATCH is refuted. Next = a client hook on the handler + pool dispatcher.
Also 20.247 R8: raising membership_peer_retry_cap STOPS THE RIG LANDING - reverted,
do not repeat. PRIOR: *** 20.246: THE CONSTRUCTION GATE (cond5) IS CLOSED BY
MEASUREMENT. Bit 4 of record+0x38 is NEVER set - 384/384 censused records across both
dumps (p2-146 paired-Tower 192/192 over 6 coherence-tested tables, the PEER record
included), and no writer exists under any static encoding, including the record-handle
convention (0x1404DF500 -> +0x30) closed this session. No fork message can feed it;
any fix there is client-side [AMENDED - see below]. PRIOR VERDICTS, all standing: 20.245 the tracking-row/
latch lifecycle is by-design and NOT a blocker (add -> one release -> latch -> quiet);
the evaluator RUNS and stops on +0x602C4 = 0; 20.242 the tracking feed exists (client
self-heals the row); 20.239/p2-151 the same-region citizen advert shipped and works.
THE USER'S FRAMING GOVERNS (20.238): the client is unmodified retail; every missing
writer is gated on server input the fork does not send. Full narrative: FINDINGS
20.238-20.246 (this file carries verdicts only - DOC GOVERNANCE).

## DEPLOYED (2026-09-01 15:0x - p2-154 ARMED)
   clients        d3809e97f927b228 (mac, 2026-08-31 23:29) - the p2-153 build:
                  track_add / track_fixup / track_set / track_c4 + trackadd and
                  retwatch probes. CORRECTED 2026-09-01: this block previously
                  recorded 9cb220cc9c971035, which is the p2-152 client - it was
                  never updated for the p2-153 deploy. Rig hash unverified since
                  (ssh needs an interactive password); its p2-153 instruments are
                  evidenced by its own p2-153 log lines.
   server exe     4f51581cbd3561c7 - RUNNING (p2-154 deploy 2026-09-01 15:0x,
                  built==deployed, lobby+ladder empty). p2-154 build: the type-45
                  PEER-CONTACT push (activity_peer_contact_encoder +
                  append_peer_contact_notification, call site in the membership
                  push) behind pool_c4_mark_push. Bind line proves both switches
                  parsed: `stage=settings ... c4_mark_push=1 peer_retry_cap=65535`.
                  settings.json diff vs .bak_p2d8_c4mark_20260901_145236 is exactly
                  two lines (+pool_c4_mark_push true, retry cap 2 -> 65535).
                  Rollback: restore that backup; exe+cache .bak_p2d6_*.
   dumps          p2-146 (rig, femu's verified graft-dump target - KEEP) and p2-150
                  (rig, verified-paired reference, PROVENANCE.txt inside) in
                  RE_output/dumps/. p2-149 DELETED (superseded, analysis banked).
   index          RE_output/logindex/p2150.db + p2150.drift.json (mac/rig/server,
                  drift-anchored) - the log evidence for 20.240/20.241; p2-152's
                  logs get their own index after the boot.
   capture        RE_scripts/capture_gameplay_plane.sh (UDP 3097/3074/3075/30976,
                  en0+en13+lo0, route resolve + liveness probe; smoke-tested).
   BOOT HYGIENE: deploy client DLLs BEFORE the user boots (a running process never
   re-reads its image; cost a boot). Restart the server with reset_lobby_claims.sh
   backgrounded (it hangs after succeeding). Use logindex/logq, not grep chains.

## WHERE WE ARE
Session/membership/identity: DONE. Entity-index/slot supply: CLOSED (20.219).
Tracking-row/latch lifecycle: CLOSED, not a blocker (20.245). Construction gate
cond5: CLOSED AS A WIRE FRONT (20.246) - the bit has no writer and is never set;
any fix there is client-side. Peer rendering remains the wall. What is LEFT:
 (1) +0x602C4, the contactable byte - the ONE missing evaluator input, and the
     only remaining blocker with a verified fork-side lever (the type-0x2D body).
     This is the p2-154 boot.
 (2) type-38 ack absence -> the withdraw-unacked-2 cycle (retry-cap switch).
 (3) UNTESTED SINCE 20.208: whether the construction path is required to render a
     peer at all (the local guardian renders with ent_recv/ent_create at ZERO).
     Now the cheapest open question in the project.

## NEXT (per 20.250 - THE c4 FRONT IS DEAD; cond5 IS THE WHOLE PROBLEM)
 p2-157 RESULT: through a sustained paired dwell (302 samples at maskB=0x3) the
 +0x602C4 reader was called ~6,100 times and NEVER ONCE asked about the peer - the
 complete c4query set for the boot is TWO pairs, each client querying only ITS OWN
 machine id (rig:1784, mac:1911). Meanwhile the PEER's byte was set to 1 on both
 machines the whole time (rig:1834, mac:54990) and each client's own row stayed 0x00.
 A working lever on a door nothing opens.
 RETRACTED: 20.245 R3 ("the evaluator was blocked by c4=0" - those reads were the SELF
 entry, where 0 is correct) and 20.246 R6's conclusion that c4 is the peer-activation
 gate (its disassembly reading of the three non-gate probes stands). p2-154/155/156
 were aimed at a byte never consulted for a peer. The tracking cluster is now fully
 EXONERATED, not half-suspected.
 CRASH DISCRIMINATOR RESOLVED: peer-only + the byte-identical p2-156 client =
 stable full dwell. Self-marking caused the p2-156 crash (20.249 confirmed); the
 c4query probe is exonerated (~6,100 calls, no incident).
 HONEST LIMIT (pre-named L5): "no peer query IN THIS SCENARIO", not "none exists".
 *** THE PROJECT IS NOW ONE FRONT. Everything in the tracking/admission cluster is
 closed or exonerated (20.219 slot supply, 20.245 row lifecycle, 20.250 contactable).
 What remains is cond5 - bit 4 of participant record+0x38 - unmoved through every
 measurement: 384/384 dump records, 300 live samples p2-155, 200 more p2-157, bit4=1
 appearing ZERO times ever.
 NEXT: cond5's DYNAMIC front (20.246 R7). Static is exhausted (20.246 R1-R4 incl. the
 record-handle encoding no prior scan covered), and the user's framing governs - the
 client is unmodified retail and rendered peers against Bungie on server input alone,
 so a writer EXISTS and is runtime-registered where static analysis cannot reach.
 THE INSTRUMENT: a write-watch on record+0x38 during a paired dwell. The address is
 already logged live every tick by ptable (table=0x1D3065B8 + i*0x2AC0 + 0x38), so the
 target needs no discovery - only a hardware/page watch or a hook on whatever writes
 the region. Design it against the instrumentation postmortem's rules: log the KEY not
 just the value, gate on novelty not a budget, and pick a control that can actually fire.
 SETTINGS NOW: pool_c4_mark_push TRUE and HARMLESS (peer-only; keep or disable, it
 changes nothing). DO NOT MARK SELF (20.249). DO NOT RAISE the retry cap (20.247 R8).
 TOOL DEBT: reset_lobby_claims.sh cries wolf every run (counts listeners, 30975 binds
 twice); c4query derefs before its dedupe check. Both in the instrumentation postmortem.
 STATE diet debt: ~185 vs 120.

## SUPERSEDED (20.221 - gate 2, still valid, no longer the front)
A) self-only BY DESIGN -> peers arrive by server-mediated replication the fork never
   sends. Front = the gameplay-plane entity message; ent_recv/ent_header/ent_create
   return as the RECEIVER (their two retirements, 20.210 R3 and 20.213 R2, are both
   suspect - they may log zero simply because nothing is sent).
B) the peer's +0x818 should become the local identity under an authority hand-off the
   fork never arranges. Front = what writes +0x818.
DISCRIMINATOR (offline, no boot): the p2-146 dump - compare the peer record 0x66514EC0
against the local 0x665118D0 and find +0x818's provenance.
DUMP: RE_output/dumps/p2-146-paired-tower/ (6.5 GB, both clients in Tower, players 0x3).
SCENARIO-SCOPED, not time-scoped: Tier-1 code/tables reusable until the GAME binary
changes; Tier-2 roster/manager state only valid for THIS scenario (a fork change that
alters what the client receives makes it stale). See 20.221 R5.

## SUPERSEDED FRAMING (do not re-run; full text in FINDINGS)
The 20.220 hunt list (hook the predicate halves, chase [rbx+8] as a wire field,
'which gate stops the loop') is SPENT: 20.221 answered it - gate 2 is an
ownership test and the loop is self-only. The predicate 0x1412AADF0 is NOT an
authority split either (identical toggling on mac and rig, p2-145).

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
RETIRED 20.241 R4: STATIC NAMING of the tracking-feed dispatch type - the feed
   arrives through a registration-table callback invoked from flattened second-.text
   (stack-obfuscated fake-rbp swaps); the dynamic discriminator is the 20.241 R5
   probe (add-site caller RVA during a paired dwell).
RETIRED 20.234: the +0x38 WRITER under every covered static encoding: accessor family
   (0x1404C8750/B30/B50/BA0/BC0 - all call sites readers), all-width disp8 x 30
   participant fns = 0, decomposed-base x 37 fns = 0, 59 stride sites enumerated.
   Second-.text SIB sites remain unattributable (no landmarks) - bounded, not proven.
RETIRED 20.220: slot SUPPLY as the blocker. Chain: loop 0x1413086E0 -> creator
  0x1416EE180 -> 0x14170F190 -> idx_alloc 0x141711D10. It IS on the path, has 145
  free slots, and is never asked - the loop stops at its GATES before creating.
  (Two allocators: per-member index [rbx+8] via 0x140B76E00; entity slot via
  0x141711D10. Both real, different jobs.)
RETIRED 20.219: THE WHOLE ENTITY-INDEX/SLOT-SUPPLY FRONT. The mask is not empty
  (145-150 free, the hysteresis midpoint); zero allocations are attempted with a
  peer present; the 44 creation failures were SELF-allocation during load. Also
  dead: type-28 as the missing message (the transfer needs no token), the
  "assignment unlocks a local fill" model (the sync SENDS, it does not fill), and
  the ordering/race reading (the lifecycle runs 38,596x per boot).
UN-RETIRED 20.221: entity-replication cluster 0x141718510/0x1717EB0/0x1718080.
  BOTH retirements (20.210 R3, 20.213 R2) are suspect - it may log zero because
  nothing sends it a peer. Treat as the RECEIVER candidate, not a dead end.
RETIRED: router-flags gate (20.218). Type-20-as-teardown (20.217 am2). Assignment
  VALUE semantics (20.217). PEER CHANNEL as appearance carrier - client<->client
  pre-packaging REFUTED by pcap (20.196, 20.208 R5); this one is HARD and still
  constrains 20.221 reading (a). Region A appearance fields (20.202).
  Admission-forge (20.170). Road C (20.113-20.144). Staging population (20.191/2).
  svc21=pool request. Full list: FINDINGS dead-end blocks.
PARKED: mac black screen (host-machine-correlated, decoupled from the failure
  loop, 20.213 R3; Ubuntu server move is the clean test) | rx-decode | reason
  hunts | posse fabrication.

## READ FIRST (any session taking over)
  0. FINDINGS 20.238-20.241 (the corrected framing + the admission front, three
     mechanisms deep, all named) then 20.234-20.237 (static closure + the dumps).
     BOOT BRIEFS p2-149/p2-150/p2-151 carry the verified-paired discipline.
  1. AGENTS.md conditional triggers; boot work loads LESSONS pre-boot checklist
     and runs gate_boot.py on the brief.
  2. ENVIRONMENTS.md before ANY deploy/capture/settings edit (trap 18: settings
     are format-sensitive text edits; NIC is not a constant; server recovery;
     RIG<->MAC FILE TRANSFER = tar-over-ssh, NEVER scp/sftp, SHA256 both ends).
  3. Log evidence for the admission front: RE_output/logindex/p2150.db (+ drift
     json) - query with logq.py --aligned.
  4. Captures contain NUL bytes (grep -a); logindex/logq over grep chains.
