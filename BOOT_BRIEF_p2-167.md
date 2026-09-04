# BOOT_BRIEF_p2-167 — THE FIELD RE-PIN (W1 fix verification) + THE ADMISSION RACE

STATUS: live (2026-09-03). Follows p2-166 (FINDINGS 20.283).

## PURPOSE
p2-166 proved the peer card REACHES the participant slot and lands one 86-byte array too
early (slot+0xEC instead of the guard's slot+0x142). This boot tests the one-line
correction, and separately tests whether the peer that lost the admission race last time
now gets its card published at all.

## GRAPHICS DELTA
ZERO new rendered models expected. W2 (the peer's gate bit) is untouched, so even a
correctly placed card should not produce a rendered peer. A rendered peer is a surprise to
explain, not a success to bank. No client writes into game data: gate_poke=0 on BOTH
machines, gate_wwatch DR/VEH/suspend retired at compile time.

## FALSIFIABLE CLAIM
TWO contracts, independent, both observable in one run:
  (A) The card lands at the field the admission guard compares.
  (B) BOTH peers get a card published, not just the one that was admitted first.

CONTENT NEGATIVE:
  - Bytes at slot+0x198 => the index is now one too HIGH; correction is one line
    (kTransportIdentityFieldIndex).
  - Bytes at slot+0xEC AGAIN => consecutive presence indices do NOT map to consecutive
    arrays in the client's decode. The approach needs rework; do NOT nudge the number a
    third time.
  - `waits=n/8` pinned at 8 with a still-absent rig card => the admission race is longer
    than 40 s, or admission never lands. The wait cap is not the fix; the trigger is.
  - Rig card still `no_admitted_row` with waits well under the cap => the refusal is not
    the race after all, and R3's timing reading is wrong.

## ABSENCE NEGATIVE
  - ZERO `result=begin` lines => the block never ran; check the deployed hash FIRST
    (0ff6911ff5a654ae). Says nothing about the card.
  - `result=begin` present, zero hex lines => the long-line emit path alone failed.
  - ZERO `peer_transport_identity` lines => no peer-bearing body went out at all: a
    PAIRING failure, not a verdict on either contract.
  - Card correct at 0x142 but `slot_card` still zero => the guard reads a different member
    than 20.280 mapped, and the re-pin is right but insufficient.

## CHAIN MARKS
  L1 session/membership/identity ....... verified-by-execution
  L2 peer channel reaches connected .... verified-by-execution (20.277)
  L3 server knows peer's own endpoint .. verified-by-execution (p2-166, both machines)
  L4 server SENDS peer's own endpoint .. verified-by-execution for the admitted peer
      (p2-166 `result=echoed`); UNKNOWN for the peer that loses the race — contract (B)
  L5 client parses the card ............ verified-by-execution (20.282)
  L6 compose carries it to the slot .... verified-by-execution (20.283 R4 — it always did)
  L7 card lands on the GUARD'S field ... THE LINK THIS BOOT RESOLVES — contract (A)
  L8 reservation record reaches 4/5 .... verified-by-execution (p2-165 ladder)
  L9 W2 peer gate bit .................. assumed-still-clear
  L10 entity construction .............. unknown

## ADVERSARIAL PASS
ADVERSARIAL PASS: waived:the adversary this cycle was the wire test, which FAILED LOUD on
the re-pin because its bit offset had been hand-counted; the fix hoisted the index into
one shared constant and made the test derive its offset from it, so writer and oracle can
no longer drift. The re-pin itself is arithmetic on a measurement (0x142-0xEC=86), not a
guess, and both directions of being wrong are pre-named above.

## INSTRUMENTS
INSTRUMENTS: "result=begin chunks=3", "stage=slot_card", "stage=slot_dump fn=%s call=%llu slot=%u off=0x%llX hex=", "stage=peer_transport_identity result=%s present=%d "

LITERAL TARGETS:
    Game/bin/x64/steam_api64.dll: "result=begin chunks=3", "stage=slot_card", "stage=slot_dump fn=%s call=%llu slot=%u off=0x%llX hex="
    RE_output/s1_accept/sunrise-server.exe: "stage=peer_transport_identity result=%s present=%d "

## DEPLOYED
  server   d7a7dc9be138b412 — wire-test 0 failures, sweep-test 0 failures, sensor-auth
           PASS, local-account PASS. Listeners verified; ladder empty.
  clients  BOTH 0ff6911ff5a654ae — hash + 3 literals asserted IN each deployed file.
  gate     verify_hook_rvas PASS (93 RVAs, 0 bad).

## SETTINGS / HYGIENE
  server   membership_peer_transport_identity=true, roster_peer_participation=true,
           membership_peer_retry_cap=2 (unchanged — the wait cap is separate by design)
  clients  gate_poke=0 BOTH, milestone_trace=true
  BOTH CLIENTS MUST BE QUIT AND RELAUNCHED — they are holding the previous DLL.
  Server was restarted by the deploy (ladder read back empty = the reset outcome).

## PRE-NAMED OUTCOMES
  1. card at 0x142 + `slot_card` non-zero + sweep stops disowning => W1 FALLS. Next: W2.
  2. card at 0x142 + `slot_card` non-zero + sweep STILL disowns => the compare is not the
     only claim condition; read the claim path, do not boot again first.
  3. card at 0x198 => one line back, re-boot.
  4. card at 0xEC again => stop; the index model is wrong, rework from the decoder.
  5. rig card now `echoed` => contract (B) holds and the race fix works.
