# BOOT BRIEF p2(133) - THE FIX, AND ITS OWN DISCRIMINATOR IN ONE BOOT

STATUS: live (2026-08-30). Reads with RE_output/claims/session-state-profile-image.md
(the derived layout) and FINDINGS 20.205 (arm A/C, the proof the profile block is causal).

## WHY THIS BOOT

p2(131)/p2(132) settled the cause by A/B: profile OFF -> 0 checksum failures, citizen join
SUCCEEDS, revision stops at 9. Profile ON, one variable moved -> failures return, 1:1 with
force-disconnect, 40/40 of them on `players>=1` updates. 597/597 failures across four runs
carry a player row; 21,832 `players=0` publishes never failed once.

The reason is now read from the client's own apply: `build_session_state` writes the two
0xFFFFFFFF "absent" markers at player-entry +0x1c and +0x108 unconditionally, and those are
exactly where the profile's region-A header and region B BEGIN. With a profile shipping,
the client stores 396 bytes there and our replica still claims absent.

`build_session_state` now models the profile. Two details of the stored image were NOT
pinnable statically, so this boot does not guess them - it enumerates them.

## THE INSTRUMENT - 18 CANDIDATE HASHES, ONE LOG, NO REBUILD TO ACT ON IT

Unresolved: (1) whether the stored name holds the obfuscated wire words or the
deobfuscated plain text; (2) where the tail's 5-bit field lands in its trailing 8 bytes.
2 x 9 = 18 variants. The server logs EVERY variant's hash once per session
(`result=variant index=N name_obfuscated=U tail_field=D hash=0x...`), plus the
absent-model hash. The client prints the hash it computed in
`session membership checksum failed, <computed> != <ours>`. Whichever variant reproduces
<computed> IS the answer - and `profile_state_variant` then makes it live as a SETTINGS
FLIP, no rebuild. Capped at 2 snapshots so a republish loop cannot flood the log.

## PURPOSE - what this boot learns, win or lose

WIN OUTRIGHT: variant 0 is already right - 0 checksum failures with the profile LIVE.
That is the milestone configuration: a stable two-player session carrying authored
identity, which this project has never held at the same time.
WIN BY DISCRIMINATION: failures continue, but the client's computed hash MATCHES one of
the 18 logged variants. The answer is then known exactly, and p2(134) is a settings flip.
LOSE INFORMATIVELY: failures continue and the computed hash matches NO variant. Then the
stored image is wrong somewhere static analysis did not reach, and the next step is the
replica capture - which now has its missing half, because this build logs what the server
actually built.

## GRAPHICS DELTA

ZERO new rendered models. `world_population` stays FALSE. No client binary or client
setting changes at all - the three observers stay disarmed on both machines. The only
delta is server-side: the replica model now writes profile bytes where it wrote two
absent markers, and the log gains at most 19 extra lines per session.

## FALSIFIABLE CLAIM

CLAIM: with `publish_player_profile` TRUE, `session_state_client_base` FALSE and
`profile_state_variant` 0, a paired Tower run logs ZERO `session membership checksum
failed` and ZERO `no membership information, forcing disconnect`, reaches
`peers valid: 0x7 ... players valid: 0x3`, the citizen join SUCCEEDS, the revision counter
stays under 100 and `stage=join result=admit` under 10.

CONTENT NEGATIVE (pre-named, all three kinds - L6):
- FAILURES CONTINUE, computed hash MATCHES a logged variant -> the model is right and only
  the variant index was wrong. Not a failure of the theory. Flip the setting, rerun.
- FAILURES CONTINUE, computed hash matches NO variant AND not the absent model -> the
  stored image is wrong beyond the two enumerated choices. The derivation in
  session-state-profile-image.md is then indicted, not the causal finding (which arm A/C
  established independently of any layout).
- FAILURES CONTINUE and the computed hash equals the ABSENT-model hash -> our new bytes
  never reached the wire; the flag or the build did not take. Check the deploy, not the
  theory.
- FAILURES STOP BUT `players valid 0x3` IS NEVER REACHED -> void, see ABSENCE NEGATIVE.

## ABSENCE NEGATIVE (L13)

