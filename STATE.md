# STATE - living snapshot

STATUS: live (2026-08-29 ~00:5x; prior text = git history. FINDINGS holds the dated
entry stack; this file holds verdict + deployed + next + reading order. Operational
/ platform / deploy facts moved to ENVIRONMENTS.md in the 08-28 governance diet.)

Updated: 2026-08-30. *** THE PROFILE PLUMBING IS DONE - SYMMETRIC, TWO MACHINES,
VERIFIED BY EXECUTION (20.194). *** Each client runs the profile apply helper on the OTHER
machine's player row, from the wire, through the unmodified client path (mac index=1 n=17,
rig index=1 n=24, both with the write detour DISARMED). The server composes 655 two-player
bodies; both clients decode and apply them.
THE UNLOCK WAS ONE BUG: region B carries FOUR presence bits and our writer emitted ONE, so
every field after it read three bits early and the trailing state hash overran the body
(20.188 -> 20.189). Block is now 181 bits.
WHAT IS NOT DONE: the block is EMPTY - region A is 232 zero bytes by construction. No name,
no identity, no appearance crosses yet. The pipe is proven; it carries nothing.
THE NEXT FRONT IS A DIFFERENT DATA FAMILY. Appearance is character_record
(middleware/datagen/character_record/appearance/: art stages, material pairs = shaders and
ornaments), NOT the session membership block (region A = identity, region B = a second
name). Serving a PEER's character record is blocked structurally: the snapshot path picks
its account from the CONNECTION and NO root->account resolution exists tree-wide (20.173).
That gap is what stands between here and two rendered guardians.
RETRACTED, MINE (20.191/20.192): the whole staging-population lane - the apply's NULL third
argument is NORMAL, not an uninitialised slot, and substituting for it SUPPRESSED the
helper. Detour retained, DISARMED, default false.
FOUR CAP/ROTATION FAILURES cost evidence this session (20.187 R5, 20.190, 20.193 R5). Fix
shipped: observer budgets keyed per (caller class, row index).
NEXT: (1) real CONTENT in the block - the name cipher is complete (20.179), then the
harvested sheet; this is the cheap rung and it proves content travels, not just shape.
(2) the character_record root->account gap - the real remaining blocker, and it is server
source work, not RE. (3) whether a peer's appearance rides the client<->client channel
instead (never decoded) - decide this BEFORE building (2), or the work may be wasted.
READ: FINDINGS 20.194, 20.193, 20.192, 20.191, 20.190, 20.189, 20.188 - newest first.

## DEPLOYED (2026-08-30, p2(117) staged - boot pending)
  server exe   `649c8da9f0e501fc`: region B written as FOUR presence bits, not one
               (the p2(116) decode failure, 20.188). Block 178 -> 181 bits. All seven
               deploy gates passed. publish_player_profile TRUE; retry-cap 2.
               NOTE: STATE's old `e41d5a92b07d20ab` matched no file on disk under any
               digest - that record was wrong; this hash is measured.
  MAC client DLL `f6fee86c573051a7`: decoder_trace with the decoder RETURN value, the
               post-decode struct dump and row candidates, plus the staging substitution
               detour DISARMED (client.staging_populate=false). Relink of p2(116)'s
               3e52bf70aaaa5a3e; no client source change.
  RIG client DLL `45ef17f93b901db9` (unchanged, no trace instruments).
  brief        BOOT_BRIEF_p2-117.md (GATE PASS, literals verified in the deployed DLL).
  artifacts    RE_output/captures/20260829_225512_p2-116/ (the ret=0 capture, all four
               logs archived); captures/p2-115_flagon_wedge/ (pcaps only - its client
               log was lost, see 20.187 R5).
  ROLLBACK: publish_player_profile=false (settings flip, no rebuild); prior exe as
            *.bak_p2d6_<stamp>; prior DLLs as steam_api64.dll.bak_p2d7_<ts>.

## THE VERDICT - ROAD C IS CLOSED (2026-08-28). The client walks its own
managed-session member table, not BAP membership. Narrative: FRONT_public-host-chain.md,
FINDINGS 20.113-20.144, HANDOFF_2026-08-27_ROAD-C.md.

