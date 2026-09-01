# STATE - living snapshot

STATUS: live (2026-08-31 22:1x). Verdict + deployed + next + reading order only.
FINDINGS holds the dated entry stack; front detail lives in FRONT_*.md and the
HANDOFF; operational facts live in ENVIRONMENTS.md.

Updated: 2026-08-31 22:1x. *** THE ADMISSION FRONT IS FULLY MAPPED, THREE MECHANISMS
DEEP, WITH THE MISSING SERVER ITEMS NAMED. Chain: (1) 20.234 closed every static
+0x38 writer; (2) 20.236/20.237 dumps proved HOST/JOINER asymmetry - the joiner's
peer record never ACTIVATES (state dword 0 vs local 5), no maskB bit; (3) 20.239
named the missing server item #1: the fork SKIPS the peer's citizen advertisement in
the same-region (shared-bubble) case; (4) p2-151 fixed that behind
membership_peer_same_region_advert (WORKS - peer_citizen=1) but exposed two more:
20.240 - (a) the client never ACKs (zero type-38) so the retry cap (=2) withdraws
the peer after 2 bodies (4112->3899-forever), and (b) "no tracking data" - the
client's machine-id-keyed array at pool+0x602BC has NO PEER ROWS, and that feed is
a SEPARATE missing item; (5) 20.241 mapped the array completely: adders named
(0x1404F4980 canonical / 0x1404F7710 self-heal), the genuine feed arrives through a
registration-table callback from flattened second-.text - dispatch type NOT
statically nameable. THE USER'S FRAMING GOVERNS (20.238): the client is unmodified
retail; every missing writer is gated on server input the fork does not send.

## DEPLOYED (2026-08-31 21:1x)
  server exe     e486ab77b071ea9e - RUNNING, sessions:[]. p2-151 build: NEW SETTING
                 server.gameplay.membership_peer_same_region_advert (default FALSE,
                 currently TRUE) - same-bubble peer advertisements build against the
                 region-bound shared host row. Rollback: flip the switch, no rebuild.
                 settings.json diff is exactly one line; backup at /tmp/settings.json
                 .bak_same_region (and *.bak_p2d6_* for exe+cache).
  clients        46b294b76e681704 (mac+rig, 2026-08-31 19:0x) - p2-149 build: ptable
                 probe self=<idx>/rec8=/selfRef= fields. No hook changes since.
  dumps          p2-146 (rig, femu's verified graft-dump target - KEEP) and p2-150
                 (rig, verified-paired reference, PROVENANCE.txt inside) in
                 RE_output/dumps/. p2-149 DELETED (superseded, analysis banked).
  index          RE_output/logindex/p2150.db + p2150.drift.json (mac/rig/server,
                 drift-anchored) - the log evidence for everything in 20.240/20.241.
  capture        RE_scripts/capture_gameplay_plane.sh (UDP 3097/3074/3075/30976,
                 en0+en13+lo0, route resolve + liveness probe; smoke-tested).
  BOOT HYGIENE: deploy client DLLs BEFORE the user boots (a running process never
  re-reads its image; cost a boot). Restart the server with reset_lobby_claims.sh
  backgrounded (it hangs after succeeding). Use logindex/logq, not grep chains.

## WHERE WE ARE
Session/membership/identity: DONE. Entity-index/slot supply: CLOSED, not a
blocker (20.219). Peer rendering: the wall, now mapped three mechanisms deep
(see Updated block). The p2-151 fix (same-region advert) is LIVE and verified;
the remaining blockers are the type-38 ack absence and the tracking-data feed.

## NEXT (per 20.241 - the tracking feed is REACHED, its dispatch is flattened)
 p2-151 verdict + 20.240 mechanisms stand. The static hunt is DONE: the +0x602BC
 tracking array is filled per-ENTITY through a registration-table callback invoked
 from flattened second-.text code (20.241 R4) - the dispatching message type cannot
 be named statically. The contact/proximity evaluator 0x1410C3F40 (0xE000 class ==
 0x2000, distance check) gates the entry: tracking rows make a peer CONTACTABLE.
 THE WORK (dynamic, one boot): probe 0x1404F4980 (canonical adder, in-gap, unpdata'd
 - verify_hook_rvas will flag it NOT-CODE; hook the CALLERS 0x140C18089/0x140C180C2/
 0x140C1830C instead, all inside .pdata fn 0x140C17E40) logging caller-RVA +
 machine-id arg during a paired dwell. The caller RVA separates the genuine feed from
 the self-heal; retail lines 194/195 timestamp the fixup. Then: type-38 ack + the
 fixup-release decide whether the fork sends a NEW message or populates an existing
 one. FALLBACK unchanged (20.238): stage-tray client-side write, host side.

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
