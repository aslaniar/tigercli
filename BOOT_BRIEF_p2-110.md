# BOOT BRIEF p2(110) - THE CLEAN PAIRED BOOT

STATUS: live (2026-08-29 ~13:1x). Author: Claude Code session.
Build under test: NOTHING NEW. Both clients `7849e28a58d40539`, server
`b9b0f3823f74d1bf` (p2(96)). ZERO DELTAS of any kind against the already-booted
p2(109) configuration: no code change, no rebuild, no memory writes, no
behaviour switch flipped, no logging change. The single difference from p2(109)
is that the mac is DISARMED (`admission_inject: false`), which it already was
post-boot. Both clients' log levels are already identical (all `debug`).

## PURPOSE

Answer the one question every paired boot since 2026-08-28 has been unable to
answer, because the mac was ARMED in every one of them:

  With BOTH clients unarmed on the current build, does 20.129's symmetric
  membership still hold - each client naming the OTHER at its real IP endpoint,
  `peers valid: 0x7`, `players valid: 0x2` - and do both then complete the
  public citizen join into PUB56.56 and land in the SAME activity instance?

WHY THIS IS NEW AND NOT A REPEAT. 20.129 measured the symmetric state on server
p2(86) on 2026-08-28, BEFORE the whole activity/slice-set switch set (p2(93):
`activity_slice_set_follows_region`, `activity_host_region_bound`,
`activity_region_survives_churn`, `activity_public_row_membership_bodies`) and
before the p2(96) censuses. Every paired boot after that - p2(102), (103),
(105), (106), (108), (109) - ran the mac ARMED with the admission forge, whose
injection poisons the mac's own bdNAT address structures. The unarmed pair on
the current build HAS NEVER BEEN RUN.

WHAT THIS BOOT EXPLICITLY DOES NOT TEST. It does not test the appearance blob
(never implemented - HANDOFF item 4), so it cannot decide whether two guardians
are VISIBLE. It does not test the admission forge (retired). It does not test
`dword[obj+0x524]` / the z-leg poller reject in isolation - p2(109) already
showed the rig completing the public citizen join, so that wall is not the
gate it was thought to be.

## GRAPHICS DELTA  (L12)

