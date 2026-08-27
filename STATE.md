# STATE - living snapshot

STATUS: live (2026-08-27 ~09:1x morning handoff to Claude; prior text = git history.
FINDINGS holds the dated entry stack; this file holds verdict + deployed + next.)

Updated: 2026-08-27 ~09:1x. NIGHT ARC COMPLETE: p2(59-64) instrument freeze incident
(opened/closed), Tower two-machine run (20.93), friends rich-presence cross-
introduction implemented (p2(64)), deployed BOTH machines - AWAITING BOOT TEST.

## WHERE WE ARE (one paragraph)
Both clients connect to our external server, run the full retail matchmaking chain,
and each SAW the other as `peer 1` in activity membership - then released it:
"Could not find tracking data for peer '1'" (20.82 link 4). Root cause located:
tracking data = managed-session (platform-plane) player records; populated ONLY by
platform-layer joins. Retail's join-target mechanism = friends rich-presence key
'connect' = "/connect:" + LE own-xuid (verified both machines). p2(64) implements
it (shim friends methods + server relay) - built, deployed, NOT YET BOOT-TESTED.

## DEPLOYED (2026-08-27 08:4x)
  client DLLs  `4173ae4b3ad5bc7b` BOTH machines - friends at VERIFIED ISteamFriends017
               ordinals {2 GetFriendCount, 3 GetFriendByIndex, 5 PersonaState,
               6 PersonaName, 36 RequestUserInfo, 41 SetRichPresence,
               43 GetFriendRichPresence, 46 RequestFriendRichPresence}
  server exe   `73a0f8f2f35327a7` (running, relaunched 09:0x) - NEW presence routes:
               POST /presence/store?xuid=<hex>&key=<k> (body=value); GET /presence
               -> "xuid key value" lines. Presence state is IN-MEMORY (restart wipes).
  fork commit  0d14916 + c2764aa (p2(64)); next number p2(65).
## MORNING TEST (the whole point)
  User boots BOTH machines normally (Whisky GUI), into the Tower. Watch, in order:
  1. `rich_presence_store result=ok` on both client logs (publish works)
  2. server /presence hits + peer 'connect' keys visible cross-machine
  3. managed_session "Adding player [xuid=<peer>]" (platform join happened)
  4. `Could not find tracking data for peer '1'` ABSENT -> MILESTONE: two guardians,
     one Tower instance. If release STILL fires with 1-3 green -> next emission
     target = the 828-bit session-plane member table (0x808086F8, layout in
     activity-schema-global-table.md) - see 20.95.
## ROLLBACK (if frozen again)
  p2(61) = `4d4aef769e5a16c4` last known good. Backups: mac
  Game/bin/x64/steam_api64.dll.bak_p2d7_20260827_010620; rig
  ...steam_api64.dll.bak_p2d7_20260827_010634. Server 73a0f8f2 stays (routes inert).
## HARD RULES (all earned 08-26/27)
  - NO client .text patching / no interface-slot binds by guessed ordinal (20.92,
    20.97: guessed ordinals froze pre-title; ordinals now from sdk isteamfriends.h).
  - Solo control boot before any two-machine run (incident p2(59) rule).
  - Never return fabricated ids to client enumeration loops (p2(63) phantom-friend).
  - Dead ends + parked fronts: STATE DEAD ENDS below + FINDINGS DO-NOTs.
## DEAD ENDS - DO NOT RESUME (authoritative, rewritten 20:45; condensed to
## one line each; full mechanism quotes in the FINDINGS entries cited)

