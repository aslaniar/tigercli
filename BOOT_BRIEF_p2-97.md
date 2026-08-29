# BOOT BRIEF p2-97 (2026-08-28) - THE ADMISSION CENSUS: verify the member-table geometry
# at runtime, and name a safe record index for the injection sitting behind the switch.

STATUS: live (2026-08-28 ~23:5x). Client-DLL-only. The injection SHIPS BUT IS SWITCHED
OFF; this boot is observation. Server unchanged from p2(96).

## PURPOSE
p2(96) closed route A: the type-0x0A admission join never reaches our server (ids
12/26/29/31/34/37/39, all dispatched, zero fallthrough, no id=10). Admission can only be
injected in-process, through our own DLL. The roster-caller lane mapped what that means -
the peer-adoption arm reads a peer's xuid ONLY out of the member-record array, which only
ADMIT (0x141777EC0) writes, which our peers never reach.

That mapping is a STATIC reading by another lane, and that lane labels its own
reserve->admit trigger chain INFERRED. Writing into live netmgr state on an unverified
reading is precisely p2(62) - six bindings changed, froze, cause now unknowable. So the
injection ships behind `client.admission_inject` (default FALSE) and this boot runs only
the census half, which verifies the geometry and answers the lane's own open runtime
question: WHICH gate blocks - the tick's state==5, or the empty member list.

WIN: `ev=admission stage=census` lines naming, per peer slot, its state / machine id /
member count, plus a member-record index that is provably unused. That confirms the
geometry AND supplies the two settings the injection needs
(`admission_member_index`, `admission_xuid`), which then flip with NO REBUILD.
LOSE: no census lines, or `ok=0` reads - the geometry is wrong and the injection must not
be flipped at all (see the negatives).

## GRAPHICS DELTA
Zero. No new rendered models, no rendering change: one detour that reads netmgr fields
and calls the original untouched. Both clients load the same Tower as p2(93)-p2(96). Boot
minimized where possible - the result is read from the logs.

## FALSIFIABLE CLAIM
With the p2(97) client DLL on both machines, each emits `ev=admission stage=install
result=ok census=1 inject=0` and then `ev=admission stage=census` lines in which the
PEER slot (the one whose machine id is the other machine's) reads `members=0`, because
the roster-caller lane's whole thesis is that our peers are never admitted and therefore
hold no member records.

CONTENT NEGATIVE: a census line showing `members>0` with a non-zero `first_xuid` for the
peer would REFUTE that thesis - the member table would already be populated and the
roster's emptiness would have another cause entirely. Do not flip the injection; re-open
20.104 instead.
SECOND CONTENT NEGATIVE: `ok=0` on the peer rows means the geometry (arena +0x860, peer
stride 0xb8, state stride 0x120, member stride 0x1a8) does not hold at runtime. The
injection MUST NOT be flipped - it would write at computed offsets that are wrong, which
is the freeze scenario.
THIRD CONTENT NEGATIVE: if every peer slot reads `state=3`, the adoption arm's own
selection (`cmp state,3 / jne -> selected`) rejects them before the member list matters,
and admission is not the blocking gate - the state is.

## ABSENCE NEGATIVE
- `ev=admission stage=install` prints on every attach attempt with its reason and echoes
  all four switch values. No line at all = the DLL did not deploy or activation never
  reached it (L13/L14) - the boot tested nothing.
- `result=fail why=range` = the adoption RVA is outside the module (wrong build), NOT a
  wrong map.
- The census logs only when the peer picture CHANGES and caps at 48 lines. A short census
  is the design; absence of repeats proves nothing.
- `inject=0` in the install line is the REQUIRED state for this boot. If it reads 1, the
  settings were mis-set and the boot is not the observation it claims to be - discard it.

## CHAIN MARKS
- The admission join never reaches this server - verified-by-execution (p2(96) id census,
  zero fallthrough, no id=10; scope: the group-host pump only).
- add_candidates has no own/peer filter; the peer's xuid can only arrive via the member
  record array - verified-by-reading (roster-caller CLAIM 1/3, raw PHASE 1/4/6).
- ADMIT writes rec+0x3c00 / +0x3c30 / and the adoption path reads xuid at +0x3c00, bit 4
  of +0x3c30, and the membership byte at +0x3b78 - verified-by-reading (raw PHASE 4/6,
  verbatim stores).
- RCX = netmgr at the adoption entry - verified-by-reading (`lea r15,[rcx+0x860]` is its
  first real instruction).
- The reserve->admit TRIGGER chain - INFERRED by the roster-caller lane itself, inherited
  from 20.108/20.109, NOT re-derived. This boot does not depend on it; the injection
  bypasses the trigger and writes the end state directly.
- The three fields are the WHOLE surface the adoption path reads - assumed. If the game
  reads more of the record elsewhere, a partially-forged record could mislead a different
  consumer. The injection writes only consumed fields to keep a wrong guess inert.
- Admission also unblocks the z-leg (+0x524) - assumed, and NOT tested by this boot. It
  is the session's leading hypothesis, nothing more.

## ADVERSARIAL PASS: waived: solo main-session boot prep, no second reviewer available
in-session (B-checkpoint exception). The adversarial surface is that this boot ships
code that can corrupt netmgr. It is disarmed three ways: the switch defaults FALSE and
the install line echoes its state; the writer refuses any record whose address head or
flags word is already non-zero; and every read and write is SEH-guarded. The census half
carries the same hot-path construction that ran clean in p2(95)/p2(96) - log only on a
changed picture, hard cap, nothing formatted otherwise.

## INSTRUMENTS:
  "ev=admission stage=census"
  "ev=admission stage=install"
  "ev=admission stage=inject"

## SWITCH POSITIONS FOR THIS BOOT
  client.admission_census    TRUE   <- the contract
  client.admission_inject    FALSE  <- MUST be false this boot
  client.admission_member_index 0   (unused while inject is false)
  client.admission_xuid      0      (zero disables the injection outright)
  join_roster_observer       FALSE  both clients
  slice_set                  56     both clients
  server: unchanged from p2(96) - all gameplay switches as p2(93)
  NOTE: the rig's settings.json carries no admission keys; the DEFAULTS are census=true /
  inject=false / 0 / 0, which is exactly this boot's intent. Verify via its install line.

## ROLLBACK
Client DLL only, and the behaviour half is already off. Prior DLL `d7eef1bafc54ea63`
(p2(96)); settings backup Game/bin/x64/Sunrise/settings.json.bak_p2d97_preboot_20260828.
Server needs no rollback.
