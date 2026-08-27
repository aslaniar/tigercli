# STATE - living snapshot

STATUS: live (2026-08-27 ~10:2x; prior text = git history.
FINDINGS holds the dated entry stack; this file holds verdict + deployed + next.)

Updated: 2026-08-27 ~10:5x. THE FRIENDS LANE IS CLOSED (20.101). The mechanism is the
STEAM LOBBY: managed_session creates one per session and each client invented ITS OWN,
so the two sessions were disjoint by construction. p2(67) pairs them - a first-writer-
wins claim on the server, PROVEN race-free in both directions before deploy. Deployed
BOTH machines, server clean, claim table empty. READY TO BOOT.

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

## DEPLOYED (2026-08-27 10:5x) - p2(67), the lobby lane's first boot
  client DLLs  `011fb9e2caec5e82` BOTH machines. create_lobby no longer invents an id
               it keeps: it claims its Nth-lobby ordinal on the server and a worker
               thread queues LobbyCreated/LobbyEnter with the WINNING id, so both
               machines' Nth lobby settles on one. Falls back to the local id after
               10 attempts = exactly p2(66) behaviour if the server is down.
               Friends interface is back to p2(61)'s two bindings (slot 64 REFUTED).
  server exe   `d8338bc0b63116b2` (seven gates passed). POST /lobby/claim?seq=&lobby=
               -> winning id as bare hex, first writer wins per ordinal; GET /lobby ->
               the table; both logged `ev=lobby stage=claim ... result=host|join`.
               IN-MEMORY: a server restart clears the pairing, so restart between runs.
  fork commit  p2(67) = 0d8b543; next number p2(68).
## THE TEST: claims/BOOT_BRIEF_p2-67.md is the contract and holds every branch,
  the read-back greps, and the pre-named 20.83 risk. In one line: steps 1-2 of the
  lobby lane are in this build, steps 3-4 are not, and the success signal is
  "Adding player" naming the PEER's xuid - never the bare line (20.101).
  Most likely partial: pairing works but the roster still names only self => the game
  needs a membership CHANGE EVENT (step 3, LobbyChatUpdate) and that becomes p2(68).
## ROLLBACK: p2(66) `c5387787cade0779` booted clean both machines (mac/rig
  .bak_p2d7_20260827_1051xx). Older: p2(61) `4d4aef769e5a16c4` (20.93),
  .bak_p2d7_20260827_0106xx. New failure mode to watch for is a HANG at matchmaking
  (callbacks never delivered), not a crash - bounded by the 10-attempt fallback.
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
    Next number continues upward; do not renumber. Last commit: 0d8b543 (p2(67));
    deployed client 011fb9e2 and server d8338bc0 both BUILT FROM IT.
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