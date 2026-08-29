# BOOT BRIEF p2(112) - THE PROFILE HARVEST (SOLO MAC)

STATUS: live (2026-08-29 ~14:0x). Author: Claude Code session.
Reads with FINDINGS 20.145, RE_output/claims/profile-builder.md (CLAIM 2/4), and
20.172 (the p2(110)/p2(111) correction that named this front).
SOLO MAC BOOT. The rig is NOT launched and the pairing is NOT exercised.
Client DLL `975b0be1ae154308` on BOTH machines (aligned; the rig is simply unused).
Server unchanged `b9b0f3823f74d1bf`, `membership_peer_retry_cap` REVERTED to 2.

## PURPOSE

p2(110) proved the networking chain is finished: both clients reach
`[AC PUBLIC TARGET CON-Y EST-Y AH->9eaa300100200003 MEM-5]`, hold `peers 0x7 /
players 0x3` at real endpoints, and land in ONE instance on a direct
client-to-client channel. What is missing is APPEARANCE:
```
  fireteam self row      pc=1     <- a real profile exists locally
  group_target host row  pc=0
  group_target peer row  pc=0
  group_target SELF row  pc=0     <- not even the local player has one there
```
`pc` is the profile-present flag (20.145). No profile, nothing to draw.

The blob is opaque and SELF-HASHED, so it must be REPLAYED, never synthesized
(20.145). This boot harvests a real one. It is the HARVEST HALF ONLY - no replay,
no server change, no write of any kind.

WHY SOLO IS SUFFICIENT (and why a paired boot would be waste): the registry profile
is the client's own LOCAL store and is "present and stable every boot, INDEPENDENT
OF THE WIRE" (profile-builder CLAIM 2). Nothing about the harvest needs a peer, a
pairing, or the server. A paired boot would add the rig's failure modes for zero
information.

WHAT THIS BOOT DOES NOT TEST. It does not replay anything, so it cannot make a
guardian visible. It does not touch admission (retired), the retry cap (reverted),
or the rig's pre-existing black screen (user-confirmed as long-standing).

## GRAPHICS DELTA  (L12)

ZERO new rendered models. Solo boot, no peer, no replay, no profile written
anywhere. The mac renders exactly what it rendered in p2(110), which was correct
and fully controllable. The only cost is the mac's usual cold shader compile.

## FALSIFIABLE CLAIM  (L6)

CLAIM: with `profile_harvest: true`, the mac logs `ev=profile stage=install
result=ok`, then at least one `ev=profile stage=commit` line carrying a nonzero
`hash=` and nonzero `regionA=`/`tail=` pointers, followed by `ev=profile stage=dump
tag=regionA ok=1` chunks totalling 232 bytes and `tag=tail ok=1` totalling 20 bytes.

PRE-NAMED CONTENT NEGATIVE 1 (the one that most changes the plan):
  If `stage=commit` fires but every `stage=dump` reports `ok=0 why=seh`, then the
  argument map read from the call site at 0x14176681a is WRONG - a5..a9 do not land
  where profile-builder-raw PHASE 2 says. In that case do NOT re-guess the slot
  order: dump the raw stack window at entry and let the bytes name the layout.

PRE-NAMED CONTENT NEGATIVE 2:
  If `stage=install result=ok` appears and NO `stage=commit` line ever does, the
  wrapper 0x1417a6040 is not on the live path in this configuration (it is reached
  through a version-change test plus a freshness throttle). The fallback is then the
  committer 0x1417664C0 itself, accepting the mid-function r15 read that this design
  deliberately declined - and that is a decision to take deliberately, not a retry.

PRE-NAMED CONTENT NEGATIVE 3 (partial, expected as a real possibility):
  Region B (136B of the 396B) is NOT harvested here and cannot be - PHASE 5 found it
  is written ONLY from a wire delta and PHASE 6 proved no profile is ever on our wire.
  A dump missing region B is the DESIGNED outcome, not a failure. If a later replay
  turns out to need region B, that is a separate open lane (raw PHASE 5/7).

## ABSENCE NEGATIVE  (L13)

