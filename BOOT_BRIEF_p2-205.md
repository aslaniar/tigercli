# BOOT BRIEF p2-205 - THE VERIFIED-CORRECT TYPE-51 ECHO (v3: SVC25-ECHO KEYING)

STATUS: prepared 2026-09-07 (post p2-204 v2 + the v3 keying iteration).
Server-only rebuild 8d881a0b580afe85 (all prior settings unchanged: bubble,
external body, allocation, assignment, worldpop ON; grant/type-9/view OFF).
Clients unchanged (be5807eca028ddea both machines). HOOK COUNT 0.

front: bubble-startup

## THE ITERATION THIS BOOT TESTS (v1 -> v2 -> v3)

- v1 (p2-203) account-slot keying: cross-attributed (2 wrong echoes, the
  confounder; fixture-reproduced).
- v2 (p2-204 v1/v2) memberKey + session keying: fail-closed always, but the
  session axis missed every first burst (measured universal: ads permanently
  stick to the FIRST session while each join spawns a fresh one) - and the v1
  cascade bug (fail-closed stars rolling back the WHOLE join burst) was found
  and fixed (the decouple), which LANDED the tower (p2-204 v2: both clients in
  city_tower_social_d2).
- v3 (THIS BUILD): the identity store is keyed by the SVC25 ECHO
  (session.identityEcho - the 8-byte session-token prefix each connection
  echoes at server hello). Measured per-client STABLE ACROSS RECONNECTS and
  per-machine DISJOINT in p2-204 (mac CF0A98397F164482 over conns 1/2/3, rig
  945602D41E66AC20 over conns 4/5/6). Fixture on the archived p2-204 log:
  **4/4 pushes HIT** under echo keying (vs v2's 1/2, v1's 0). A collision
  guard refuses a second digits-owner in one echo bucket (the p2-203-shaped
  token-sharing mode) - fail closed, never a wrong echo.

## PURPOSE (what this boot learns, win or lose)

SEND the type-51 bubble-startup echo with identity attribution that finally
matches the client's own, and MEASURE what the client does with a
validator-passing startup. Win: result=stored on every burst whose client
advertised, the boot-end dump check MATCHES the client's own DAT_1426BDCC8
row-2 window, and ANY new client line past the p2-204 census. Lose
(pre-named): stored + dump-verified + silence = the apply half (FUN_140B928D0)
is verified inert (lane #4's static verdict, confirmed by measurement) and row
8 goes architectural (the receive blocks are client-internal-only, VMP gate
[unmixed+0xCD5]).

## GRAPHICS DELTA

Zero new rendered models expected. Server-only. No client hooks.

## FALSIFIABLE CLAIM

1. Every join burst whose recipient session carries an svc25 echo and whose
   client advertised (capture echo= line) delivers type-51:
   `stage=bubble_startup push lookup_key=<echo> result=stored bytes=443
   echo=<0x56 hex>`. The captured form is the client's own advertised
   "steamid:<id>#<token>" + zero pad + version 0x06.
2. The boot-end dump check (RE_scripts/identity_dumpcheck.py) compares the
   echo=<hex> bytes against the client's identity row - MATCHES.
3. CONTENT NEGATIVES (each names its cause, none is silent): no_echo (svc25
   body too short - echo 0), no_identity (the client never advertised on any
   session with its echo), collision_REFUSED (two clients shared one echo
   token - the p2-203 shape, fail-closed by the guard).

## EFFECT CLAIM (distinct from delivery)

DELIVERY: the type-51 frame rides the proven svc9 path (p2-203 delivered 4x).
EFFECT (pre-named, not claimed): the client decodes (femu-proven W8), the
validator memcmps the echo against its OWN row (verified by the dump check),
and the apply half runs - lane #4: a ring-push/telemetry recorder that cannot
flip AF1/AF2/AF3 or [unmixed+0xCD5]. Downstream movement (entity lines,
receive-block construction) is the win, not the expectation.

## ABSENCE NEGATIVE (L13)

stored + dump MATCHES + zero new client lines => the apply half is verified
inert for our state; row 8 = the VMP job gate, client-internal-only; the
project's next question is architectural (which client state the fork can
trigger, or whether the receive blocks need a co-state we cannot reach).
stored + dump MISMATCH => a byte-level attribute bug (the diff offset is
logged by identity_dumpcheck - one iteration). no_identity on a client that
advertised => the echo-keyed store missed; the capture/push lines name the
echo and the fix is mechanical.

