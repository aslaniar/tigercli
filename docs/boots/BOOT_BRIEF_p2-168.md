# BOOT_BRIEF_p2-168 — MAC SOLO: THE COPIER'S DIRECTION AND ITS SOURCE GATE BYTES

STATUS: live (2026-09-03). Solo validation boot. Follows 20.285.

## PURPOSE
The gate byte that gates the whole peer-claim path is never computed by client code; it
arrives inside a wholesale image copy. This boot makes the existing pubrest observer
CLASSIFY that copy, which it has never once managed to do.

Win or lose it learns: does a copy whose DESTINATION is the live participant table happen
on the mac at all, and does its SOURCE image carry the gate bit? Solo is sufficient for
both - the copier already fires solo (20.252 R1 captured it at Tower landing on a solo
client) - and it validates the classifier before any paired run spends two machines.
SOLO CANNOT ANSWER, and this brief does not claim it: whether a SECOND participant's
presence changes the source image. That is the paired follow-up.

## GRAPHICS DELTA
ZERO new rendered models. Nothing about rendering changes: no gate is opened, no card
placement changes, no client write into game data (gate_poke=0, gate_wwatch DR/VEH/suspend
retired at compile time). This boot only makes an existing observer say which direction a
copy went.

## FALSIFIABLE CLAIM
The pubrest observer now classifies every copy as `publish` or `restore` instead of
`unknown`, and reports the source image's gate bytes for records 0..7.

CONTENT NEGATIVE:
 - `role=unknown` still, on every call => the seed did not work. The registry is filled
   from caller 0x4F78EC (the pool ctor's return address), so either that caller never
   appears this boot or arg3 there is not the table. Read the caller census, do not guess.
 - A `restore` appears and `f38src_*` are all 00 => the fork's restore source never
   carries the bit. That is the EXPECTED result and it is a real finding: it makes the
   source's own provenance the next question, not the copier.
 - A `restore` appears with any `f38src_*` bit4 set => the mechanism exists locally and
   something suppresses it downstream. That would be the biggest result available here.
 - NO copy with dest==table appears at all => 20.254 R1's restore was rig-specific or
   phase-specific; the mac reaches the Tower by a different path.

## ABSENCE NEGATIVE
 - ZERO `stage=pubrest` lines => the hook did not attach or the copier never ran. Check
   the census line for pubrest attached=1 FIRST; says nothing about direction or bytes.
 - `stage=pubrest` present but ZERO `pubrestimg` lines => the image dump budget (two shots)
   was not reached, not that the image is empty.
 - `role` present but `src_ok=0` => the source image was unreadable at record 0, so every
   f38src value on that line is meaningless. Do not read 00 as "the bit is clear" when
   src_ok=0; that is the 0xFF/00 conflation the emitter already guards against.

## CHAIN MARKS
  L1 the walk reaches the guard only if the gate bit is set ... verified-by-reading (20.285 R1)
  L2 nothing computes the bit ........................ verified-by-reading (20.234, scope waived)
  L3 the bit arrives via a wholesale image copy ...... verified-by-execution (20.252 R1)
  L4 a copy with dest==live-table happens ............ verified-by-execution on the RIG
      (20.254 R1, by geometry); UNKNOWN on the mac - this boot
  L5 the copy's direction is observable .............. THE LINK THIS BOOT RESOLVES
  L6 the restore source's gate bytes ................. unknown - this boot, first look
  L7 what populates the source image ................. unknown; obfuscated statically

## ADVERSARIAL PASS
ADVERSARIAL PASS: waived:the adversary was the tooling. TOOLS' "check before you fork"
rule stopped me building a probe that already existed - pubrest has been hooked at the
copier since p2-160 and already emits the exact f38src field this front needs. Its defect
was ordering, not absence: it classifies against a registry the participant walk fills at
t=90284, while the copier runs at t=81670 and t=86868, so every call was `unknown` by
construction - including one whose src the same log proves was a table. And
verify_hook_rvas rejected the fix's first form, correctly, because a call-site constant
was named like a hook target; its report ("FRAGMENT offset=0x11c of 0x1404f77d0") is what
confirmed the address is the pool ctor's publish site.

## INSTRUMENTS
INSTRUMENTS: "stage=pubrest fn=%s when=%s call=%llu caller_rva=0x%llX role=%s ", "f38src_0..7=", "f38dest_0..3="

LITERAL TARGETS:
    Game/bin/x64/steam_api64.dll: "stage=pubrest fn=%s when=%s call=%llu caller_rva=0x%llX role=%s ", "f38src_0..7=", "f38dest_0..3="

## DEPLOYED
  server   6f018fcd42d309a4 - all 8 harness gates rc=0. Listeners verified, ladder empty.
  client   MAC ONLY f71b1978aeb43b6c - hash + 3 literals asserted in the deployed file.
           Rig left on 0ff6911ff5a654ae and NOT launched (solo boot).
           Rollback: steam_api64.dll.bak_p2d7_20260903_182929.
  gate     verify_hook_rvas PASS (93 RVAs, 0 bad) after the rename.

## SETTINGS / HYGIENE
  server   membership_peer_transport_identity=true, roster_peer_participation=true
  client   gate_poke=0, milestone_trace=true
  MAC ONLY. Launch one client, reach the Tower, dwell ~60 s, quit.
  Server restarted by the deploy (ladder read back empty = the reset outcome).

## PRE-NAMED OUTCOMES
  1. restore seen + f38src all 00 => expected; front moves to what fills the source image,
     and the copier is closed as a lever. Next question is the source's provenance.
  2. restore seen + a bit4 set => the local mechanism exists; hunt what suppresses it.
  3. only publishes seen => the mac's Tower path does no restore; the paired run decides
     whether a peer's arrival triggers one.
  4. role still unknown => classifier defect, fix from the caller census, no re-boot needed
     to diagnose.
