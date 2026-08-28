# STATE - living snapshot

STATUS: live (2026-08-27 ~10:2x; prior text = git history.
FINDINGS holds the dated entry stack; this file holds verdict + deployed + next.)

Updated: 2026-08-27 ~18:3x.

## THE VERDICT (20.113 - read this before anything else)
THE ACTIVITY CLIENT DOES NOT TRUST BAP MEMBERSHIP. It enumerates the game's OWN
managed-session member table and tracks only members that reach state 10
(ESTABLISHED). Any peer not in that table is warned about ("Could not find tracking
data") and its reservation RELEASED, once, latched (20.112). The walk is reached via
the session id at +0x1C7C0 and gated on session state 6..9 at +0x1AEF8 - both
offsets derived independently in 20.109 - and it enforces the same member ladder the
community handbook documents (skips 3, collects only 10).
RETIRES A WHOLE CLASS: no type-12 wire shape, trailing field, bitmask, reason byte
or roster push can substitute for session membership. Twenty boots aimed one layer
too high.
THE ONLY GAP LEFT: no client has ever dialed the gameplay endpoint (zero datagrams
on 30976, ever). Road C - the SERVER as group-session host, both clients its members
- is therefore not the cheapest road but the ONLY one. Our group host already models
the ready->established ladder; A (peer-native Steam rendezvous) and B (in-process
injection) both dead-end at the same ladder.
*** 20.114 FOUND THE TOP OF THE CHAIN. *** The client searches for a session ONCE
and takes the answer as final. We answer with the OTHER CLIENT's Steam-identity
blob - a road our shim stubs and that has never run - or with nothing at all if it
searched first. The protobuf nesting was never the gap (our encoder already matches
the handbook's documented shape); WHICH HOST WE NAME is. `build_search_descriptor`,
which builds a descriptor naming THIS SERVER's gameplay endpoint, is DEAD CODE -
grep returns only its definition.
DONE (p2(75), DEPLOYED): `sessionSearch` now answers with a descriptor naming THIS
SERVER's gameplay endpoint, behind `server.gameplay.search_self_host` (default true,
flip false + restart to restore the relay, no rebuild). First change in this project
aimed at the top of the chain instead of the bottom.
p2(75) PHASE 1 RAN (20.115): the contract HELD - first non-empty search answer this
project has produced for a first searcher, naming our own endpoint, routable=1. And
still zero datagrams on 30976, because the client CANCELS ITS OWN SEARCH 31 ms after
starting it and exits matchmaking as HOST. It never evaluated our endpoint, which
exonerates the topology suspect.
CAUSE (handbook 16.6, ordering verified, causal link inferred): our svc-43
configuration answer is EMPTY BUT PRESENT (2 bytes). Zero timing thresholds drive an
immediate advertisement change, the generation changes, the active search dies.
NEXT: encode a real configuration. The VALUES are documented (16.4: lane policy
service-config 1, search-only 60 s, desperation 60 s, one provider-policy entry;
bubble policy max players 9, posse 3, matchmade 6, service-config 1); the FIELD
LAYOUT is not, and a wrong nesting is a policy-31 fatal decode (16.5). Phase 2
paired run deliberately deferred until the configuration is real.
Chain, link by link, with marks: FRONT_public-host-chain.md.

## WHERE WE ARE
Both clients reach the Tower and run the retail chain; each hosts its own private
session and neither ever appears on the other's roster. p2(74) verified WHY on both
roles: each client aims every activity-host join at its OWN session (session id ==
account handle, bit for bit), so the public half is never bound (20.111).

## DEPLOYED (2026-08-27 18:04) - p2(75) self-host search answer, see BOOT_BRIEF_p2-75.md
  client DLLs  `d703d6472914f3dc` BOTH machines: p2(74) + the shared matchmaking
               change (client behaviour unchanged - consume_http answers only
               /SignOn). Three literals asserted post-copy.
  server exe   `ab26ade01c671839`: serves `build_search_descriptor` for
               sessionSearch, logged `stage=descriptor where=serve_self`. Knob
               `server.gameplay.search_self_host` (default true) is in the deployed
               settings.json. Routes and the claim table are IN-MEMORY:
               RE_scripts/reset_lobby_claims.sh BETWEEN runs.
  fork commit  p2(75) = fd7e556; next number p2(76).
## ROLLBACK: p2(74) client `bf791db513362b41` = mac .bak_p2d7_20260827_180419, rig
  .bak_p2d7_20260827_180425; server p2(74) `8870459b31b87cc2`. Behaviour-only, no
  rebuild: `search_self_host: false` + restart. DO NOT BOOT p2(71) (ABI bug).
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