# BOOT BRIEF p2(122) - THE PAIRED BOOT, SYMMETRIC: DOES THE *MAC* APPLY THE PEER'S ROW?

STATUS: live (2026-08-30). Reads with FINDINGS 20.193 (p2(121): confirmed on the rig,
unmeasured on the mac) and 20.192.

## WHY THIS BOOT REPEATS p2(121)

p2(121) PROVED the claim one-way: the rig ran the profile helper 21 times on row index=1 -
the mac's row, applied from the wire. The mac could not answer the same question because
its observer budget was gone four minutes before the peer arrived (it idled in the Tower
while the rig's trap-18 launch failure was repaired). Budgets are now keyed on
(path, row index), so index 0 can no longer starve index 1 on either machine. Nothing else
changed: same server, same disarmed detour, same settings.
PROCEDURE CHANGE THAT MATTERS: launch both clients CLOSE TOGETHER. p2(121)'s asymmetry was
caused by run length, not by code, and a long solo idle can still waste a class budget.

## PURPOSE - what this boot learns, win or lose

Every boot from p2(116) to p2(120) was SOLO: one client, `members=2 players=1`, and the
profile row being applied was the client's OWN. The wire path is proven for that case
(20.192). It has never been tested with two machines, which is the case the whole project
is for. This boot puts the rig and the mac in the same instance and asks whether each
client applies the OTHER's player row.

## GRAPHICS DELTA

TWO guardians would be the maximum possible new rendered models, and NEITHER is expected to
appear. The block we publish is the minimal EMPTY profile (region A = 232 zero bytes), and
appearance is not in this data family at all (character_record - 20.173). What is under test
is whether the profile APPLY fires for a peer's row. Do not read an absent guardian as a
failure of this boot; read the log lines. Minimization is not possible below two machines -
two is the minimum that can express the claim.

## FALSIFIABLE CLAIM (the one contract under test)

CLAIM: BOTH clients emit `ev=ingress stage=apply path=WIRE index=1` - i.e. each applies the
other's profile row, not only its own. The rig half is already VERIFIED (20.193 R3); this
boot is for the mac half and for reproducing the rig's.

CONTENT NEGATIVE (pre-named): the mac reaches `members=3 players=2` applies (its uncapped
`stage=update` lines prove arrival) but emits NO `path=WIRE index=1` line, while the rig
does. That is a REAL asymmetry between the two clients and not a budget artifact this time -
the mac's index=1 class has its own untouched 24-line budget. It would mean the two clients
take different apply paths, and the next read is why the mac's session differs.

SECOND: neither machine emits index=1. Then 20.193 R3 does not reproduce and the rig's 21
fires need re-examination before anything is built on them.

THIRD: both clients apply both rows cleanly and nothing renders. That is the EXPECTED
outcome and a PASS - it hands the front to the character_record lane (20.173's root->account
gap), the next structural blocker.

FOURTH, the render observation: the mac's screen went black as the rig loaded in p2(121)
(20.193 R6) - a render black, not a freeze. Note whether it reproduces. Do not chase it in
this boot; it is an observation riding along, not the contract.

## ABSENCE NEGATIVE (L13 - what ZERO instrument lines means)

- Zero `stage=install` on EITHER machine: that machine's DLL did not load. Both must show it.
- `staging_populate=1` in any install line: the detour is armed and this boot is void -
  20.191 proved substitution SUPPRESSES the helper. Both machines must read 0.
- Zero `ev=ingress path=WIRE` on a machine whose peer joined: the profile path did not run
  there. Compare against that machine's `stage=decoded players=` to see whether a
  player-bearing body ever arrived.
- Zero `ev=dtrace` on the rig specifically: the rig has never carried these instruments
  before this session. Its DLL is 4baa7e81b152d5a1 and its `decoder_trace` was null until
  today - if the rig is silent, suspect its settings file before suspecting the client.

LIVENESS LINE (both machines):
`ev=dtrace stage=install result=ok staging_populate=0 decoder=0x173BFC0 apply=0x1781800`

## CHAIN MARKS (L16)

| Link | Mark |
|---|---|
| Boot, signon, join, region, membership, transport, co-location (PAIRED) | VERIFIED-BY-EXECUTION (p2(110)) |
| Server publishes a profile block, 181 bits | VERIFIED-BY-EXECUTION (20.189, solo) |
| Decoder accepts it | VERIFIED-BY-EXECUTION (20.189 R1, 29/29, solo, players=1 bodies) |
| Apply runs + helper fires from the wire | VERIFIED-BY-EXECUTION (20.192, solo, own row) |
| Server composes a `players=2` body | VERIFIED-BY-EXECUTION (20.193 R1, 69 bodies) |
| Decoder accepts a two-row body | VERIFIED-BY-EXECUTION (20.193 R2, both machines applied players=2) |
| A client applies a PEER's profile row | VERIFIED-BY-EXECUTION on the RIG (20.193 R3, 21 fires index=1); UNMEASURED on the mac - THIS BOOT |
| Staging substitution suppresses the helper | VERIFIED-BY-EXECUTION (20.191 R2 / 20.192 R2) - detour DISARMED both machines |
| Appearance content (character_record, peer's record unservable) | VERIFIED-BY-READING (20.173) - NOT this boot |
| Render / co-presence | UNKNOWN (parked 20.110/20.111) |

## INSTRUMENTS

INSTRUMENTS:
  ev=dtrace stage=decoded
  ev=dtrace stage=staging
  path=%s

## LITERAL TARGETS

LITERAL TARGETS:
  Game/bin/x64/steam_api64.dll: ev=dtrace stage=decoded, ev=dtrace stage=staging, path=%s

## ADVERSARIAL PASS

ADVERSARIAL PASS: waived: no new hook RVAs, no server change, both write detours disarmed

waived: server exe unchanged from p2(117) and re-verified 649c8da9f0e501fc after a manual
relaunch; both clients on the same DLL 4baa7e81b152d5a1; the only behaviour under test is
one already proven solo, now with a second machine present.

## DEPLOYED FOR THIS BOOT
  server exe     `649c8da9f0e501fc` (region B = 4 presence bits; publish_player_profile TRUE)
  MAC client DLL `cadb28325fb3e7cf`  per-(path,index) budgets; detour DISARMED
  RIG client DLL `cadb28325fb3e7cf`  same build, deployed and literal-checked
  lobby claims   NOT cleared since p2(121) - see PRE-BOOT below

## PRE-BOOT STATE (verified this session)
  - server process up, all four listeners present (tcp 30975; udp 3074/3075/30976)
  - solo control boots already done and healthy: p2(119), p2(120); paired: p2(121)
  - LOBBY CLAIMS: reset_lobby_claims.sh restarts the server and then HANGS (STATE hard
    rule); an interrupt kills the server. p2(121) ran fine on the claim table left by the
    p2(120) restart, so a reset is NOT required here. If one is wanted, run it and let it
    hang, then recover per ENVIRONMENTS "SERVER DIED AFTER AN INTERRUPTED SCRIPT".

## AFTER THE BOOT - REQUIRED
`bash RE_scripts/capture_boot.sh p2-122` - it pulls BOTH client logs plus the server log.
