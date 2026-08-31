# BOOT BRIEF p2(131) - THE CONTROL RUN: IS THE PROFILE BLOCK BREAKING THE STATE CHECKSUM?

STATUS: live (2026-08-30). Reads with FINDINGS 20.203/20.204 (whose R1 severity reading
and whose next-boot recipe this brief CORRECTS), l9-profile-layout.md ADDENDUM, and
HANDOFF_2026-08-30_CONSUMER-HUNT.md.

## WHY THIS BOOT - THE OFFLINE ANALYSIS THAT REPLACED THE CAPTURE PLAN

p2(130) staged a replica capture to find "an unknown content delta" between the client's
28,768-byte session state and ours. The delta is not unknown. Five measurements taken
from logs ALREADY ON DISK, no boot spent:

1. COMPARE DIRECTION PROVEN. All 268 "expected" values in the mac's
   `session membership checksum failed, <computed> != <expected>` lines are hashes this
   server published (268/268 exact against `stage=membership result=built ... hash=`).
   NONE of the 268 computed values ever appear. The client hashes its applied state
   against our published tail word; our model is wrong, not lagging.
2. NOT CHRONIC-AND-SELF-HEALING. FATAL, 1:1. mac log today: 268 checksum failures /
   268 `no membership information, forcing disconnect`. Prior log: 722 / 722.
   20.203 R1's "usually self-heal via republish" is NOT supported by the logs.
3. IT DRIVES A PERMANENT RECONNECT LOOP. 18,192 membership revisions and 2,119
   `stage=join result=admit` in 83 minutes (~4/s = kRetryInterval 250 ms). Fail ->
   force-disconnect -> rejoin -> publish_membership resets the record -> republish ->
   fail. The revision explosion is the EFFECT, not stale-server age.
4. IT IS A REGRESSION. mac logs sunrise.log.p2d110_133157 and .p2d112_141049
   (2026-08-29): ZERO checksum failures, ZERO forced disconnects - and p2d110 reached
   the full `peers valid: 0x7 ... players valid: 0x3` membership. Our hash was ACCEPTED
   on a complete 3-peer/2-player body two days ago.
5. THE DISCRIMINATOR. Mapping each of the 268 failures back to its exact revision via
   the expected-hash key:
        (members,players) -> failures:  (2,1)=126  (3,1)=114  (3,2)=28   (*,0)=0
   The server published 8,595 updates carrying `players=0`; not one ever failed.
   EVERY failure carries a player row. A player row is the only place
   `write_player_delta` emits the profile block, and `build_session_state` has ZERO
   profile awareness - it always models the profile-absent shape (zeros). The client
   stores the decoded profile inside the player-table entry (20.201: stride 0x1a8 =
   424 = kPlayerStride), which lies inside the hashed 28,768 bytes; the player table
   ends at exactly 28768. Timeline closes it: profile bodies were first ACCEPTED by
   the client at p2(116) (2026-08-29 22:55); every mac log before that has zero
   failures, every log after has 100%.

This boot does not hunt. It runs the control that turns that into a fact or kills it,
using only settings flips already on disk.

## PURPOSE - what this boot learns, win or lose

ONE question: DOES REMOVING THE PROFILE BLOCK FROM THE PLAYER ROW MAKE THE CLIENT
ACCEPT OUR MEMBERSHIP STATE HASH?

WIN: arm A is clean and arm C reproduces the failure -> the profile block is proven
causal, the black screen has a fix we already own the inputs for (we AUTHOR those
bytes), and the fix is `build_session_state` writing the profile into the player entry
rather than a 28 KB byte hunt.
LOSE: arm A still fails -> the profile hypothesis is dead in one boot, the regression
lives elsewhere, and p2(132) becomes the replica capture WITH the missing half added
(see CARRY-FORWARD).

Either way this boot is decisive and costs no rebuild on either machine.

## THE TWO ARMS (one contract, control + reintroduction of ONE variable)

`session_state_client_base` is held FALSE in BOTH arms - it is not a variable here, and
its own disposition is a separate boot (see CARRY-FORWARD). U10 respected: one contract.

ARM A - REPRODUCE THE 2026-08-29 KNOWN-GOOD CONFIG
  server settings: publish_player_profile FALSE, session_state_client_base FALSE
  clients: unchanged binaries; decoder_trace / world_trace / state_diff ALL FALSE
  run: reset_lobby_claims.sh -> mac to Tower solo -> confirm landing -> rig joins Tower

ARM C - REINTRODUCE THE SINGLE VARIABLE
  server settings: publish_player_profile TRUE, session_state_client_base FALSE
  clients: identical to arm A
  run: reset_lobby_claims.sh -> same sequence

RESET BETWEEN ARMS IS MANDATORY (STATE hard rule; 20.203 R3 cost a whole misreading).

## GRAPHICS DELTA

