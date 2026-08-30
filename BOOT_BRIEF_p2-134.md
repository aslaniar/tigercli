# BOOT BRIEF p2(134) - THE INSTRUCTION-VERIFIED FIX, PLUS THE CAPTURE THAT ENDS THE GUESSING

STATUS: live (2026-08-30). Reads with FINDINGS 20.206 (why p2(133)'s derivation was
unsound) and RE_output/claims/session-state-profile-image.md.

## WHY THIS BOOT

p2(133) failed: the client's computed hash for revision 2 matched none of 18 variants nor
the absent model. The static re-audit (20.206) walked the actual reader instead of the
summary docs and found the derivation's premise wrong - "copied verbatim" covers the
DELTA->STATE hop only; the WIRE->DELTA hop transforms fields.

Walking the region-A reader (the name loop 0x1416d3460 and the chunk reads that follow)
produced ONE instruction-verified defect in our image, plus confirmation of the rest:
- THE NAME TERMINATOR IS NOT ZERO. The loop stores key ^ (source * multiplier) for EVERY
  word INCLUDING the zero terminator, and only THEN tests the source word and exits. The
  stored word at index L is key16(L) - non-zero. p2(133) left it zero, so every hash it
  published was wrong by that one word regardless of anything else.
- CONFIRMED CORRECT in our image: chunks 4/5 read 6 bits then DEC (0x1416d352e /
  0x1416d3555), so our written 1 stores 0; chunk 7 is two 64-bit VALUE reads stored as
  host qwords at +0xc0/+0xc8 (0x1416d35b5 / 0x1416d35c4); region B's four flags are all
  clear in our body so its reader (0x1416d3c30, a second obfuscated name block) never
  runs and writes nothing.

## THE INSTRUMENT - THE CAPTURE, SO THIS BOOT CANNOT COME BACK EMPTY

The remaining unknowns (the tail's stored form, and whether the delta's unread areas are
really zero) are not derivable from what any lane has read. So this boot ALSO measures:
- CLIENT: state_diff retargeted from the checksum verifier (which logged zero calls in
  p2(130) - it does not run in this flow) to the APPLY 0x141781800, .pdata-verified by
  verify_hook_rvas.py. It runs the original FIRST and then dumps the two 424-byte player
  entries at base+0x3b60 - the stored bytes, after the profile has landed.
- SERVER: dumps the 424-byte player entry IT built for the same revision
  (`result=entry revision=N slot=S hex=...`).
Two 424-byte records, same revision, both in logs. The diff is exact and small.

## PURPOSE - what this boot learns, win or lose

WIN OUTRIGHT: the terminator was the last defect - 0 checksum failures with the profile
live, which is the milestone configuration.
WIN BY MEASUREMENT: failures continue, and the two hex dumps name every remaining wrong
byte in one pass. No further hypothesis testing, ever - the layout stops being derived.

## GRAPHICS DELTA

ZERO new rendered models. world_population FALSE. The client hook is read-only and
pass-through: it calls the original first and only reads memory afterwards, SEH-guarded,
capped at 2 non-empty entries.

## FALSIFIABLE CLAIM

CLAIM: with the terminator fix, publish_player_profile TRUE, session_state_client_base
FALSE and variant 0, a paired Tower run logs ZERO `session membership checksum failed`,
ZERO `no membership information`, reaches `peers valid 0x7 / players valid 0x3`, the
citizen join SUCCEEDS, revision stays under 100 and admits under 10.

CONTENT NEGATIVE (pre-named - L6):
- FAILURES CONTINUE + BOTH DUMPS PRESENT: expected second-best. The byte diff names the
  remaining defects; the derivation is replaced by measurement. This is a PASS for the
  instrument even though the fix failed.
- FAILURES CONTINUE + NO `ev=sdiff stage=entry` LINES: the apply hook did not fire (the
  p2(130) class). Then the apply is not the write site either, and the entry must be
  found another way - do not re-run this shape.
- `result=unreadable`: base+0x3b60 is not the player table in the apply's coordinates;
  the 0x3c68-0x108 arithmetic from helper B is wrong and needs re-reading.