CLOSED BY EXECUTION (boots #10-#12):
  - TYPE-12 WIRE SHAPE - parses, accepted with two descriptors + peer row. (20.81)
  - DELIVERY-GAP THEORY - both endpoints shipped, release fired anyway naming
    a LOOKUP failure, not an address. (20.74.4 -> refuted by boot #10)
  - GATE-TABLE <-> REASON-ENUM correspondence - unique fireteam ids SPREAD
    reason 1 to both machines instead of clearing it. (20.83 retracted 20.84)
  - NAMING ROUTE (`reason_name`) - never called on release path; hook attached,
    refusal occurred, zero calls. (20.85 -> 20.86)
  - `client.region_private` as cause of privacy-mode - decision path never ran.
    HYGIENE REMAINS OPEN: Mac sets it true, rig lacks the key entirely. (20.82)
  - WS opcodes 701/702 as fireteam lead - already tagged subclass-swap. (20.82)
STANDING:
  - MEMBER ROW SHAPE BY BLIND SWEEP - six shapes swept, none informative; row
    read comes from schema (20.61), which is NOT resuming the sweep. (20.49-51)
  - TRAILING-FIELD VALUES (counts vs masks) - untestable until a peer is actually
    admitted; all prior verdicts measured on self-peers pre-p2(45).

## READ FIRST (any session taking over)
  1. AGENTS.md (router) + the conditional triggers there; boot work ALSO loads
     LESSONS.md PRE-BOOT CHECKLIST and runs gate_boot.py on the brief.
  2. INCIDENT_2026-08-25_false-loops.md - why lessons 13/14/11 exist.
  3. FINDINGS_2026-08-25.md 20.78 -> 20.86 newest-first (today's whole arc);
     walk supersession links via RE_output/INDEX_findings.md or q.sh.
  4. Contract refs: RE_output/claims/s1-accept-contract.md (BAP),
     msg12-schema-decoded.md (type-12), transport-relay-design.md,
     client-steam-vtable-names.md, msg12-parser-read.md.
  5. Captures contain NUL bytes - grep them with `grep -a`.

## OPERATIONAL FACTS
  - Fork repo: RE_build/Sunrise-fork-inventory, branch upstream-gameplay-scoped.
    HISTORY NOTE: TWO COMMITS CLAIM p2(39) (f2d0995 Claude, 9639aa4 opencode).
    Next number continues upward; do not renumber. Last commit: 1533fb7 (p2(64)
    + TLS status diagnostic). NOTE: deployed client 4173ae4b predates 1533fb7
    (that commit only adds a server-side log line; redeploy optional).
  - Build: cd RE_build/Sunrise-fork-inventory/build && cmake . && make -j8
    (src/steam/** compiles ONLY into steam_api64.dll; client hooks too).
  - Deploy server: bash RE_scripts/deploy_p2d6_gameplay.sh (gates inside;
    asserts deployed==built; restamps cache - old exe+cache pairs are inseparable).
  - Deploy client DLL: bash RE_scripts/deploy_client_dll.sh <mac|rig> "<literals...>"
    - hash assert + literal grep IN the deployed file; never skip.
  - Server START (after deploy): nohup bash mac-port/launch-server-macos.sh
    (GPTK wine 7.7, SunriseServer prefix). Verify: lsof TCP 8443/30975/8099 + UDP
    3074; crafted nat probe gets 16B reply (python snippet in morning handoff).
    NOTE: curl TLS to 8443 fails with server-side SEC_E_UNSUPPORTED_FUNCTION - red
    herring for the client (client presence/signon ride in-process consume_http).
    Server presence store is IN-MEMORY: restart wipes stored keys.
  - CLIENT LAUNCH: user does it via WHISKY GUI (bottle D1FB4A66-...). CLI launches
    (mac-port script or raw wine with that prefix) WEDGE at bootflow:start even on
    known-good builds - autonomous boots are NOT viable on the mac client (08-27).
    Rig client boot untested autonomously; user boots it.
  - Logs: server RE_output/s1_accept/Sunrise/logs/sunrise.log; each client
    <game>/Sunrise/logs/sunrise.log (mac: Game/bin/x64/Sunrise/logs/). Grep
    ev=steamnet / ev=activity / peers valid / ev=relay stage=register.
  - Rig: ssh master ~/.ssh/cm-rig to rasla@192.168.1.136 (ControlMaster socket;
    password needed only to REOPEN). Rig sleep disabled on AC (08-27). Rig game dir:
    C:\Users\rasla\Downloads\destiny-preservation\dcv build\bin\x64\.
  - Identities: Mac steamId ...861 (xuid ...ec5); rig ...862 (xuid ...ec6). Member
    keys are BOOT-SCOPED - reread per boot, do not hardcode.
  - Mac note: use /usr/bin/python3 for DB/sqlite work (miniconda's sqlite3 is
    broken here); plain `python3` for capstone; rg for corpus greps.

## NEXT-BOOT OBSERVABLES (friends lane, from BOOT_BRIEF_p2-62)
  success chain: rich_presence_store ok -> peer 'connect' key read cross-machine ->
  "Adding player [xuid=<peer>]" in managed_session -> tracking-data release ABSENT ->
  two guardians, one Tower instance. Failure branches pre-named in BOOT_BRIEF_p2-62.
## PARKED: rx-decode layer (20.92) | reason hunts (20.86) | blind sweeps
   (20.49-51) | posse fabrication (20.87) | type-54 bubble (per 20.96).
## READ FIRST (handoff)
  1. HANDOFF_OPENCODE_TO_CLAUDE_2026-08-27.md (this handoff; verify vs STATE)
  2. FINDINGS 20.96/20.97 + activity-name-table.md + activity-schema-global-table.md
  3. INCIDENT p2(59) file for the freeze rules; LESSONS PRE-BOOT CHECKLIST
  4. BOOT_BRIEF_p2-62.md = the standing test contract