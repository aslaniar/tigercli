STATUS: live (handoff opencode -> Claude, 2026-08-27 ~09:3x; verify against
STATE.md, which outranks handoffs when both are current).

# HANDOFF -> CLAUDE: friends cross-introduction, awaiting its first boot test

## 1. THE GOAL AND WHERE IT STANDS

Goal: two guardians in one Tower instance. The full retail chain already ran end
to end once (FINDINGS 20.93, boot of 08-26 ~22:30): search served, foreign
activity-host connection through our proxy, both clients saw `peer 1` in
activity membership - then both released it: "Could not find tracking data for
peer '1'" (20.82 link 4).

Root cause located and the fix IMPLEMENTED but NOT BOOT-TESTED:
- Tracking data = managed-session (platform-plane) player records. Built only
  when a player is added at the platform layer (20.96).
- Retail's join-target mechanism = SteamFriends rich presence: each client
  publishes key `connect` = "/connect:" + LE bytes of own xuid; friends read it
  and platform-join. VERIFIED: both clients attempted to publish exactly this
  (failed - stubbed) before 20.96 (20.96 has both hex strings).
- p2(64) implements it end to end: shim stores own keys + relays via server;
  friend enumeration/persona/rich-presence reads served for one peer. Deployed
  `4173ae4b3ad5bc7b` on BOTH machines, hash-identical.

## 2. YOUR ONE JOB: the boot test

Boot both machines (user does this - Whisky GUI launches; CLI launches wedge
at bootflow:start even on known-good builds, see 20.97/STATE OPERATIONAL
FACTS), get to the Tower, then read the three logs:
  mac client  Game/bin/x64/Sunrise/logs/sunrise.log
  rig client  C:\Users\rasla\...\dcv build\bin\x64\Sunrise\logs\sunrise.log
  server      RE_output/s1_accept/Sunrise/logs/sunrise.log (spans several boots)

Success chain, in order (BOOT_BRIEF_p2-62.md is the contract):
  1. `ev=steamnet stage=rich_presence_store result=ok` on both clients
  2. server /presence hits; each client reads the peer's 'connect' key
  3. managed_session "Adding player [xuid=<peer>]" (peer's xuid, LE)
  4. `Could not find tracking data for peer '1'` ABSENT
     -> two guardians in one Tower instance = MILESTONE.

Pre-named failure branches (BOOT_BRIEF_p2-62):
  - stores ok, no peer reads -> friend-enumeration slot mapping wrong
  - peer reads ok, no Add player -> connect-string semantics wrong (maybe
    needs session id not xuid) -> decode target identified
  - Add player ok, release still fires -> emit the 828-bit session-plane
    member table next (0x808086F8, layout in activity-schema-global-table.md)
  - freeze pre-title again -> NO; ordinals are verified now. If it somehow
    happens, capture the winedbg backtrace the user reported seeing.

## 3. ROLLBACK (memorize before booting)

p2(61) = `4d4aef769e5a16c4` = last known good (full chain ran on it, 20.93).
  mac: Game/bin/x64/steam_api64.dll.bak_p2d7_20260827_010620
  rig: ...steam_api64.dll.bak_p2d7_20260827_010634
Server exe `73a0f8f2f35327a7` stays regardless (presence routes are inert
without callers; the client's presence fetch is IN-PROCESS consume_http and
never touches the TLS listener - curl TLS failures on 8443 are a red herring).

## 4. SERVER OPS (verified 08-27 morning)

Running via `nohup bash mac-port/launch-server-macos.sh` (GPTK wine 7.7,
prefix ~/Library/Application Support/SunriseServer/pfx). It died overnight
once (cause unknown) -> that alone produces marionberry at login.
Verify aliveness in order:
  1. lsof TCP 8443/30975/8099 LISTEN + UDP 3074/3075/30976
  2. crafted UDP nat probe gets a 16-byte reply:
     python3 -c "import socket,struct; s=socket.socket(socket.AF_INET,
     socket.SOCK_DGRAM); s.settimeout(3);
     s.sendto(struct.pack('>HH',1,1),('192.168.1.164',3074));
     print(s.recvfrom(64)[0].hex())"
  3. server log: ev=discovery stage=reply lines appear
Presence state is IN-MEMORY: a server restart wipes stored keys (clients
republish on their next presence cycle, so just re-run the boot).

## 5. DO-NOT (each cost a boot or a crash)

- No client .text patching / no guessed interface ordinals. p2(59) vtable
  detours and p2(62/63) guessed friends slots each froze the client pre-title
  (INCIDENT p2(59) file, 20.97). Ordinals come from sdk isteamfriends.h.
- No reason-byte hunts on release (route closed 20.86; hook stays installed).
- No member-row blind sweeps (20.49-51); no region_private as cause (20.82);
  ws 701/702 are a known subclass-swap (20.82).
- Solo mac control boot before any two-machine run - ALWAYS (p2(59) incident).
- Do not boot autonomously via CLI on the mac: wedges at bootflow:start even
  on known-good builds (20.97 overnight note). User launches clients.

## 6. READ ORDER

1. STATE.md (verdict + deployed + hard rules) - outranks this file
2. FINDINGS 20.96/20.97 (layer identification + vtable audit),
   activity-name-table.md (types 0..57), activity-schema-global-table.md
   (the desc-pointer table + 828-bit session-plane member table = fallback
   emission target if the boot shows release-with-green-1-2-3)
3. BOOT_BRIEF_p2-62.md (the standing test contract)
4. RE_output/incidents/INCIDENT_2026-08-26_p2-59-freeze.md (closed; rules)
5. obf_fold.py exists (RE_scripts, self-test passed) if you hit obfuscated
   code; TOOLS.md registration still pending.

## 7. STATE OF THE TREE

Fork: upstream-gameplay-scoped @ p2(64) commits (0d14916 + c2764aa), clean.
Main repo: FINDINGS/STATE/index updated this morning; commit before starting.
Next fork number: p2(65). Server exe rebuilt with a TLS status log line
(4bccb09905052757, rebuilt 09:0x) - deployed exe is still 73a0f8f2; the
rebuild only adds a handshake-fail status log (safe to deploy with p2(65)).
