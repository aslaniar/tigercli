# Plan: boot-gate v3 + verdict v2 (deterministic fixes for the nine
# empty-mask-loop mechanisms) - 2026-08-31

Source: POSTMORTEM_2026-08-31_THE-EMPTY-MASK-LOOP.md (~8 boots on a non-
blocker; root cause: a return code read as a state). Companion to
enforcement-layer.md (the four interception points; this adds the BEFORE-BOOT
and VERDICT machinery the loop exposed).

## THE UNIFYING PRINCIPLE (from the postmortem's own pattern section)

Every mechanism was a CHEAP PROXY accepted in place of a DIRECT MEASUREMENT,
then refined instead of replaced. The deterministic form of the fix is always
the same: **the brief must NAME the direct thing, and the gate checks the
naming exists.** Where the direct thing doesn't exist, building it IS the
boot. This converts all nine mechanisms into three enforcement classes:
  GATED    - the gate refuses until the field/artifact exists
  MECHANICAL - a script computes and prints the discriminating fact
  FORCED-JUDGMENT - the gate forces the naming; a reviewer challenges content

## IMPLEMENTATION SET (in the postmortem's priority order)

### 1. GATE v3 - `STATE READERS:` field (mechanism #1, the root cause)
Brief template v3: every state the boot asserts about the client must have a
named DIRECT READER - the hook/function that observes the state itself.
"inferred from a return/error code" is NOT a reader.
- gate_boot.py checks: every line in `ASSERTED STATES:` names a reader that
  is (a) in the deployed instrument manifest, or (b) explicitly declared as
  `BUILD: <name>` - in which case building it is the boot's stated purpose.
- Falls out of the instruments.json manifest (enforcement-layer plan).

### 2. OUTCOME LEDGER + third-branch counter (mechanism #6)
- RE_output/map/boot_outcomes.jsonl: one record per boot
  {date, boot_id, front, outcome_class} where outcome_class is one of
  hypothesis-survived | hypothesis-wrong | third-branch (behavior changed,
  outcome didn't).
- Written by the boot-closing ritual (session; the class is a judgment but
  the RECORDING is mechanical).
- gate_boot.py: reads the front's last K outcomes; >=2 consecutive
  third-branch -> REFUSE unless the brief contains a `MODEL REVIEW:`
  section (which must name what causal assumption dies).
- Fully deterministic once recording is habitual.

### 3. boot_verdict v2 - per-arm discriminator table (mechanism #2)
- boot_verdict.sh gains: failure signatures parsed from the boot brief (or
  CLI), then a side-by-side table: signature | solo-arm count | paired-arm
  count.
- Verdict line: signatures present in BOTH arms = NOT peer-attributable
  (the solo arm is a DISCRIMINATOR, not just a crash guard).
- Fully mechanical.

### 4. bootstrap_check - unbuilt-instrument visibility (mechanism #8)
- grep claims/*.md for "definitive instrument" / "the instrument that
  would" / "instrument that would" -> print each with file:line under
  "SPECIFIED INSTRUMENTS - CHECK IF BUILT".
- Pure visibility; deterministic.

### 5. BRIEF TEMPLATE v3 fields (mechanisms #3, #4, #5, #7 - forced judgment)
- `DISCHARGE LIST:` - recorded counter-cases (cause absent, outcome
  unchanged). Rule: a counter-case is ranked #1 until discharged. Gate: if
  the list is non-empty, hunt item #1 must reference discharging one.
- Hunt items each carry `falsifies: <claim>` - items that falsify nothing
  rank below items that falsify something (anti-novelty-bias, #4).
- `EFFECT CLAIM:` field distinct from `DELIVERY CHECK:` (mechanism #5) -
  "arrived and decoded" is delivery; the pre-named claim must be the
  effect. Delivery proof rides in the same boot.
- `ABANDON OUTCOME:` + `WIDE NET:` - already in the template (mechanism #7);
  gate v3 now ENFORCES their presence.
- gate can verify field presence and cross-references; content quality is
  the verify-agent rubric's job.

### 6. logq truncation flag + width discipline (mechanism #9)
- logq.py: when --tail/limit truncates, print "TRUNCATED: showing N of M"
  IN the output - a conclusion written from a truncated view is then
  visibly standing on a truncated view.
- Width discipline (a ret wider than the callee's declared width is a WIDTH
  question first): template/lane-brief checklist line; not fully
  automatable (needs callee signature knowledge).

## KEEP-LIST PROMOTIONS (from the postmortem's "what went right")
- instrument-carries-its-own-oracle: promoted to the lane-brief template as
  standard on any probe reading a value we cannot check by other means.
- mtrace zero-census pattern ("attached but never called" vs "never
  hooked"): already standard; noted as the reason several conclusions held.

## HONEST CLASSIFICATION
  GATED (deterministic): #1 field+manifest, #6 counter, #7 section
    presence, #2 table, #8 grep, #9 truncation flag
  FORCED-JUDGMENT (gate forces naming, rubric challenges content):
    #3/#4 falsifies lines, #5 effect-vs-delivery, #1 reader-directness
  The postmortem itself flagged #3/#4 as judgment-prone; the brief-field
  approach is the agreed compromise.

## BUILD SEQUENCE
1. boot-brief template v3 fields + gate_boot v3 checks (STATE READERS,
   third-branch counter, ABANDON/WIDE-NET enforcement)
2. boot_outcomes.jsonl ledger + recording ritual line in the boot-close
   convention
3. boot_verdict v2 per-arm table
4. bootstrap_check unbuilt-instrument grep
5. logq truncation flag
6. registration: TOOLS.md, FINDINGS entry, ENFORCEMENT.md ledger rows
   (mechanism -> enforcement status per the ledger design)

## ADDENDUM (2026-08-31, post the launch-freeze crash)
The freeze at launch is the C-class (08-30 postmortem C5/C4) striking again
while this plan sat pinned. Concretely added to preflight.py's checks:
- client DLL export count + directory size vs last-known-good manifest
  (C5: the fastest load-time-failure check, takes seconds)
- deployed DLL == built DLL on BOTH machines (re-asserted, not assumed)
- instrument manifest reconciliation: every brief-declared hook present in
  the deployed binary AND in the manifest
- known-trap checklist as ASSERTIONS, not prose: detour target size >=
  footprint (from the spine), no foreign threads, no hot-path hooks
  without a CALL FREQUENCY field
Also: pre-commit hook INSTALL becomes part of step 1 (pending since 08-26).
The pin is over: this plan is the pen session's next work item.

## ACCEPTANCE
- gate refuses a brief missing each new required field (negative tests)
- third-branch counter refuses boot #3 after two recorded third-branches
- boot_verdict prints the per-arm table from a real capture pair
- bootstrap_check surfaces a "definitive instrument" sentence from the
  corpus (the 0x141711D10 allocator probe is the known live example)
- all negative tests run before positive ones (they must fail on purpose)
