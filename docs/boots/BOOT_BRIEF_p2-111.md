# BOOT BRIEF p2(111) - RAISE THE PEER RETRY CAP

STATUS: live (2026-08-29 ~13:4x). Author: Claude Code session.
Reads with FINDINGS 20.171 (the diagnosis) and 20.170 (the boot it builds on).
ONE VARIABLE. Settings only: `membership_peer_retry_cap` 2 -> 6 on the server.
NO REBUILD. No client change of any kind. Both clients stay on `7849e28a58d40539`,
disarmed, byte-identical, exactly as they booted p2(110).

## PURPOSE

p2(110) established the session layer is finished (both clients hold each other at real
endpoints, one instance, direct client<->client channel) and that the remaining gate is
that neither client ever instantiates the peer PLAYER. 20.171 traced that to a single
mechanism: the server publishes a peer row, spends its whole retry budget inside ~50 ms
of load-burst sends, and latches `peerWithdrawn` permanently before the client's
acknowledgement lands (observed +28, +37, +54 ms after each withdrawal).

This boot asks ONE question: does giving the client a larger retry budget let the peer
row survive to an acknowledgement?

WHAT IT DOES NOT TEST. It does not test whether the budget should be time-based rather
than body-counted (fix (b) in 20.171) - that is the next step only if this one is
directional but insufficient. It does not touch `activityJoinedForeignSession` (a real
but separate defect, 20.171 RESULT 1). It does not test the appearance blob, so even a
complete success does not produce a VISIBLE second guardian.

## GRAPHICS DELTA  (L12)

Unchanged from p2(110), and p2(110) settled the question empirically: NEITHER client
instantiated a peer player, so nothing peer-shaped was submitted to either renderer.
If this boot succeeds at the publish layer, each client may for the first time
instantiate a peer player - that is ONE new never-rendered model per machine, and it is
the co-presence render class parked at 20.110/20.111.
Minimisation already in place, unchanged: `hold_spawn: true` / `spawn_hold_ms: 30000` on
both clients; the appearance blob is not implemented, so a peer that does instantiate
resolves to a default body, the cheapest possible first co-presence render.
ACCEPTED RISK, restated from p2(110): a render death on co-presence remains possible and
is itself information. Rollback is a settings flip; nothing is compiled.

## FALSIFIABLE CLAIM  (L6)

CLAIM: with `membership_peer_retry_cap = 6`, at least one session's peer row survives to
an acknowledgement - i.e. a `membership_peer result=included` run is followed by
`membership_ack result=ok` for the SAME session WITHOUT an intervening
`result=withdrawn`, and `unackedPeerBodies` resets rather than latching.

PRE-NAMED CONTENT NEGATIVE 1 (the one that most changes the plan):
  If `result=withdrawn` still fires and now reports `unacked=6` on every session, the
  cap is NOT the gate. The budget is being spent by burst cadence regardless of its size,
  and the target becomes fix (b) - make the budget time-based - not a larger number.
  In that case do NOT raise the cap again; the third raise would be a fix guess (U7).

PRE-NAMED CONTENT NEGATIVE 2:
  If the peer row survives to an ack (claim confirmed) but NEITHER client logs
  `Adding player` for the other's xuid, then publication was never the gate either, and
  the target moves to the client-side consumer of the peer row - the msg-12 membership
  handler - with the p2(110)/p2(111) log pair as the A/B.

PRE-NAMED CONTENT NEGATIVE 3 (partial, and expected as a real possibility):
  20.171 recorded that session ...105 is a DIFFERENT case - a genuine 15 s ack gap, not a
  ~50 ms race. If some sessions survive and others still withdraw, that is a PARTIAL
  confirmation, not a failure: it separates the burst-race population from the
  ack-silence population and each then gets its own lane. Do not read a partial as a null.

## ABSENCE NEGATIVE  (L13)

