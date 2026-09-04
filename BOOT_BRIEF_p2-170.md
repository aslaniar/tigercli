# BOOT_BRIEF_p2-170 — THE CASCADE TEST: CORRECT CARD + GATE FORCED OPEN

STATUS: live (2026-09-03). Paired. Answers "is the rest of the chain real".

## PURPOSE
Every link past the gate has been verified alone; the chain has never run end to end,
because until 20.284 the guard was always fed an EMPTY field. p2-166 forced the gate open
667 times and saw nothing - a null that meant nothing, since the card was landing in the
neighbouring field at the time. That combination - gate open AND a correct card - has
never been tested. This boot tests it.

WIN OR LOSE IT LEARNS: whether filling the guard's field actually arms the claim, stops
the admission sweep disowning the peer record, and sets the mask bit (W2). It answers
whether the remaining work is "two known problems" (the server-side gate, and movement)
or "our model of this chain is wrong".

## GRAPHICS DELTA
UP TO ONE new rendered model, and that would be the headline. Expected outcome is still
NO peer body: entity construction has never been reached and is a separate stage. A
rendered peer is the best case, not the baseline - do not read its absence as failure of
the claim step, which is what the counters measure.

## FALSIFIABLE CLAIM
Forcing the gate open, WITH the peer's real identity in the field the guard reads, causes
the guard to claim the peer's reservation record.

CONTENT NEGATIVE:
 - guard called, but the sweep still disowns the peer record (mask returns to 0) => the
   identity compare is NOT the claim condition. The 20.280 cascade model is wrong, and the
   parked server-side gate question is NOT worth solving as specified.
 - guard called, record claimed, mask set, but entity counters unchanged => the cascade is
   real and ends short of construction. W2 falls; the front moves to entity creation
   (20.208 R6 / 20.213 R1 levers), and movement remains untouched.
 - guard called, record claimed, mask set, counters move => the chain is real end to end.
 - guard NOT called despite poke=1 => the poke did not take. Read gatepoke gate_ok before
   concluding anything about the cascade.

## ABSENCE NEGATIVE
 - ZERO stage=gatepoke lines => the switch is not live in the running client (settings not
   reloaded, or the client was not relaunched). Says NOTHING about the cascade.
 - gatepoke present with gate_ok=0 => the write itself failed; the gate never opened.
 - ZERO stage=pgate lines => the participant walk never ran; the session did not reach the
   state under test. Re-run; do not interpret.
 - ZERO ent_gate calls WITH pgate showing ALL-PASS => the walk reached the guard call site
   and the guard still did not run: a contradiction that indicts the instrument, not the
   game (U13).

## CHAIN MARKS
  L1 card lands in the guard's field ......... verified-by-execution (20.284 R1, 1559 samples)
  L2 the guard reads that field .............. verified-by-reading (20.285 R3)
  L3 the gate can be forced open ............. verified-by-execution (p2-166, 667 calls)
  L4 guard -> claim (find-or-create) ......... verified-by-reading (20.285 R5) - THE LINK
      THIS BOOT RESOLVES, and the first test of it with a NON-EMPTY card
  L5 claim -> sweep stops disowning .......... assumed (20.280 cascade) - tested here
  L6 mask bit set (W2) ....................... unknown - measured here for the first time
  L7 entity construction ..................... unknown; never reached
  L8 peer movement ........................... UNSTARTED; the obvious carrier was retired
      (20.196/20.208 R5). Not in scope and not measured by this boot.

## ADVERSARIAL PASS
ADVERSARIAL PASS: waived:the poke is a THROWAWAY DIAGNOSTIC under the AGENTS.md carve-out,
armed for this boot and reverted at its end - it answers "does X matter", and cannot be
the delivered mechanism. The single-variable discipline is the reason only the poke moved:
the speculative knobs (peer row-flag mask, lease size) stay OFF so a positive result is
self-attributing. Ordering rationale: failing here costs one boot; failing here AFTER
solving the server-side gate would cost that work too.

## INSTRUMENTS
INSTRUMENTS: "stage=gatepoke fn=%s call=%llu i=%u rec8=0x%llX mask=0x%X f38_was=0x%02X f38_now=0x%02X gate_ok=%u state_self=0x%02X state_ok=%u", "ALL-PASS-would-claim", "stage=gatebit fn=%s call=%llu container=0x%llX value=%d bitreq=%llu"

LITERAL TARGETS:
    Game/bin/x64/steam_api64.dll: "stage=gatepoke fn=%s call=%llu i=%u rec8=0x%llX mask=0x%X f38_was=0x%02X f38_now=0x%02X gate_ok=%u state_self=0x%02X state_ok=%u", "ALL-PASS-would-claim", "stage=gatebit fn=%s call=%llu container=0x%llX value=%d bitreq=%llu"

## DEPLOYED
  server   6f018fcd42d309a4 - 8/8 harness gates rc=0; listeners 3/3, nat ok, ladder empty,
           claims reset to 0 immediately before this run.
  clients  BOTH f71b1978aeb43b6c (hash asserted in both deployed files).
  gate     verify_hook_rvas PASS (93 RVAs, 0 bad).

## SETTINGS / HYGIENE
  server   membership_peer_transport_identity=true, roster_peer_participation=true
  clients  *** gate_poke=1 BOTH MACHINES (JSON re-validated after edit on both) ***
           milestone_trace=true. Speculative knobs OFF.
  RELAUNCH BOTH CLIENTS - settings are read at start.
  *** REVERT gate_poke TO 0 ON BOTH MACHINES THE MOMENT THIS BOOT ENDS (AGENTS.md). ***
  Backups: mac settings.json.bak_poke_<stamp>; rig settings.json.bak_poke_20260903.

## PRE-NAMED OUTCOMES
  1. mask set + counters move => chain real end to end. Next: movement, and the server-side
     gate becomes a delivery problem rather than a research one.
  2. mask set + counters flat => W2 FALLS, front moves to entity construction.
  3. record claimed but sweep still disowns => cascade model wrong; do NOT spend effort on
     the parked gate question as specified. Re-derive the claim condition.
  4. gate_ok=1 but guard never called => instrument or walk-precondition problem; diagnose
     from pgate's other conditions, no re-boot needed.
