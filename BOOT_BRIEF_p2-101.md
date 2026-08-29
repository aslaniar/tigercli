# BOOT BRIEF p2-101 (2026-08-29) - THE INJECTION, ARMED ON THE MAC ONLY. Does a
# fabricated a7 get the peer onto the guest list?

STATUS: live (2026-08-29 ~01:0x). FIRST BEHAVIOUR CHANGE ON THE CLIENT in this chain.
Armed on the MAC ONLY; the rig is the control. Server unchanged from p2(96).

## PURPOSE
Everything the injection needs is now measured (20.162): the creator's full call, the
slot layout end to end, and the fact that the "mystery 0x50 blob" is just the ASCII
identity string. One input is unknown - a7, the per-session machine id, which is
different every boot and which our server has never seen.

This boot tests candidate (iii) from 20.162: that a7 is a purely LOCAL key, so a
plausible fabricated value suffices. The fabrication chosen is NOT random - it is the
peer's SESSION-FORM machine id (rig E622D0F738836C84 -> 0x846C8338F7D022E6), which is a
genuine, stable, peer-specific identifier, and which 20.153 showed is the form the
client's own tracking lookups are keyed on. If any consumer downstream matches on it, a
real id beats a random one; if a7 must be the true per-session value, this fails and we
go hunting for it on the peer channel.

The injection calls the game's OWN creator (0x1417692E0) rather than hand-forging the
slot, so every field is written by the game - including the flags bit 5 that ADMIT's
recorded stores never explained (20.158). a5 and a6 are the template CAPTURED from the
real kind=5 call this same boot, with only the steam id and the machine-id head
substituted; every byte we do not understand stays byte-faithful.

WIN: `ev=admission stage=inject result=called ... machine_now=0x846C8338F7D022E6`,
then a census line showing peer=1 populated, and - the real prize - the mac's roster
naming the RIG's xuid (0x110000130aa9ec6) in an `Adding player` line. That would close
20.104 and confirm the whole admission thesis.
LOSE: any of the stages below fails; each failure is separately informative.

## GRAPHICS DELTA
Zero new rendered models. If the injection works the mac's roster UI may name a second
guardian, but nothing new is RENDERED - the appearance blob (20.145) is untouched and no
peer model can appear. Boot minimized where possible.

## FALSIFIABLE CLAIM
With inject armed on the mac, `ev=admission stage=inject result=called` appears exactly
once with `machine_now` equal to the injected id, because slot 1 was measured free on
both machines in p2(97)/p2(98) and the creator writes the machine id at slot+0xC8.

CONTENT NEGATIVE: `result=id_build_failed` means the captured identity template did not
have the "steamid:<digits>#" shape the substitution expects - a bug in my parser, not a
statement about the game.
SECOND CONTENT NEGATIVE: `result=called` but `machine_now=0x0` means the creator ran and
refused to populate the slot - our arguments are wrong somewhere, and the a7 question is
NOT yet answered because we never got a slot at all.
THIRD CONTENT NEGATIVE: slot populated but the roster still names only self. THAT is the
answer to this boot's actual question: a slot alone is insufficient, the member record
(ADMIT's half) is also required, and 20.158's two-half analysis is confirmed.
FOURTH CONTENT NEGATIVE: slot populated, roster names the peer, but the world swap still
stalls. That splits the admission hypothesis from the z-leg one - both were bundled in
20.157 and this would separate them.

## ABSENCE NEGATIVE
- `ev=admission stage=install ... inject=1` MUST appear on the mac and `inject=0` on the
  rig. If the mac reads inject=0 the settings did not parse and the boot tested nothing.
- No `stage=inject` line at all, with inject=1 echoed, means the guard chain refused:
  either no template was captured (no `tag=a5` line), or slot 1 was not free
  (`read_peer` returned a machine id), or a required setting was zero.
- The injection is one-shot per process behind an atomic. Exactly one line is expected.

## CHAIN MARKS
- The creator's full ABI and every argument's nature - verified-by-execution (20.162,
  both machines, five arg lines each).
- The 0x50 blob is the identity string - verified-by-execution (slot48 dump).
- Slot 1 is free on both machines - verified-by-execution (p2(97) census + p2(98) idx=1).
- kind=5 creates, kind=10 does not - verified-by-execution (20.160).
- a5/a6 are peer-specific - verified-by-execution (20.162).
- Calling the creator re-entrantly from the adoption detour is safe - ASSUMED. Same
  thread, same subsystem, and the creator does not call itself, but this is the first
  time we invoke a game function rather than observe one.
- A fabricated a7 suffices - ASSUMED, and it is this boot's entire question.
- The peer's session-form machine id is a better fabrication than a random value -
  INFERRED from 20.153 (tracking lookups are keyed on that form). Not proven.

## ADVERSARIAL PASS: waived: solo main-session boot prep, no second reviewer available
in-session (B-checkpoint exception). Adversarial surface: this is the first call INTO a
game function and the first write to live netmgr state in this chain, and p2(99) is the
recent reminder of what a wrong argument does. Mitigations: every argument is either
measured (rcx/edx/r8d/r9d, a5/a6 templates) or a value we control (a7/a8); the target
slot is re-read and must be empty; the whole thing is one-shot, switch-gated, and armed
on ONE machine so the rig remains a working control; and the prior DLL plus a settings
backup are on disk. If the mac crashes, the rig still tells us the session was otherwise
healthy.

## INSTRUMENTS:
  "ev=admission stage=inject"
  "ev=admission stage=census"
  "ev=admission stage=install"

## SWITCH POSITIONS FOR THIS BOOT
  MAC  admission_inject         TRUE   <- the contract, this machine only
       admission_peer_steam_id  76561198776753862   (the rig)
       admission_peer_machine   9542145991190258406 (rig session-form id, LE)
       admission_a7             9542145991190258406 (the fabrication under test)
       admission_census         TRUE
  RIG  admission_inject         FALSE  (control; no admission keys, defaults apply)
  both join_roster_observer FALSE, slice_set 56
  server unchanged from p2(96); gameplay switches as p2(93)

## ROLLBACK
Client DLL `c12eca660aeadcb8` (p2(100)) is on both machines as
steam_api64.dll.bak_p2d7_20260828_2326xx. Mac settings backup
Game/bin/x64/Sunrise/settings.json.bak_p2d101_preboot_20260829. Flipping
admission_inject to false disarms with no rebuild. Server needs no rollback.