The pass condition is again an ABSENCE of failure lines, which a run that never published
a player row also produces. A clean result is VOID unless ALL of these are present:
  - server: `stage=membership result=built ... members=3 players=2 ... profile=1 variant=0`
  - server: `client_base=0` on every membership line (settings witness)
  - server: at least one `result=variant` block (proves the new binary is the one running)
  - server: `stage=join result=admit` for BOTH machines
  - mac: `peers valid: 0x7 ... players valid: 0x3`
  - mac: `Citizen join for region 'PUB56.56 ... succeeded!`
If `result=variant` lines are absent, the OLD server binary is running - stop and redeploy.
If `members=3 players=2` never appears, no profile was ever published and the boot tested
nothing.

## MEASUREMENT

  mac  : grep -ac 'session membership checksum failed'        -> expect 0
  mac  : grep -ac 'no membership information'                 -> expect 0
  mac  : grep -c  'succeeded!'                                -> expect >=1
  mac  : grep -a  'peers valid' | uniq -c                     -> must show 0x7 / 0x3
  srv  : last 'result=built revision=<n>'                     -> expect <100
  srv  : grep -ac 'stage=join result=admit'                   -> expect <10
  ON FAILURE: take the `checksum failed, <computed> !=` values and grep them against the
  `result=variant ... hash=` table in the same log. A hit names the variant outright.

Banked comparisons: baseline 289 failures / rev 23,908 / 0 successes; arm A 0 / 9 /
SUCCEEDED; arm C 40+ / 68+ / 0.

## CHAIN MARKS (L16)

| Link | Mark |
|---|---|
| The profile block causes the state-hash rejection | VERIFIED-BY-EXECUTION (arm A/C, single variable, both directions) |
| Failures occur only on player-bearing updates | VERIFIED-BY-EXECUTION (597/597 across four runs) |
| The apply writes 0xFFFFFFFF at +0x1c and +0x108 under the profile gate | VERIFIED-BY-DISASSEMBLY (0x141782408 / 0x141782410 / 0x14178241b) |
| Region A is 232B at +0x20; region B 136B at +0x108; tail 20B at +0x190 | VERIFIED-BY-DISASSEMBLY (l9-profile-layout CLAIM 2/4) |
| The session layer copies the block verbatim, so we can compute it | VERIFIED-BY-DISASSEMBLY (CLAIM 3) |
| Region-A chunk offsets (name +0x00, dec bytes +0xb2/+0xb3, SOIDs +0xc0/+0xc8) | VERIFIED-BY-EXECUTION (20.202, two accounts) |
| The historical table base is the correct one | VERIFIED-BY-EXECUTION (arm A, 9/9 accepted with client_base FALSE) |
| Stored name is obfuscated vs plain | UNKNOWN - ENUMERATED THIS BOOT |
| Tail 5-bit field position | UNKNOWN - ENUMERATED THIS BOOT |
| Absent chunks are zero in the stored image | ASSUMED (cleared-entry model; the hash match would confirm it) |

## DEPLOYED (p2(133))

  server exe     `c5ae6936f6020003` (NEW - built and deployed 2026-08-30; prior
                 35ae2802aa7cdeb7 kept as sunrise-server.exe.bak_p2d133_*).
                 SETTINGS: publish_player_profile TRUE, session_state_client_base FALSE,
                 profile_state_variant absent = 0, world_population FALSE.
  clients mac+rig `30fe49c6914902f2` UNCHANGED, observers disarmed, verified byte-exact.
  ROLLBACK: restore the .bak_p2d133_* exe, or simply set publish_player_profile false,
            which is arm A and is known good.

## LITERAL TARGETS

LITERAL TARGETS:
  RE_output/s1_accept/sunrise-server.exe: result=variant, profile_state_variant, name_obfuscated, stage=membership result=built

## ADVERSARIAL PASS

ADVERSARIAL PASS: waived: server-only change, no client binary or setting touched; the
profile-absent path is byte-identical to the code arm A proved correct (the new bytes are
written only under `profile.publish`); the extra logging is capped at 2 snapshots;
rollback is one settings flip to a configuration already measured clean.

## RUN SHAPE

1. (DONE) Build, deploy, back up the prior exe, verify literals in the deployed binary.
2. (DONE) `reset_lobby_claims.sh` - restarts onto the new binary and zeroes the revision.
3. mac to orbit, then Tower, SOLO. Confirm the landing.
4. Rig joins the Tower. Hold ~90 s.
5. Record the six measurements; on failure, cross the computed hashes against the variant
   table before anything else.
6. Archive both logs to RE_output/captures/<ts>_p2-133/.
