# BOOT BRIEF p2-103 (2026-08-29) - THE FULL RECORD. Does copying a live member record
# survive setup:orbit?

STATUS: live (2026-08-29 ~02:0x). Behaviour change, MAC ONLY; rig is the control. Server
unchanged from p2(96).

## PURPOSE
p2(102) closed 20.104: the mac's roster named the RIG's xuid. The mechanism works and a
fabricated a7 survives the consumer layer. The same boot then froze at `setup:orbit`.

Cause (20.164): the member record was INCOMPLETE. ADMIT writes 48 bytes of address block
across three movups; the injection wrote eight - the xuid - and left the rest zero, on the
principle that writing only what the adoption path reads keeps a wrong guess inert. That
principle failed because flags 0x3D sets bit 0, marking the record PRESENT, which makes it
visible to every consumer rather than only the mapped one.

This boot copies a WHOLE live field group - 0xF8 bytes from +0x3b78, covering the
membership byte, the address block, the flags word, +0x3c32 and +0x3c68 - from member
record 0 (self's, present and complete on every boot) into record 1, then substitutes the
xuid. Replay-with-substitution has succeeded twice in this chain; partial synthesis has
failed twice.

WIN: the roster names the rig as in p2(102) AND the client passes `setup:orbit` and
reaches `activity:in_world`.
LOSE: still frozen - which narrows the cause to something the copy does not fix, and the
first suspect is named below.

## GRAPHICS DELTA
Zero new rendered models. The appearance blob (20.145) is untouched; on a full win the
roster names a peer and NOTHING new renders. Boot minimized where possible.

## FALSIFIABLE CLAIM
With the full-record injection armed on the mac, `stage=inject` reports `member=1
members_now=1` and the client reaches `activity:in_world`, because the only measured
difference between the injected record and a real one - the 0xF0 bytes p2(102) left zero -
is now copied verbatim from a live record.

CONTENT NEGATIVE: `member=0` means either the template record 0 was not live at injection
time (it is read at the same instant, so this would be a timing fact worth knowing) or
record 1 was not free.
SECOND CONTENT NEGATIVE: still frozen at setup:orbit. Then the incompleteness was not the
cause, and the KNOWN APPROXIMATION becomes the first suspect: the copied address block is
SELF's, so the peer's record carries self's address bytes. Any consumer that routes or
compares on those bytes sees two records claiming one address. That would be diagnosed by
instrumenting the record's other readers, NOT by another guess at its contents.
THIRD CONTENT NEGATIVE: reaches in_world, roster names the peer, world still does not swap
to PUB56. That SPLITS the admission and z-leg hypotheses bundled since 20.157 and sends
the swap back to fn 0x140E1D400 / dword[obj+0x524].

## ABSENCE NEGATIVE
- `stage=install ... inject=1` on the mac, `inject=0` on the rig, or the settings did not
  parse and the boot tested nothing.
- No `stage=inject` line with inject=1 means the guard chain refused: no captured
  template, slot 1 occupied, or a zero setting.
- One-shot behind an atomic; exactly one inject line expected.

## CHAIN MARKS
- The roster names the peer once slot AND record exist - verified-by-execution (p2(102)).
- A fabricated a7 survives creation AND the consumer - verified-by-execution (p2(102)).
- The freeze followed a record missing 0xF0 of its bytes - verified-by-execution
  (p2(102) froze; p2(101), which created a slot with NO record at all, did not).
- ADMIT writes 48 bytes of address block - verified-by-reading (20.159 raw PHASE 6).
- Record 0 is live and complete every boot - verified-by-execution (every census).
- Copying self's address block is CORRECT for the peer - KNOWN FALSE, accepted as an
  approximation. It is structurally valid where zeros were not; see the second content
  negative.
- The incompleteness caused the freeze - INFERRED. This boot is its test.

## ADVERSARIAL PASS: waived: solo main-session boot prep, no second reviewer available
in-session (B-checkpoint exception). Adversarial surface: this writes 0xF8 bytes of live
netmgr state, up from 11, and the previous version of this code froze the client. Against
that: the bytes are a verbatim copy of a record the game itself built moments earlier, not
synthesised; the template is verified live and the target verified empty before any write;
every access is SEH-guarded; the sequence is one-shot; it is armed on ONE machine with the
rig as a working control; and it disarms with a settings flip and no rebuild. A freeze is
a recoverable outcome that has already happened once and cost one boot.

## INSTRUMENTS:
  "ev=admission stage=inject"
  "ev=admission stage=census"
  "ev=admission stage=install"

## SWITCH POSITIONS FOR THIS BOOT
  MAC  admission_inject TRUE, member_index 1, xuid 76561198776753862,
       peer_steam_id 76561198776753862, peer_machine 9542145991190258406,
       a7 9542145991190258406, census TRUE
  RIG  admission_inject FALSE (control)
  both join_roster_observer FALSE, slice_set 56; server unchanged from p2(96)

## ROLLBACK
Flip admission_inject to false - no rebuild. Write-free DLL `5d7e6bd61e078c24` is on both
machines and is the current mac baseline. Settings backup
Game/bin/x64/Sunrise/settings.json.bak_p2d101_preboot_20260829.
