# STATE - living snapshot

STATUS: live (2026-08-27 ~10:2x; prior text = git history.
FINDINGS holds the dated entry stack; this file holds verdict + deployed + next.)

Updated: 2026-08-27 ~18:3x.

## THE VERDICT (20.118 - read this before anything else)
*** THE DOOR IS OPEN. *** p2(78) forced the TOWER's region public (slice set 56,
settings-only) and the client dialed the gameplay endpoint for the FIRST time in
this project: 64 datagrams, DTLS, establish, group join, membership built, player
added, `join result=completed`. Client side: `reserve` fired for a SECOND MACHINE at
member state 10 = ESTABLISHED (the state 20.113 proved the game requires), peers
valid went 0x1 -> 0x3, the activity client took the PUBLIC TARGET role, and the
tracking-data warning + peer-reservation release that ended every peer's life
(20.112) did not fire once. L6 and L7 are VERIFIED-BY-EXECUTION.

TWO BOUNDED DEFECTS REMAIN, both in code we own, and the order matters:
1. APPLICATION-READY GATE - BUILT AND PROVEN (p2(79), 20.119). The join now runs the
   whole ladder in order, the peer's parameter request is answered, and
   `join result=completed` fires. Admits fell 13 -> 4. KEEP.
1b. THE ~22.8 s REBUILD IS NOT AN IDLE TIMEOUT. 20.119 said "complete silence" and
   p2(80) added a keepalive on it; BOTH ARE RETRACTED (20.120). The silence was a
   grep that omitted `stage=packet`, which was arriving every ~250 ms throughout.
   The keepalive fired ZERO times and the cycle is unchanged - it is a lifetime the
   peer enforces regardless of traffic. DO NOT ADD MORE TRANSPORT TRAFFIC.
   THE REAL LEAD: every cycle our own log reads `parameters result=ambiguous
   walked=0x00000000 stopped=21 tail=8039` for `public-session-reservations`, and
   handbook p43 registry index 21 IS `publicSessionReservations`. The client then
   logs "Updating public bubble reservation peer request ... to '0' SLOTS" and
   recycles ~22.8 s later. PARAMETER 21 IS NOT A QUICK BUILD: our ANSWER for it is
   already a deliberate clear root bit ("no value, keep your own") because its BODY
   LAYOUT IS UNRECOVERED - which is also why the read walk is ambiguous. Inventing a
   body is the policy-31 fatal-decode class (handbook 16.5).
   NEXT: p2(81) captures the peer's OWN request bytes (`result=body_capture`) so the
   layout can be decoded offline. BOOT_BRIEF_p2-81.md, GATE PASS, observation only.
2. L8 - ONE SESSION, MANY PEERS. Both clients named the SAME group session, and
   `claim()` rebinds its single record to whichever endpoint joined last, so they
   steal it from each other and every snapshot stays members=2 players=1.
   `kSnapshotMemberCount = 2` is where it starts.

## WHERE WE ARE
Both clients reach the Tower and run the retail chain; each hosts its own private
session and neither ever appears on the other's roster. p2(74) verified WHY on both
roles: each client aims every activity-host join at its OWN session (session id ==
account handle, bit for bit), so the public half is never bound (20.111).

## DEPLOYED (2026-08-27 20:3x) - p2(81) parameter-body capture, see BOOT_BRIEF_p2-81.md
  client DLLs  `3fa02bb785a1cacc` BOTH machines. server exe `72177ecd4083e6b0`.
  Behaviour identical to p2(80) plus one log line on a copied reader.
  settings     BOTH machines `region_public_slice_set: 56` (the Tower); orbit (24)
               and initial slice set (48) untouched. Server `search_self_host: true`.
               Claims IN-MEMORY: reset_lobby_claims.sh BETWEEN runs.
  fork commit  p2(81); next number p2(82).
  NOTE         p2(80)'s keepalive is a PROVEN NO-OP (20.120) - it fired zero times.
               It is left in place, inert; do not cite it as a fix.
