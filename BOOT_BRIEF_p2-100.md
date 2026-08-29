# BOOT BRIEF p2-100 (2026-08-29) - THE ARGUMENT CAPTURE, NARROWED. Re-run of p2-99 with
# the dereference that crashed both clients removed.

STATUS: live (2026-08-29 ~00:4x). SUPERSEDES BOOT_BRIEF_p2-99.md. Client-DLL-only,
LOGGING-ONLY. The p2(97) injection is still in the tree and still switched OFF. Server
unchanged from p2(96).

## PURPOSE
p2(99) crashed both clients at character selection (INCIDENT: FINDINGS 20.161). Cause was
mine: the dumper derived its argument shapes from the two slot-creator call sites inside
the message-30 apply - the sites p2(98) had just proven never execute - and applied them
to the join-gate site 0x141772A99 that actually fires and that I had not read. There only
a5 and a6 are pointers; a7 is a bare `rbx` and a8 is the return of the timestamp helper
0x1402fe650. Dereferencing a7 killed the process. Both machines were rolled back to
p2(98) `5d7e6bd61e078c24` and verified by hash.

This boot re-runs the SAME capture with a7/a8 logged as VALUES and never dereferenced.
It is strictly narrower than p2(99); nothing new is touched.

The question is unchanged and still the last one before the injection can be written: the
peer slot must be created for slot 1, and we can neither call the creator (four stack
arguments, contents unknown) nor hand-write it (a 0x50-byte blob, contents unknown). p2(99)
got two of the four before it died and they were decisive - a5 is an identity STRING, a6
leads with the machine id - so the structures are peer-specific and the injection must
SYNTHESISE them, not replay them. What is still missing is a6's layout past the machine id
and the produced slot's blob, which is exactly what slot48/slot88 will show.

WIN: `stage=arg` lines for a5, a6, a7a8, slot48, slot88 - five lines, one machine each.
LOSE: another crash, which would mean a5/a6/arena are not as safe as two boots suggest -
see ADVERSARIAL.

## GRAPHICS DELTA
Zero. No new rendered models, no rendering change. Both clients load the same Tower as
p2(93)-p2(98). Boot minimized where possible; the result is read from the logs.

## FALSIFIABLE CLAIM
Each client reaches the Tower as it did on p2(98) AND emits five `ev=admission stage=arg`
lines, because the only delta from the crashing build is the removal of two dereferences,
and every pointer still dereferenced returned ok=1 in p2(99) (a5, a6) or has been read
without incident across p2(97) and p2(98) (the arena).

CONTENT NEGATIVE: if slot48/slot88 come back all-zero, the 0x50-byte blob is not written
by this call and 20.159's store list needs re-reading before any hand-write attempt.
SECOND CONTENT NEGATIVE: if a6's bytes past the machine id differ between the two
machines in a way that tracks something other than identity, the block is not purely
peer-specific and part of it may be copyable after all - which would simplify the
injection.

## ABSENCE NEGATIVE
- `ev=admission stage=install result=ok` must appear as in p2(98). Without it the DLL did
  not deploy (L13/L14) and the boot tested nothing.
- The dump is one-shot behind an atomic exchange, gated on `kind==5 && machine_after!=0`.
  Five lines is the complete expected output; fewer means the dumper truncated, which is
  a bug in my code, not evidence about the game.
- A crash before character selection again means the remaining reads are unsafe, which is
  itself the finding - roll back to p2(98) and stop dereferencing anything here.

## CHAIN MARKS
- a5 and a6 are pointers at the FIRING call site - verified-by-reading (0x141772a7e
  `lea rax,[rbp+0x1b0]`; 0x141772a85 `mov [rsp+0x28],rsi` from 0x1402ffd20) AND
  verified-by-execution (both returned ok=1 in p2(99) before the crash).
- a7 is a bare rbx and a8 is a timestamp - verified-by-reading (0x141772a79, 0x141772a6d)
  and verified-by-execution (dereferencing a7 crashed the process).
- The arena pointer is safe to read - verified-by-execution (census reads across p2(97)
  and p2(98), ok=1 every time).
- a5/a6 are peer-specific identity data - verified-by-execution (p2(99) partial capture).
- The slot's 0x50-byte blob is written by this call - ASSUMED (20.159 store list, static);
  slot48/slot88 is the test.
- SEH inside a noexcept detour makes a bad dereference survivable - DISPROVEN by p2(99).
  No read in this build relies on it as a safety net; every dereference is on a pointer
  already proven readable.

## ADVERSARIAL PASS: waived: solo main-session boot prep, no second reviewer available
in-session (B-checkpoint exception). Adversarial surface is the obvious one - this build
is a re-run of one that crashed both clients an hour ago. The mitigation is not a guard
but a removal: the two dereferences that faulted are gone, and what remains was
demonstrably safe in the very boot that crashed. Rollback is one command and the prior
DLL is already on disk on both machines.

## INSTRUMENTS:
  "ev=admission stage=arg"
  "ev=admission stage=slot_create"
  "ev=admission stage=install"

## SWITCH POSITIONS FOR THIS BOOT
  client.admission_census    TRUE
  client.admission_inject    FALSE  <- MUST stay false
  client.admission_member_index 0
  client.admission_xuid      0
  join_roster_observer       FALSE  both clients
  slice_set                  56     both clients
  server: unchanged from p2(96); gameplay switches as p2(93)

## ROLLBACK
Client DLL only. p2(98) `5d7e6bd61e078c24` is on both machines as
steam_api64.dll.bak_p2d7_20260828_2316xx and is the verified known-good. Server needs no
rollback.
