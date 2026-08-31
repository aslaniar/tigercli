# BOOT BRIEF p2-108 (2026-08-29) - FIND THE ENDPOINT ARRAY: what does the bdNAT dialer
# actually hold, and where did the identity string get into it?

STATUS: live (2026-08-29 ~12:2x). MAC ONLY behaviour change (admission_inject=true,
same inject shape as p2(103)-(107)); rig is the control. Server unchanged p2(96).
New client build 013d44aca4630c92 (fork p2(108)): ONE new log-only pass-through probe
(nat_probe) on the bdNAT logging shim 0x9E3230.

## PURPOSE
20.168 caught the wedge: at setup:orbit the client runs Demonware NAT traversal and
dials SIX INTRO REQs whose "addresses" are ASCII windows (stride exactly 6) over the
injected peer identity string - an endpoint ARRAY full of identity-string bytes.
p2(107) named the logging shim all bdNAT lines emit through (0x9E3230) and showed the
dialing logic is in its indirect callers, unreachable statically (zero direct xrefs -
obfuscated dispatch).

This boot dumps the dial site's arguments at the shim entry:
```
  rcx - the bdNAT client/transport object (the candidate-array pointer likely lives
        inside it; a 0x80-byte SEH-guarded dump)
  r8  - unknown third argument (dumped)
  r9  - the endpoint payload the shim formats as the dial target (dumped)
```
If the identity-string bytes appear inside one of the dumps, the array is FOUND: its
container and field offset are visible in the hex, and field_xref on that offset then
names who WRITES it - which is where a real peer's endpoint bytes would come from, the
fix point. If the string does not appear inline, the dumped pointers still name the
objects to chase next.

WIN: an `ev=nat stage=dump` hexdump whose bytes contain a recognizable window of
"steamid:...#..." - giving the array's address, container and stride.

## GRAPHICS DELTA
Zero new rendered models. Inject shape byte-identical to p2(103)-(107). The only new
code is one log-only pass-through that fires at NAT-retry cadence (not per-frame),
capped at 8 dumps. Expected mac outcome: the known black screen at setup:orbit.

## FALSIFIABLE CLAIM
With admission_inject=true on the mac, the mac log contains `ev=nat stage=dial` lines
followed by `ev=nat stage=dump` hexdumps BEFORE the setup:orbit entry, and at least one
dump's hex contains identity-string bytes ("737465616D6964..." onward) at some offset.

CONTENT NEGATIVE 1: dial lines appear but NO dump contains identity-string bytes ->
the array is not among rcx/r8/r9 targets; the dumps still name the objects, and the
next step is dumping one level deeper (the pointers INSIDE the dumped object), not
more guessing.
CONTENT NEGATIVE 2: no ev=nat lines at all AND no bdNAT retail lines -> the dial never
ran this boot (different wedge path); compare against the p2(106)/p2(107) archived logs
before concluding anything.
CONTENT NEGATIVE 3: no ev=nat lines but bdNAT retail lines DO appear -> the probe did
not attach (check for ev=nat stage=install result=fail); instrument failure, not a
system fact.

## ABSENCE NEGATIVE
- No `ev=nat stage=install result=ok` line => the probe did not install; the boot
  tests nothing on this lane.
- No inject line => the record never existed; the dial may still run for the real
  channel, so nat lines alone prove the probe works but not the wedge path.

## CHAIN MARKS
- The wedge is the bdNAT INTRO dial against identity-string endpoints - verified-by-log
  (20.168, byte-exact stride-6 windows).
- All bdNAT log lines emit through shim 0x1409E3230 - verified-by-execution (p2(107)
  caller capture, three targets, one RVA).
- The shim reads only its own stack args (deepest slot 6) and its cookie - verified-
  by-reading (full linear disassembly this session); the 16-slot bit-exact forward
  covers every caller on record.
- The shim is reached by indirect dispatch - verified-by-reading (zero direct E8/rip
  xrefs into it; xref_scan this session).
- The endpoint array is reachable from the shim's arguments - UNKNOWN (this boot).
- Who writes the identity string into endpoint-shaped bytes - UNKNOWN (the field_xref
  half AFTER this boot names it).
- The p2(106) reader probes are bounded to the pre-wedge window (recorded); the bdNAT
  dial sits INSIDE that window, so this lane is not affected by the wedge.

## ADVERSARIAL PASS: waived - solo main-session prep (B-checkpoint exception). Residual
risk: one more detour on an ABI-verified function (16-slot forward, pre-attach caller-
frame check done), SEH-guarded dumps of three borrowed pointers, log-only, capped at 8.
The p2(99) dereference rule is respected: every dump is guarded, no argument is assumed
to be a pointer of any particular shape.

## SWITCH POSITIONS FOR THIS BOOT
  MAC  admission_inject TRUE (params retained), admission_census TRUE
  RIG  admission_inject FALSE (control; no admission keys)
  Server unchanged p2(96) b9b0f3823f74d1bf; claims reset before boot.

## INSTRUMENTS:
  "ev=nat stage=dial"
  "ev=nat stage=dump"
  "ev=nat stage=install"
  "ev=admission stage=inject"

## LITERAL TARGETS:
  Game/bin/x64/steam_api64.dll: ev=nat stage=dial, ev=nat stage=dump, ev=nat stage=install, ev=admission stage=inject

## ROLLBACK
Flip mac admission_inject to false - no rebuild. Prior DLLs on disk as
steam_api64.dll.bak_p2d7_* on both machines. Server unchanged; DO NOT BOOT p2(71).

## ADDENDUM (2026-08-29 ~12:3x) - INSTRUMENT CORRECTION, BOOT p2(109)
The first p2(108) run burned the 8-call dump cap on TYPE-0 shim calls - suppressed
bdNAT startup messages (UPnP/bdNet init, dispatch jumps straight to the epilogue,
nothing logged) at t=16-17k - so the INTRO dial at t=76837 (121 lines, wedge
reproduced, hitch asserts in setup:orbit) went undumped. Correction in fork p2(109)
`7849e28a58d40539`: dump only calls whose type selector rdx is 1..3 (the three arms
that actually log, disassembly-verified), cap raised to 16. Mac deployed and armed;
the rig stays on 013d44aca4630c92 as control (unarmed; the probe is mac-relevant
only) - realign the rig at the next natural close. The falsifiable claim, negatives,
and everything else in this brief stand unchanged.