## ROLLBACK: p2(80) server `4d966c3d8808d1c2`, client `a604e2eed3995b3e`.
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

## OPERATIONAL FACTS
  - Fork repo: RE_build/Sunrise-fork-inventory, branch upstream-gameplay-scoped.
    HISTORY NOTE: TWO COMMITS CLAIM p2(39) (f2d0995 Claude, 9639aa4 opencode).
    Next number continues upward; do not renumber. Deployed hashes live in
    DEPLOYED above, not here; build tree matches deployed.
  - Build: cd RE_build/Sunrise-fork-inventory/build && cmake . && make -j8. BOTH
    targets take EXPLICIT source lists in Sunrise/CMakeLists.txt, NOT globs - a new
    .cpp must be added there or it silently fails to link (bit c2764aa and p2(67)).
  - Deploy server: RE_scripts/deploy_p2d6_gameplay.sh (gates inside; asserts
    deployed==built; restamps cache - old exe+cache pairs are inseparable). Client:
    deploy_client_dll.sh <mac|rig> "<literals...>" - hash + literal assert, never skip.
  - NEVER launch the server or deploy to the rig chained with other work in one shell
    call: both hang holding a pipe AFTER succeeding, and an interrupt then leaves the
    server dead or the machines on different builds (ENVIRONMENTS.md "SHELL").
  - Server START (after deploy): nohup bash mac-port/launch-server-macos.sh (GPTK
    wine 7.7, SunriseServer prefix). Verify: lsof TCP 8443/30975/8099 + UDP 3074, and
    a crafted nat probe gets a 16B reply (snippet in HANDOFF_OPENCODE_TO_CLAUDE).
    8443 TLS is BROKEN (SEC_E_UNSUPPORTED_FUNCTION) - do not route anything new
    through it. SignOn rides in-process consume_http, which answers ONLY /SignOn;
    everything else that must reach the server uses the plaintext admin listener
    8099 (20.99). Presence store is IN-MEMORY: restart wipes stored keys.
  - CLIENT LAUNCH: user does it via WHISKY GUI (bottle D1FB4A66-...). A CLI launch
    does NOT wedge - it stops at bootflow:start task ENUM(0), which is the
    press-to-start gate, because nothing presses a key (20.99 item 5; a good boot
    shows ENUM(0) completing after ~15.7 s of human input). Nothing is wrong with
    the binary or the prefix. Autonomous boots would need synthesized input.
  - Logs: server RE_output/s1_accept/Sunrise/logs/sunrise.log; clients
    <game>/Sunrise/logs/sunrise.log. `bash RE_scripts/boot_verdict.sh` reads both
    machines + server and rules mechanically.
  - Rig: ssh master ~/.ssh/cm-rig to rasla@192.168.1.136 (password only to REOPEN);
    ICMP is firewalled so `ping` is NOT an aliveness test - the socket is. Sleep
    disabled on AC. Game dir C:\Users\rasla\...\destiny-preservation\dcv build\bin\x64\.
  - Identities: mac steamId ...861 / xuid ...ec5 (DEFAULT, no key in settings.json);
    rig ...862 / ...ec6 (authored). Member keys are BOOT-SCOPED; never hardcode.
  - Mac: /usr/bin/python3 for DB/sqlite (miniconda's is broken); plain `python3` for
    capstone. Static RE: destiny2_unpacked_full.exe, base 0x140000000, .text raw 0x600
    va 0x1000, .pdata raw 0x20B9A00 for exact function bounds. LOG STRINGS ARE NOT IN
    THE BINARY - use caller capture (LESSONS 18c), not string xrefs.

## PARKED: rx-decode (20.92) | reason hunts (20.86) | blind sweeps (20.49-51) |
   posse fabrication (20.87) | type-54 bubble (20.96).
## READ FIRST (any session taking over)
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