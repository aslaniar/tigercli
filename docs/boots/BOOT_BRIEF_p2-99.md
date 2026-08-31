# BOOT BRIEF p2-99 (2026-08-29) - CAPTURE THE SLOT CREATOR'S ARGUMENTS. The last unknown
# before the injection can be written instead of guessed.

STATUS: live (2026-08-29 ~00:2x). Client-DLL-only, LOGGING-ONLY. The p2(97) injection is
still in the tree and still switched OFF. Server unchanged from p2(96).

## PURPOSE
p2(98) closed the server road by measurement: the message-30 apply's two slot-creator
call sites never execute, and only the join gate creates a slot - with kind=5, not the
kind=10 both the roster lane and 20.159 assumed. So the DLL injection is the road, its
target is slot 1 (probed and left empty on both machines), and everything about it is now
measured EXCEPT one thing: how to actually make the slot.

Two ways, both stalled on the same gap:
  (a) CALL the real creator 0x1417692E0 - correct by construction, but it takes eight
      arguments and four are stack pointers to structures the join gate builds, contents
      unknown.
  (b) HAND-WRITE the slot - the store list is known (20.159) except a 0x50-byte blob at
      slot+0x50.
This boot dumps both sides of that gap during the one real kind=5 call: the four stack
arguments, and the slot the call produced.

WIN: `ev=admission stage=arg` lines for a5..a8 and for the created slot. If the argument
bytes are dominated by this machine's own identity (its machine id, its address), the
structures are PEER-SPECIFIC and an injection must substitute, not copy. If they look
session-generic, replay with a changed index and machine id is viable - which would make
the injection a short, safe function instead of a synthesis problem.
LOSE: `ok=0` on the dumps, or no arg lines at all - see ABSENCE.

## GRAPHICS DELTA
Zero. No new rendered models, no rendering change: the existing log-only detour gains a
one-shot hexdump. Both clients load the same Tower as p2(93)-p2(98). Boot minimized where
possible; the result is read from the logs.

## FALSIFIABLE CLAIM
Each client emits exactly one set of `ev=admission stage=arg` lines (a5, a6, a7, a8,
slot48, slot88) with `ok=1`, because p2(98) proved the kind=5 call fires exactly once per
boot on each machine and produces a non-zero machine id.

CONTENT NEGATIVE: `ok=0` on the a5..a8 dumps means those arguments are not readable
memory at the time of the call - they would be outputs or scratch, not inputs, and the
replay idea (a) dies. The hand-write road (b) then needs the slot dumps alone.
SECOND CONTENT NEGATIVE: if `slot48`/`slot88` come back all-zero, the 0x50-byte blob is
not populated by this call after all, and 20.159's store list needs re-reading before any
hand-write.
THIRD CONTENT NEGATIVE: if the argument bytes contain this machine's OWN machine id
(mac 0x1D34C7FAE1AFD61D / rig 0x9CE86D46E739E86A as measured in p2(98)), the structures
are peer-specific - which is a RESULT, not a failure: it tells us exactly which bytes an
injection must substitute.

## ABSENCE NEGATIVE
- `ev=admission stage=install result=ok` must appear as in p2(98). Without it the DLL did
  not deploy or activation never reached it (L13/L14) and the boot tested nothing.
- The dump is one-shot and gated on `kind==5 && machine_after != 0`. Zero arg lines while
  slot_create lines DO appear means the kind=5 call did not create this boot - a real
  anomaly against p2(98), not an empty result.
- Six arg lines is the complete expected output. Fewer is a truncation bug in the dumper,
  not evidence about the game.

## CHAIN MARKS
- Only the join gate creates a slot, kind=5, once per boot per machine -
  verified-by-execution (p2(98), both machines identical).
- The apply path never reaches the creator - verified-by-execution (p2(98), zero
  occurrences).
- Slot 0 is self; slot 1 is probed and left free - verified-by-execution (p2(97) census +
  p2(98) idx=1 kind=10 line).
- The creator's ABI: RCX obj, EDX index, R8D kind, R9D flag, four stack args -
  verified-by-reading (both apply call sites) and exercised without incident in p2(98).
- The creator writes slot+0x48/+0x50../+0xc8/+0xd8 - verified-by-reading (20.159 store
  list); THAT THE 0x50 BLOB IS AMONG THEM AT RUNTIME is what slot48/slot88 test.
- The four stack arguments are INPUTS the join gate built - assumed. They could be output
  buffers; the first content negative is exactly that case.

## ADVERSARIAL PASS: waived: solo main-session boot prep, no second reviewer available
in-session (B-checkpoint exception). Adversarial surface: the dumper reads borrowed
pointers supplied by the game. Every read is SEH-guarded and bounded to 64 bytes, into a
fixed stack buffer, and the whole block is one-shot per process behind an atomic
exchange. It runs AFTER the original call, so it cannot perturb the creation it observes.

## INSTRUMENTS:
  "ev=admission stage=arg"
  "ev=admission stage=slot_create"
  "ev=admission stage=install"

## SWITCH POSITIONS FOR THIS BOOT
  client.admission_census    TRUE
  client.admission_inject    FALSE  <- MUST stay false; 20.158/20.160 show it has no
                                       valid target until the slot half is written
  client.admission_member_index 0
  client.admission_xuid      0
  join_roster_observer       FALSE  both clients
  slice_set                  56     both clients
  server: unchanged from p2(96); gameplay switches as p2(93)

## ROLLBACK
Client DLL only, all halves observation. Prior DLL `5d7e6bd61e078c24` (p2(98)). Server
needs no rollback.