- ENTRIES DUMPED BUT ALL ZERO: the profile never reached the entry, which would move the
  fault upstream of the apply entirely.

## ABSENCE NEGATIVE (L13)

A clean run is VOID unless: server `members=3 players=2 ... profile=1 variant=0`,
`client_base=0`, both `stage=join result=admit`, mac `peers valid 0x7 / players valid 0x3`,
and `Citizen join ... succeeded!`. If `result=variant`/`result=entry` lines are absent the
OLD server binary is running - stop. The variant budget is now spent only on
PLAYER-BEARING snapshots (p2(133) wasted half its instrument on a players=0 body - the
"budget per event class" rule).

## MEASUREMENT

  mac : grep -ac 'checksum failed' / 'no membership information'   -> expect 0
  mac : grep -c 'succeeded!'                                        -> expect >=1
  mac : grep -a 'ev=sdiff stage=entry'                              -> the client's bytes
  srv : grep -a 'result=entry'                                      -> our bytes
  srv : last revision (<100) / admits (<10)
  ON FAILURE: diff the two hex dumps for the same revision, field by field.

## CHAIN MARKS (L16)

| Link | Mark |
|---|---|
| The profile block causes the hash rejection | VERIFIED-BY-EXECUTION (arm A/C) |
| The stored name terminator is key16(L), not zero | VERIFIED-BY-DISASSEMBLY (0x1416d34a2 stores before 0x1416d34a6 tests the SOURCE word) |
| Chunks 4/5 store read-6-bits minus 1 | VERIFIED-BY-DISASSEMBLY (0x1416d352e / 0x1416d3555) |
| Chunk 7 stores two host qwords at +0xc0/+0xc8 | VERIFIED-BY-DISASSEMBLY (0x1416d35b5 / 0x1416d35c4) |
| Region B is unread when its four flags are clear | VERIFIED-BY-DISASSEMBLY (0x1416d3c56 gate) |
| The player table is base+0x3b60 in apply coordinates | VERIFIED-BY-DISASSEMBLY (helper B 0x1417af2de: 0x3c68 - 0x108) |
| The historical replica base (15192) is correct | VERIFIED-BY-EXECUTION (arm A 9/9) + the same arithmetic |
| The tail's stored form | UNKNOWN - MEASURED THIS BOOT |
| Whether unread delta areas are zero | UNKNOWN - MEASURED THIS BOOT |

## DEPLOYED (p2(134))

  server exe `e152051ae4f56cca` via deploy_p2d6_gameplay.sh (all seven harness gates
             passed; cache restamped - the hot-copy that broke p2(133)'s restart is not
             repeated). Settings: profile TRUE, client_base FALSE, variant 0, wpop FALSE.
  clients mac+rig `5e7ce5327a235955`, deployed via deploy_client_dll.sh with literal
             provenance asserted on both. state_diff TRUE; decoder_trace and world_trace
             FALSE (decoder_trace shares the apply address and MUST stay off).
             Rig settings pushed and read back byte-exact.
  ROLLBACK: publish_player_profile FALSE is arm A and is measured stable.

## LITERAL TARGETS

LITERAL TARGETS:
  RE_output/s1_accept/sunrise-server.exe: result=entry, result=variant, profile_state_variant
  Game/bin/x64/steam_api64.dll: ev=sdiff, stage=entry

## ADVERSARIAL PASS

ADVERSARIAL PASS: waived: one read-only pass-through detour on a .pdata-verified function
start (gated by verify_hook_rvas.py, 0 bad), reads SEH-guarded and capped; the server
change is one 2-byte word in the replica model plus logging; the profile-absent path is
untouched and remains the measured-stable rollback.

## RUN SHAPE

1. (DONE) Build, gate RVAs, deploy client DLL to both machines, deploy server via the
   canonical pipeline, arm state_diff on both, restart, verify hashes and literals.
2. mac to orbit, then Tower, SOLO. Confirm the landing.
3. Rig joins the Tower. Hold ~90 s.
4. Measure; on failure go straight to the two hex dumps and diff them.
