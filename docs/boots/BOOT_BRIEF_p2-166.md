# BOOT_BRIEF_p2-166 — THE PEER'S OWN ENDPOINT (W1 source fix + the first slot_dump run)

STATUS: live (2026-09-03). Supersedes nothing; p2-165's contract was never actually
re-run — see PROVENANCE CORRECTION.

## PROVENANCE CORRECTION (why this is not "p2-165 again")
The 2026-09-03 16:44 archive was read at first as a second boot. It is not: it is
p2-165's session, still running, snapshotted by the deploy script's auto-archive hook.
Proof — both archives carry the identical `slot_card=1078`, and the widened DLL's mtime
is 16:44:47, six seconds AFTER that archive was written. The widened build has never
been loaded by a game process, so `slot_dump`'s zero lines were an absent instrument,
not a failed one. `%02zX` was replayed on this exact toolchain
(x86_64-w64-mingw32-clang++, same Wine) and emits all three chunks correctly; the
shipped p2-165 DLL's disassembly carries three unrolled slot_dump LEA sites at
0x31805/0x318b7/0x31967, in the same function as slot_card at 0x31a0e. The instrument
was fine. The deploy-without-relaunch was the defect.

## PURPOSE
Win or lose, this boot learns WHERE THE PEER-IDENTITY CARD BREAKS, by separating two
causes that p2-165 could not separate because only one of them was observable:

  (a) SOURCE — the server was composing the wrong endpoint. `activity_membership_push`
      read the card from `descriptor::read(peerCitizen.descriptor)`, but that descriptor
      is the ACTIVITY-HOST endpoint for a region, not the peer's own transport endpoint.
      p2-165's server log shows `addr=3232235940` (192.168.1.164, the mac) on all six
      builds — including the body whose peer row named the RIG (key 0x846C8338F7D022E6).
      The mac was being told its peer lives at the mac's own address.
  (b) TRANSPORT — the entry->slot compose hop dropping a correct card (20.282's reading).

p2-165 could only ever have seen (b) because (a) guaranteed the card was wrong anyway.
This boot fixes (a) and makes (b) directly observable for the first time.

## GRAPHICS DELTA
ZERO new rendered models expected. No entity is expected to appear: W2 (peer gate bit
clear) and the predicate-2/3 rungs are untouched by this change. A rendered peer would
be an over-delivery and must be treated as a surprise to explain, not a success to bank.
MINIMIZATION: no client writes into game data this boot — `gate_poke=0` on BOTH clients,
and the gate_wwatch DR/VEH/suspend machinery is retired at COMPILE TIME
(`constexpr bool kWatchEnabled = false`), so LESSONS 19 / U18 does not apply. The only
client-side additions are read-only detour emits.

## FALSIFIABLE CLAIM
ONE contract: **the server now sends each client its PEER's own transport endpoint, and
the client's participant slot either receives those bytes or is shown dropping them.**

CONTENT NEGATIVE (the claim is refuted if):
  - `stage=peer_transport_identity` shows the SAME `card=` in both directions. The fix
    did not take; the member-key join is wrong and `net_addr_for_member` matched one row
    for both bodies.
  - `result=no_admitted_row` or `result=ambiguous_member_key`. The measured key
    (memberKey & 0xFFFFFF == machineId >> 40) does not hold for this boot's identities.
    That is a REFUTATION OF THE KEY, not of the endpoint thesis, and it is fail-closed:
    the card is published as absent rather than wrong.
  - `slot_card` still all-zero WITH a correct per-direction card. Then (a) is fixed and
    (b) is real: the compose hop is the wall, and `slot_dump` says at which offset the
    bytes stop.

## ABSENCE NEGATIVE (L13 — what zero lines MEAN, per instrument)
  - ZERO `stage=slot_dump result=begin` lines => the block did not run at all: either
    the client is on the old DLL again (check the deployed hash BEFORE reading anything
    else) or no slot's card fingerprint changed. NOT a statement about the 86 bytes.
  - `result=begin` PRESENT but zero `off=0x...hex=` lines => the block ran and the
    long-line emit path alone failed. Isolated to the emitter; the boot's other findings
    still stand. This split is the whole reason the short line exists.
  - ZERO `stage=peer_transport_identity` lines => no peer-bearing membership body went
    out. That is a PAIRING failure, and says nothing about the card or the compose hop.
  - ZERO `stage=pgate` lines => the participant table was never walked; the session did
    not reach the state under test. Re-run, do not interpret.

## CHAIN MARKS (L16 — every link, not just the one under test)
  L1 session/membership/identity ........ verified-by-execution (every boot since 20.44)
  L2 peer channel reaches `connected` ... verified-by-execution (20.277, t=330639)
  L3 server knows peer's own endpoint ... verified-by-execution (p2-165 `ev=gameplay
      stage=identity` logged addr=0xC0A801A4 and 0xC0A80188 — BOTH machines, distinct)
  L4 server SENDS peer's own endpoint ... THE LINK THIS BOOT RESOLVES (was: refuted —
      p2-165 sent the activity-host endpoint in both directions)
  L5 client parses the card ............. verified-by-execution (20.282: encode->send->
      decode, the ingress parser consumed it, no reject/freeze)
  L6 entry->slot compose carries it ..... unknown (never observed with a CORRECT card;
      this boot's first honest look)
  L7 W2 peer gate bit (bitreq 7 mac / 6 rig) ... assumed-still-clear (p2-165: value=0)
  L8 reservation record reaches 4/5 ..... verified-by-execution (p2-165 resv ladder: rig
      rec=1 at t=71031, mac rec=2 by t=624219 — the 20.277 3/4 stall is NOT universal)
  L9 entity construction ................ unknown (predicate 1 never satisfiable yet)

## ADVERSARIAL PASS
ADVERSARIAL PASS: waived:the adversary in this cycle was the artifact audit that killed
my own two prior claims — the `%zX` hypothesis (replayed and disproven on the real
toolchain) and the "p2-166 boot" premise (disproven by mtime + identical slot_card
count). The surviving server defect is source-verified in the code, not inferred from
logs alone, and its join key is measured on two machines independently.

## INSTRUMENTS
INSTRUMENTS: "result=begin chunks=3", "stage=slot_dump fn=%s call=%llu slot=%u off=0x%llX hex=", "stage=slot_card", "stage=peer_transport_identity result=%s present=%d "

LITERAL TARGETS:
    Game/bin/x64/steam_api64.dll: "result=begin chunks=3", "stage=slot_dump fn=%s call=%llu slot=%u off=0x%llX hex=", "stage=slot_card"
    RE_output/s1_accept/sunrise-server.exe: "stage=peer_transport_identity result=%s present=%d "

## DEPLOYED (asserted by the tooling, not remembered)
  server   a6665bb1ef1514a0  — gates: wire-test 0 failures (incl. both
           peer_transport_identity cases), sweep-test 0 failures, sensor-auth PASS,
           local-account PASS. Listeners verified; ladder empty (fresh claim table).
  clients  BOTH 51a61752c4d00988 — hash + 3 literals asserted IN each deployed file.
           Rig backup steam_api64.dll.bak_p2d7_20260903_172938; mac
           .bak_p2d7_20260903_172907.
  gate     verify_hook_rvas.py PASS (93 RVAs, 0 bad, 10 known not-code).

## SETTINGS / HYGIENE
  server   membership_peer_transport_identity=true, roster_peer_participation=true,
           membership_peer_same_region_advert=true, membership_peer_retry_cap=2
  clients  gate_poke=0 BOTH (verified on disk, both machines), milestone_trace=true,
           notifier_hook=false (mac)
  RELAUNCH BOTH CLIENTS. p2-165's cycle was spent because a staged DLL was never loaded.
  Server was restarted by the deploy, which is the reset_lobby_claims outcome (ladder
  read back empty) — no separate reset needed for THIS run, required before the next.

## PRE-NAMED OUTCOMES (read top-down; each names its next action)
  1. cards DIFFER per direction + `slot_card` non-zero
     -> W1 FALLS. Next: W2 (the peer gate bit) with the record already at 4/5.
  2. cards DIFFER per direction + `slot_card` still zero + `slot_dump` shows the bytes
     at some other offset -> the guard reads the wrong field; re-pin from slot_dump.
  3. cards DIFFER + `slot_card` zero + `slot_dump` shows the bytes NOWHERE in 0x300
     -> the compose hop drops them outright. Read the entry->slot writer statically;
     do NOT spend another boot first.
  4. cards SAME in both directions -> the member-key join failed. Re-derive it from
     this boot's `ev=gameplay stage=identity` + `stage=membership_peer` pairs.
  5. `result=no_admitted_row` -> the activity body outran the gameplay admission; the
     card needs to be published on a later trigger, not sourced differently.
