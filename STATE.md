# STATE - living snapshot

STATUS: live (2026-08-27 ~10:2x; prior text = git history.
FINDINGS holds the dated entry stack; this file holds verdict + deployed + next.)

Updated: 2026-08-27 ~10:3x. TWO independent defects found by reading BEFORE booting:
p2(64)'s presence relay never left the client process (20.99), and its friends
bindings moved SetRichPresence off the one slot the publish was measured arriving at
(20.100). Both fixed. p2(66) deployed BOTH machines = census + publish, deliberately
NOT the milestone swing. Server clean, presence table empty. READY TO BOOT.

## WHERE WE ARE (one paragraph)
Both clients connect to our external server, run the full retail matchmaking chain,
and each SAW the other as `peer 1` in activity membership - then released it:
"Could not find tracking data for peer '1'" (20.82 link 4). Root cause located:
tracking data = managed-session (platform-plane) player records; populated ONLY by
platform-layer joins. Retail's join-target mechanism = friends rich-presence key
'connect' = "/connect:" + LE own-xuid (verified both machines). p2(64) implemented
it but relayed through client::network::consume_http, which answers ONLY /SignOn -
so every store was silently dropped and no peer row could exist (20.99). p2(65)
puts the routes on the plaintext admin listener (8099) with a worker-thread socket
client, VERIFIED ON THE WIRE: both machines POST 200 and both GET both rows.

## DEPLOYED (2026-08-27 10:0x)
  client DLLs  `c5387787cade0779` BOTH machines (p2(66)). Friends table 256 slots
               (was 80; client calls to offset 0x690) so every unbound slot NAMES
               ITSELF instead of reading past the array. ONE new binding:
               set_rich_presence at slot 64, on MEASUREMENT (publish arrives there
               t=2662 every boot), behind a VirtualQuery arg guard. 3/5/43 are
               called but UNKNOWN - left unbound. Friends methods do ZERO I/O on the
               calling thread; a worker carries presence to <ext.host>:8099.
  server exe   `7ff2b4918ae27ee7` (relaunched clean 10:0x, seven gates passed).
               Presence routes are on the PLAINTEXT ADMIN LISTENER 8099: POST
               /presence/store?xuid=<hex>&key=<k>&value=<v>; GET /presence ->
               "xuid key value" lines. IN-MEMORY, and EMPTY as of the relaunch.
  fork commit  p2(66); next number p2(67).
## THE TEST - contract + all branches: claims/BOOT_BRIEF_p2-66.md. NOT the milestone
  attempt. User boots BOTH machines (Whisky GUI) into the Tower; it answers two:
  (a) CENSUS - every friends slot destiny2 calls, now the table spans 256:
      grep -a 'stage=stub table=0' <client log> | grep -oE 'slot=[0-9]+' | sort -u
      Anything outside {3,5,43,64} is new and is where enumeration + the presence
      read actually live. That list unblocks the milestone build.
  (b) PUBLISH - `rich_presence_store value=/connect:<hex>` -> `rich_presence_relay
      http=200` -> the PEER's GET showing both rows = publish path closed.
      `result=not_a_string_pair` = slot 64 is not SetRichPresence (safe, logged,
      and arg1/arg2 name the real signature).
  Milestone chain (peer read -> "Adding player" -> release absent) waits for the
  census. Fallback if it ever goes green and release still fires: the 828-bit
  session-plane member table (0x808086F8, activity-schema-global-table.md, 20.95).
## ROLLBACK (if frozen again)
  p2(65) = `23a32b2f4ca26fe2` (mac/rig .bak_p2d7_20260827_1020xx) - working transport,
  wrong bindings. p2(61) = `4d4aef769e5a16c4` last FULL-CHAIN-good (20.93): mac
  .bak_p2d7_20260827_010620, rig .bak_p2d7_20260827_010634. Server 7ff2b491 stays
  (presence routes are inert without callers).
## HARD RULES (all earned 08-26/27)
  - NO client .text patching / no interface-slot binds by guessed ordinal (20.92,
    20.97: guessed ordinals froze pre-title; ordinals now from sdk isteamfriends.h).
  - consume_http answers ONLY /SignOn - anything that must reach the standalone
    server goes over the network, not through it (20.99). No I/O on friends slots.
  - A MEASURED CALL OUTRANKS A PUBLISHED HEADER. This client's friends object does
    not match isteamfriends.h at the slots we have measured; do not re-derive
    ordinals from it, and do not bind 3/5/43 until the census names them (20.100).
  - Solo control boot before any two-machine run (incident p2(59) rule).
  - Never return fabricated ids to client enumeration loops (p2(63) phantom-friend).
  - Dead ends + parked fronts: STATE DEAD ENDS below + FINDINGS DO-NOTs.
## DEAD ENDS - DO NOT RESUME (authoritative; mechanism quotes in the cited FINDINGS)

CLOSED BY EXECUTION (boots #10-#12): type-12 wire shape (20.81) | delivery-gap
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
  2. BOOT_BRIEF_p2-66.md = the standing test contract (p2-62 and p2-65 SUPERSEDED,
     20.99 / 20.100).
  3. FINDINGS_2026-08-25.md 20.100 -> 20.93 newest-first; walk supersession via
     RE_output/INDEX_findings.md or q.sh. Then 20.96/20.97 + activity-name-table.md
     + activity-schema-global-table.md for the fallback emission target.
  4. INCIDENT p2(59) freeze rules; INCIDENT_2026-08-25_false-loops.md (L13/14/11).
  5. Contract refs in claims/: s1-accept-contract.md (BAP), msg12-schema-decoded.md,
     transport-relay-design.md, client-steam-vtable-names.md, msg12-parser-read.md,
     steamfriends-vtable-audit.md (read WITH 20.100 - parts of it are retracted).
  6. Captures contain NUL bytes - grep with `grep -a`. HANDOFF_OPENCODE_TO_CLAUDE_
     2026-08-27.md is HISTORICAL as of 20.99 (its section 2 briefs the dead relay);
     the rest of it still holds.