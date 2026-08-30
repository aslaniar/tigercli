# BOOT BRIEF p2(132) - ARM C: ISOLATE THE PROFILE BLOCK AGAINST A PROVEN-GOOD BASELINE

STATUS: live (2026-08-30). Reads with BOOT_BRIEF_p2-131.md (arm A, PASSED) and
FINDINGS 20.205. One line changes from the arm A configuration.

## WHY THIS BOOT

p2(131) arm A ran `publish_player_profile` FALSE + `session_state_client_base` FALSE and
came back clean on every measure: 0 checksum failures, 0 forced disconnects, revision
stopped at 9, 2 join admits, `peers valid 0x7 / players valid 0x3` reached, and
`Citizen join for region 'PUB56.56' succeeded!` - a line that appeared ZERO times across
557 failures in the two baseline runs. The server published 4 updates at
`members=3 players=2` and the client accepted all 9 of 9.

That settles one thing on its own: with the profile off, the HISTORICAL layout hashes
correctly. If the +8 shift (`session_state_client_base` TRUE) were the right model,
FALSE would have failed. It did not fail - 9/9 accepted. So client_base FALSE is now the
PROVEN-GOOD base, and p2(129)'s shift is the suspect, not the fix.

Two variables still moved together between the failing baseline and arm A. This boot
moves exactly one, against the proven-good base.

## PURPOSE - what this boot learns, win or lose

ONE question: WITH THE LAYOUT HELD AT THE PROVEN-GOOD BASE, DOES THE PROFILE BLOCK ALONE
BREAK THE STATE-HASH AGREEMENT?

This boot is a win in both directions, which is why it is worth the reset:
- FAILURES RETURN -> the profile block is proven causal. The fix is named and bounded:
  `build_session_state` must model the profile bytes inside the player entry. We AUTHOR
  that content, so it is a layout question, not a search. Ship it as p2(133).
- CLEAN -> the profile block is exonerated and `session_state_client_base` TRUE was the
  entire regression. That would mean this boot IS the milestone configuration: a stable
  two-player session WITH the profile pipeline live, which is the best position this
  project has held. Then the next question is no longer the checksum at all - it is
  whether a guardian renders, on a session that finally is not collapsing.

## THE ONE CHANGE

  server  publish_player_profile     FALSE -> TRUE     <- the only edit
  server  session_state_client_base  FALSE (held - proven good by arm A)
  clients decoder_trace / world_trace / state_diff  FALSE (held, both machines)
  server  world_population           FALSE (held)

No rebuild. No redeploy. No client binary change. STAGED AND VERIFIED ALREADY - see
PRE-STAGED below.

## GRAPHICS DELTA

ZERO new rendered models by construction. `world_population` stays FALSE, so no entity
is injected. The profile block carries a name and identity, not geometry: region A is
fully decoded and holds no gear hash, shader, ornament or material reference (20.202).
If a guardian renders in this boot it is NOT from anything this boot publishes, and that
would itself be a finding worth its own entry.

## FALSIFIABLE CLAIM

CLAIM: turning `publish_player_profile` back on, with everything else at the arm A
configuration, restores the failure signature: `session membership checksum failed`
lines return, 1:1 with `no membership information, forcing disconnect`, the citizen join
for PUB56.56 fails instead of succeeding, the revision counter climbs at ~4/s
(kRetryInterval 250 ms) instead of stopping in single digits, and every failing revision
carries `players>=1`.

CONTENT NEGATIVE (pre-named, both kinds - L6):
- ARM C IS CLEAN (0 failures, citizen join succeeds, revision stays low) while
  `players valid 0x3` is reached: the profile block is NOT the cause. Then
  `session_state_client_base` TRUE was the whole regression, the two baseline runs are
  explained, and NOTHING further is owed on the checksum. Go straight to the render
  question with the profile live.
- FAILURES RETURN BUT ON `players=0` UPDATES TOO: the discriminator breaks. 557/557
  failures across two runs carried a player row; a `players=0` failure would falsify the
  mechanism even while reproducing the symptom, and the fix territory moves off the
  player entry.
- FAILURES RETURN AT A DIFFERENT RATE OR WITHOUT THE 1:1 DISCONNECT PAIRING: the
  rejection is not the same rejection; do not fold it into the same story.

## ABSENCE NEGATIVE (L13)

This boot ships NO new instrument, and unlike arm A its PASS prediction is the PRESENCE
of failure lines - so the dangerous absence here is the opposite one: a quiet log that
looks like exoneration because the run never got far enough to publish a player row.

REQUIRED LIVENESS - a clean arm C is VOID unless ALL of these are present:
  - server: `stage=membership result=built ... members=3 players=2` at least once
    (a player row was actually published - this is the whole variable)
  - server: `client_base=0` on every membership line (the arm witness; `client_base=1`
    means the settings did not take and the arm is void)
  - server: `stage=join result=admit` for BOTH machines
  - mac: `peers valid: 0x7 ... players valid: 0x3`
  - mac: `session state is changing from 'peer-joining' to 'peer-established'`
  - mac: `Citizen join for region 'PUB56.56 ... succeeded!`
If `members=3 players=2` never appears, the profile block was never published and the
boot tested nothing - rerun, do not record a result.

OTHER ABSENCES:
  - No `stage=membership result=built` at all: server did not restart onto the edit.
    Check the process and the settings diff, not the theory.
  - `ev=sdiff` / `ev=wtrace` lines beyond their `result=skipped why=disarmed` install
    line: an observer re-armed; the counts still stand but note the noise.

