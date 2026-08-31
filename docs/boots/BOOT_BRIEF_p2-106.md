# BOOT BRIEF p2-106 (2026-08-29) - WHO READS THE FORGED RECORD BEFORE THE WEDGE?

STATUS: live (2026-08-29 ~11:4x). Behaviour change, MAC ONLY (admission_inject=true,
same inject shape as p2(103)-(105) plus FOUR NEW LOG-ONLY reader probes); rig is the
control. Server unchanged p2(96). New client build 7df1d0e9aff01861 (fork p2(106)).

## PURPOSE
20.167 settled that the wait at setup:orbit is CLIENT-INTERNAL: the client believes it
has a peer (slot + record + roster naming, 4 reproductions) and neither talks nor
waits on the wire. The only record reader we know is the one that LOGS (adoption).
The static field census (field_xref on +0x3b78/+0x3c00/+0x3c30, pdata_bounds-resolved)
names FOUR more functions whose code touches the record fields. This boot asks which
of them RUNS for the forged record between the roster naming and the wedge - and what
the last record-directed activity before setup:orbit is.

WIN: one or more of the four probes logs rec=1 (a pointer arg inside record 1's span)
between the inject line and setup:orbit. The LAST such line before the wedge names the
consumer to read in full - and the fix follows the named reader, not another guess.

THE FOUR PROBES (all log-only, 4 regs + 16 stack slots forwarded bit-exact):
```
  0x1777EC0  ADMIT itself: four bit tests on the flags word (+0x3c30)
  0x1771060  353B predicate: membership byte (+0x3b78) == 0 gate
  0x178FE00  2409B: reads the flags word (+0x3c30) as a word
  0x17A0B60  3927B: reads BOTH the flags word and the membership byte
```
Pre-attach verification (LESSONS 18 cor 2): none reads its caller's frame beyond the
arg area, and the deepest ABI (0x178FE00) consumes 13 stack slots - inside the 16
forwarded. Hit classification is POINTER-BASED: each probe compares rcx/rdx/r8/r9
against the record spans (arena + i*0x1a8 + 0x3b78 .. +0xF8, i in 0..7); the inject
line now carries the exact rec1 pointer. rec=0 lines are SELF's record (noise, still
logged for the A/B); rec=1 lines are the signal. Caps: 48 hits per fn, first 2 misses
per fn logged as the LIVENESS proof.

## GRAPHICS DELTA
Zero new rendered models. The inject shape is byte-identical to p2(105); the only new
code is four log-only pass-throughs. The expected outcome on the mac is the known
black screen at setup:orbit.

## FALSIFIABLE CLAIM
With admission_inject=true on the mac, at least one `stage=reader` line with rec=1
appears in the mac log between the inject line and the setup:orbit entry - i.e. at
least one of the four static candidates runs for the forged record before the wedge.

CONTENT NEGATIVE 1: rec=0 lines appear but NO rec=1 line from any probe -> the four
candidates touch only self's record; the wedging consumer reads the record through a
SHIFTED BASE (field_xref's disp32 blind spot) or through a different structure
entirely. Next: page-guard VEH on the record span (catches every access regardless of
base shape), NOT more static guessing.
CONTENT NEGATIVE 2: rec=1 lines appear AND the client nevertheless passes setup:orbit
into in_world -> a probe perturbed timing or the record's readers are not the wedge;
split the hypotheses and re-run once before concluding.
CONTENT NEGATIVE 3: rec=1 lines appear and the LAST one is ADMIT (0x1777EC0) ->
the writer path is the last toucher and the wedge is downstream of admission in the
z-leg/bubble machinery; hand the question to fn 0x140E1D400 / dword[obj+0x524] (the
20.157 bundling).

## ABSENCE NEGATIVE
- Zero `stage=reader` lines of ANY kind (not even miss samples) => the probes never
  ran: check the install line first - it must show 4 readers attached. This is an
  instrument failure (L13), not a system fact.
- No `stage=install result=ok` line, or a `result=fail why=attach_reader/range_reader`
  line => the new probes did not attach; the boot tests nothing.
- No `stage=inject result=called member=1` line => the inject was refused (as in every
  armed boot's guard chain) - the record never existed, so rec=1 is impossible and the
  boot only proves the probes' miss path.

## CHAIN MARKS
- The injection makes the client believe it has a peer; the roster names the peer;
  the client wedges at setup:orbit - verified-by-execution (p2(102)/(103)/(104)/(105)).
- The wait is client-internal, not networked - verified-by-execution (20.166 solo,
  20.167 paired, live channel).
- The four probed functions contain code that touches the record fields - verified-
  by-reading (field_xref + pdata_bounds this session; stack-frame false positives
  filtered; fragment reader excluded as the already-hooked adoption function).
- The four functions RUN, and for record 1 - UNKNOWN (this boot's test).
- The wedge consumer is among them - UNKNOWN (that is the point).
- 16-slot pass-throughs are safe on these four ABIs - verified-by-reading
  (pre-attach disassembly; deepest stack-arg read = slot 13 < 16).
- Solo-control rule: the inject half is byte-identical to p2(105) (already booted
  armed on the mac); the NEW code is log-only pass-throughs with a settings-gated
  census flag. Solo control waived on that basis; rollback is a settings flip.

## ADVERSARIAL PASS: waived - solo main-session prep (B-checkpoint exception). Main
residual risk: four new detours on ABI-unknown functions. Mitigated by the 16-slot
bit-exact forward, the pre-attach caller-frame check, log-only bodies, per-probe
caps, and the rig as an unarmed control running the SAME build.

## SWITCH POSITIONS FOR THIS BOOT
  MAC  admission_inject TRUE (params retained), admission_census TRUE
  RIG  admission_inject FALSE (control; no admission keys)
  Server unchanged p2(96) b9b0f3823f74d1bf; claims reset before boot.

## INSTRUMENTS:
  "ev=admission stage=reader"
  "ev=admission stage=inject"
  "ev=admission stage=census"
  "ev=admission stage=install"

## LITERAL TARGETS:
  Game/bin/x64/steam_api64.dll: ev=admission stage=reader, ev=admission stage=inject, ev=admission stage=census, ev=admission stage=install

## ROLLBACK
Flip mac admission_inject to false - no rebuild. Prior DLLs on disk as
steam_api64.dll.bak_p2d7_* on both machines (mac 5d7e6bd61e078c24 write-free is the
deep baseline). Server unchanged; DO NOT BOOT p2(71).
