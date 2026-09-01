# BOOT BRIEF TEMPLATE (2026-08-26) - one per boot, gate-enforced

Every game boot gets a brief at this shape. `python3 RE_scripts/gate_boot.py
<brief.md>` checks sections 1-6 mechanically (exit 1 = do not boot). Full
reasoning: LESSONS.md PRE-BOOT CHECKLIST + Universal Lessons 2/5/6/12/13/14/16.
Example of the filled form: BOOT_BRIEF_p2-48.md.

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
