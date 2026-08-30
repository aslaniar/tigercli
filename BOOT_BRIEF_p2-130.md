# BOOT BRIEF p2(130) - THE CHECKSUM HUNT: CAPTURE THE CLIENT'S REPLICA

STATUS: live (2026-08-30). Reads with RE_output/claims/state-diff (this boot's target),
l9-profile-layout.md ADDENDUM, and tonight's findings: the black screen at peer arrival
= membership checksum rejection escalating to force-disconnect on the Tower region-56
citizen-join session.

## WHY THIS BOOT

2026-08-30 named the black-screen mechanism: the client rejects our membership bodies -
"session membership checksum failed, <client_hash> != <our_hash>" - chronically every
boot, escalating to "no membership information, forcing disconnect" when membership
churns at peer arrival. The addendum's 8-byte player-table shift (p2(129) fix,
session_state_client_base) shipped and fired - and the hash STILL disagreed live:
client 0x00B5AD1E vs ours 0x4E3DA953 on the same body (rev 921). The shift was real
but insufficient: the client's 28,768-byte replica differs from our freshly-built
state in CONTENT we have never seen.

This boot captures those bytes.

## THE INSTRUMENT (state_diff, one detour, read-only)

The checksum verifier 0x141772100 (fn 0x141772100..0x1417722F8, .pdata START - the
gate caught a dropped digit in my first RVA, 0x1722100, exactly the p2(112) class):
- rcx = a session-state holder;
- it copies [rcx+8 .. +0x7060) - 0x7060 = 28768 = kSessionStateSize EXACTLY - to a
  scratch at [rcx+0x7068];
- hashes the copy with lookup3, initial 0xDEAE2F4E (immediate at offset 0x76).
So holder+8 IS the client's replica at compare time.

Per call the hook logs our own lookup3 over the captured bytes + holder + the
original's return. The first two calls dump the replica in full (113 lines of 0x100 B).

## PURPOSE - what this boot learns, win or lose

One question: WHAT BYTES DOES THE CLIENT'S REPLICA HOLD THAT OUR STATE DOES NOT?
Desk-side after the boot: take a capture whose logged hash equals a "checksum failed"
line's FIRST value (validates the capture), take the body whose sent hash equals that
line's SECOND value (from the server's own log), rebuild our state for it, and
byte-diff. Every differing region is then named, and the hash fix becomes exact.

## GRAPHICS DELTA

ZERO new rendered models. One read-only detour, pass-through, capped, SEH-guarded.
Client settings unchanged except the new arm flag. Server UNCHANGED from the
p2(129)-fix deploy (35ae2802, client_base=1 armed).

## FALSIFIABLE CLAIM

CLAIM: a captured replica's logged hash equals a "checksum failed" line's computed
value, and the byte-diff against our state for the same body shows differences
confined to identifiable regions (candidate: bytes the client persists from earlier
updates or default-fills, which our clean rebuild lacks).

CONTENT NEGATIVE: every captured hash matches our own state hash for its body
(no disagreement captured). Then the replica content agrees at compare time and the
rejection lives in WHICH state gets hashed (e.g. the compare hashes a different
buffer than holder+8) - the diff moves to the call site, not the bytes.

SECOND: captures are all unreadable (`result=unreadable`). Then holder+8 is not the
replica at hook time (the copy source is computed later) - the dump moves to the
return side of the call.

## ABSENCE NEGATIVE (L13)

- Zero `ev=sdiff` lines: the DLL did not load or the flag is off - both asserted by
  the deploy gate literals (`stage=verify`, `ev=sdiff`) and the settings diff.
- `stage=install result=skipped why=disarmed`: settings fault, fix per trap 18.
- Install ok but zero `stage=verify` lines after a full paired session: the verifier
  never ran, meaning the checksum path we saw failing takes a different function -
  itself a finding; the failure lines in the same log then name the real site via
  their own existence.
- `result=unreadable` on every call: holder+8 wrong at entry - see SECOND above.
- Dump lines present but NO matching hash pair in the log: the capture is valid but
  no failure occurred while dumping - rerun with the dump cap spent later (the hook
  caps dumps at the first two calls by design; a rebuild moves the cap if needed).

LIVENESS: `ev=sdiff stage=install result=ok fn=0x1772100 replica=holder+8 bytes=28768
init=0xDEAE2F4E` on BOTH machines, then `ev=sdiff stage=verify` lines.

## CHAIN MARKS (L16)

| Link | Mark |
|---|---|
| Client rejects our membership bodies on state checksum | VERIFIED-BY-EXECUTION (2026-08-30, log lines + server hash pairing) |
| Rejections escalate to force-disconnect at peer arrival | VERIFIED-BY-EXECUTION (2026-08-30: "no membership information, forcing disconnect" -> citizen-join session dies -> black) |
| The +8 table shift is necessary but insufficient | VERIFIED-BY-EXECUTION (client_base=1 live; hash still disagreed on rev 921) |
| 0x141772100 copies holder+8 (28768 B) and hashes with 0xDEAE2F4E | VERIFIED-BY-DISASSEMBLY (this session, instruction-cited) |
| The client's replica bytes at compare time | UNKNOWN - THIS BOOT |
| The exact content delta | UNKNOWN - desk-side after this boot |
| Solo landing regression | CLOSED: stale server state; reset between runs (2026-08-30) |

## INSTRUMENTS

INSTRUMENTS:
  stage=verify
  stage=dump
  ev=sdiff

## LITERAL TARGETS

LITERAL TARGETS:
  Game/bin/x64/steam_api64.dll: stage=verify, ev=sdiff

## ADVERSARIAL PASS

ADVERSARIAL PASS: waived: one read-only detour on a .pdata-verified function start
(the gate additionally caught and corrected a dropped-digit RVA in this hook before
deploy - the p2(112) class), reads SEH-guarded, dumps capped at 2 full + 32 hash
lines, no server change (server stays at the p2(129)-fix build with client_base=1).

## RUN SHAPE

Solo-control first: server freshly restarted (reset rule honored this time), rig
client to orbit FIRST, mac second (the 2026-08-30 solo-loop reading). Then rig joins
the Tower to reproduce the peer-arrival churn. The hook fires on every checksum
verify - the first dumps land in orbit, before any Tower load.
