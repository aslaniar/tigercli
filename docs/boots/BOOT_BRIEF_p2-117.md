# BOOT BRIEF p2(117) - THE REGION-B FIX: DOES THE DECODER ACCEPT OUR BLOCK NOW?

STATUS: live (2026-08-30). Reads with FINDINGS 20.188 (the ret=0 capture) and the
region-B reader spec (0x1416D3C30, read to its unconditional `mov al,1` return).

## PURPOSE - what this boot learns, win or lose

p2(116) captured the decoder returning FALSE for the body carrying our profile block and
TRUE for the members-only body in the same millisecond. The cause is now named: our writer
emitted region B as ONE presence bit; the reader takes FOUR. The client consumed our single
bit as flag 1, ate the first three bits of the 104-bit tail as flags 2-4, and read every
field after region B three bits early - overrunning the body on the trailing 32-bit state
hash, which sets the reader's error flag. The writer now emits four. Block total 178 -> 181
bits (verified by summing the field widths from source: 180 + the caller's gate bit).

This boot asks ONE question: does `ok` flip from 0 to 1 on the player-bearing body?

## GRAPHICS DELTA

ZERO new rendered models expected. Solo mac run, write detour still disarmed. If `pc=1`
lands, a row's profile is applied for the first time - that is a LOG event, not a render;
region A carries identity only (20.173) and appearance is a different data family
(character_record, not the session block). Minimized: one machine, no rig, no peer.

## FALSIFIABLE CLAIM (the one contract under test)

CLAIM: with region B written as four presence bits, the decoder 0x14173BFC0 returns
NONZERO for the membership body carrying our player row.

CONTENT NEGATIVE (pre-named): `ev=dtrace stage=decoded ... ok=0` on a call whose paired
dump shows `players>=1` means the three-bit underrun was NOT the whole failure. The next
read is then the tail's own field widths and the trailing state hash, since those are the
fields the underrun was corrupting and they have never been verified independently.

SECOND CONTENT NEGATIVE (named in advance by the region-B lane): `ok=1` but the profile
still does not apply. The apply's region-B copy is an unconditional 136 bytes and nothing
proves the decoded struct's region-B area is zeroed, so a stale-byte copy could fail a
state hash downstream. DO NOT pre-solve this. Log it and stop.

## ABSENCE NEGATIVE (L13 - what ZERO instrument lines means)

- Zero `stage=install`: DLL did not load or `decoder_trace` false. Boot says nothing.
- `stage=install` present, zero `stage=decoded`: the decoder never fired. Contradicts
  p2(115) and p2(116); indicts the build, not the finding.
- Zero `stage=decoded_row` lines: no body in the run carried a player row, so the claim
  was never exercised. NOT a refutation - re-run. `stage=decoded` prints `players=`
  unconditionally, so this case is always distinguishable from a real ok=0.
- Zero `stage=staging`: EXPECTED, the detour is disarmed. Their presence is a bug.

LIVENESS LINE: `ev=dtrace stage=install result=ok staging_populate=0 decoder=0x173BFC0 apply=0x1781800`

## CHAIN MARKS (L16)

| Link | Mark |
|---|---|
| Boot, signon, activity join, region seeding, membership, transport | VERIFIED-BY-EXECUTION (p2(110)) |
| Body delivered + acked | VERIFIED-BY-EXECUTION (20.182 R1) |
| Decoder REJECTS the one-bit region-B block | VERIFIED-BY-EXECUTION (20.188 R1, ret=0x0) |
| Region B wire = 4 presence bits + payloads | VERIFIED-BY-READING (reader 0x1416D3C30, full body) |
| Writer now emits 4 bits, block = 181 | VERIFIED-BY-READING (source field-width sum) |
| Decoder ACCEPTS the corrected block | UNKNOWN - this boot |
| Row base 0x4240 | VERIFIED-BY-EXECUTION (20.188 R3) |
| Staging / stage-6..9 routing | VERIFIED-BY-READING, UNREACHABLE until the decode passes |
| Appearance = character_record family, peer's record unservable (no root->account resolution) | VERIFIED-BY-READING (20.173) - NOT on this boot's path |
| Render / co-presence | UNKNOWN (parked) |

## INSTRUMENTS

INSTRUMENTS:
  ev=dtrace stage=decoded
  ev=dtrace stage=staging
  staging_populate=%u

## LITERAL TARGETS

LITERAL TARGETS:
  Game/bin/x64/steam_api64.dll: ev=dtrace stage=decoded, ev=dtrace stage=staging, staging_populate=%u

## ADVERSARIAL PASS

ADVERSARIAL PASS: waived: solo observation run, write detour disarmed, no new hook RVAs

waived: the only behaviour change is three extra zero bits in a body the client already
receives, and the server rollback is publish_player_profile=false (settings flip, no
rebuild) or the *.bak_p2d6_<stamp> exe. Client instrument unchanged from p2(116) except
for a relink.

## DEPLOYED FOR THIS BOOT
  server exe     `649c8da9f0e501fc` - region B 1 -> 4 presence bits. All seven deploy
                 gates passed; membership-wire-test and sweep-test rc=0, failures=0.
  MAC client DLL `f6fee86c573051a7` - same instrument as p2(116), relinked.
  settings       server publish_player_profile TRUE; client decoder_trace TRUE,
                 staging_populate FALSE.

## AFTER THE BOOT - REQUIRED
`bash RE_scripts/capture_boot.sh p2-117` BEFORE any other run starts.
