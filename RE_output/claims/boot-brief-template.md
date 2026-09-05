# BOOT BRIEF TEMPLATE (2026-08-26; v3 brief-tie fields 2026-09-05) - one per
# boot, gate-enforced

Every game boot gets a brief at this shape. `python3 RE_scripts/gate_boot.py
<brief.md>` checks sections 1-6 plus the v3 fields mechanically (exit 1 = do
not boot). Full reasoning: LESSONS.md PRE-BOOT CHECKLIST + Universal Lessons
2/5/6/12/13/14/16 + docs/plans/boot-gate-v3.md + TOOLING_AUDIT_2026-09-05.
Example of the filled form: BOOT_BRIEF_p2-48.md; v3 self-test fixture:
RE_output/map/boot_brief_v3_selftest.md.

## PURPOSE
What THIS boot learns, win or lose. What it explicitly does NOT test.

## GRAPHICS DELTA  (L12)
How many NEW never-rendered models this experiment introduces; what was done to
minimize that number. "Zero new models" must be stated when true.

## FALSIFIABLE CLAIM  (L6)
The single delivery contract under test, and the pre-named CONTENT negative:
"if <observable> shows <value>, then <specific conclusion X>".

## ABSENCE NEGATIVE  (L13)
If ZERO instrument lines appear: first hypothesis = the instrument never ran
(measurement invalid), not that the system lacks the behavior. Name which
deployment-provenance check proves liveness, e.g. grep -ac "<literal>" deployed.dll.

## CHAIN MARKS  (L16)
The full chain as a list; mark EVERY link: verified-by-execution |
verified-by-reading | assumed | unknown. The link this boot resolves is called
out. Never write "one boot away" with any link unmarked or assumed.

## ADVERSARIAL PASS: <session-id | waived: <one-line reason>>
Mandatory review before boot for: wire/codec encode fixes; third attempt on the
same question (U7); claims containing "should now" without an execution mark
(U16). Reviewer agent: .opencode/agent/verify.md. Waivers must name the reason;
the gate records it in the artifact.

## INSTRUMENTS: literal1, literal2
Byte-literals that MUST appear in the deployed binary if shipped this build.
gate_boot.py --literals <deployed-file> verifies them IN the deployed artifact,
not the build dir (L14).

## WIDE NET (2026-08-31, user directive)

Every instrumentation boot ships probes for ALL plausible points along the
suspect chain, not just the current lead. A single-site capture earns one bit
per boot while the boot is the expensive resource. Before writing the brief:
enumerate the chain's decision points (entry, each gate, each sink) and give
every one either a probe or a pre-named reason why it cannot fire.

## FRONT: <front-name> (2026-09-05, empty-mask #6)
The front this boot belongs to. Opts the brief into the outcome ledger
(RE_output/map/boot_outcomes.jsonl): >=2 consecutive third-branch outcomes
on this front REFUSE the next boot unless a MODEL REVIEW section is present.
Record the outcome at boot close: `python3 RE_scripts/boot_outcome.py --boot
<id> --front <name> --class hypothesis-survived|hypothesis-wrong|third-branch`.

## ABANDON OUTCOME (empty-mask #7)
A pre-named outcome that ABANDONS this front (not "next lead" - the front
dies). Continuation must not be structurally guaranteed regardless of result.

## PRIOR ART (2026-09-05, 09-05 FAILURE 5)
The q.sh queries run on this front's CENTRAL ADDRESS and CENTRAL NOUN, each
with its verdict (e.g. `q.sh 0x818 -> 20.260: loop is not the peer path`).
`none: <why>` only for ops/settings boots with no RE front. Any line citing a
closed/dead/retracted/superseded finding requires a DEAD-END AUDIT section:
the cheap check for whether building to escape the dead end is justified.

## STATE READERS (empty-mask #1 - the root cause)
Every state the boot asserts about the client/server names its DIRECT reader -
the instrument that observes the state itself. "Inferred from a return code"
is rejected by the gate. If no direct reader exists, write
`BUILD: <name>` - building it IS the boot's purpose.

## READOUT TRIGGER (T2.1 - p2-177's impossible decisive read)
Per instrument: THE EVENT THAT MAKES IT EMIT, each cited from a PRIOR LOG in
which that instrument emitted under that trigger (archive/logindex citation),
or the explicit words `NEVER-OBSERVED (first-fire risk)`.

## OBSERVER BUDGET (B2) and CALL FREQUENCY (C3)
Per instrument: the event class the budget covers ("the first 2
PLAYER-BEARING snapshots", not "the first 2"). Per hook: per-load / per-tick /
rare. Write `n/a (server-side only)` / `n/a (no hook changes)` when true.

## HOOK COUNT: N (B4) + INSTRUMENT LIVENESS (B3)
HOOK COUNT: the number of hooks this build installs; the gate verifies it ==
the checked count from verify_hook_rvas.py (rva==0 entries are silently
skipped by the verifier, so a shrunk table shows up as a MISMATCH - 09-05
FAILURE 2). INSTRUMENT LIVENESS lists literals that must appear in the files
named under INSTRUMENT SOURCES (the brief tied to what the instrument can
actually log):

    INSTRUMENT SOURCES:
        RE_build/.../hooks/pubrest.cpp
    INSTRUMENT LIVENESS: pubrestimg, role=

## EFFECT CLAIM (empty-mask #5)
The EFFECT this boot pre-names, distinct from DELIVERY. "Arrived and decoded"
is delivery, never the question. Delivery proof rides in the same boot; the
pre-named claim is the effect.

## FIX SURFACE: server | client (U18 - THE CLIENT IS NEVER MODIFIED)
If client: a SERVER-SIDE GAP section is required naming the specific wire
item the server is missing. A client-side proposal without the gap section
is rejected by the gate.

## MODEL REVIEW (conditional - required after >=2 consecutive third-branches)
Names the causal assumption that dies. The gate tells you when you need it.
