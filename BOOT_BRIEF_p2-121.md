# BOOT BRIEF p2(121) - THE PAIRED BOOT: DOES A *PEER'S* PROFILE APPLY?

STATUS: live (2026-08-30). Reads with FINDINGS 20.192 (the wire path proven, solo) and
20.188-20.191. FIRST TWO-MACHINE RUN SINCE THE PROFILE PATH OPENED.

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

CLAIM: with two clients in the same instance, each client's `ev=ingress stage=apply
path=WIRE` fires for a player row whose `index` is NOT its own - i.e. a peer's profile is
applied, not just the local player's.

CONTENT NEGATIVE (pre-named): wire fires occur but every one carries `index=0` and the
decoded body reports `players=1` on both machines - meaning the server never published two
player rows into one body, and the problem is server-side row composition, not the client.
Check the server's `ev=gameplay stage=membership result=built ... players=N` first: if N
never reaches 2, the client is exonerated before any client-side work starts.

SECOND CONTENT NEGATIVE: `players=2` bodies are built and delivered but the decoder returns
`ok=0` on them - the two-row body has an encoding fault the one-row body does not. That
sends the work back to `write_membership`'s row loop, not to the apply.

THIRD: both clients apply both rows cleanly and nothing renders. That is the EXPECTED
outcome of this boot and is a PASS, not a failure - it hands the front to the
character_record lane (20.173's root->account gap), which is the next structural blocker.

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
| Server composes a `players=2` body | ASSUMED - verified in p2(110) BEFORE the profile writer existed; never with it |
| Decoder accepts a two-row body | UNKNOWN - THIS BOOT |
| A client applies a PEER's profile row | UNKNOWN - THIS BOOT, the whole point |
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
  MAC client DLL `4baa7e81b152d5a1`  staging_populate FALSE, decoder_trace TRUE, ingress TRUE
  RIG client DLL `4baa7e81b152d5a1`  same - FIRST rig deploy carrying these instruments;
                 rig settings backed up as settings.json.bak_claude_p2d121
  lobby claims   CLEARED - server restarted 2026-08-30, `ladder` reports sessions:[]

## PRE-BOOT STATE (verified this session)
  - server process up, all four listeners present (tcp 30975; udp 3074/3075/30976)
  - solo control boots already done and healthy: p2(119), p2(120)

## AFTER THE BOOT - REQUIRED
`bash RE_scripts/capture_boot.sh p2-121` - it pulls BOTH client logs plus the server log.
