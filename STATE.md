# STATE - living snapshot

STATUS: live (2026-08-28 ~15:3x; prior text = git history. FINDINGS holds the dated
entry stack; this file holds verdict + deployed + next + reading order. Operational
/ platform / deploy facts moved to ENVIRONMENTS.md in the 08-28 governance diet.)

Updated: 2026-08-28 ~14:0x. *** CO-LOCATION ACHIEVED (FINDINGS 20.140). *** Both
clients sit in ONE public Tower instance: identical session-description
D9AED900:EBB92CF2, region PUB56.56, AH 9EAA3001:00200003, both 'public AH instance
ready'; each names the OTHER's xuid (every prior run read PEER=0); peer channel
reached connected4 and HELD (0 owner-loss, vs 63 teardowns in p2(88)); 0 errors and
1 rebind on BOTH machines. Deployed p2(89)+capacity: `2997d2810f11b1ab`.
THREE DEFECTS CLOSED TONIGHT, in order: the server never answered the client's SECOND
BAP link (GAHN starvation - one root cause behind all three restart errors, 20.137);
the source for that link must be per-ACCOUNT, keyed on the BAP account slot, since the
two links do NOT share a member key (same identity blob, windows [0..7] vs [5..12],
20.138); and kBapConnectionCount was 4 while a client needs 3 links, a ceiling only
survivable while the third link kept dying (20.139).
REMAINING: **L9 RENDER, UNBUILT** - nothing replicates another player's character
records (family-0/family-3), so the shared Tower reads empty. Co-location and render
are now cleanly separated for the first time; every earlier render observation was
confounded by the clients being in different instances.
L9 SCOPED (20.141-20.144): the static half - what the other guardian LOOKS like - is
absent from every carrier measured. NOT on the peer channel (pcap: ~26 opaque bytes
per tick at 4 Hz, too small by an order of magnitude); NOT reachable by subscribing to
the peer's root (no root->account resolution exists anywhere); NOT produced by the
physics plane (never runs, and "produces no wire output either way" - do NOT flip
`physicsHostSession`). TARGET CHOSen: the group-session player row has a 264-byte
identity/profile slot and `write_player_delta` writes `kPlayerProfileAbsent` on EVERY
row. NEXT ACTION = source those 264 bytes before writing them (do not guess the
layout): `tcpdump ... tcp port 30975` during a CLIENT-HOSTED session, which needs no
code. Full plan + operational notes: HANDOFF_2026-08-28_L9-RENDER.md.

## THE VERDICT - ROAD C IS CLOSED (2026-08-28)
The client does not trust BAP membership; it walks its own managed-session member table
and the only route to a live peer is the game's peer layer. That road is now walked end to
end and CO-LOCATION IS ACHIEVED - see the Updated block above. The full narrative of how it
was opened and closed lives in FRONT_public-host-chain.md (the chain, link by link),
FINDINGS 20.113-20.144, and HANDOFF_2026-08-27_ROAD-C.md (historical).

## WHERE WE ARE (rewritten 08-28; the old p2(74)-era text is superseded by 20.131/132)
Both clients reach the Tower, share ONE group session (members=3 players=2, peers
valid 0x7 both sides) and ONE activity host (00200003, both EST-Y). What is still
missing is one message: the server never speaks to 00200003, so the public activity
client is deaf and the public bubble reserves 0 peer slots (20.132).

## DEPLOYED (2026-08-28 ~14:0x) - p2(89) + BAP capacity; CO-LOCATION ACHIEVED
  server exe   p2(89) `2997d2810f11b1ab` (d721435): serves the client's SECOND BAP link
                (`OUT GAH`) from that ACCOUNT's private session, and kBapConnectionCount
                4 -> 12 so two clients can each hold their three links. BOOT 2026-08-28
                ~14:0x: both clients in ONE public Tower instance, each naming the other's
                xuid, peer channel held, 0 errors / 1 rebind on BOTH (FINDINGS 20.140).
                settings.json gameplay: activity_host_region_bound TRUE,
                publish_join_machine_ids TRUE, activity_public_row_membership_bodies
                65535 (backup .bak_p2d89_preboot_20260828). Prior: p2(87)
                `966c66bc00d96a6b` (6122885) killed the activity-host churn (20.131).
  client DLLs  `4831be3cb85db735` BOTH machines (p2(84), unchanged). settings BOTH:
                join_roster_observer FALSE, slice_set 56.
  fork commit  p2(89) = d721435 (the whole 2026-08-28 lane; p2(88)'s intermediate
                states were deployed and booted but not committed separately - their
                defects were fixed before the p2(89) deploy). Next number p2(90).
  ROLLBACK: server p2(86) `4b2bff83c05f4bb9` (.bak_p2d6_20260828_095725 pair) or
            switch false; server p2(82) `fb8aaf0` (.bak_p2d6_20260828_010113).
            DO NOT BOOT p2(71).
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
  0. HANDOFF_2026-08-27_ROAD-C.md - the newest handoff; it carries road C end to end.
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