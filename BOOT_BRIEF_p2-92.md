# BOOT BRIEF p2-92 (2026-08-28) - setup flags, precision shape: peer rows, self row clear

## PURPOSE
This boot tests p2(92): group-session membership snapshots publish member fields
11/12 = 1 on every row EXCEPT the recipient's own (p2(91)'s all-rows shape broke the
citizen join). The map (ms-start-gate3.md) proved fields 11/12 are the setup-complete
flags (client descriptor table 0x141ca68e0: the only 1-byte member fields, last two)
landing at member-record bytes +181/+183 (the gate's +0xED/+0xEF readers, base-corrected).
Win: the mac derives the rig (and host) as setup-complete, passes
'Waiting for managed-session-start for all peers', and the Tower RENDERS on the mac.

## GRAPHICS DELTA
No new rendered models. The win case = the mac's existing Tower view finally
presenting (slice-set 56, already precached in prior boots). L12: zero new models.

## FALSIFIABLE CLAIM
With fields 11/12 = 1 on all rows except the recipient's own, the mac's world
controller passes the managed-session-start gate and renders the shared Tower.
CONTENT NEGATIVE 1: mac's gate still times out -> the flags need the PEER-DELTA
tail carriers too (peer-entry dword @+0xD0 bit 10 - the fork's 3 absent tail flags
cannot express it today; next step is a peer-delta bitstream pass, named in
ms-start-gate3 OPEN items).
CONTENT NEGATIVE 2: the citizen join breaks again -> the self-row rule is wrong in
the other direction (the host row at members[0] echoes the recipient's identity and
may also need to stay clear); one-line refinement.
CONTENT NEGATIVE 3: the RIG's join breaks instead -> row-shape asymmetry between
recipients; invert per-recipient and re-test.

## ABSENCE NEGATIVE
- `stage=settings ... member_setup_flags=1` at bind MUST appear (it did: t=131 echo).
- Wire proof: bapdecode.py --pcap on this boot's capture must show message-30 member
  rows carrying fields 11/12 = 1 on non-self rows and 0 on the recipient's own row.
  If decoded bodies show 0 everywhere, the switch did not reach the composer -
  provenance failure, boot tested nothing.
- If neither client joins (no join_target lines), server liveness failure - void boot.

## CHAIN MARKS
- Fields 11/12 = the only 1-byte member fields, last two (descriptor 0x141ca68e0) -
  VERIFIED (ms-start-gate3).
- Record offsets +181/+183 = the gate's +0xED/+0xEF (base difference state+8 vs
  state+0x40) - verified-by-reading (ms-start-gate3).
- All-rows shape breaks the citizen join - verified-by-execution (p2(91) boot, 0
  failures after switch-off).
- Recipient's own row = members[recipient+1], found by NetAddr - verified-by-reading
  (snapshot_builder.cpp: members[0]=host, members[i+1]=peers[i]).
- flagA<->flagB order and host-row safety - assumed (flagged honestly in the lane;
  this boot measures both).
- Session-state hash tolerance - verified-by-execution empirically (prior addendum).

## ADVERSARIAL PASS
ADVERSARIAL PASS: waived - solo main-session boot prep, no second reviewer available
in-session. Judged by: the mac's screen (user observation) + the mac log's
managed-session-start passage + zero prune/destroy lines + the wire decode above.

## INSTRUMENTS
INSTRUMENTS: member_setup_flags, activity_member_setup_flags
Deployed exe byte-literals (provenance): both strings must exist in
RE_output/s1_accept/sunrise-server.exe (verified by the gate pre-boot).
Runtime liveness:
- `stage=settings ... member_setup_flags=1` at bind (already observed at t=131).
- bapdecode.py wire check: fields 11/12 = 1 on non-self rows in message-30 bodies.
- The claim line: mac log passes the gate; user sees the Tower on the mac.
