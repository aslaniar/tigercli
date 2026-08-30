# BOOT BRIEF p2(135) - THE FIX, EVERY FIELD MEASURED AGAINST THE LIVE CLIENT

STATUS: live (2026-08-30). Reads with FINDINGS 20.207. This is NOT a probe boot: no new
instrument ships, and every byte of the profile image it publishes was read from the
client's own decode of a body we published, not derived.

## WHY THIS BOOT

p2(134)'s adversarial pass found that a working instrument was already deployed and
firing: the `ev=ingress` hook dumps, per applied profile, the decoded region A, region B,
the tail, AND the two header words - tagged with the caller RVA so the WIRE path
(caller_rva=0x178245D, the apply's helper-A call) is distinguishable from the client's own
local applies. It had been logging our published profile all along.

Against that ground truth, eight of the nine profile fields our replica model writes were
already correct. ONE was wrong:

  MEASURED tail: 0000000000000000 00000001 01000000 00000000
    tail+0x00 = 0            our model: 0             OK
    tail+0x04 = 0            our model: 0             OK
    tail+0x08 = 0x01000000   our model: 0x01000000    OK
    tail+0x0c = 0x00000001   our model: NOTHING       <-- the defect
    tail+0x10 = 0            our model: 0             OK

The 5-bit tail field stores as a DWORD at tail+0x0c. p2(133) published nothing there, so
every hash it sent was short by that word regardless of anything else. Also confirmed
against the same dumps: header1=0x00000000 and header2=0x00000000 (our model wrote both
as 0 already), the name stores as plain UTF-16 with a key16(L) terminator (`SUNRISE0`
followed by C2C4 - byte-identical to what the server builds), the SOIDs store as host
qwords at region A +0xc0/+0xc8, and region B stores 136 zero bytes.

## PURPOSE

Does the corrected replica model make the client accept our membership state hash with the
profile LIVE? That is the whole question. Win = the milestone configuration: a stable
two-player Tower session carrying authored identity.

## GRAPHICS DELTA

ZERO new rendered models. world_population FALSE. No client binary or client setting
change of any kind. The only delta is one 4-byte write in the server's replica model.

## FALSIFIABLE CLAIM

CLAIM: with the tail fix, publish_player_profile TRUE, session_state_client_base FALSE,
a paired Tower run logs ZERO `session membership checksum failed`, ZERO `no membership
information`, reaches `peers valid 0x7 / players valid 0x3`, the citizen join SUCCEEDS,
revision stays under 100 and admits under 10.

CONTENT NEGATIVE (pre-named - L6):
- FAILURES CONTINUE: the profile image is still wrong somewhere. NO NEW INSTRUMENT IS
  NEEDED to find out - the `ev=ingress` dumps in the same log already carry the client's
  exact decoded bytes for the failing revision, and `result=entry` carries ours. The next
  step is a desk diff of two records we will already hold, not another boot.
- FAILURES STOP BUT `players valid 0x3` IS NEVER REACHED: void, see ABSENCE NEGATIVE.
- FAILURES STOP AND THE SESSION HOLDS: done; move to the render question.

## ABSENCE NEGATIVE (L13)

A clean run is VOID unless ALL of: server `members=3 players=2 ... profile=1 variant=0`
and `client_base=0`; both `stage=join result=admit`; mac `peers valid 0x7 / players valid
0x3`; mac `Citizen join ... succeeded!`. If `ev=ingress stage=apply path=WIRE` lines are
absent, no profile ever reached the client and the boot tested nothing.

## MEASUREMENT

  mac : grep -ac 'checksum failed' / 'no membership information'  -> expect 0
  mac : grep -c 'succeeded!'                                       -> expect >=1
  mac : grep -a 'peers valid' | uniq -c                            -> must reach 0x7 / 0x3
  srv : last revision (<100), admits (<10)
  ON FAILURE: diff `ev=ingress stage=dump` (client) against `result=entry` (ours) for the
  same revision. Both are already in the logs.

## CHAIN MARKS (L16)

| Link | Mark |
|---|---|
| The profile block causes the hash rejection | VERIFIED-BY-EXECUTION (arm A/C, single variable) |
| header1 = 0, header2 = 0 on the wire path | VERIFIED-BY-EXECUTION (ev=ingress stage=apply, caller_rva=0x178245D) |
| Stored name = plain UTF-16 + key16(L) terminator | VERIFIED-BY-EXECUTION (client decoded `SUNRISE0` + C2C4) + VERIFIED-BY-DISASSEMBLY (0x1416d34a2 stores before 0x1416d34a6 tests) |
| SOIDs store as host qwords at +0xc0/+0xc8 | VERIFIED-BY-EXECUTION (client decode) |
| Region B stores 136 zero bytes | VERIFIED-BY-EXECUTION (tag=regionB_ifwire all zero) |
| Tail word2 = 0x01000000 at +0x08 | VERIFIED-BY-EXECUTION |
| Tail 5-bit field = dword 1 at +0x0c | VERIFIED-BY-EXECUTION - THE FIX |
| The historical replica base is correct | VERIFIED-BY-EXECUTION (arm A 9/9) |
| Nothing else in the entry differs | INFERRED by elimination - this boot tests it |

## DEPLOYED (p2(135))

  server exe `789d8d9f0ed94e9e` via deploy_p2d6_gameplay.sh; all SEVEN harness gates
             passed (s1, cache-check, equip-diff, selection-version, membership-sweep,
             membership-wire, local-account). Settings: profile TRUE, client_base FALSE,
             variant 0, world_population FALSE.
  clients mac+rig `5e7ce5327a235955` UNCHANGED from p2(134).
  ROLLBACK: publish_player_profile FALSE is arm A and is measured stable.

## LITERAL TARGETS

LITERAL TARGETS:
  RE_output/s1_accept/sunrise-server.exe: result=entry, stage=membership result=built, publish_player_profile

## ADVERSARIAL PASS

ADVERSARIAL PASS: waived: server-only change of one 4-byte field in the replica model,
gated by seven harness tests; no client change; the profile-absent path is untouched and
remains the measured-stable rollback. The claim rests on measurement of the live client,
not on derivation - which is the specific failure mode of p2(133).

## RUN SHAPE

1. (DONE) Build, deploy via the canonical pipeline, verify hash and gates, server restarted
   clean (ladder sessions empty).
2. mac to orbit, then Tower, SOLO. Confirm the landing.
3. Rig joins the Tower. Hold ~90 s.
4. Measure. On failure, desk-diff the two records already in the logs - do not boot again.
