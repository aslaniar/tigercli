# STATE - living snapshot

STATUS: live (2026-08-28 ~21:3x; prior text = git history. FINDINGS holds the dated
entry stack; this file holds verdict + deployed + next + reading order. Operational
/ platform / deploy facts moved to ENVIRONMENTS.md in the 08-28 governance diet.)

Updated: 2026-08-28 ~21:5x. *** THE PHASE IS MAPPED. IT IS A COMPUTED RETURN VALUE ***
*** (fn 0x140E22C70: 4 = switch-now, 0 = not yet), NOT A FIELD WE CAN PUBLISH INTO. ***
*** A PUBLIC TRANSITION ALWAYS GETS 0. TRACE IN FLIGHT, NO BOOT PENDING. ***
Both clients still stop at `Finished precaching slice-set 'PUB56.56'` with no switch
task. p2(94) (caller-capture, logging only) resolved all six transition-manager log
sites; 20.154 has the map. The deciding read is
`byte[rdi+0x660][ dword[rdi+0x53c] ] == byte[rdi+0x350]` - a per-member-SLOT byte array
compared against one reference byte, which is the shape of the region record's 32
transition-token lanes. 20.153's dismissal of the token is CORRECTED: it checked the
value (we publish 2, the client is at 2) and never checked which lane the client reads.
The teleport retirement in 20.153 stands (it is a mirror of a client message-22 report,
never a host command channel). NEXT GATE: static trace naming [rdi+0x53c], [rdi+0x660]
and [rdi+0x2bc]; then one targeted fix. No boot until the trace names it.
READ FIRST: FINDINGS 20.154, then 20.153.

## DEPLOYED (2026-08-28 ~21:3x) - server p2(93); client DLL p2(94) (instrument)
  server exe   p2(93) `50d1f4cccbad0a56` (fork 9fd3134): the published slice set follows the
                client's REPORTED region instead of the destination's arrival bubble, behind
                activity_slice_set_follows_region=TRUE (FINDINGS 20.153). LIVE and required:
                p2(90) activity_region_survives_churn=TRUE (region seed; 20.147/20.148).
                activity_member_setup_flags=FALSE (p2(91)/p2(92) in tree, switched off -
                20.152/20.153). Settings echo verified at launch:
                `region_bound=1 join_machine_ids=1 public_row_bodies=65535
                region_survives_churn=1 member_setup_flags=0 slice_follows_region=1`.
                Settings backup .bak_p2d93_preboot_20260828.
  client DLLs  p2(94) `003baf5ff811ff79` BOTH machines: caller-capture on six
                transition-manager lines (LOGGING ONLY, no behaviour). Prior baseline
                `ae4d41f76b5202a5` restores via deploy_client_dll.sh.
  fork commit  p2(93) = 9fd3134 (server), p2(94) = 61f72d1 (client). Next p2(95).
  ROLLBACK: flip activity_slice_set_follows_region to false (no rebuild). Binary rollback
                p2(86) `4b2bff83c05f4bb9`; DO NOT BOOT p2(71).

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
  0. FINDINGS 20.153 (newest; retracts the 08-28 evening lead) + BOOT_BRIEF_p2-93.md.
     HANDOFF_2026-08-27_ROAD-C.md carries road C end to end (historical).
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