# STATE - living snapshot

STATUS: live (2026-08-29 ~02:2x; prior text = git history. FINDINGS holds the dated
entry stack; this file holds verdict + deployed + next + reading order. Operational
/ platform / deploy facts moved to ENVIRONMENTS.md in the 08-28 governance diet.)

Updated: 2026-08-29 ~02:2x. *** 20.104 IS CLOSED - THE ROSTER NAMED THE PEER, TWICE. ***
*** BUT A FORGED PEER BREAKS setup:orbit, SO ADMISSION MUST BECOME REAL. ***
Slot + member record injected into the client makes the adoption path name the other
player's xuid (p2(102), reproduced p2(103)) - the question open since 20.104. It also
makes the client try to USE that peer during activity setup, and a forged peer cannot
answer: p2(102) froze, p2(103) black-screened with moving frames, both at setup:orbit.
20.164's "the record was incomplete" is REFUTED by p2(103) (a verbatim copy of a live
record changed nothing). Two forge attempts, two broken clients - U7 says stop.
ALSO SETTLED: the server road for admission is closed by measurement (20.157/20.160); the
public world swap is NOT the managed-session-start gate and its phase branch is CLOSED
(20.156); the unpacked exe carries our own hook bytes at hooked call sites (20.155).
NEXT GATE: capture the PEER CHANNEL (udp 3097, both directions, read by size/cadence -
TOOLS.md). The clients have talked directly since 20.144 and we have never read it for
this question. No client writes, no risk to either machine.
READ FIRST: HANDOFF_2026-08-29_ADMISSION.md, then FINDINGS 20.165 -> 20.153.

## DEPLOYED (2026-08-29 ~02:2x) - THE TWO CLIENTS ARE ON DIFFERENT BUILDS, SEE HANDOFF
  server exe   p2(96) `b9b0f3823f74d1bf`: group-host message-id census (observation) on
                top of p2(93) slice_follows_region=TRUE and p2(90) region seed. All
                gameplay switches as p2(93); member_setup_flags stays FALSE.
  MAC client   `5d7e6bd61e078c24` (p2(98)) - WRITE-FREE, no injection code.
                settings: admission_inject FALSE (parameters retained and working).
  RIG client   `ba6013a2d08cbd46` (p2(103)) - injection code present, disarmed by
                settings default (no admission keys on that machine).
                ALIGN BEFORE BOOTING - one deploy_client_dll.sh per shell call.
  fork commit  p2(103) = 3e0cd10. Next number p2(104).
  ROLLBACK: every prior DLL is on disk on both machines as
                steam_api64.dll.bak_p2d7_<ts>. Server rollback p2(86) `4b2bff83c05f4bb9`;
                DO NOT BOOT p2(71). Flipping admission_inject disarms with no rebuild.

## THE VERDICT - ROAD C IS CLOSED (2026-08-28)
The client does not trust BAP membership; it walks its own managed-session member table
and the only route to a live peer is the game's peer layer. That road is now walked end to
end and CO-LOCATION IS ACHIEVED - see the Updated block above. The full narrative of how it
was opened and closed lives in FRONT_public-host-chain.md (the chain, link by link),
FINDINGS 20.113-20.144, and HANDOFF_2026-08-27_ROAD-C.md (historical).

## WHERE WE ARE
Co-location holds at the session layer (one group target, peers 0x7 / players 0x3 both
sides, one activity host 00200003, both EST-Y). 20.132's "the server never speaks to
00200003" is now NAMED: the missing agreement is the published SLICE SET, not a missing
link - see 20.153. p2(93) is the test.

## HARD RULES (earned 08-26/27)
  - NO .text patching; NO interface slot bound by a guessed ordinal. Census FIRST
    (LESSONS 18): a table sized past the interface, per-slot stubs, argument capture.
    A measured call outranks a published header - isteamfriends.h disagreed with this
    client at every slot we checked (20.100/20.103).
  - Bundle OBSERVATION freely; bundle BEHAVIOUR only behind a switch flippable without
    a rebuild. p2(62) changed six bindings, froze, and its cause is now unknowable.
  - consume_http answers ONLY /SignOn. Anything reaching the standalone server goes
    over the network (steam/interfaces/server_link.h), not through it (20.99). No
    blocking I/O on a game-thread interface method, ever.
  - "Adding player [xuid=..]" fires EVERY boot for the caller's own xuid. Read WHICH
    xuid; the bare line proves nothing (20.101).
  - Solo control boot before any two-machine run (p2(59)). Never return fabricated ids
    to client enumeration loops (p2(63)).
  - One long-running or ssh-touching action per shell call; both hang AFTER succeeding
    and an interrupt leaves the server dead or the machines on different builds.

## DEAD ENDS - DO NOT RESUME (one line each; mechanism in the cited FINDINGS)
RETRACTED 2026-08-27, do not re-derive from older entries: "Could not find tracking
  data" as the release - it self-heals (20.105) | the friends lane as closed - it was
  mis-mapped, slot 43 IS the string-pair setter (20.103) | counts-vs-bitmasks (U2) as
  the lever - we send player_updates=0b11 and the client still reports 1 (20.104).
CLOSED BY EXECUTION: friends rich-presence cross-introduction as the JOIN ROUTE - the
  pipeline never touches Steam (20.107) | type-12 wire shape (20.81) | delivery-gap
  theory (20.74.4) | gate-table<->reason-enum, which also makes the REASON BYTE
  unreliable (20.83/84) | naming route `reason_name` (20.85/86) | `client.region_private`
  as privacy cause (20.82; hygiene CLOSED 08-27: both machines false) | ws 701/702
  as fireteam lead (20.82) | steam_player_group - derived from the roster (20.104).
RETIRED BY 20.113 (the whole class, not one lead): every attempt to make a peer
  appear by SHAPING a BAP body - member row sweeps (20.49-51, 20.61), trailing-field
  values, bitmasks, reason bytes, roster pushes. The client reads its session member
  table, not our declarations. Do not reopen any of these.

## PARKED: rx-decode (20.92) | reason hunts (20.86) | blind sweeps (20.49-51) |
   posse fabrication (20.87) | type-54 bubble (20.96).
## READ FIRST (any session taking over)
  0. HANDOFF_2026-08-29_ADMISSION.md - the newest handoff; it carries the admission
     chain end to end and warns about the two clients being on different builds.
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
  5. Contract refs in claims/: s1-accept-contract.md (BAP), msg12-schema-decoded.md,
     transport-relay-design.md, client-steam-vtable-names.md, msg12-parser-read.md.
     steamfriends-vtable-audit.md is LARGELY RETRACTED - read only with 20.100/20.101.
  6. Captures contain NUL bytes - grep with `grep -a`. HANDOFF_OPENCODE_TO_CLAUDE_
     2026-08-27.md is HISTORICAL as of 20.99 (its section 2 briefs the dead relay);
     the rest of it still holds.