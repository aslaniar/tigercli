# STATE - living snapshot

STATUS: live (2026-08-27 ~10:2x; prior text = git history.
FINDINGS holds the dated entry stack; this file holds verdict + deployed + next.)

Updated: 2026-08-27 ~11:1x. p2(67) BOOTED: lobby pairing WORKS both directions, no
freeze, and the 20.83 shared-id risk did not bite - but the roster still named only
self, because neither client was ever told a second member arrived (20.102). p2(68)
supplies both halves: each shim learns the peer's xuid from the claim answer, fires
LobbyChatUpdate, and serves member count/index at the corroborated slots 17/18.
Deployed BOTH machines, server clean, claim table empty. READY TO BOOT.

## WHERE WE ARE (one paragraph)
Both clients connect to our external server, run the full retail matchmaking chain,
and each SEES the other as `peer 1` - then releases it: "Could not find tracking
data for peer '1'". Tracking data = managed-session player records, and 20.101
identified what actually populates them: THE MANAGED SESSION'S MEMBERSHIP IS A STEAM
LOBBY. "Adding player [xuid=..]" already fires on every boot - always for exactly
one xuid, the client's own - because each client's create_lobby invents its OWN
lobby id locally (mac 0x010900000CC46DB7, rig 0x010900000CC46DB4) and nothing ever
hands either one a foreign id. The friends rich-presence route was a wrong turn: the
census proved slot 64 is not SetRichPresence and NO string-pair setter is called on
that interface. Salvage from it: the presence transport (20.99) is a working
cross-machine key/value store, reusable as the lobby-id channel.

## DEPLOYED (2026-08-27 11:1x) - p2(68), lobby lane steps 3-4
  client DLLs  `115a5b715f217c52` BOTH machines. Learns the peer xuid from the claim
               answer, fires LobbyChatUpdate(506) on membership growth, serves
               GetNumLobbyMembers(17)/GetLobbyMemberByIndex(18). Unimplemented slots
               now log ARGUMENT REGISTERS, so a wrong ordinal still names the real
               one in the same boot.
  server exe   `896b37eec11fe30d` (seven gates passed). POST /lobby/claim?seq=&lobby=
               &xuid= -> "<winner> <member>..." all bare hex; first writer wins per
               ordinal, membership recording is idempotent so the host discovers a
               late peer by re-polling. GET /lobby -> table. IN-MEMORY: run
               RE_scripts/reset_lobby_claims.sh BETWEEN runs.
  fork commit  p2(68); next number p2(69).
## THE TEST: claims/BOOT_BRIEF_p2-68.md is the contract and holds every branch.
  Read it with `bash RE_scripts/boot_verdict.sh` (both clients + server, rules
  mechanically). Success signal is still an "Adding player" xuid that is NOT the local
  machine's - never the bare line (20.101). Section 4 of that output is now a slot +
  ARGUMENT map, so a negative result names the next target instead of costing a boot.
## ROLLBACK: p2(67) `011fb9e2caec5e82` reached the Tower on both machines (mac/rig
  .bak_p2d7_20260827_1111xx). Older good: p2(61) `4d4aef769e5a16c4` (20.93).
  Residual risk in p2(68) is BEHAVIOURAL (an unexpected callback confusing matchmaking),
  not a crash: the two new bindings take only integers and cannot fault.
## HARD RULES (all earned 08-26/27)
  - NO .text patching, and NO interface slot bound by a guessed ordinal (20.92/20.97).
    A MEASURED CALL OUTRANKS A PUBLISHED HEADER: isteamfriends.h disagreed with this
    client at every slot we checked (20.100/20.101). Census first - logged_empty over
    a table WIDER than the interface names every real caller, for free.
  - consume_http answers ONLY /SignOn. Anything that must reach the standalone server
    goes over the network (steam/interfaces/server_link.h), not through it (20.99).
    No blocking I/O on a game-thread interface method, ever.
  - "Adding player [xuid=..]" fires EVERY boot for the caller's own xuid. Read WHICH
    xuid; the bare line proves nothing (20.101).
  - Solo control boot before any two-machine run (incident p2(59) rule).
  - Never return fabricated ids to client enumeration loops (p2(63) phantom-friend).
  - Dead ends + parked fronts: STATE DEAD ENDS below + FINDINGS DO-NOTs.
