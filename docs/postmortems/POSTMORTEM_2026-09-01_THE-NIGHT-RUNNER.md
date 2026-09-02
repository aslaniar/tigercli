# POSTMORTEM - THE 0831/0901 NIGHT RUNNER (2026-09-01)

STATUS: closed postmortem (2026-09-01). Subject: the ~30-lane overnight wave
(night_0831_lane*, night_0901_lane*, night_0901_synthesis_DRAFT.md) and the three boots
it fed - p2-154, p2-155, p2-156. Written for a workflow-fixing session. Companion
records: FINDINGS 20.246-20.249. Sibling: POSTMORTEM_2026-09-01_INSTRUMENTATION.md.

## THE ONE-LINE SUMMARY

The night verified an enormous amount of work correctly and then handed forward one
unexamined inherited premise. Everything it proved about the MESSAGE was true; nothing
it proved established that the message was aimed at the right thing, and no lane was
tasked with asking.

## WHAT THE NIGHT GOT RIGHT (this is most of it, and it should not be lost)

- Lane E derived the type-0x2D wire format from the client's own schema tree, walked the
  reflection decoder to the field level, and then RAN THE REAL HANDLER against an
  authored body in femu. That result held under three later independent re-verifications,
  including my own re-run and the shipping C++ encoder's exact bytes (20.247 R5).
- The static closure work (lanes B/G/P) was disciplined: confidence marks, explicit
  negative results, and a "recorded after FOUR attempts" stop rule in lane P.
- The night's own red team caught two real errors before morning (20.241 R1's "the fixup
  appends when absent" - it is read-only; and "count increments" at a site that
  DECREMENTS) and banked them as corrections rather than quietly editing.
- Lane K independently re-derived geometry that lane H had asserted, and disagreed with
  ms-start-gate3 in writing rather than silently.

## ERROR 1 - THE INHERITED PREMISE NOBODY WAS ASKED TO TEST (the expensive one)

Every lane took as given that the peer-render blocker was "+0x602C4 is zero, so the
evaluator aborts" (20.245 R3). The night then spent its best work - the schema
derivation, the femu chain, the boot sketch - on making that byte nonzero.

On 2026-09-01, one probe that logged what the reader ASKS FOR showed each client queries
that function about its OWN machine id and nothing else (20.249 R1). If that holds
through a paired dwell, the abort was the self entry being skipped correctly and the byte
was never the blocker.

THE MECHANISM THAT FAILED: a ~30-lane wave had no lane whose job was to falsify the
premise the other lanes were built on. Lane briefs were shaped as "deepen X" and "close
the static route to Y". None was "prove the front is the front".
THE FIX: one lane per wave, spawned FIRST, whose deliverable is the evidence that the
current front is real - and which is allowed to come back with "it is not".

## ERROR 2 - "BOOT-READY" CONFLATED TWO DIFFERENT CLAIMS

The synthesis wrote: the body is "femu-verified END TO END", "BOOT-READY", "the fork can
author this wire item today with zero further RE".

What was verified: IF the handler runs, it sets the byte. What was never examined: whether
a fork-sent type-45 message REACHES that handler on a live client. That gap is exactly
what p2-154 spent a boot discovering (20.247), and it was foreseeable - the night's own
lane C/I work had established that pool handlers are reached through a runtime
registration table, which is precisely the shape that can accept a message and route it
nowhere.
THE FIX: separate "the callee does X" from "the call happens" in the readiness language.
A femu proof is a statement about a function, never about a route.

## ERROR 3 - AN INCOMPLETE CENSUS REPORTED AS A COMPLETE ONE

Lane G's CLAIM G5 - "EVERY +0x38 byte across all six table copies ... reads 0x00" -
sampled records 0..3 of 32. Checking all 32 (20.246 R3) turned up two nonzero bytes,
which on inspection were heap residue in a buffer whose masks pointed at empty slots. The
VERDICT survived; the EVIDENCE as written did not support it, and if those two bytes had
been real the claim would have been false with high confidence attached.
THE FIX: a census states its denominator in the claim line. "6 tables x 4 of 32 records"
is a different sentence from "6 tables, all records", and only one of them was true.

## ERROR 4 - A LOCAL MISTAKE GENERALISED INTO A PROPERTY OF THE FORMAT

The synthesis's NIGHT ADDENDUM reported that count=2 bodies decode with the second key's
last byte corrupted, concluded the multi-id packing convention was unresolved, and made
"two count=1 bodies" the verified-safe recommendation. But lane E's own driver8 had
already produced a correct count=2 body, and re-running it reproduced both ids exactly.
The main session's count=2 attempt had used a different packing; the addendum promoted
one bad hand-pack into a property of the wire format.
Cost: the p2-154 design was narrowed for no reason. (The multi-id path was later verified
4/4 including negative controls - and then misused, which is ERROR 6.)
THE FIX: before writing "the format does X", diff your reproduction against the lane's
own verified artifact. Two disagreeing results are a bug in one of them, not a finding.

## ERROR 5 - PER-BOOT VALUES WRITTEN AS CONSTANTS

The boot sketch named 0x846C8338F7D022E6 and 0xF5D3535B98AEB768 as the expected machine
ids. The rig's is stable across boots; the mac's is not (it changed every boot - almost
certainly a GPTK/Wine derivation). Caught pre-boot, but a brief that names literals for
values read live will eventually make a correct result look wrong.
THE FIX: observables are expressed relatively ("the OTHER client's first-registered
identity key") unless the value has been shown stable across boots.

## ERROR 6 - A DISPUTED CLAIM CARRIED FORWARD, AND A SAFE RESULT MISUSED

The night's red team DISPUTED C6 ("no missing feed to populate") and the synthesis
carried the claim anyway, marked but load-bearing. Separately, lane E's verified multi-id
capability was later used by me to mark the client's OWN machine id, which crashed a
client (20.249). The lane proved the ENCODER handles N ids; it never proved any
particular id was safe to name. A verified mechanism is not a licence for every input.

## WHAT THIS CHANGES ABOUT RUNNING A NIGHT WAVE

1. Spawn a FALSIFY-THE-FRONT lane first; let it come back negative.
2. Readiness language distinguishes callee-proven from route-proven.
3. Census claims carry their denominator.
4. Contradictions between the wave's own artifacts are resolved before synthesis, not
   averaged into a recommendation.
5. Literals in a brief are per-boot until proven stable.
6. The red team's unresolved disputes block the synthesis line they touch.

## WHAT NOT TO CONCLUDE

Not "the night was wasted". It produced the schema derivation, the femu chain, the static
closures and the corrections that make the current front legible - and 20.246's dump
census, which stands. The failure is one of FRAMING and of readiness language, not of
craft, and every specific artifact it produced survived independent re-verification.