NOT zero, and this is deliberate and named. If the boot succeeds at the session
layer, each client renders ONE new never-rendered model: the peer guardian.
That is the co-presence render class parked at 20.110/20.111 ("phantom
duplicate + render death follow co-presence"). Minimisation actually in place:
  - `hold_spawn: true`, `spawn_hold_ms: 30000` on BOTH clients (already set) -
    the spawn waits for load rather than racing it.
  - The appearance blob is NOT implemented, so a peer that does replicate will
    resolve to a default/placeholder body, not a full custom armour set - the
    cheapest possible first co-presence render.
  - Mac renderer compiles shaders cold every launch (LESSONS #12): expect a
    long first-frame on the mac, do NOT read it as a stall before 90 s.
ACCEPTED RISK: a render death on co-presence is a REAL possible outcome. It is
also information (it would move the render class from parked to reproducible),
and it costs one boot. Rollback is a settings flip, not a rebuild.

## FALSIFIABLE CLAIM  (L6)

CLAIM: with both clients unarmed, each client's
`networking:session:membership:dump` for the `[group_target:...]` session
reaches `peers valid: 0x7, non-dormant: 0x7` with the third row naming the
other machine's REAL endpoint - mac sees `a=[192.168.1.136:3097:...]`, rig sees
`a=[192.168.1.164:3097:...]` - and `players valid: 0x2`.

PRE-NAMED CONTENT NEGATIVE 1 (the one that most changes the plan):
  If both clients reach `activity:in_world` and BOTH group_target dumps stay at
  `peers valid: 0x3` (host + self) for the whole boot, then 20.129's symmetric
  membership DID NOT survive p2(86) -> p2(96). The target then becomes that
  server diff - an enumerable, fully-owned set of changes - and NOT any
  client-side admission forge, which is retired either way.

PRE-NAMED CONTENT NEGATIVE 2:
  If both reach `peers valid: 0x7` but the server's `ev=activity stage=roster`
  stays `foreign=0` and `stage=peer_advert` stays `peer_citizen=0` for the whole
  boot, then session membership and the ACTIVITY roster are separate
  publications, and the activity-roster path is the next target - not membership.

PRE-NAMED CONTENT NEGATIVE 3:
  If both reach `peers valid: 0x7` AND `foreign=1`, but the two clients report
  DIFFERENT AH IDs / different `session id` in their citizen-join lines, then
  membership is solved and the gate is instance assignment.

## ABSENCE NEGATIVE  (L13)

If a client emits ZERO `membership:dump` lines: FIRST hypothesis is that the
measurement is invalid, not that membership is absent.
  - Liveness proof, mac: `grep -ac admission_census Game/bin/x64/steam_api64.dll`
    == 1 (VERIFIED this session). The mac's client log levels are ALREADY all
    `debug`, identical to the rig (VERIFIED this session) - no change needed and
    none made, so the 20.153 non-identical-instruments trap does not apply.
  - Liveness proof, rig: the rig already emitted 16 `membership:dump` lines in
    p2(109) at `client: debug` - the line is known-live on that machine.
  - Server liveness: `ev=activity stage=roster` fired 100+ times in p2(109);
    silence there means the server is not pumping, not that foreign==0.
If the PCAP is empty: the mac's "received by filter" counter is BOGUS (20.166,
hard-earned). An empty pcap is proven real ONLY by sending a probe packet
(python socket to 127.0.0.1:3097) and confirming it lands in the capture.
Route check first: `route -n get 192.168.1.136` must say en0.

## CHAIN MARKS  (L16)

  L1  both DLLs == 7849e28a58d40539            VERIFIED-BY-EXECUTION (hashed both, this session)
  L2  both clients unarmed                     VERIFIED-BY-READING (settings.json on both, this session:
                                               mac admission_inject=false; rig key absent -> defaults false)
  L3  both region_public=false, slice_set=56   VERIFIED-BY-READING (both settings.json, this session)
  L4  server b9b0f3823f74d1bf,                 VERIFIED-BY-EXECUTION (hash) + VERIFIED-BY-READING
      publish_join_machine_ids=true            (server.gameplay block, this session)
  L5  UDP 30976 is the SERVER, not a client    VERIFIED-BY-EXECUTION (lsof shows sunrise-server bound;
                                               `ev=gameplay stage=endpoint port=30976`; mac client log
                                               contains ZERO occurrences of 30976).
                                               *** THIS CORRECTS 20.167 R3/R4 AND 20.169 R3 ***
  L6  rig alone completes public citizen join  VERIFIED-BY-EXECUTION (p2(109) rig log t=80860
      into PUB56.56 and holds in_world         "Citizen join ... succeeded!", in_world t=80079..610625)
  L7  mac alone, UNARMED, does the same        UNKNOWN  <- resolved by this boot
  L8  both clients hold each other as          VERIFIED-BY-EXECUTION on p2(86) ONLY (20.129);
      established peers at real endpoints      ASSUMED on the current build  <- resolved by this boot
  L9  both land in the SAME activity instance  UNKNOWN  <- resolved by this boot
  L10 two guardians VISIBLY render             UNKNOWN - depends on the appearance blob (never
                                               implemented) and the parked render class (20.110/20.111).
                                               NOT claimed by this boot.

No link is marked "one boot away". L7/L8/L9 are the three this boot resolves;
L10 is explicitly out of scope.

## ADVERSARIAL PASS: waived: this boot ships ZERO behaviour change, ZERO memory
writes, ZERO new code, no wire/codec encode change, and - after the settings
check - zero deltas of ANY kind against the already-deployed, already-booted
p2(109) configuration beyond the mac being disarmed. Both clients' log levels
were already identical, so the 20.153 trap (an asymmetry read off non-identical
instruments) does not apply and nothing had to be touched to avoid it. U7's
escalation trigger guards a third fix-guess riding a boot; there is no fix in
this boot to guess wrong. Recorded as a waiver, not a pass.

## INSTRUMENTS: admission_census, admission_inject, nat_probe

Per-binary literal check (gate_boot.py --literals cannot span two binaries -
known gap, 20.157 tool note; take the structural gate plus this explicit check):
  - mac  Game/bin/x64/steam_api64.dll                 : all three present (VERIFIED this session)
  - rig  "dcv build\bin\x64\steam_api64.dll"          : same file hash 7849e28a58d40539 (VERIFIED)
Both binaries are byte-identical, so one literal check covers both.

## PRE-BOOT SEQUENCE (in order, one long-running action per step)

  1. (no settings delta - verified both clients already all-`debug` and the mac
     already disarmed; the settings file was left byte-identical, hash
     897f17e7708d61b9)
  2. `bash RE_scripts/reset_lobby_claims.sh` - MANDATORY (stale in-memory lobby
     claims silently invalidate any paired test from p2(67) on). KNOWN BUG
     (20.167): its relaunch leg can silently fail leaving listeners 0/3 - VERIFY
     4/4 listeners after, and if it failed launch
     `mac-port/launch-server-macos.sh` directly with captured output.
  3. `route -n get 192.168.1.136` must report en0; `arp -a | grep 192.168.1.136`
     must NOT show a "permanent" self-referential entry (20.166(c) / 20.167 -
     with it present the rig is unreachable).
  4. Start capture: tcpdump on en0 AND lo0, 4-port filter, then the probe-packet
     liveness check.
  5. Launch RIG first. Wait for `activity:in_world` in its log.
  6. Launch MAC. Let both sit ~5 min in the tower.
  7. Collect: both client logs, server log, both pcaps.
