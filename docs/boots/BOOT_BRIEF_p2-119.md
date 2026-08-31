# BOOT BRIEF p2(119) - THE SAME EXPERIMENT, WITH AN OBSERVER THAT CAN SEE IT

STATUS: live (2026-08-30). Reads with FINDINGS 20.190 (why p2(118) was a false negative),
20.189, 20.188.

## WHY THIS BOOT REPEATS p2(118)

p2(118)'s detour worked: 8/8 substitutions on player-bearing bodies, every one against a
NULL pointer, zero skips, no crash. But profile_ingress gates its whole report behind a
single 8-line budget, and the local registry commits spent all eight during load - 35
seconds before the staging window opened. A wire-path fire would have printed NOTHING.
The boot could not answer its own question. The observer now has separate budgets per
caller class, so the local burst can no longer starve the wire path, and every line is
labelled path=WIRE or path=local. Nothing else changed - same server, same detour, same
arming.

## PURPOSE - what this boot learns, win or lose

p2(117) fixed the decode (29/29 pass) and the apply now runs on player-bearing rows for the
first time. It arrives with a NULL third argument at session stage 4, so the apply reads its
profile fields - gate, header, mask, region-A pointer, tail pointer - out of NULL and applies
nothing. This boot substitutes a staging object we own for that NULL and asks whether the
apply then runs its profile helper.

THIS IS THE FIRST WRITE DETOUR THIS PROJECT HAS SHIPPED. Read the SAFETY section.

## GRAPHICS DELTA

ZERO new rendered models expected. Solo mac run; the row being applied is the local player's
own. A success here is a LOG event (the profile helper firing from a wire caller), not a
render. Appearance is a different data family entirely (character_record - 20.173), so no
guardian can appear from this boot and none should be looked for. Minimized: one machine.

## FALSIFIABLE CLAIM (the one contract under test)

CLAIM: with a populated staging object substituted for the NULL third argument, the apply
0x141781800 invokes its profile helper, and `ev=ingress stage=apply` records a line reading
`path=WIRE`.

CONTENT NEGATIVE (pre-named): substitutions logged (`ev=dtrace stage=staging ... nth=N`) but
still zero non-0x17A6101 helper fires means the staging object's SHAPE is wrong - the five
offsets are right individually but something else in the object gates the helper. The next
read is then 0x1417806C0's body, not another field guess.

SECOND CONTENT NEGATIVE: the helper fires but with mask/hash values that do not match what we
wrote (mask 0x109, hash 0) means the apply is sourcing region A from somewhere other than our
buffer, and the pointer fields are not what 20.183 R2 read them to be.

THIRD, from the region-B lane: the helper fires and then a downstream state hash mismatches,
because the apply's unconditional 136-byte region-B copy moved bytes we did not model. DO NOT
pre-solve this. Log it and stop.

## ABSENCE NEGATIVE (L13 - what ZERO instrument lines means)

- Zero `stage=install`: DLL did not load. Boot says nothing.
- `stage=install` with `staging_populate=0`: THE DETOUR IS DISARMED and the boot tests
  nothing. This is the liveness check that matters most this run - the settings flip is the
  entire experiment.
- Zero `stage=staging` lines WITH `staging_populate=1` in the install line: no player-bearing
  body arrived with a NULL pointer, so the detour never armed. NOT a refutation - re-run.
- `stage=staging result=skipped why=non_null_r8`: a player-bearing body arrived with a
  NON-null pointer. The detour deliberately passes those through. If this is the only staging
  line, the p2(117) measurement did not reproduce and that is the finding.
- Zero `ev=ingress` lines at all: the observer is off. Confirm `client.profile_ingress = true`.
- `ev=ingress` lines present but ALL `path=local`: the wire path genuinely never fired. This
  is now a REAL negative rather than p2(118)'s budget artifact, because the wire class holds
  its own 8 dumps that the local burst cannot consume.

