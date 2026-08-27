# STATE - living snapshot

STATUS: live (2026-08-27 ~10:2x; prior text = git history.
FINDINGS holds the dated entry stack; this file holds verdict + deployed + next.)

Updated: 2026-08-27 ~10:4x. CENSUS BOOT DONE (p2(66), both machines, both in the
Tower). THE FRIENDS LANE IS CLOSED - slot 64 is not SetRichPresence and no
string-pair setter is called at all (20.101). THE REAL MECHANISM IS THE STEAM LOBBY:
managed_session creates one per session, each client creates ITS OWN, so the two
sessions are disjoint by construction. join_lobby is implemented and never called.
NEXT = the lobby lane (p2(67)).

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

## DEPLOYED (2026-08-27 10:0x) - p2(66) is the CENSUS build; it has now RUN
  client DLLs  `c5387787cade0779` BOTH machines. Friends table 256 slots, all
               logged_empty except personaName=0, overlayNeedsPresent=49 and
               set_rich_presence=64 - and the boot REFUTED slot 64 (non-string args
               on both machines), so that binding comes out in p2(67).
               KNOWN REGRESSION: presence_worker never starts in this build - its
               only reachable caller bails at the argument guard first (20.101 #7).
  server exe   `7ff2b4918ae27ee7` (seven gates passed). Cross-machine key/value
               store on the PLAINTEXT ADMIN LISTENER 8099, PROVEN both directions:
               POST /presence/store?xuid=<hex>&key=<k>&value=<v>; GET /presence ->
               "xuid key value" lines. IN-MEMORY. This is the lobby-id channel.
  fork commit  p2(66) = 9abc573; next number p2(67).
## NEXT: THE LOBBY LANE (p2(67)) - every step evidence-backed by 20.101
  1. create_lobby publishes own {activity, lobby id} to the server (reuse the 8099
     presence store - already proven cross-machine, 20.99).
  2. Second client's create_lobby returns the ALREADY-ADVERTISED lobby id instead of
     inventing one, so both managed sessions name the SAME lobby.
  3. Fire a LobbyChatUpdate callback for the peer (queue_callback already exists and
     create_lobby already uses it) to provoke member enumeration.
  4. Serve the member-enumeration matchmaking slots the callback provokes - which
     ones they are gets MEASURED by the same census method, not guessed.
  SUCCESS SIGNAL: "Adding player [xuid=<PEER's xuid>]" - note the line already fires
  every boot for the client's OWN xuid, so read WHICH xuid, never just the line.
  Then: tracking-data release ABSENT = two guardians, one Tower instance.
  Fallback if release still fires: 828-bit session-plane member table (0x808086F8,
  activity-schema-global-table.md, 20.95).
## ROLLBACK: p2(66) `c5387787cade0779` booted clean both machines - it IS the safe
  base now. Older: p2(61) `4d4aef769e5a16c4` (20.93), mac/rig
  .bak_p2d7_20260827_0106xx. Server 7ff2b491 stays (routes inert without callers).
## HARD RULES (all earned 08-26/27)
  - NO client .text patching / no interface-slot binds by guessed ordinal (20.92,
    20.97: guessed ordinals froze pre-title; ordinals now from sdk isteamfriends.h).
  - consume_http answers ONLY /SignOn - anything that must reach the standalone
    server goes over the network, not through it (20.99). No I/O on friends slots.
  - A MEASURED CALL OUTRANKS A PUBLISHED HEADER (20.100/20.101). Census first:
    logged_empty over a table wider than the interface names every real caller.
  - "Adding player [xuid=..]" fires EVERY boot for the client's own xuid. Read WHICH
    xuid; the bare line is not a success signal (20.101).
  - Solo control boot before any two-machine run (incident p2(59) rule).
  - Never return fabricated ids to client enumeration loops (p2(63) phantom-friend).
  - Dead ends + parked fronts: STATE DEAD ENDS below + FINDINGS DO-NOTs.
## DEAD ENDS - DO NOT RESUME (authoritative; mechanism quotes in the cited FINDINGS)

CLOSED BY EXECUTION: FRIENDS RICH-PRESENCE CROSS-INTRODUCTION - slot 64 is not
  SetRichPresence and no string-pair setter is called on that interface at all;
  friends slots called are only 3/5/43, a few times each (20.101). The p2(62)/p2(63)
  freeze cause is UNKNOWN and no longer worth finding: the out-of-bounds theory is
  retired (nothing above slot 79 is ever called). | type-12 wire shape (20.81) | delivery-gap
  theory (20.74.4) | gate-table<->reason-enum (20.83/84) | naming route
  `reason_name` (20.85/86) | `client.region_private` as privacy cause - HYGIENE
  STILL OPEN, mac sets it true and rig lacks the key (20.82) | ws 701/702 as
  fireteam lead, known subclass-swap (20.82).
STANDING: member row shape by blind sweep - the row read comes from schema, which
  is NOT resuming the sweep (20.49-51, 20.61) | trailing-field values (counts vs
  masks) - untestable until a peer is admitted; all prior verdicts were measured on
  self-peers pre-p2(45).

## OPERATIONAL FACTS
  - Fork repo: RE_build/Sunrise-fork-inventory, branch upstream-gameplay-scoped.
    HISTORY NOTE: TWO COMMITS CLAIM p2(39) (f2d0995 Claude, 9639aa4 opencode).
    Next number continues upward; do not renumber. Last commit: 3f7e9d2 (p2(65));
    deployed client 7d8b453a and server 7ff2b491 both BUILT FROM IT.
  - Build: cd RE_build/Sunrise-fork-inventory/build && cmake . && make -j8
    (src/steam/** compiles ONLY into steam_api64.dll; client hooks too).
  - Deploy server: RE_scripts/deploy_p2d6_gameplay.sh (gates inside; asserts
    deployed==built; restamps cache - old exe+cache pairs are inseparable). Client:
    deploy_client_dll.sh <mac|rig> "<literals...>" - hash + literal assert, never skip.
  - Server START (after deploy): nohup bash mac-port/launch-server-macos.sh
    (GPTK wine 7.7, SunriseServer prefix). Verify: lsof TCP 8443/30975/8099 + UDP
    3074; crafted nat probe gets 16B reply (python snippet in morning handoff).
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
  - Identities: mac steamId ...861 (xuid ...ec5, DEFAULT - no key in settings.json);
    rig ...862 (...ec6, authored). Member keys are BOOT-SCOPED; never hardcode.
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