## MEASUREMENT (same six as arm A, so the arms are directly comparable)

  mac  : grep -ac 'session membership checksum failed'       -> C expects >0
  mac  : grep -ac 'no membership information'                -> C expects == above
  mac  : grep -a  'Citizen join' | grep -c 'succeeded'       -> C expects 0
  mac  : grep -a  'peers valid' | uniq -c                    -> must show 0x7 / 0x3
  srv  : last 'result=built revision=<n>'                    -> C expects hundreds+
  srv  : grep -ac 'stage=join result=admit'                  -> C expects >>2
  plus : the (members,players) map of every FAILED revision  -> C expects players>=1 only
Archive both logs to RE_output/captures/<ts>_p2-132_armC/ BEFORE relaunching anything.

REFERENCE - the two results already banked:

| Measure | baseline (profile ON, base ON) | arm A (both OFF) |
|---|---|---|
| checksum failures | 289 | 0 |
| forced disconnects | 289 | 0 |
| citizen join | 289 failed, 0 succeeded | SUCCEEDED |
| max revision | 23,908 | 9 |
| join admits | 2,426 | 2 |
| peers / players | 0x7 / 0x1 | 0x7 / 0x3 |

## CHAIN MARKS (L16)

| Link | Mark |
|---|---|
| Client compares its computed state hash against our published tail word | VERIFIED-BY-EXECUTION (268/268 expected values matched to server hash= lines) |
| Every checksum failure force-disconnects the group session | VERIFIED-BY-EXECUTION (268/268, 722/722, 289/289 - three logs, 1:1 each) |
| Failures occur ONLY on updates carrying a player row | VERIFIED-BY-EXECUTION (557/557 across two independent runs; 21,832 `players=0` publishes, zero failures) |
| The profile block is the only content a player row gained | VERIFIED-BY-READING (`write_player_delta` gates it on publishProfile) |
| `build_session_state` models no profile bytes | VERIFIED-BY-READING (no profile term in session_state.cpp) |
| The historical layout hashes correctly with the profile off | VERIFIED-BY-EXECUTION (arm A: 9/9 accepted, client_base=0) |
| `session_state_client_base` TRUE is WRONG | STRONGLY INDICATED by arm A, not yet isolated - this boot holds it FALSE and does not test it |
| The profile block alone breaks the hash | UNKNOWN - THIS BOOT |
| The client stores the profile inside the hashed player entry | ASSUMED for exact in-entry offsets (20.201 measured the array: base session+0x3b80, stride 0x1a8 = kPlayerStride) |
| Appearance closures 20.196 / 20.198 | VERIFIED-BY-EXECUTION but CONFOUNDED - measured on a session force-disconnecting ~1.2x/s. Not reopened here; re-verify once stable |

## DEPLOYED STATE (unchanged - no rebuild, no redeploy)

  server exe        35ae2802aa7cdeb7   (both flags read at runtime)
  clients mac+rig   30fe49c6914902f2   (observers disarmed by flag, verified byte-exact)
  ROLLBACK: restore settings.json.bak_p2d132_armC (server) - one line.

## PRE-STAGED (done, verified - do not re-edit)

  server settings.json line 120  "publish_player_profile": true,     <- STAGED
  server settings.json line 123  "session_state_client_base": false, <- held from arm A
  backup: RE_output/s1_accept/Sunrise/settings.json.bak_p2d132_armC
  clients: untouched since arm A (all three observers false on both machines)
The edit is INERT until the server restarts. The running arm A session is unaffected.

## LITERAL TARGETS

LITERAL TARGETS:
  RE_output/s1_accept/sunrise-server.exe: stage=membership result=built, client_base=, publish_player_profile, session_state_client_base

(No new instrument ships; the measurement is pre-existing retail and server log lines,
which is why REQUIRED LIVENESS above is the load-bearing guard rather than an install
line.)

## ADVERSARIAL PASS

ADVERSARIAL PASS: waived: no binary changes on any machine; one server boolean flipped
back to the value it held all week; rollback is one backed-up text file.

## RUN SHAPE

1. Archive the arm A logs first (they are the control and the mac log rotates on
   relaunch): RE_output/captures/<ts>_p2-131_armA/.
2. `bash RE_scripts/reset_lobby_claims.sh` - restarts the server onto the staged edit
   and zeroes the revision counter, which two measurements depend on.
3. Confirm the arm witness on the first membership line: `client_base=0` AND the run
   must eventually show `players=2`. If `client_base=1`, stop - the edit did not take.
4. mac to orbit, then Tower, SOLO. Confirm the landing before the rig moves.
5. Rig joins the Tower. Hold ~90 s.
6. Record the six measurements plus the failed-revision (members,players) map. Archive.
7. Do not chase a side observation into a third variable in this boot (ARH).

## CARRY-FORWARD

- p2(133) if arm C fails: teach `build_session_state` to write the profile bytes into the
  player entry at the historical base. `state_diff` (deployed, disarmed) becomes the
  VERIFIER of that layout, and the server needs a revision-keyed dump of its own built
  replica so a diff has two halves - the gap that made p2(130)'s recipe unrunnable.
- p2(133') if arm C is clean: the checksum front CLOSES. Go to the render question on a
  stable session, and re-verify the confounded appearance closures cheaply first.