## WHERE WE ARE
Session / activity / transport: DONE and symmetric (20.170 R1-R3, 20.172). Appearance:
NOT DONE, and the cause is named in code we own (20.173 R5). Next work is SERVER-SIDE
profile authoring, gated behind three unknowns 20.173 lists - region B's 136-byte
layout is UNREAD, and nothing establishes that setting the present bit with a malformed
block is better than leaving it clear (the apply's one flag gates A + B + tail together).
`foreign=` is NOT a peer diagnostic: it is `activityJoinedForeignSession`, never
assigned anywhere in the tree (6 reads, 0 writes) - a dead flag (20.171 R1, which
stands).
OPEN, recorded not chased: `peer_advert` reports `peer_citizen=1` ONLY on the 8
`result=built` lines where regions DIFFER (48 vs 56); all 62 same-region lines report 0.
A second activity soid `0x9EAA300100200004` appears alongside `...0001`. Public bubble
reservation still `0` slots (20.132), now measured with two clients co-located.
RIG BLACK SCREEN: USER-CONFIRMED PRE-EXISTING ("it was always like that") and it
reproduces SOLO before any peer joins. Presentation only - inventory opens, log keeps
pumping, ZERO errors. It is a CONSTANT across p2(110)/p2(111), not a signal. Do not
spend a paired boot on it.

## HARD RULES (earned 08-26/27)
  - NO .text patching; NO interface slot bound by a guessed ordinal. Census FIRST
    (LESSONS 18). A measured call outranks a published header (20.100/20.103).
  - EVERY hook RVA goes through `RE_scripts/verify_hook_rvas.py` before a boot. A
    module-range check passes on a WRONG address and the detour then never fires
    (20.173 R1 cost a boot exactly this way).
  - Bundle OBSERVATION freely; bundle BEHAVIOUR only behind a switch flippable without
    a rebuild. p2(62) changed six bindings, froze, and its cause is now unknowable.
  - consume_http answers ONLY /SignOn. Anything reaching the standalone server goes
    over the network (steam/interfaces/server_link.h), not through it (20.99). No
    blocking I/O on a game-thread interface method, ever.
  - "Adding player [xuid=..]" fires EVERY boot for the caller's own xuid. Read WHICH
    xuid; the bare line proves nothing (20.101).
  - Solo control boot before any two-machine run (p2(59)); never return fabricated ids
    to client enumeration loops (p2(63)).
  - CENSUS BEFORE FILTER, always. Three 08-29 retractions came from asserting a
    mechanism off a filtered view (20.172).
  - One long-running or ssh-touching action per shell call; both hang AFTER succeeding
    and an interrupt leaves the server dead or the machines on different builds.

## DEAD ENDS - DO NOT RESUME (one line each; mechanism in the cited FINDINGS)
CLOSED BY p2(110)/20.170 - THE WHOLE ADMISSION-FORGE LANE (20.158 -> 20.169): its
  premise ("the mac's member table never names the rig") is FALSE on the current build
  and was false when the lane opened - 20.129 had already measured the symmetric state.
  The injection poisons the mac's OWN bdNAT address structures, so every "peer missing /
  peer cannot answer / NAT Type: **UNKNOWN**" reading from p2(102)-p2(109) was measuring
  a machine we broke ourselves. Do not forge a peer record. Do not substitute an endpoint
  into a forged slot (20.169's fork (a) is MOOT - the real endpoint arrives on its own).
RETRACTED 2026-08-27 (do not re-derive): "Could not find tracking data" as the release
  (20.105) | friends lane as closed - slot 43 IS the string-pair setter (20.103) |
  counts-vs-bitmasks as the lever (20.104).
RETRACTED 2026-08-29 by 20.172, all three MINE: peer-player instantiation read off the
  wrong session | "EST-N/MEM-0 wall" (regex could not match hex) | the peer retry cap as
  the gate (raising it BLOCKED the Tower load; it is a tuned brake).
CLOSED BY EXECUTION: friends rich-presence as the JOIN ROUTE (20.107) | type-12 wire
  shape (20.81) | delivery-gap theory (20.74.4) | gate-table<->reason-enum, which also
  makes the REASON BYTE unreliable (20.83/84) | `reason_name` (20.85/86) |
  `client.region_private` as privacy cause (20.82) | ws 701/702 (20.82) |
  steam_player_group (20.104).
RETIRED BY 20.113 (the whole class, not one lead): every attempt to make a peer
  appear by SHAPING a BAP body - member row sweeps (20.49-51, 20.61), trailing-field
  values, bitmasks, reason bytes, roster pushes. The client reads its session member
  table, not our declarations. Do not reopen any of these.

## PARKED: rx-decode (20.92) | reason hunts (20.86) | blind sweeps (20.49-51) | posse
   fabrication (20.87) | type-54 bubble (20.96) | client-memory profile harvest (20.173).
## READ FIRST (any session taking over)
  0. FINDINGS 20.185 -> 20.178 (the wedge: found, measured, named) and
     HANDOFF_2026-08-29_STAGE-TRAY.md (the pickup doc - the write-detour job).
     HANDOFF_2026-08-29_PROFILE-WRITER.md is SUPERSEDED (its job shipped at 20.178;
     the wedge hunt moved past it). HANDOFF_2026-08-29_ADMISSION.md is HISTORICAL
     as of 20.170. HANDOFF_2026-08-27_ROAD-C.md carries road C (historical).
  1. AGENTS.md (router) + its conditional triggers; boot work ALSO loads LESSONS.md
     PRE-BOOT CHECKLIST and runs gate_boot.py on the brief.
  2. FINDINGS 20.107 FIRST (the layer map + what we have never touched), then
     20.105/20.106 (the pipeline and its addresses). Those three set the scope.
     LESSONS 18 is the instrument that produced them and applies to any unknown code.
  3. FINDINGS_2026-08-25.md 20.107 -> 20.93 newest-first; walk supersession via
     RE_output/INDEX_findings.md or q.sh. Then 20.96/20.97 + activity-name-table.md
     + activity-schema-global-table.md for the fallback emission target.
  4. INCIDENT p2(59) freeze rules; INCIDENT_2026-08-25_false-loops.md (L13/14/11).
  5. Contract refs in claims/: s1-accept-contract.md, msg12-schema-decoded.md,
     transport-relay-design.md, client-steam-vtable-names.md, msg12-parser-read.md,
     l9-profile-layout.md + profile-builder.md (the appearance lane).
     steamfriends-vtable-audit.md is LARGELY RETRACTED - read with 20.100/20.101.
  6. Captures contain NUL bytes - grep with `grep -a`. HANDOFF_OPENCODE_TO_CLAUDE_
     2026-08-27.md is HISTORICAL as of 20.99; the rest of it holds.