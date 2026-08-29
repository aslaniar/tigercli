# BOOT BRIEF p2-102 (2026-08-29) - BOTH HALVES. Slot + member record. Does the roster
# finally name the peer?

STATUS: live (2026-08-29 ~01:3x). Behaviour change, MAC ONLY; the rig runs the same
binary with inject off as the control. Server unchanged from p2(96).

## PURPOSE
p2(101) proved the slot half works: the game's own creator accepted a FABRICATED a7 and
populated slot 1 with the peer's identity, state=5. It also proved that is not enough -
`members=0`, and the roster still named only self, which is exactly what 20.158 predicted
and BOOT_BRIEF_p2-101 pre-named as its third content negative.

This boot adds the second half - the member record - which has existed since p2(97) and
sat orphaned because it had no slot to attach to. It writes only the three fields the
adoption path reads (20.157), plus the slot's member list pointing at them:
```
  rec+0x3c00 = the peer's xuid    rec+0x3c30 = 0x3D    rec+0x3b78 = 0
  slot1+0xe8 = 1                  slot1+0xf0 = 1  (member index 1; index 0 is slot 0's)
```
NOTE the flags value: 0x3D, what a LIVE record was measured to carry in p2(97) - not
ADMIT's documented 0x1D, whose disassembly never accounted for bit 5 (20.158). We write
what real records hold, not what one writer's stores explain.

WIN: `stage=inject result=called member=1 members_now=1`, and then the mac logging
`Adding player [xuid=0x110000130aa9ec6]` - the RIG's xuid. That closes 20.104 and proves
the admission thesis end to end.
LOSE: each failure below is separately diagnostic.

## GRAPHICS DELTA
Zero new rendered models. Even on a full win the roster may name a second guardian but
NOTHING new renders - the appearance blob (20.145) is untouched, so no peer model can
exist. Boot minimized where possible.

## FALSIFIABLE CLAIM
With both halves armed on the mac, `ev=admission stage=inject` reports `member=1
members_now=1`, because the slot creation was already proven to land in p2(101) and the
member write targets index 1, which the p2(97) census showed unused.

CONTENT NEGATIVE: `member=0` means inject_member refused - the record at index 1 already
had a non-zero address head or flags word, so index 1 is NOT free and another must be
chosen.
SECOND CONTENT NEGATIVE: `members_now=1` but the roster still names only self. Then the
member record is present and the adoption path still rejects the peer - and the remaining
gates are the ones 20.157 CLAIM 4 named: the tick's state==5 outer mask, or the
adoption arm's `cmp state,3 / jne` selection. The fabricated a7 would then be suspect at
the CONSUMER layer even though it passed at creation.
THIRD CONTENT NEGATIVE: roster names the peer but the world swap still stalls. That
SPLITS the admission and z-leg hypotheses, which 20.157 bundled - a real and useful
result, and it would send the swap back to fn 0x140E1D400 and dword[obj+0x524].

## ABSENCE NEGATIVE
- `stage=install ... inject=1` on the mac, `inject=0` on the rig. Otherwise the settings
  did not parse and the boot tested nothing.
- No `stage=inject` line while inject=1 means the guard chain refused: no template
  captured, slot 1 not free, or a required setting zero. All four settings must be
  non-zero on the mac.
- One-shot behind an atomic; exactly one inject line is expected.

## CHAIN MARKS
- The slot half works and a fabricated a7 is accepted at creation - verified-by-execution
  (p2(101): ret non-zero, machine_now set, state=5).
- A slot without a member record leaves the roster unchanged - verified-by-execution
  (p2(101): members=0, only self logged).
- The three fields are the whole surface the adoption path reads - verified-by-reading
  (20.157, raw PHASE 4).
- Member index 1 is free - verified-by-execution (p2(97) census: slot 0 uses index 0).
- A live record carries flags 0x3D - verified-by-execution (p2(97) census).
- The member array and slot array do not alias despite a shared base - verified-by-reading
  (record fields sit at +0x3c00 offsets; slot fields below +0x100).
- The fabricated a7 survives the CONSUMER layer - ASSUMED, and the second content
  negative is exactly its test.
- Admission unblocks the world swap - ASSUMED, bundled since 20.157, and the third
  content negative is what would separate it.

## ADVERSARIAL PASS: waived: solo main-session boot prep, no second reviewer available
in-session (B-checkpoint exception). Adversarial surface: two writes into live netmgr
state now instead of one. Mitigations unchanged and proven across p2(101): the record is
re-read and must be empty before writing, every access is SEH-guarded, the whole sequence
is one-shot, armed on ONE machine, and disarms via settings with no rebuild. p2(101) ran
this same code path for the slot half without incident.

## INSTRUMENTS:
  "ev=admission stage=inject"
  "ev=admission stage=census"
  "ev=admission stage=install"

## SWITCH POSITIONS FOR THIS BOOT
  MAC  admission_inject        TRUE    <- the contract, this machine only
       admission_member_index  1       (unused record; index 0 is slot 0's)
       admission_xuid          76561198776753862  (the rig, = 0x110000130AA9EC6)
       admission_peer_steam_id 76561198776753862
       admission_peer_machine  9542145991190258406
       admission_a7            9542145991190258406
       admission_census        TRUE
  RIG  admission_inject        FALSE   (control)
  both join_roster_observer FALSE, slice_set 56; server unchanged from p2(96)

## ROLLBACK
Flip admission_inject to false - no rebuild. Client DLL `530c56b85d229b5f` (p2(101)) and
`c12eca660aeadcb8` (p2(100)) are both on disk on each machine. Settings backup
Game/bin/x64/Sunrise/settings.json.bak_p2d101_preboot_20260829. Server needs no rollback.