ZERO new rendered models, and arm A publishes strictly LESS than the live config: the
profile block is removed from the wire. `world_population` stays FALSE (peer-visibility
rule: observer first, and its observer front is not this boot's contract). No client
binary changes; the three client observers are DISARMED, so the client renders and logs
strictly less than p2(130). No .text patching, no new interface binding.

## FALSIFIABLE CLAIM

CLAIM: with `publish_player_profile` FALSE and `session_state_client_base` FALSE, a full
paired Tower run reaches `peers valid: 0x7 ... players valid: 0x3` on the mac and logs
ZERO `session membership checksum failed` and ZERO `no membership information, forcing
disconnect`, with the server's `revision=` counter staying under 100 and
`stage=join result=admit` under 10; and with `publish_player_profile` TRUE (arm C) the
failures return 1:1 with forced disconnects and the revision counter climbs at ~4/s.

CONTENT NEGATIVE (pre-named, both kinds - L6):
- ARM A STILL FAILS (checksum failures > 0 while players valid reaches 0x3): the profile
  block is NOT the cause. The hypothesis dies here. The regression then lives in the
  server build itself or in the client DLL between 2026-08-29 14:10 and today, and
  p2(132) is the replica capture plus a git bisect of the server binary.
- BOTH ARMS CLEAN (arm C also logs zero failures): the profile block is exonerated AND
  something else that differed today is the cause - most likely the stale server or
  `session_state_client_base`, since arm C differs from the failing live config only in
  that flag. That would make client_base=TRUE the culprit and p2(129)'s "fix" the
  regression. Cheap to settle: a third arm with client_base TRUE.
- BOTH ARMS FAIL IDENTICALLY: neither flag is the variable; the delta is outside these
  settings entirely and the binaries are the next suspects.
- ARM A CLEAN BUT NEVER REACHES players valid 0x3: NOT a pass. See ABSENCE NEGATIVE -
  zero failures on a membership plane that never carried two players proves nothing.

## ABSENCE NEGATIVE (L13)

This boot ships NO new instrument, so its "zero lines" trap is the sharpest one on the
board: THE PASS CONDITION IS THE ABSENCE OF LINES, and absence is exactly what a
half-run also produces. A clean log is therefore only admissible alongside POSITIVE
liveness evidence that the membership plane actually ran to the two-player state.

REQUIRED LIVENESS - a clean arm A is VOID unless ALL of these are present:
  - mac client log: `networking:session:membership:dump: ... peers valid: 0x7,
    non-dormant: 0x7, ... players valid: 0x3`
  - mac client log: `session state is changing from 'peer-joining' to 'peer-established'`
    and `peer join successful`
  - server log: `stage=membership result=built revision=<n> members=3 players=2`
  - server log: `stage=join result=admit` for BOTH machines
  - mac client log: `Citizen join for region 'PUB56.56` reaching its success line
If any is missing, the arm did not test the contract - rerun, do not record a result.

OTHER ABSENCES AND WHAT THEY MEAN:
  - No `stage=membership result=built` at all: the server did not publish; the flip
    broke parsing (trap 18) or the server did not restart. Check the settings diff and
    the process, not the theory.
  - Server publishes but the mac logs no `group_target:` membership lines: the client
    never joined the group session - a transport/join fault, unrelated to this contract.
  - `ev=sdiff` / world_trace lines PRESENT: the observers were not disarmed; the arm is
    still valid for the checksum counts but the log is noisier than declared - note it.
  - Zero forced disconnects AND zero checksum failures AND zero player rows: void, see
    REQUIRED LIVENESS.

## MEASUREMENT (all from lines the deployed binaries already emit)

Per arm, recorded before touching the next arm:
  mac  : grep -ac 'session membership checksum failed'      -> expect A: 0   C: >0
  mac  : grep -ac 'no membership information, forcing disc' -> expect A: 0   C: == above
  mac  : grep -a  'peers valid'  | uniq -c                  -> must show 0x7 / 0x3
  srv  : max revision in 'stage=membership result=built'    -> expect A: <100  C: 1000s
  srv  : grep -ac 'stage=join result=admit'                 -> expect A: <10   C: 100s
  human: black screen on the mac at rig arrival?            -> expect A: NO   C: YES
Archive both logs per arm under RE_output/captures/<ts>_p2-131_arm<A|C>/.

## CHAIN MARKS (L16)

| Link | Mark |
|---|---|
| Client compares its computed state hash against OUR published tail word | VERIFIED-BY-EXECUTION (268/268 expected values matched to server `hash=` lines, 2026-08-30 offline) |
| Every checksum failure force-disconnects the group session | VERIFIED-BY-EXECUTION (268/268 and 722/722, 1:1 in two logs) |
| The failures drive a permanent rejoin loop | VERIFIED-BY-EXECUTION (18,192 revisions / 2,119 admits in 83 min at the 250 ms retry cadence) |
| Our hash was ACCEPTED on a full 3-peer/2-player body on 2026-08-29 | VERIFIED-BY-EXECUTION (p2d110/p2d112 mac logs: 0 failures, `peers valid 0x7 / players valid 0x3`) |
| Failures occur ONLY on updates carrying a player row | VERIFIED-BY-EXECUTION (268/268 have players>=1; 8,595 `players=0` publishes, 0 failures) |
| The profile block is the only content a player row gained | VERIFIED-BY-READING (`write_player_delta` gates it on publishProfile; nothing else changed in the row) |
| `build_session_state` models no profile bytes | VERIFIED-BY-READING (no profile term anywhere in session_state.cpp, both worktrees) |
| The client stores the profile inside the hashed player entry | VERIFIED-BY-EXECUTION for the array (20.201: base session+0x3b80, stride 0x1a8 = kPlayerStride); ASSUMED for the exact in-entry offsets |
| The profile block is what breaks the hash | UNKNOWN - THIS BOOT |
| `session_state_client_base` TRUE is correct | UNKNOWN - held FALSE here, separate boot |
| Appearance route closures 20.196/20.198 | VERIFIED-BY-EXECUTION but CONFOUNDED: measured with publish_player_profile TRUE, i.e. on a session force-disconnecting ~1.2x/s. Not reopened by this boot; re-verify cheaply once stable |

## DEPLOYED STATE THIS BOOT ASSUMES (unchanged - no rebuild, no redeploy)

  server exe        35ae2802aa7cdeb7   (p2(130) build; both flags read at runtime)
  clients mac+rig   30fe49c6914902f2   (unchanged; all three observers disarmed by flag)
  ROLLBACK: restore the two backed-up settings files; nothing else was touched.

## THE EDITS (trap 18 - TEXT INSERT ONLY, never a serialiser round-trip)

SERVER  RE_output/s1_accept/Sunrise/settings.json
  line 120  "publish_player_profile": true,      -> false,   (arm A)  -> true, (arm C)
  line 123  "session_state_client_base": true,   -> false,   (both arms)
CLIENT  Game/bin/x64/Sunrise/settings.json  and the rig's copy
  line 57   "decoder_trace": true,  -> false,
  line 59   "world_trace": true,    -> false,
  line 60   "state_diff": true,     -> false,
Back up each file first as settings.json.bak_p2d131_<what>; diff before writing; the
only changed lines must be these; parse once with a JSON READER afterwards to confirm
validity. Rig: edit locally, scp up, scp back down, compare hashes (ENVIRONMENTS
TRAP 18 step 4 - it cost a launch on 2026-08-30).

## LITERAL TARGETS

LITERAL TARGETS:
  RE_output/s1_accept/sunrise-server.exe: stage=membership result=built, client_base=, publish_player_profile, session_state_client_base

(L14 provenance: the deployed server really does emit the counters this boot reads and
really does carry both flag names. No new instrument ships - the measurement is entirely
pre-existing retail and server log lines, which is why REQUIRED LIVENESS above is the
load-bearing guard rather than an install line.)

## ADVERSARIAL PASS

ADVERSARIAL PASS: waived: no binary changes on any machine; server settings flips of two
existing runtime-read booleans plus disarming three client observers; strictly less code
runs and strictly fewer bytes are published than in p2(130); rollback is restoring two
backed-up text files.

## RUN SHAPE

1. Disarm the three client observers on BOTH machines (trap 18 procedure). Confirm by
   reading each file back with a JSON reader.
2. Arm A: edit the server settings (profile FALSE, client_base FALSE).
   `bash RE_scripts/reset_lobby_claims.sh` -> server restarts on the new settings.
3. mac to orbit, then Tower, SOLO. Confirm the landing (20.203 R3: a solo control first,
   always). Then launch the rig and join the Tower.
4. Hold the paired state ~90 s. Record the six measurements. Archive both logs.
5. Arm C: edit ONE line (profile TRUE). `reset_lobby_claims.sh` again. Repeat 3-4.
6. Record. Do not change anything else; do not chase a side observation into a third
   variable in this boot (ARH).

## CARRY-FORWARD (whatever this boot returns)

- p2(132a) if arm A is clean: teach `build_session_state` to write the profile bytes into
  the player entry. We author that content, so this is a layout question, not a search.
  `state_diff` (already deployed) becomes the VERIFIER of that layout.
- p2(132b) the client_base disposition: one arm, profile FALSE, client_base TRUE.
- IF THE REPLICA CAPTURE IS EVER RUN, two gaps in p2(130)'s staged recipe must be closed
  first: (1) it is NOT a settings flip - `kChecksumFnRva` and `kReplicaOffset` are
  constexpr, so retargeting to the apply (rcx-0x858) needs a code change, rebuild and
  redeploy on both machines; (2) the diff has only ONE HALF - the server never dumps its
  built replica, so a revision-keyed server-side state dump has to ship in the same
  build or there is nothing to diff against.
