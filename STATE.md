# STATE - living snapshot

STATUS: live (2026-08-29 ~00:5x; prior text = git history. FINDINGS holds the dated
entry stack; this file holds verdict + deployed + next + reading order. Operational
/ platform / deploy facts moved to ENVIRONMENTS.md in the 08-28 governance diet.)

Updated: 2026-08-29 ~12:0x. *** THE WEDGE MECHANISM IS CAUGHT: NAT TRAVERSAL DIALING ***
*** THE IDENTITY STRING AS IP ADDRESSES. *** p2(106): the four static record-reader
candidates NEVER RAN (miss-sample proof; ADMIT ran once, for self, pre-inject). But
~3 s before setup:orbit wedges, the client runs bdNATTravClient and sends SIX "INTRO
REQ"s to endpoints that are ASCII windows over the injected identity string
"steamid:..." at stride exactly 6 (sockaddr-shaped) - even its own "Public Addr" is
ASCII. The client-internal wait is a NAT-retry loop against garbage endpoints: the
record is adopted and then fed to a connection path that needs the peer's REAL
transport endpoint. Fix is NOT more forging - it is naming who builds the endpoint
array and what a real entry contains. NEXT (pre-named in 20.168): caller capture on
the retail funnel for "sent INTRO REQ" (free, existing instrument) + one-shot endpoint
array dump at the dial site + field_xref on the array base. READ: FINDINGS 20.168 ->
20.153; HANDOFF_2026-08-29_ADMISSION.md for the chain.

## DEPLOYED (2026-08-29 ~12:0x)
  server exe   p2(96) `b9b0f3823f74d1bf`: unchanged. Claims reset. NAT probe valid.
  MAC client   `7df1d0e9aff01861` (fork p2(106): admission hooks + reader census).
                admission_inject DISARMED post-boot (false); flip to re-arm.
  RIG client   `7df1d0e9aff01861` - same build, disarmed by settings default.
  fork commit  p2(106). Next number p2(107).
  artifacts    p2(105) pcap + p2(106) mac log in RE_output/captures/p2-104_peer_admission/.
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