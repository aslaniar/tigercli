# BOOT_BRIEF_p2-165 — THE TRANSPORT-IDENTITY CARD (W1 fix verification)

## PURPOSE
Does the client's admission sweep CLAIM the peer's reservation record once the fork
publishes the peer's 86-byte transport identity in the member row? This is the first
boot of the W1 fix (settings key membership_peer_transport_identity): if the cascade
holds, the guard stops matching the blank placeholder and ent_pass fires for the peer.
NOTE (user directive 2026-09-03): NO SOLO CONTROL RUN — the off-path is wire-tested
byte-identical (9/9 cases) so any digestion change is attributable to the new field by
construction; the solo's attribution value is already covered.

## GRAPHICS DELTA
No new rendered models expected: the change is wire-content only. If a peer renders,
that IS the finding (first-ever peer render) — count and screenshot it.

## FALSIFIABLE CLAIM
The peer row's transport identity reaches the participant slot's +0x142 (slot_card
line, non-zero, starting with the rig's NetAddr bytes C0 A8 01 88) and the sweep stops
disowning the peer's reservation record (rec mask keeps its bit / gains bit 7).
CONTENT NEGATIVE: if slot_card still reads all-zero after the membership lands while
the server logged stage=peer_transport_identity result=built, the composer ignores the
field (wrong field position or a different compose path) — W1 is NOT the wall's root.

## ABSENCE NEGATIVE
Zero slot_card lines or zero resv_ident lines means the rebuilt probe DLL did not load
or the new first-seen-key/budget path broke the observers — the boot is INVALID as a
test of the fix (check the DLL hash ddaa2ef905483abe in both logs first). Zero
gatebit lines means ent_gate never ran — the poke is not armed (ent_gate requires it,
p2-162); the boot tests nothing without it.

## CHAIN MARKS
- guard compares slot+0x142 (86 B) vs rec+0x3144 (86 B): verified-by-reading (20.278,
  20.280; r9=slot+0x142 at 0x141702717; lookup 0x1417C40F0 test word [rec+0x3112]).
- sweep disowns unclaimed records (clears both mask words): verified-by-reading
  (20.280; 0x1417021C0 family, clear 0x1417C4810) — and verified-by-execution against
  the p2-164 timeline (t=328727 clear coincides with the membership ingress apply).
- blank cards claim the blank placeholder (rec1 immune, real record disowned):
  verified-by-execution (p2-164 log reads; rec1 mask 0x0080/0x00C0 stable, rec2
  cleared).
- the card's content source = the peer's advertised NetAddr blob: verified-by-reading
  (20.272 R3: reservation identity = the fork-published NetAddr; write_net_addr is the
  fork's own composer; descriptor::read recovers the same endpoint).
- the field reaches the body: verified-by-execution (membership-wire-test 9/9, byte
  exact readback at the computed bit offset; 20.281).
- the required mask bit = 7 (mac) / 6 (rig): ASSUMED from the red-team derivation
  (20.279 R2); gatebit lines pin it this boot — treat the derivation as unproven until
  then.
- the claim sets rec+0x3114 while the guard tests rec+0x3112 (birth-set word):
  verified-by-reading (20.280); whether a RE-BORN record lands bit 7 in the guard's
  word is UNKNOWN until this boot (the residual pin).

## ADVERSARIAL PASS
ADVERSARIAL PASS: waived:this brief executes the red-team session's own gated design (verdict 20.279 + BOOT_IMPL spec section C); its four prerequisites were satisfied in 20.280/20.281.

## INSTRUMENT SET + BUDGETS (census before filter)
ent_gate (24 + first-seen keys, gatebit on change), ent_pass (24 + first-seen), connmgr
(24 + first-seen), resv (change-gated incl. mask; resv_ident full 86B), ptable/slot_card
(change-gated), pubrest, admission, nat, ingress — all pre-existing read-only observers,
same build both machines (ddaa2ef905483abe). NOTIFIER OFF (mac notifier_hook=false, rig
absent). gate_poke ARMED both machines — the sanctioned throwaway diagnostic; ent_gate
never runs without it (p2-162). REVERT BOTH pokes to 0 immediately after the boot.

## PRE-NAMED OUTCOMES (read top-down; each names its next action)
(0) any client reject / freeze / decode failure on the +688-bit body -> schema legality
    failure -> fix the encoder bit accounting; do not read further.
(L) no slot_card AND no resv_ident lines -> probe DLL not loaded (hash check) -> boot
    invalid, re-deploy.
(a) ent_pass > 0 -> FULL cascade: the peer record passed all three predicates. The
    first-ever peer render is expected; proceed to the entity-creation front.
(b) peer-slot leave rets flip to retcls=1/3 (bail 3) on the peer slot -> the card
    LANDED and stopped matching the placeholder, but the peer's record is still not
    selectable (mask bit 7 not in the guard's word, or record states) -> W1 verified;
    the W2/W3 levers follow (re-birth/sequencing; the join-flow rung).
(c) peer-slot rets stay retcls=2 (bail 5) AND slot_card is NON-zero -> the card landed
    but the guard still matches the placeholder or another wrong record -> read resv
    lines: if rec mask gains bit 7 (0x0080) the claim ran; if not, the claim did not
    select the peer's record -> chase the claim pass inputs.
(d) slot_card stays zero AND server logged result=built -> the client's composer drops
    the field (wrong field position) -> back to the schema walk with the slot_card
    evidence.
(e) server logs result=no_descriptor/read_rejected on every body -> the peer advert
    carried no endpoint this run -> the identity source dried up; check the advert
    path before blaming the encoder.

## SETTINGS / HYGIENE
server: membership_peer_transport_identity=true (live, restarted).
clients: gate_poke=1 both; notifier_hook off both. Server reset done pre-launch, no
client logged in. Boot scope is FIXED at this brief: no instrument tweaks mid-boot.
