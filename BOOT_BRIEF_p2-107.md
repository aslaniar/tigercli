# BOOT BRIEF p2-107 (2026-08-29) - NAME THE DIALER: who sends the INTRO REQs against
# the identity-string endpoints?

STATUS: live (2026-08-29 ~12:0x). MAC ONLY behaviour change (admission_inject=true,
same inject shape as p2(103)-(106)); rig is the control. Server unchanged p2(96).
New client build 205c930b07333763 (fork p2(107)): three caller-capture targets added
to the retail funnel - the ONLY code change.

## PURPOSE
20.168 caught the wedge mechanism: ~3 s before setup:orbit wedges, the client runs
bdNATTravClient and dials SIX INTRO REQs whose "addresses" are ASCII windows (stride
exactly 6, sockaddr-shaped) over the injected peer identity string. The endpoint array
is garbage because the adopted record feeds a connection path that needs the peer's
REAL transport endpoint. This boot names the code: the funnel's caller capture reports
the module-relative RVA of every line that carries a target substring, and the three
bdNAT lines come from DIFFERENT call sites (bdNATTravClient.cpp 461/464/812), so one
boot yields three RVAs bracketing the dial.

WIN: `ev=retail stage=caller` lines for "sent INTRO REQ" (the dialer), "Public Addr",
and "Request timed out" (the retry loop). The INTRO sender's RVA then feeds the static
half - disassemble the owner, name the endpoint-array argument, field_xref the array
base to find who WRITES it. That writer is where a real peer's endpoint bytes come
from, and it is the fix point.

NOTE ON THE STAGED DESIGN: the endpoint-array dump at the dial site needs a hook on the
named function, so it is the NEXT boot after this one (the RVA is this boot's
deliverable). Static analysis between the two boots may make the dump unnecessary: if
the array's base displacement is visible in the dialer's disassembly, field_xref alone
names the writer.

## GRAPHICS DELTA
Zero new rendered models. The inject shape is byte-identical to p2(103)-(106); the only
new code is three target strings in an existing log observer. Expected mac outcome: the
known black screen at setup:orbit.

## FALSIFIABLE CLAIM
With admission_inject=true on the mac and the wedge reproduced, the mac log contains
`ev=retail stage=caller target=sent INTRO REQ rva=0x...` (plus the two companion bdNAT
targets) BEFORE the setup:orbit entry - naming the dialer's code address.

CONTENT NEGATIVE 1: the ev=retail capture shows the INTRO lines (site=95) but NO
stage=caller line for them -> the funnel target match failed (ordering, or the line
is emitted through a different funnel path). Instrument failure - do not conclude
anything about the dialer; debug the observer, not the game.
CONTENT NEGATIVE 2: caller lines appear with rva=0 or base=0 -> module resolution
failed for that caller; the abs= field still names the absolute address, and the base
is derivable from any other resolved line on the same machine.
CONTENT NEGATIVE 3: no INTRO lines at all this boot (the dial never ran) -> the wedge
took a different path this time; compare the log tail against p2(106)'s archived log
before concluding anything.

## ABSENCE NEGATIVE
- Zero stage=caller lines for ALL targets (including the long-standing "Adding
  player") => the funnel observer itself did not attach - an install-level failure,
  not a target failure.
- No inject line => the record never existed and the wedge path never started; the
  boot only proves the funnel runs.

## CHAIN MARKS
- The wedge is the bdNAT INTRO dial against identity-string endpoints, ~3 s before
  setup:orbit - verified-by-log (20.168, byte-exact stride-6 windows decoded).
- The funnel's return address IS the emitting game function - verified-by-execution
  (LESSONS 18c; it resolved the roster caller and six transition RVAs in p2(94)).
- The three bdNAT lines pass through the same funnel - verified-by-log (p2(106):
  they appear as ev=retail site=95 lines).
- The dialer RVA leads to the endpoint array's writer - UNKNOWN (the static half
  after this boot).
- The four p2(106) record-reader probes are bounded: they prove non-execution ONLY
  within the pre-wedge window (user's observation, recorded in 20.106 prep); consumers
  downstream of the wedge are unobservable in a wedged boot. This does not affect the
  bdNAT lane - the dial sits inside the window.
- Solo-control rule: the inject half is byte-identical to p2(105)/(106); the only new
  code is three target strings in a log observer that has shipped in every recent
  boot. Solo control waived on that basis.

## ADVERSARIAL PASS: waived - solo main-session prep (B-checkpoint exception). Residual
risk is nil beyond the standing inject risk already accepted five times: the new code
reads no game memory, writes no game memory, and only adds three strstr patterns to an
existing per-line loop.

## SWITCH POSITIONS FOR THIS BOOT
  MAC  admission_inject TRUE (params retained), admission_census TRUE
  RIG  admission_inject FALSE (control; no admission keys)
  Server unchanged p2(96) b9b0f3823f74d1bf; claims reset before boot.

## INSTRUMENTS:
  "sent INTRO REQ"
  "Public Addr"
  "Request timed out"
  "ev=admission stage=reader"
  "ev=admission stage=inject"

## LITERAL TARGETS:
  Game/bin/x64/steam_api64.dll: sent INTRO REQ, Public Addr, Request timed out, ev=admission stage=inject, ev=admission stage=reader

## ROLLBACK
Flip mac admission_inject to false - no rebuild. Prior DLLs on disk as
steam_api64.dll.bak_p2d7_* on both machines. Server unchanged; DO NOT BOOT p2(71).