If ZERO `ev=profile` lines of ANY kind appear: FIRST hypothesis is that the
measurement is invalid, not that no profile exists.
  - Deployment provenance (L14): `grep -ac "ev=profile stage=commit"` on the DEPLOYED
    mac DLL == 1 (VERIFIED by deploy_client_dll.sh, which greps the deployed file).
  - Arming provenance: `profile_harvest` must read true in the mac's settings.json.
    If it is false the observer logs `stage=install result=skipped why=disarmed` -
    so even the disarmed path is LOUD, and total silence indicts the DLL load, not
    the setting.
  - The install line is unconditional once armed, so `install result=ok` with no
    `commit` is content negative 2, NOT an absence.

## CHAIN MARKS  (L16)

  L1  networking chain complete (EST-Y, MEM-5,
      peers 0x7, players 0x3, one instance)      VERIFIED-BY-EXECUTION (p2(110), both machines)
  L2  every group_target row is pc=0             VERIFIED-BY-EXECUTION (p2(110), both machines)
  L3  pc is the profile-present flag             VERIFIED-BY-READING (20.145)
  L4  a real blob exists in the local registry
      (fireteam self row pc=1)                   VERIFIED-BY-EXECUTION (p2(110)) +
                                                 VERIFIED-BY-READING (CLAIM 2)
  L5  0x1417a6040's entry args carry marker +
      region A + header + tail + expected hash   VERIFIED-BY-READING (raw PHASE 2, call
                                                 site 0x14176681a) - NOT yet executed
  L6  the harvest reads those args correctly     UNKNOWN  <- THIS BOOT RESOLVES L6
  L7  a replayed blob sets pc=1 on a
      group_target row                           UNKNOWN - not attempted, needs L6 first
  L8  two guardians VISIBLY render               UNKNOWN - behind L7, and behind region B
                                                 if the replay turns out to need it

No link is written as "one boot away". L6 is the only link this boot resolves.

## ADVERSARIAL PASS: waived: read-only observation, no writes of any class, no server
change, solo (no peer, no pairing), zero new rendered models, and gated by a setting
that defaults FALSE so it disarms with no rebuild. This is the FIRST attempt at the
profile front - the three failed attempts today (render hypothesis, retry cap,
`Adding player` as an instrument) were all on the ADMISSION/MEMBERSHIP question,
which p2(110) closed; U7's trigger counts attempts at a question, and this is a new
one. The design also follows an EXISTING verified lane deliverable rather than a
fresh inference. STATED RISK, not waived away: this is a detour on an INTERNAL
function - the same mechanism that poisoned the mac across p2(102)-p2(109). That
mechanism was destructive there because it WROTE; this one only reads, dereferences
exactly two pointers, and guards both with SEH. Recorded as a waiver, not a pass.

## INSTRUMENTS: ev=profile stage=commit, ev=profile stage=dump, ev=profile stage=install

Verified present in the DEPLOYED mac DLL `975b0be1ae154308` by
deploy_client_dll.sh's literal grep (it greps the deployed file, not the build dir).
The rig carries the identical binary and is not launched this boot.

## PRE-BOOT SEQUENCE

  1. DONE - client DLL built `975b0be1ae154308`, deployed and hash-asserted on BOTH
     machines; literal verified in the deployed file.
  2. DONE - `profile_harvest: true` armed on the MAC only; `admission_inject` stays
     false; rig has no `profile_harvest` key and defaults false.
  3. DONE - server settings reverted (`membership_peer_retry_cap` 2).
  4. Restart the server so the reverted cap loads, and clear claims:
     `bash RE_scripts/reset_lobby_claims.sh` (verify 3/3 + nat ok + claims 0).
     Not strictly required for a solo harvest, but it leaves the machine in the
     known-good p2(110) configuration for whatever runs next.
  5. Clear the mac client log slate.
  6. Launch the MAC only. Reach character select and enter the world; the commit
     loop runs on the roster/profile sync tick, so orbit is enough - no Tower
     required. Dwell ~2 min.
  7. Collect the mac client log into RE_output/captures/p2-112_profile_harvest/.
     NO pcap needed: the harvest is client-internal and touches no wire.
