# STATE - living snapshot

STATUS: live (2026-08-27 ~10:2x; prior text = git history.
FINDINGS holds the dated entry stack; this file holds verdict + deployed + next.)

Updated: 2026-08-27 ~16:2x. p2(71)/p2(72) freeze bugs found and fixed; p2(73)
observation boot COMPLETE (20.110): the self-pipeline is verified live on both
machines and both roles, and the join request never fires because there is no
client-to-client connect layer.
DECISION TAKEN - ROAD C. Not A (peer-native Steam rendezvous: the client asked
get_certificate once, got 0, and has never called send_rendezvous) and not B
(in-process injection: the roster is a reconcile loop, so an entry with no live
peer link is removed on the next tick and nothing replicates behind it). Road C
makes the SERVER the group-session host and both clients its members. Its whole
server half is already built - UDP endpoint, association, DTLS, peer transport,
group host, and a membership publisher that names host + peer + player - and has
NEVER received one datagram. Chain, link by link, with marks:
FRONT_public-host-chain.md.
NEXT GATE: BOOT_BRIEF_p2-74.md (GATE PASS), link L4 - why the client aims every
activity-host join at its OWN session and never at the one this server
advertised. Observation only; six caller-capture targets + one server line.

## WHERE WE ARE
Both clients reach the Tower, run the retail chain, and see each other as `peer 1`.
Neither ever appears on the other's PLAYER roster. Thirteen boots have been spent at
the wrong altitude - see SCOPE, which supersedes every prior framing of this problem
including 20.82's ("tracking data" is a self-healing warning, not the release: 20.105).

## SCOPE (2026-08-27; L3 static map -> 20.108/20.109; road C taken 16:2x)
THE STEAM LAYER IS COSMETIC TO THIS GOAL. The managed-session player pipeline makes
NO Steam call (20.106/20.107). Do not add friends/matchmaking bindings for this goal.
THE ROSTER IS A RECONCILE LOOP fed by add-candidates, sourced from host-side
reserve -> admit -> adoption into session+0xC8, driven by connection-layer type-0x0A
through a global candidate table on the single network-pump thread. Every address,
stride, and edge: 20.108 (pipeline) and 20.109 (seam) - do not re-copy them here.
20.110 verified that pipeline live for SELF on both machines; the join plane never
flows. Road C and its chain: FRONT_public-host-chain.md.

## DEPLOYED (2026-08-27 16:13) - p2(74) road-C observation, see BOOT_BRIEF_p2-74.md
  client DLLs  `bf791db513362b41` BOTH machines: p2(73) + six new caller-capture
               targets (peer-reservation release, initiate_search, matchmaking
               gatherer advertising, activity_host_changed, waiting to connect to
               AH, join request to AH). Six literals asserted post-copy.
  server exe   `8870459b31b87cc2`: p2(73) + `ev=activity stage=join_target`, which
               names own|advertised|unknown per activity-host join. Routes and the
               claim table are IN-MEMORY: RE_scripts/reset_lobby_claims.sh BETWEEN
               runs.
  settings     mac `client.region_private` true -> false (rig never had the key).
               Divergent since 20.82, measured inert there; declared in the brief.
  fork commit  p2(74) = 38581f2; next number p2(75).
## ROLLBACK: p2(73) `3e7f6ea1b60671a6` = mac .bak_p2d7_20260827_161348, rig
  .bak_p2d7_20260827_161355; server p2(73) `896b37eec11fe30d`. DO NOT BOOT p2(71)
  (ABI bug). Older good: p2(61) `4d4aef769e5a16c4`.
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
STANDING: member row shape by blind sweep (20.49-51, 20.61) | trailing-field values,
  untestable until a peer is actually admitted.

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