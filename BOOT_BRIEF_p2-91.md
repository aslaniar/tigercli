# BOOT BRIEF p2-91 (2026-08-28) - member setup flags: does the mac's world instantiate?

## PURPOSE
This boot tests p2(91): group-session membership snapshots now publish member fields
11/12 = 1 (behind activity_member_setup_flags), which the client's managed-session
member record reads at +0xED/+0xEF - the inputs of the per-peer activity-setup-complete
derivation (FINDINGS 20.150/20.151, ms-start-gate2.md). Win: the mac's world controller
passes 'Waiting for managed-session-start for all peers' and the Tower renders on BOTH
clients in the SHARED instance. Lose: the gate still times out on the mac and the
carrier is one of the still-zero fields (peer-entry dword @+0xD0 bit 10, or fields 8/9).

## GRAPHICS DELTA
No new rendered models expected. The WIN case renders the standard Tower on the mac
(it currently black-screens) - same slice-set 56, no new content. L12: zero new models.

## FALSIFIABLE CLAIM
With member fields 11/12 = 1 on every composed snapshot row, the mac's client derives
the rig (and the host) as setup-complete, passes the managed-session-start gate, and
renders the shared Tower (mac screen recovers from black; both clients standing in
instance 50B9AD15-shaped group target).
CONTENT NEGATIVE 1: the mac's gate still times out with flags published -> fields 11/12
are not the +0xED/+0xEF carriers; next lever is peer-entry dword @+0xD0 bit 10 (the
lane's other named input), then fields 8/9.
CONTENT NEGATIVE 2: a client PRUNES members or destroys players after the change ->
the flags are consumed somewhere harmful; switch off (rollback below), reinterpret.
CONTENT NEGATIVE 3: own-session establishment breaks (MEM stuck low on either client) ->
the flags on the client's OWN row are the problem; refine to peer-rows-only.

## ABSENCE NEGATIVE
- `ev=gameplay stage=settings ... member_setup_flags=1` MUST appear at server bind.
  Zero such line = the switch did not parse; the boot tests the old behavior (U9).
- The composed snapshots' flags are wire-verifiable: capture_bap30975.sh + bapdecode.py
  (--pcap) on the boot window MUST show member fields 11/12 present with value 1 in
  message-30 bodies. Bodies decoded with fields 11/12 = 0 mean the switch did not reach
  the composer - provenance failure, boot tested nothing.
- If NO session_seed/session churn lines and NO client join happen (clients never
  connect), the boot is void - server liveness first.

## CHAIN MARKS
- Gate geometry (peer scan stride 288, state@+0, established=10) - VERIFIED
  (ms-start-gate.md, 0x140C17FCD).
- Setup-complete setter is client-local (0x1404F3870), derived from state ladder PLUS
  member-record flags @+0xED (reader 0x14177A080, stride 0xB8) / @+0xEF (0x14177A060)
  - VERIFIED (ms-start-gate2.md).
- The fork publishes fields 8/9/11/12 as 0 (fields 11/12 named FlagA/FlagB) - VERIFIED
  (session_messages.cpp pre-patch).
- Field 11/12 -> +0xED/+0xEF mapping - ASSUMED (the client's message-30 bit-reader is
  unmapped; this boot is the measurement).
- Session-state hash tolerance of extra member-flag bytes - VERIFIED non-blocking
  empirically (l9-profile-layout ADDENDUM; hash not a gate on exercised paths).

## ADVERSARIAL PASS
ADVERSARIAL PASS: waived - solo main-session boot prep, no second reviewer available
in-session. Judged by: mac's world render (user observation) + mac log
'managed-session-start' passage + absence of prune/destroy lines; not by error counts.

## INSTRUMENTS
INSTRUMENTS: member_setup_flags, activity_member_setup_flags
Deployed exe byte-literals (provenance): both strings above must exist in
RE_output/s1_accept/sunrise-server.exe.
Runtime liveness:
- `stage=settings ... member_setup_flags=1` at bind (must appear).
- Wire verification: bapdecode.py on the boot capture shows member fields 11/12 = 1.
- The claim line: mac's world_controller passes the gate (log) + user sees the Tower.
