# POSTMORTEM - THE WIRE-WATCH INSTRUMENT (gate_wwatch, p2-158/p2-159)

STATUS: closed postmortem (2026-09-02). Subject: the DR-based gate-byte watch - three
abnormal host outcomes in three armed boots (rig crash, rig crash, mac MACHINE freeze),
the instrument retired, and what the failure class teaches. Companion: FINDINGS
20.252-20.255. Written per the instrumentation-postmortem series
(POSTMORTEM_2026-09-01_INSTRUMENTATION.md).

## THE ONE-LINE SUMMARY

The watch answered its question (the gate-byte writer, 20.252/20.254) but carried three
invasive mechanisms - a first-chance VEH, per-thread debug registers, and a 4 Hz
suspend/setcontext sweep - whose host cost we priced at zero, shipped to a platform where
the core mechanism cannot even work, and mitigated twice for a root cause we never had.

## TIMELINE (facts only)

- p2-158 (build b241ecda precursor): rig crash ~3k ticks after the watch captured the
  landing restore. Crash silent; WER dump triage-grade, context garbage.
- p2-158 mac solo: selftest FAIL (Rosetta cannot deliver DR hits - PRE-NAMED as claim
  (e) before deployment). The mac kept running the full sweep machinery anyway.
- p2-159 (build b241ecda): sweep bug found by the selftest control (threads born after
  the first sweep were never armed - the sweep only ran on re-arm). Fixed: sweep every
  cycle. Rig selftest ok x2, landing capture clean, capture-then-quiet fired, client
  SURVIVED the landing that killed p2-158.
- p2-159 continued: rig crashed anyway, minutes later, in Tower, solo (silent log-end,
  new WER dump). Same session: the mac's entire machine froze.
- Decision: watch retired (install emits `result=retired`; no VEH/DR/sweep in any future
  boot). pubrest (a plain detour, DR-independent) retained - it had already delivered the
  behavioral lever (20.255 R3: type-12 -> message-fed image -> staging).

## DEFECT 1 - "OBSERVATION IS FREE" APPLIED OUTSIDE ITS DOMAIN

The project's detour probes are read-only pass-throughs: the "bundle OBSERVATION freely"
rule is TRUE for that class. The watch imported three mechanisms from a different class -
exception interception, hardware debug registers on every game thread, and periodic
thread suspension - and treated them as observation because no game memory was written.
Each mechanism alone is a plausible host-disturber; jointly they are unbounded. RULE
(now LESSONS U18): an instrument that installs a vectored exception handler, writes
debug registers, or suspends game threads is a BEHAVIOURAL change by default; it ships
only with a platform-validated mechanism, pre-named kill criteria, and a retirement that
is one line long (ours was).

## DEFECT 2 - THE KNOWN-INERT PLATFORM STILL CARRIED THE FULL RISK

Claim (e) pre-named that the mac cannot deliver DR hits. Confirmed on the mac's first
boot. Correct response: strip the watch from the mac that day. Actual response: the mac
kept sweeping every 250ms - suspending and setting context on ~55 Wine-translated
threads 4 times a second for a mechanism that could never fire - until the machine
froze. The freeze is attributable to the sweep class (Wine server lock interaction is
the prime suspect; unproven, and it does not matter for the decision). RULE: when a
mechanism is known-inert on a platform, the instrument is disabled THERE first - risk
with zero possible benefit is the purest waste a boot can carry.

## DEFECT 3 - COVERAGE BY INVARIANT, NOT BY MEASUREMENT

The sweep-once design left every thread born after the first sweep unwatched while the
census would have reported full coverage - a silent false-negative machine. The selftest
control caught it (loudly, twice, on both machines) - the control discipline PAID. But
the bug class was preventable: coverage was an invariant of the design ("sweeps happen")
instead of a measured output ("threads covered / total, every cycle" - the denominator
rule, added only after). RULE: any watch/sweep instrument prints its coverage
denominator every cycle, from boot one.

## DEFECT 4 - A MITIGATION TREATED AS A ROOT CAUSE

Capture-then-quiet was designed against "repeated #DB exposure during the landing
transition" - a hypothesis, never proven. The rig then survived the landing (mitigation
"worked") and crashed later anyway, in a different phase. We did not claim the crash was
fixed in the brief (the pre-named text said "removes the repeat-exposure component"),
but the temptation to read survival-at-landing as confirmation was real and the crash
arrived regardless. RULE: a mitigation that survives one test confirms the mitigation,
not the mechanism. Name the residual risk in the same sentence as the fix.

## DEFECT 5 - THE EXCEPTION-MACHINERY STATE CHANGE OPENED A NEW HOLE

Capture-then-quiet disarms slots in software; any thread whose context was not yet
updated still carried an armed DR. A hit on a disarmed slot fell through the handler as
CONTINUE_SEARCH - an unhandled EXCEPTION_SINGLE_STEP - the exact crash class under test,
introduced BY the mitigation. Caught by the adversarial review, fixed by the consumption
rule (any #DB whose Dr6 names a DR address we armed is ours, regardless of software
mask). RULE: every state change to exception machinery must be walked through the
question "what does the handler now do for a hit it no longer expects" - the handler's
consumption rule must be a function of the HARDWARE state, not the software's intent.

## WHAT WORKED (copied, not just survived)

- The by-construction self-test: caught the sweep bug loudly on two machines; its
  FAIL-voids-silence semantics prevented a false negative from reaching a conclusion.
- Pre-named platform outcome (claim (e)): the mac failure was diagnosed in one line.
- Brief validity conditions: claim (d) made ring/mask/quiet state explicit before boot.
- The retirement decision itself: executed at the second crash without defending the
  instrument, and pubrest kept working because it never shared the watch's machinery.
- The offline fallback (pubrest on the clean chokepoint 0x1403CB340) delivered the
  behavioral lever (20.255 R3) AFTER the watch had already delivered its own answer -
  proving the chokepoint was the cheaper instrument for every question after the first.

## THE THROUGH-LINE

The watch was the right CLASS of instrument for "catch an unknown writer" - and the
wrong SHIPMENT: three boots, two platforms, no kill-switch, mitigations ahead of root
cause. The moment the writer was named (20.252), every remaining watch question had a
cheaper clean-detour answer. The instrument's retirement is not a failure of the
observation - the observation succeeded - it is the correction of a cost model that
priced host disturbance at zero. The next instrument (pubrest) is a plain detour, and
the behavioral boot it serves ships with the watch retired.

## CONVERTED RULES

- LESSONS U18 (new): invasive-instrument gate - VEH / debug registers / thread
  suspension = BEHAVIOURAL by default; platform-mechanism validation before paired
  exposure; auto-retire at two abnormal outcomes; disabled on platforms where the
  mechanism is inert.
- The retirement itself is the conversion: gate_wwatch::install's `kWatchEnabled=false`
  with the rationale in place.
- tool debt: none open from the watch; pubrest's one-shot dump volume (~1,427 lines)
  is accepted and pre-named in the brief.