## DEAD ENDS - DO NOT RESUME (one line each; mechanism lives in the cited FINDINGS)
CLOSED BY EXECUTION: friends rich-presence cross-introduction - no string-pair setter
  is called on that interface at all, and only slots 3/5/43 are ever called (20.101;
  the p2(62)/p2(63) freeze cause is unknown and no longer worth finding, the
  out-of-bounds theory being retired) | type-12 wire shape (20.81) | delivery-gap
  theory (20.74.4) | gate-table<->reason-enum, which also makes the REASON BYTE an
  unreliable signal (20.83/84) | naming route `reason_name` (20.85/86) |
  `client.region_private` as privacy cause - HYGIENE STILL OPEN, mac sets it true and
  rig lacks the key (20.82) | ws 701/702 as fireteam lead, subclass-swap (20.82).
STANDING: member row shape by blind sweep - the row read comes from schema, which is
  NOT resuming the sweep (20.49-51, 20.61) | trailing-field values (counts vs masks) -
  untestable until a peer is actually admitted (all verdicts pre-p2(45) used self-peers).

## OPERATIONAL FACTS
  - Fork repo: RE_build/Sunrise-fork-inventory, branch upstream-gameplay-scoped.
    HISTORY NOTE: TWO COMMITS CLAIM p2(39) (f2d0995 Claude, 9639aa4 opencode).
    Next number continues upward; do not renumber. DEPLOYED = p2(68) 071e083
    (client 115a5b71, server 896b37ee); build tree matches deployed.
  - Build: cd RE_build/Sunrise-fork-inventory/build && cmake . && make -j8. BOTH
    targets take EXPLICIT source lists in Sunrise/CMakeLists.txt, NOT globs - a new
    .cpp must be added there or it silently fails to link (bit c2764aa and p2(67)).
  - Deploy server: RE_scripts/deploy_p2d6_gameplay.sh (gates inside; asserts
    deployed==built; restamps cache - old exe+cache pairs are inseparable). Client:
    deploy_client_dll.sh <mac|rig> "<literals...>" - hash + literal assert, never skip.
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
    <game>/Sunrise/logs/sunrise.log (mac Game/bin/x64/Sunrise/logs/). Grep
    ev=steamnet / ev=presence / ev=activity / peers valid / ev=relay stage=register.
  - Rig: ssh master ~/.ssh/cm-rig to rasla@192.168.1.136 (password only to REOPEN);
    ICMP is firewalled so `ping` is NOT an aliveness test - the socket is. Sleep
    disabled on AC. Game dir C:\Users\rasla\...\destiny-preservation\dcv build\bin\x64\.
  - Identities: mac steamId ...861 / xuid ...ec5 (DEFAULT, no key in settings.json);
    rig ...862 / ...ec6 (authored). Member keys are BOOT-SCOPED; never hardcode.
  - Mac: /usr/bin/python3 for DB/sqlite (miniconda's sqlite3 is broken here);
    plain `python3` for capstone; rg for corpus greps.

## PARKED: rx-decode (20.92) | reason hunts (20.86) | blind sweeps (20.49-51) |
   posse fabrication (20.87) | type-54 bubble (20.96).
## READ FIRST (any session taking over)
  1. AGENTS.md (router) + its conditional triggers; boot work ALSO loads LESSONS.md
     PRE-BOOT CHECKLIST and runs gate_boot.py on the brief.
  2. FINDINGS 20.101 FIRST - it closes the friends lane and opens the lobby one.
     Boot briefs p2-62/65/66 are all superseded by it.
  3. FINDINGS_2026-08-25.md 20.101 -> 20.93 newest-first; walk supersession via
     RE_output/INDEX_findings.md or q.sh. Then 20.96/20.97 + activity-name-table.md
     + activity-schema-global-table.md for the fallback emission target.
  4. INCIDENT p2(59) freeze rules; INCIDENT_2026-08-25_false-loops.md (L13/14/11).
  5. Contract refs in claims/: s1-accept-contract.md (BAP), msg12-schema-decoded.md,
     transport-relay-design.md, client-steam-vtable-names.md, msg12-parser-read.md.
     steamfriends-vtable-audit.md is LARGELY RETRACTED - read only with 20.100/20.101.
  6. Captures contain NUL bytes - grep with `grep -a`. HANDOFF_OPENCODE_TO_CLAUDE_
     2026-08-27.md is HISTORICAL as of 20.99 (its section 2 briefs the dead relay);
     the rest of it still holds.