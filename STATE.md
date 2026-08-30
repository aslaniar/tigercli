# STATE - living snapshot

STATUS: live (2026-08-29 ~00:5x; prior text = git history. FINDINGS holds the dated
entry stack; this file holds verdict + deployed + next + reading order. Operational
/ platform / deploy facts moved to ENVIRONMENTS.md in the 08-28 governance diet.)

Updated: 2026-08-29 ~15:0x. *** THE STACK IS DONE EXCEPT ONE THING: THE PROFILE BLOCK'S
WIRE ENCODING. *** p2(114) (grand capture, observation only, no crash, no new black
screen) proved THREE independent ways that NO profile block exists anywhere on our wire:
0x1417AF360 fired 8x on EACH client and every caller was the local registry commit
(0x17A6101) with ZERO wire-path applies; zero svc-9 upstream; and all 50 decoded
downstream type-12 bodies are ours, with `kPlayerProfileAbsent = 0` hardcoded.
ALSO PROVEN (20.174 R2, corroborated at runtime by 20.175 R3): the wire apply VALIDATES
NOTHING - verify=0 makes 0x1417AF6D3 skip the entire lookup3, and region B is an
unconditional 136B memcpy. AN AUTHORED BLOCK NEEDS NO CORRECT HASH.
NEW CAPABILITY (20.175 R4): the CLIENT->SERVER BAP direction now decrypts - the nonce is
the base with its LAST BYTE XOR 0x01 (`kReceiveDirectionMask`, our own plaintext.cpp:218).
571/571 frames, 0 failures. bapdecode.py only ever did s2c. First upstream census: svc-10
(2475/4812 x24), svc-171 (one 36,720B body), svc-29, svc-250; svc-9 ZERO. The svc-171 and
svc-10 bodies are the largest UNREAD objects on our wire.
THE DECODER IS FOUND AND ITS WIDTH TABLES ARE READ (20.176 + 20.177). Decoder =
**0x14173BFC0** (0x14173B920 REFUTED, a memcmp comparator). The player row and the whole
profile block are now specified BIT BY BIT with nothing guessed, and every offset
independently reproduces l9-profile-layout CLAIM 5.
*** A MINIMAL, DECODER-CORRECT WRITER IS FULLY SPECIFIED IN 20.177 RESULT 5 (150 bits).
NO CODE WAS WRITTEN - the session ended at the spec. ***
THREE TRAPS AN ENCODER MUST RESPECT (all read from the decoder, all easy to get wrong):
 (1) region A's 9 presence bits go out in WIRE order 1,2,4,8,0x100,0x10,0x20,0x40,0x80 -
     NOT bit order, and the 9-bit "mask" is BUILT BY THE READER, never sent as a field;
 (2) chunks 4 and 5 are `read(6) - 1`, so write 1 to store 0;
 (3) the tail's 5-bit field must have bit 0x10 CLEAR or a further section is read.
The "obvious" encoding (two headers then 232+136+20 raw bytes) is WRONG and would desync
the body from the gate bit onward. It was not shipped.
HAZARD, DISCHARGED BY CONSTRUCTION (20.177 R4): region A returns bool and a FALSE makes
the decoder skip region B's read (desync). The minimal writer sends chunks 1/4/5 - a zero
name word and two zero bytes - which forces all four of its exit conditions true without
depending on the delta buffer's prior contents (nothing is proven to zero it).
NO HASH IS EVER REQUIRED on the wire path (20.174 R2, corroborated at runtime 20.175 R3).
NEXT: the wedge mechanism is MEASURED (20.178): the client refuses the flag-on body at the
transport layer, pre-decode (no ack, no ingress; size/fragment-count ruled out). Next gate:
replay the p2(113) harvested REAL region-A block instead of the minimal 178-bit shape - if
accepted, diff names the wrong bits; if refused, the refusal is structural and 20.174 R2's
"no hash required" needs re-examination at the transport layer. Flag publish_player_profile
is live TRUE; flag OFF restores the p2(110) baseline (settings flip, no rebuild).
READ: FINDINGS 20.178 first, then HANDOFF_2026-08-29_PROFILE-WRITER.md, then 20.177.

## DEPLOYED (2026-08-29 ~15:3x, p2(115) - the minimal profile writer deploy)
  server exe   p2(115) `a7a7a1cfd4e26abb` (commit 2e11e4a): write_minimal_profile behind
               NEW setting `publish_player_profile` (live = TRUE in s1_accept/Sunrise/
               settings.json); retry-cap code default 6 -> 2. Boot NOT yet run.
  MAC client   `7849e28a58d40539`. DISARMED (`admission_inject: false`).
  RIG client   `7849e28a58d40539` - byte-identical to the mac. Disarmed (key absent).
  fork commit  p2(115). Next number p2(116).
  fork commit  p2(114). Next number p2(115).
  MAC+RIG DLL  `45ef17f93b901db9` (profile_harvest + profile_ingress, armed on BOTH;
               both are read-only and disarm via settings with no rebuild).
  artifacts    RE_output/captures/p2-110_clean_paired/ (mac+rig+server logs, en0+lo0
               pcaps, BOOT_BRIEF_p2-110.md); p2(109) server log archived there too.
  ROLLBACK: prior DLLs on disk both machines as steam_api64.dll.bak_p2d7_<ts>; server
                rollback p2(86) `4b2bff83c05f4bb9`; DO NOT BOOT p2(71).

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
  0. FINDINGS 20.170 (p2(110), the clean paired boot) - READ THIS BEFORE ANY OTHER
     08-29 material. It confirms symmetric membership, names the new front, and
     corrects 20.167/20.169. HANDOFF_2026-08-29_ADMISSION.md is HISTORICAL as of
     20.170: its "capture the peer channel" recommendation was executed and its
     premise (the forge) is closed.
     HANDOFF_2026-08-27_ROAD-C.md carries road C (historical).
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