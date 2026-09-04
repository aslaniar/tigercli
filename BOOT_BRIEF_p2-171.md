# BOOT_BRIEF_p2-171 — W2 ON ONE LINE (repeat of p2-170 with the corrected instrument)

STATUS: live (2026-09-03). Paired, poke armed. The last boot before the handoff.

## PURPOSE
p2-170 answered the cascade question (the claim sticks; no entity follows) but W2 itself was
read wrong THREE times in one session - `value=0` on the gatebit line is a container counter,
not the bit's state, and the bit's real home is the field resv_rec already printed as `mask`.
This boot re-runs the identical scenario with a probe that states W2 outright, so the handoff
carries a measured W2 rather than an inferred one.

WIN OR LOSE IT LEARNS: for every reservation record - including the one carrying the peer's
real identity - whether the bit the guard demands is set, on the same line as the record's
state and identity. An offline replay over p2-170's recorded values already shows the shape:
the BLANK records carry the required bit, the peer's record does not.

## GRAPHICS DELTA
ZERO new rendered models expected, same as p2-170: entity construction is not reached and
nothing in this build changes that. Instrument-only change plus the poke. A rendered peer
would be a surprise to explain, not a success to bank.

## FALSIFIABLE CLAIM
Every resv_rec line now reports the guard's bit requirement(s) and whether the record
satisfies them, and the peer-identity record reports NOT satisfied.

CONTENT NEGATIVE:
 - the peer's record reports the required bit SET => p2-170's reading was wrong and W2 is
   already passed; the blocker is elsewhere and the entity front must be re-scoped.
 - reqA=0 AND reqB=0 on every line => the requirement was never pinned this boot; every
   setA/setB reads -1 and W2 is UNMEASURED, not negative. Do not read -1 as a clear bit.
 - only one of reqA/reqB populated on the mac => only one container was seen; p2-170 saw
   two (6 and 7). Not a defect by itself, but the single value may be the wrong one for
   the peer's record - say so rather than concluding.

## ABSENCE NEGATIVE
 - ZERO stage=resv_rec lines => the reservation dump never ran; W2 unmeasured, and nothing
   about the bit can be concluded.
 - ZERO stage=gatebit lines => the requirement was never pinned, so setA/setB are -1 by
   construction. An instrument result, not a game result.
 - ZERO stage=gatepoke lines => the poke did not arm; this is then a repeat of a
   no-poke boot and says nothing about the cascade.

## CHAIN MARKS
  L1 card in the guard's field ............... verified-by-execution (20.284)
  L2 gate forced open, guard runs ............ verified-by-execution (p2-170, 1190 calls)
  L3 claim sticks, record retained ........... verified-by-execution (p2-170 - the record
      holds its word at the top of the ladder instead of being disowned)
  L4 W2: is the REQUIRED bit set ............. THE LINK THIS BOOT MEASURES DIRECTLY
      (offline replay says no on the peer's record, yes on the blanks - to be confirmed live)
  L5 entity construction ..................... verified-by-execution as NOT REACHED
      (counters flat at 8/7 across every boot this session)
  L6 movement ................................ UNSTARTED, out of scope

## ADVERSARIAL PASS
ADVERSARIAL PASS: waived:the adversary was an offline replay of the new column over p2-170's
recorded values, which validated the arithmetic AND caught a real defect before deploy - the
mac pins TWO requirements (6 and 7) from two containers, so the single global I first wrote
would have answered W2 for whichever container fired last. It now reports both. That replay
is the p2-160 lesson applied: a recorded run is a fixture, and shipping without it spends a
launch to run a unit test.

## INSTRUMENTS
INSTRUMENTS: "reqA=%u setA=%d reqB=%u setB=%d", "stage=gatebit fn=%s call=%llu container=0x%llX value=%d bitreq=%llu"

LITERAL TARGETS:
    Game/bin/x64/steam_api64.dll: "reqA=%u setA=%d reqB=%u setB=%d", "stage=gatebit fn=%s call=%llu container=0x%llX value=%d bitreq=%llu"

## DEPLOYED
  server   6f018fcd42d309a4 - unchanged from p2-170; listeners 3/3, nat ok, claims reset 0.
  clients  BOTH a96a6a70f578fc40 - hash + 2 literals asserted in each deployed file.
           Rollbacks: mac .bak_p2d7_20260903_191132 / rig .bak_p2d7_20260903_191141.
  gate     verify_hook_rvas PASS (93 RVAs, 0 bad).

## SETTINGS / HYGIENE
  clients  gate_poke=1 BOTH (verified by reading the value back on each machine)
  server   membership_peer_transport_identity=true, roster_peer_participation=true
  RELAUNCH BOTH CLIENTS.
  *** REVERT gate_poke TO 0 ON BOTH THE MOMENT THIS BOOT ENDS (AGENTS.md carve-out). ***

## PRE-NAMED OUTCOMES
  1. peer record reqX set=0, blanks set=1 => W2 CONFIRMED as "the bit is on the wrong
     records". Hand off with W2 measured; the entity front owns what follows.
  2. peer record set=1 => W2 already passed; re-scope before the handoff.
  3. setA/setB all -1 => instrument, not game. Fix the pin, no boot needed to diagnose.
