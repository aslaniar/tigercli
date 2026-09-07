# BOOT BRIEF p2-202 - THE DUTY-CYCLED DESIGNATION: type 9 on every keepalive

STATUS: prepared 2026-09-07 (post p2-201 clean null). Front:
**activity-host-designation** (streak 1). Server-only: the p2-201 type-9 push
re-armed onto the keepalive cadence (the brief's own pre-named retry variant).

## PURPOSE (what this boot learns, win or lose)

p2-201 delivered 4 type-9 pushes with correct bodies and produced ZERO new
client lines. The pre-named timing suspect: the burst fires at the first
publish, long before the client's activity-session machinery finishes (the mac
was still in initial_slice_set_loading), and the client's session lookup
degrades to a silent no-op. This boot carries the designation on EVERY
keepalive frame (5s cadence), so it stays on the wire until the client's
session record exists. Win: ANY new client line past the p2-201 baseline.
Lose (pre-named): silence closes the designation arm entirely and the next
lever is the type-51 'V'-magic handshake or a non-empty type-54 table.

## GRAPHICS DELTA

Zero new rendered models expected. Server-only; clients stay
be5807eca028ddea. No client hooks (HOOK COUNT 0).

## FALSIFIABLE CLAIM

With activity_start_host_push=true, every keepalive-due frame (per live
activity session, 5s cadence) carries one type-9 notification with the same
13-byte body ([01][session id LE][04 00 00 00]). The server logs
`stage=start_host push session=... bytes=13` per keepalive, so the send count
rises from p2-201's 4 to dozens per client. CONTENT NEGATIVE: p2-201's corpus
(the 4 burst pushes) is the "burst only" arm; this boot's delta is the count.

## EFFECT CLAIM (distinct from delivery)

DELIVERY: dozens of type-9 pushes per client per boot instead of 4. EFFECT
(pre-named, not claimed): once the client's session record exists, one of the
re-sends hits the live window and the host state-machine step runs; any
downstream movement is the win. A clean null CLOSES the designation arm
(streak 2 -> model review before any further boot on this front).

## ABSENCE NEGATIVE (L13)

Silence after dozens of well-timed re-sends cannot be a timing miss: the
designation message itself is then inert for this client state (the session
id may be the wrong identity for the client's session table, or the state
machine requires a predecessor state the fork never published). The follow-up
lane must then decode the client's session-record identity (DAT_14280E210
unmix, 0x140E36C30) rather than re-timing.

## CHAIN MARKS (L16)

- burst-time delivery + body layout ......................................... verified-by-log (p2-201: 4 pushes, no crash, no new lines)
- the re-send rides the keepalive frame (same nonce chain, same key) ......... verified-by-reading (the keepalive branch's existing append chain)
- edge-guarded client-side .................................................. verified-by-disasm (the apply is a state-machine step; unknown session = null no-op)
- keepalive cadence 5s ...................................................... verified-by-reading (kKeepaliveIntervalMs; the 20.5s teardown margin)

## ADVERSARIAL PASS: self - three ways this boot could mislead me

1. A repeated type-9 on an ALREADY-hosting session might not be a clean no-op
   (state-machine re-entry). The client's own edge guards are the protection;
   if a client misbehaves, the readout must distinguish that from the
   designation effect. The gate flips OFF for a byte-identical revert.
2. The session id could be the wrong identity entirely (the client's session
   table may key on a different id - DAT_14280E210's unmix input). Silence
   then means "wrong key", and ABSENCE NEGATIVE routes to that decode.
3. The keepalive frames now carry one more notification per frame; if the
   frame size pushes some client buffer edge, the whole keepalive could drop -
   the keepalive itself is the canary (a teardown/reconnect storm would show).

## PRIOR ART (09-05 FAILURE 5)

- p2-201 (this front, streak 1): delivered, null, timing suspect named.
- q.sh "start_activity_host": apply-table row 2 + the p2-201 record. Verdict:
  no boot has carried the duty-cycled variant; this is the first.

## DEAD-END AUDIT

- The view road (20.326): not re-armed.
- The burst-time-only variant: superseded by this boot, not reverted-to
  (the gate covers both: the re-send REPLACES nothing - the burst push and
  the keepalive re-send are the same helper; this boot turns the cadence on).
- The type-51 handshake and the non-empty type-54: next levers, not this boot.

## STATE READERS (a direct reader per asserted state)

- "we re-send" -> `stage=start_host push` count >> 4 in the server log.
- "the client ran the step" -> ANY new client line past p2-201 (the census
  diff is the reader; p2-201's corpus is the baseline archive).
- "the keepalive survived" -> no reconnect/teardown storm (the 20.5s margin).

## WIDE NET (probes at every decision point on the suspect chain)

All existing instruments (HOOK COUNT 0):
- server TX: the per-keepalive `stage=start_host push` lines (count + cadence).
- the frame: the keepalive's own delivery is the canary (a dropped or
  oversize frame shows as a teardown/reconnect storm against the 20.5s margin).
- client RX: the census diff vs the p2-201 archive (all 116 line shapes
  compared mechanically), the ent/mgr/pool instruments, the retail-site lines.
- boot_verdict both-machine comparison vs the p2-201 archive.

## FIX SURFACE: server

Server only: the keepalive-branch call site (the helper already existed).
Client untouched. No SERVER-SIDE GAP section.

## ABANDON OUTCOME (pre-named)

activity_start_host_push=false: no type-9 anywhere (burst or keepalive);
byte-identical to the p2-200 burst shape.

## NEGATIVE TEST (the arm that fails on the bad state, and where it RAN)

1. THE HELPER: ran in boot p2-201 (4 delivered pushes, correct bodies, no
   client-side error).
2. THE FRAME CHAIN: ran in every boot (the keepalive global-state push is the
   same append/publish chain; p2-201's burst used the identical helper).
3. THE CADENCE: the keepalive itself is the negative control - if the frames
   dropped, the client's 20.5s teardown would fire (absent = delivered).

## MODEL REVIEW (required: streak 1 on this front)

Streak 1 (p2-201 null). THIS BOOT IS THE BRIEF'S OWN PRE-NAMED RETRY VARIANT
(adversarial pass item 1 of p2-201: "the FIRST retry variant is sending type 9
again later (on the roster/keepalive cycle), before concluding the
designation is wrong"). The dead assumption under review: "the session id the
fork knows is the identity the client's session table holds" - if this boot
nulls too, that assumption is the next one to attack (ABSENCE NEGATIVE
routes to the DAT_14280E210 unmix decode), and no further designation-arm
boot is allowed without a model review of it.