## CHAIN MARKS (L16)

- the type-51 wire form ................. verified-by-emu (W8: femu-validated, every validator window)
- the identity capture (descriptor steamid) verified-by-log (p2-204: 15 captures, both machines)
- the echo-keyed store (v3) ............. verified-by-replay (fixture: 4/4 hits on the archived p2-204 wire shape; p2-203's confounder still reproduced under OLD keying - the fixture's negative arm)
- the echo stability + disjointness ..... verified-by-log (p2-204: six svc25 lines; mac CF0A over conns 1/2/3, rig 9456 over conns 4/5/6)
- the burst-survival decouple ............ verified-by-execution (p2-204 v2: bubble no_identity + worldpop ok at the same t, twice per client)
- the readout tool ....................... verified-by-dump (identity_dumpcheck.py positive control on dump_p2146: MATCH at the lane-6g address 0x7FF7593BDD38)

## ADVERSARIAL PASS: self - four ways this boot could mislead me

1. COLLISION MODE: the p2-203 token-sharing shape (two clients, one echo) -
   the guard REFUSES the second owner (logged result=collision_REFUSED). A
   refused capture = some burst misses = named, never a wrong echo.
2. ECHO ZERO: a session whose svc25 body is short (echo never stamped) -
   its pushes log result=no_echo. All six svc25 lines of p2-204 had echoes;
   a new-client shape could differ.
3. THE DUMP TIMING (the p2-203 lesson): the mac client's full dump must be
   taken ~60-90s AFTER the pushes land (both clients in-world), NOT at
   session end. THE OPERATOR INSTRUCTION: dump when the server log shows
   result=stored lines.
4. THE ALLOCATION/WORLDPOP ARMS changed the burst bytes vs p2-203: the
   client-census diff is a LINE-SHAPE diff (logq shape census), not byte
   counts; server-side families are attributed by their own log lines.

## PRIOR ART (09-05 FAILURE 5 - q.sh each central term)

- q.sh "bubble_startup | type-51": type51-bubble-startup-spec.md W1-W8 (closed
  wire form), 20.328 R3/R4, 20.329, p2-204 v1/v2 records (this session's
  ledger: the matrix + the v3 keys).
- q.sh "identity capture | svc25": this session's measurement (the echo
  stability + disjointness, p2-204 v2; the collision history in p2-203).
- q.sh "receiver | job-gate": lane #4 claims 6f/6g (the VMP boundary
  [unmixed+0xCD5], the apply half = telemetry recorder, the row-2 layout).
- the fixture (identity_keying_20260907.py v3: PASS 4/4 on the p2-204 archive;
  the p2-203 negative reproduced) + identity_dumpcheck (positive control, PASS).

## DEAD-END AUDIT

- Account-slot keying (v1): cross-attributes - retired, fixture-negative kept.
- Digits/memberKey + session-id keying (v2): never cross-attributes but the
  session axis misses every first burst (the reconnect fact) - retired.
- A "formula" between steamid digits and wire memberKey: none exists (the
  p2-204 matrix); the echo is the measured durable key, not a derivation.
- view/type-9/grant arms: closed (20.326/20.327/20.324) - settings OFF.
- The relay/retarget/ladder family: closed (rows 5-7) - untouched.

## STATE READERS (a direct reader per asserted state)