LIVENESS LINE: `ev=dtrace stage=install result=ok staging_populate=1 decoder=0x173BFC0 apply=0x1781800`

## SAFETY - why this write detour cannot repeat p2(102)-p2(109)

The admission poisonings wrote into the client's OWN live structures and silently invalidated
eight boots. Every property below is the opposite of that, and each is checkable in the source:

1. It NEVER writes through a client pointer. The incoming third argument is logged and
   discarded, never dereferenced. 20.184 R2 showed those values are TLS tick counts on the
   stage-2 path, so writing through one would be a wild write to an arbitrary address.
2. It substitutes only where the client passes NULL - displacing nothing, because there is no
   client object at that address to lose (8/8 player-bearing applies in p2(117)).
3. A non-null pointer on a player-bearing body is passed through UNTOUCHED and logged.
4. Members-only applies (players=0) are never touched; they keep their original argument and
   their original behaviour.
5. The buffers are ours: static, process-lifetime (the callee may retain the pointer), zeroed
   before every fill.
6. Capped at 8 substitutions per run, each one logged with the discarded pointer.
7. Disarm is `client.staging_populate = false` - a settings flip, no rebuild. Rollback is the
   prior DLL on disk.

## CHAIN MARKS (L16)

| Link | Mark |
|---|---|
| Boot, signon, join, region, membership, transport | VERIFIED-BY-EXECUTION (p2(110)) |
| Body delivered + acked | VERIFIED-BY-EXECUTION (20.182 R1) |
| Decoder ACCEPTS our block (region B = 4 bits) | VERIFIED-BY-EXECUTION (20.189 R1, 29/29) |
| Apply runs on player-bearing rows | VERIFIED-BY-EXECUTION (20.189 R2, 8 calls) |
| Apply's third arg is NULL at stage 4 | VERIFIED-BY-EXECUTION (20.189 R2, 8/8) |
| Profile helper has never fired from the wire | VERIFIED-BY-EXECUTION (20.189 R3, 0 of 8) |
| Row base 0x4240 | VERIFIED-BY-EXECUTION (20.188 R3, reproduced 22x) |
| A populated staging object makes the helper fire | UNKNOWN - THIS BOOT |
| The detour substitutes correctly against NULL | VERIFIED-BY-EXECUTION (20.190 R1, 8/8, no skips, no crash) |
| profile_ingress can see a wire fire at all | FIXED this build; unproven until a line prints |
| What sets the stage to 4 vs 2 per body | UNKNOWN, newly opened by 20.189 R5 |
| Appearance = character_record family; peer's record unservable | VERIFIED-BY-READING (20.173) - not this boot |
| Render / co-presence | UNKNOWN (parked) |

## INSTRUMENTS

INSTRUMENTS:
  ev=dtrace stage=staging
  why=non_null_r8
  staging_populate=%u

## LITERAL TARGETS

LITERAL TARGETS:
  Game/bin/x64/steam_api64.dll: ev=dtrace stage=staging, why=non_null_r8, staging_populate=%u

## ADVERSARIAL PASS

ADVERSARIAL PASS: waived: solo run; write detour bounded by the seven properties above

waived: single machine, no rig, no peer. Server unchanged from p2(117). The detour writes
only into buffers the DLL owns and substitutes only for NULL.

## DEPLOYED FOR THIS BOOT
  server exe     `649c8da9f0e501fc` (unchanged from p2(117); region B = 4 presence bits).
  MAC client DLL `4baa7e81b152d5a1` - staging detour ARMED-CAPABLE, null-only arming.
  settings       server publish_player_profile TRUE; client decoder_trace TRUE,
                 profile_ingress TRUE, staging_populate TRUE  <-- THE EXPERIMENT.

## AFTER THE BOOT - REQUIRED
`bash RE_scripts/capture_boot.sh p2-119` BEFORE any other run starts.