If ZERO `ev=activity stage=membership_peer` lines appear at all: FIRST hypothesis is that
the measurement is invalid, not that the peer was never found.
  - Liveness: the same line fired 11 times in p2(110) on this exact server binary, which
    is UNCHANGED by this boot (settings-only). Its absence therefore indicts the boot
    (clients never co-located, claims not reset, one client never reached in_world),
    not the instrument.
  - Provenance of the change itself: `membership_peer_retry_cap` must read 6 in the
    DEPLOYED settings file AND the withdrawal line must report `unacked=6` if it fires.
    An `unacked=2` line in this boot means the server did not reload the setting -
    measurement invalid, restart it properly and re-run.
  - Capture liveness: en0 + lo0 tcpdump, probe-packet verified BEFORE launch. The mac's
    "received by filter" counter is BOGUS (20.166); only the probe proves an empty pcap.

## CHAIN MARKS  (L16)

  L1  both DLLs identical + disarmed              VERIFIED-BY-EXECUTION (p2(110), unchanged)
  L5  30976 is the SERVER                         VERIFIED-BY-EXECUTION (20.170 R0)
  L7  mac unarmed reaches in_world                VERIFIED-BY-EXECUTION (20.170)
  L8  both hold each other at real endpoints      VERIFIED-BY-EXECUTION (20.170 R1)
  L9  both in the SAME activity instance          VERIFIED-BY-EXECUTION (20.170 R3)
  L11 server FINDS the peer (`havePeer` true)     VERIFIED-BY-LOG (20.171 R2, 11 lines)
  L12 server PUBLISHES a peer row                 VERIFIED-BY-LOG (`result=included`, peer_row=1)
  L13 the row is withdrawn before an ack lands    VERIFIED-BY-LOG + VERIFIED-BY-READING (20.171 R2/R3)
  L14 the cap is what withdraws it                VERIFIED-BY-READING (the code path) ;
                                                  that RAISING it changes the outcome is
                                                  ASSUMED  <- THIS BOOT RESOLVES L14
  L15 client instantiates the peer player on
      receiving a surviving peer row              UNKNOWN  <- content negative 2 covers it
  L16 two guardians VISIBLY render                UNKNOWN - blocked behind L15 and behind
                                                  the appearance blob (never built)

No link is written as "one boot away". L14 is the only link this boot resolves.

## ADVERSARIAL PASS: waived: one variable, settings-only, no rebuild, no client change,
no memory writes, no wire/codec encode change, and fully reversible by editing one
integer back. This is the FIRST attempt at this specific question (the peer-row retry
budget), not a repeat - U7's trigger is not met. The change is also directional rather
than speculative: it moves a deployed value BACK to the tree's own documented default
(6), it does not invent one. Recorded as a waiver, not a pass.

## INSTRUMENTS: membership_peer, membership_ack, stage=roster

All three already exist in the deployed server `b9b0f3823f74d1bf` and all three fired in
p2(110). No instrument is added or changed by this boot, so there is no new literal to
verify - the liveness argument in ABSENCE NEGATIVE covers them.

## PRE-BOOT SEQUENCE (in order, one long-running action per step)

  1. Back up `RE_output/s1_accept/Sunrise/settings.json`, then set
     `server.membership_peer_retry_cap` from 2 to 6. Verify by re-reading the file.
  2. `bash RE_scripts/reset_lobby_claims.sh` - restarts the server (which RELOADS the
     settings) and clears the in-memory lobby-claim table. MANDATORY between any two
     runs. Verify 3/3 TCP listeners + UDP 30976 + `nat: ok` + `claims after: 0`.
     KNOWN BUG (20.167): its relaunch leg can silently fail; if listeners are 0/3 launch
     `mac-port/launch-server-macos.sh` directly with captured output.
  3. `route -n get 192.168.1.136` must report en0; `arp -a | grep 192.168.1.136` must NOT
     show a "permanent" self-referential entry (20.166(c) / 20.167).
  4. Clear all three log slates (server rotates on restart; move both client logs aside).
  5. Start captures on en0 AND lo0, 4-port filter, then the probe-packet liveness check.
  6. Launch RIG first. Wait for `activity:in_world` in its log.
  7. Launch MAC. Let both sit ~5 min in the Tower.
  8. Collect: both client logs, server log, both pcaps, into
     RE_output/captures/p2-111_retry_cap/.
