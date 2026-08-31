# BOOT BRIEF p2(116) - THE DECODE VERDICT + THE ROW BASE (staging detour built, DISARMED)

STATUS: live (2026-08-30). Reads with FINDINGS 20.187 (the run-to-run variance),
20.183-20.185 (the staging diagnosis), HANDOFF_2026-08-29_STAGE-TRAY.md.

## PURPOSE - what this boot learns, win or lose

Three things, none of which needs the write detour to fire:

1. **Does our profile block DECODE?** The decoder 0x14173BFC0 returns a boolean its caller
   at 0x1416E33AC tests (`test al,al; je` -> the `[rbx+9]=1` abort store, VERIFIED-BY-
   READING this session). Nobody has ever logged that return value. `ok=0` on a
   player-bearing body means our bytes ARE malformed and the "our bytes were never the
   problem" headline is wrong; `ok=1` means the decode succeeds and the loss is downstream.
2. **Where is player row 0?** 20.184 R1 leaves the row base UNRESOLVED between +0x4240 and
   +0x4280 (the member-delta stride 0xb8 x2 ends near 0x4280). The staging detour NEEDS
   this base to point region A at real data, and the handoff flags it as a prerequisite.
   This boot dumps 64 bytes at 0x4240, 0x4280 AND 0x43c0 on any body with players>0,
   settling it from one run instead of guessing.
3. **Which KIND of run did we get?** 20.187 measured two runs of the same build+settings
   behaving differently - one applying player rows, one never doing so. Until we can tell
   them apart at read time, any result from a staging experiment is uninterpretable.
   `stage=decoded players=N` vs `stage=update players=N` separates them directly.

The staging write detour ships in the same DLL but is DISARMED. It is flipped by a
settings key with NO rebuild, so if this run reaches the players=1 apply state the user can
arm it and re-run immediately.

## GRAPHICS DELTA

ZERO new rendered models. This is a solo mac run; the detour is disarmed, so nothing new
is applied and nothing new is drawn. Minimized by construction: single machine, no rig, no
peer, no second guardian. (L12)

## FALSIFIABLE CLAIM (the one contract under test)

CLAIM: the decoder 0x14173BFC0 returns NONZERO for the membership body that carries our
player row with the profile-present gate set.

CONTENT NEGATIVE (pre-named, L6): `ev=dtrace stage=decoded ... ok=0` on a call whose paired
`stage=decoded ... players>=1` dump shows a row means THE DECODE FAILS on our block. That
retires the staging lane outright and sends the work back to the writer - specifically to
region A's chunk encodings, since 20.180 verified only the EXIT conditions, never that the
reader consumed the bits we wrote.

SECOND CONTENT NEGATIVE: `ok=1` with `players=0` on every single call means this run is a
20.187-type-two run and the boot answers question 3 only. That is a REAL result, not a
failure - it tells us the state is not reliably reproducible and the next move is to find
what makes a run apply player rows, before spending anything on staging.

## ABSENCE NEGATIVE (L13 - what ZERO instrument lines means)

- Zero `ev=dtrace stage=install` lines: the DLL did not load or `decoder_trace` is false.
  Instrument did not run; the boot says NOTHING about decoding. Check the deployed hash.
- `stage=install` present but zero `stage=decoded` lines: the decoder hook attached and the
  decoder never fired - dispatch never reached it. That contradicts p2(115), where it fired
  16 times, and would indict the build, not the client.
- Zero `stage=<...>_row` lines: no body in the whole run carried a player row. This is the
  20.187 type-two run and is EXPECTED to be possible; it is not an instrument failure,
  which is why `stage=decoded` prints `players=` unconditionally as the liveness witness.
- Zero `stage=staging` lines: EXPECTED. The detour is disarmed this run. Their absence
  confirms disarm; their PRESENCE on a disarmed run is a bug and invalidates the boot.

LIVENESS LINE (must appear if the instrument ran at all, independent of outcome):
`ev=dtrace stage=install result=ok staging_populate=0 decoder=0x173BFC0 apply=0x1781800`

## CHAIN MARKS (L16 - every link, marked)

| Link | Mark |
|---|---|
| Boot, signon, activity join, region seeding | VERIFIED-BY-EXECUTION (p2(110), p2(115)) |
| Session membership + transport symmetric | VERIFIED-BY-EXECUTION (p2(110)) |
| Server writes the profile block, bit-exact | VERIFIED-BY-READING + smoke (20.178/20.179) |
| Body delivered and acked | VERIFIED-BY-EXECUTION (20.182 R1, 91 sendqueue lines) |
| Decoder fires on our bodies | VERIFIED-BY-EXECUTION (p2(115), 16 calls) |
| Decoder RETURN value on a player-bearing body | UNKNOWN - this boot |
| Player row base (0x4240 / 0x4280 / 0x43c0) | UNKNOWN - this boot |
| Apply runs for a player-bearing body | VERIFIED-BY-EXECUTION in one run, CONTRADICTED in another (20.187) |
| Staging slot [+0x1af60] has no readable writer | VERIFIED-BY-READING (20.185 R2) |
| Apply reads profile from staging [+0x19/+0x1c/+0x20/+0x28/+0x198] | VERIFIED-BY-READING (20.183 R2) |
| Populating staging makes the row apply | UNKNOWN - NOT tested this boot (detour disarmed) |
| Region B layout (136B, the appearance candidate) | UNKNOWN - parallel lane, sample data already on disk (20.187 R6) |
| Render / co-presence | UNKNOWN (parked 20.110/20.111) |

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

waived: solo single-machine observation run, write detour disarmed by settings, no server
rebuild, no new hook addresses (both RVAs re-verified as .pdata function starts by
verify_hook_rvas.py this session: kDecoderRva 0x173BFC0 ok, kApplyRva 0x1781800 ok).
Rollback is a settings flip plus the previous DLL, which is on disk.

## THE WRITE DETOUR (built, DISARMED, read before arming)

This is the FIRST write detour this project has shipped. The p2(102)-p2(109) admission
poisonings were write detours done carelessly: they wrote into the mac's OWN bdNAT
structures and silently invalidated eight boots (20.170). The shape here makes that failure
mode unreachable:

- It NEVER writes through a client pointer. The apply's incoming r8 is logged and
  DISCARDED. This is deliberate: 20.184 R2 showed those values are TLS tick counts, not
  addresses, so the handoff's literal instruction ("populate staging[+0x19]...") would have
  been a wild write to an arbitrary address.
- It SUBSTITUTES a static buffer we own (0x400 bytes, plus a 232-byte region A and a
  20-byte tail), populated with gate=1, header1=0, mask=0x109, and pointers to our own
  region A and tail. Static, not stack, because the callee may retain the pointer.
- It arms ONLY when the decoded update carries a player row (players>0), so members-only
  applies keep their original argument and their original behaviour.
- It is capped at 8 substitutions per run and logs every one, including the discarded
  pointer.
- Disarm is `client.staging_populate = false` - no rebuild. Rollback is the prior DLL,
  on disk as steam_api64.dll.bak_p2d7_<ts>.

## AFTER THE BOOT - REQUIRED

Run `bash RE_scripts/capture_boot.sh p2-116` BEFORE any other run starts. p2(115)'s client
log was overwritten because this step was skipped, which cost this session a whole
false-retraction cycle (20.187 R5).