- "the identity was captured under its echo" -> `ev=identity stage=capture result=stored echo=<hex> account=N digits=0x.. machine=0x..`.
- "two clients shared a token" -> `ev=identity stage=capture result=collision_REFUSED echo=<hex> ...`.
- "the push went out with the right identity" -> `stage=bubble_startup push ... lookup_key=<echo> result=stored bytes=443 echo=<hex>`.
- "the echo was byte-right" -> `python3 RE_scripts/identity_dumpcheck.py --log <archive server log> --dump <mac full dump>` -> MATCHES.
- "the client moved" -> ANY new client line past the p2-204 archive shape census.
- "the receiver opened" -> ent_recv instance census > 0 (the boot-end dump).

## WIDE NET (probes at every decision point)

All existing instruments (HOOK COUNT 0): the capture lines (echo/digits/
machine), the push lines (lookup_key/member_key/result/echo), the worldpop +
allocation + assignment lines (the other arms ride the same bursts), the
client census diff vs the p2-204 archive, boot_verdict's both-machine
comparison. No client hooks - the dump is the decisiveness.

## FIX SURFACE: server (the v3 rebuild)

1. Session.identityEcho (server/bap/internal.h): the 8-byte svc25 echo kept
   at server hello (plaintext.cpp stamp).
2. matchmaking_route.cpp capture: stores under the echo; the digits/machine
   stay logged (the matrix); the collision guard refuses a second digits
   owner per echo (fail closed).
3. activity_message_push: the type-51 push loads by the recipient session's
   echo; logs lookup_key (echo) + member_key (the wire matrix) + result + the
   sent echo bytes.
4. The arm decouple (p2-204 fix 2) stays: a fail-closed bubble never rolls
   back the burst.
NO SERVER-SIDE GAP: the wire items this boot sends ARE the handshakes under
test; the client renders peers on server input alone (THE CLIENT IS NEVER
MODIFIED).

## ABANDON OUTCOME (pre-named)

activity_bubble_startup=false: no type-51 anywhere; the burst returns to the
p2-204 v2 shape (worldpop/allocation/assignment unchanged). Everything else
is a settings flip with the .bak_p2-204_pre_full backup standing.

## NEGATIVE TEST (the arm that fails on the bad state, and where it RAN)

1. THE KEYING (v3): fixture PASS on the ARCHIVED p2-204 log - 4/4 pushes hit
   under echo keying, and the OLD slot keying still reproduces the p2-203
   confounder (2 wrongs) on the same data. The fixture is the negative test
   for this boot's fix, on pre-boot data.
2. THE COLLISION GUARD: the p2-203 shape (two clients, one echo) is the guard's
   subject - exercised in the fixture's OLD-keying negative (the same data
   would produce collision_REFUSED under v3, never a wrong echo).
3. THE READOUT TOOL: identity_dumpcheck.py positive control on dump_p2146
   (MATCH at the lane-6g address) - a wrong address or window fails this arm.
4. THE BOOT'S OWN NEGATIVE: no_identity/no_echo/collision arms all name their
   cause in the log (pre-named, none is a silent surprise).

## MODEL REVIEW (required: front history - 2 prior boots)

Front bubble-startup: p2-203 (hypothesis-wrong, confounded by slot keying),
p2-204 (hypothesis-wrong, the session-axis reconnect fact). BOTH failures
were INSTRUMENT/KEYING defects, not evidence about the client's apply - the
echo has never reached the wire for a correctly-attributed identity. Dead
assumptions named and killed this session: (a) "the account slot can
attribute a client" - refuted by measurement + fixture; (b) "ads and joins
share a session" - refuted (ads stick to the first session); (c) "a formula
exists between the namespaces" - refuted (the matrix). The v3 key (svc25
echo) is measured data: stable across reconnects, per-machine disjoint, and
guard-railed against its own failure mode. This boot's verdict decides the
front: stored+verified+silent => the apply is inert and the front closes by
measurement (row 8 goes architectural); any client movement => the startup
semantic is real and we chase it. No further type-51 iteration without a
model review after this boot.