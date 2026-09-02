# POSTMORTEM - INSTRUMENTATION, WHOLE SESSION (2026-09-01)

STATUS: closed postmortem (2026-09-01). Subject: every instrument this session relied on
or built - across p2-154, p2-155, p2-156 and the static work between them - and what each
could and could not say. Written for a workflow-fixing session. Companion records:
FINDINGS 20.246-20.249. Sibling: POSTMORTEM_2026-09-01_THE-NIGHT-RUNNER.md.

## THE ONE-LINE SUMMARY

Three boots asked "what is the value?" of a probe that could not say "what was the
question?", and the answer to the second turned out to matter more than the answer to the
first. Every other defect here is smaller than that one.

## DEFECT 1 - A PROBE THAT LOGGED THE ANSWER AND NOT THE QUESTION (three boots)

track_c4 hooked 0x1404F7680, the +0x602C4 reader, as a `retwatch` probe: it emits the
RETURN VALUE when that value changes. Across p2-153, p2-154 and p2-155 it said the same
thing - one line, al=0, then silence through tens of thousands of calls - and that was
read as "the peer's contactable byte is zero".

The function takes a POOL and a MACHINE ID. The probe recorded neither. So it could never
distinguish:
  (a) the byte is zero for the peer we care about, from
  (b) the reader is not asking about that peer at all.
p2-156 gave the same hook a probe that logs pool + queried id. It produced two lines
total, and they said (b): each client asks only about its OWN identity (20.249 R1). One
probe field, changed once, put three boots' premise in question.

RULE: a probe on a LOOKUP function logs the key, not just the result. "Returns 0" is not
a measurement until you know what was asked.

## DEFECT 2 - BUDGETS SPENT BEFORE THE EVENT OF INTEREST (p2-154)

track_c4's enter/leave budget (12 lines) was exhausted at t=194424. The type-45 body under
test arrived at t=544883. Every detailed return-value observation in that boot predates
the thing the boot existed to test by six minutes. Only the change-gated retwatch, which
has no budget, produced usable evidence.

This is the project's own "BUDGET OBSERVERS PER EVENT CLASS" rule failing again, in the
form it takes when the event is LATE rather than merely rare.

WHAT WORKED, and is the pattern to copy: `pooldisp` (p2-155) emits ONE line per DISTINCT
message type via a seen-bitmap, with no budget at all. The type-45 dispatch it existed to
catch happened on call 57 of 149 - a 12-line budget would have missed it; the bitmap
caught it and stayed flood-proof. `c4query` reuses the shape with a 16-entry pair table.

RULE: when the event is late in a hot path, gate on NOVELTY (first-seen key), not on a
count. A budget measures the beginning of a boot; novelty measures the boot.

## DEFECT 3 - A CONTROL THAT COULD NOT FIRE (p2-155)

I built t30_handler as the positive control - type 30 being the one pool body known to
land - so that "no type 45" would be a fact about the client rather than about a broken
hook. It logged calls=0: the fork sends no type-30 body in a Tower dwell, so the control
was never exercised. It neither validated nor invalidated anything, and the "the hook
works" burden fell to the nine other live types pool_disp happened to catch.

A control chosen without checking that it FIRES in the scenario under test is decoration.
RULE: before shipping a control, confirm from a prior boot's logs that the control event
occurs in that scenario.

## DEFECT 4 - AN INSTRUMENT THAT OVERSTATED WHAT IT DID (p2-156)

The server's peer-contact line printed `ids=2` unconditionally while the appender deduped
zeros and duplicates; in the degenerate self-peer case it claimed a two-id body for a
one-id body. I noticed this mid-boot and let it stand because it did not affect the paired
reading. That was the wrong call - a log line that overstates the wire is the exact defect
class this project has burned boots on, and "it does not matter this time" is how it
survives to matter later. Fixed in the revert: it now prints the real count.

RULE: a line that reports what was sent is derived from what was sent, never from what was
intended.

## DEFECT 5 - INCOMPLETE SAMPLING PRESENTED AS A CENSUS (night lane G, inherited)

Four of thirty-two records per table, written as "every record". Detailed in the
night-runner postmortem; repeated here because the instrument lesson is separate from the
lane lesson: a census tool should print its denominator in its own output so the claim
cannot be written larger than the scan.

## DEFECT 6 - A GUARD ORDERED AFTER THE THING IT GUARDS (p2-156, unresolved)

`emit_c4query` dereferences rdx (memcpy of the machine id) BEFORE the seen-pair check, so
it reads through the caller's pointer on every one of thousands of calls rather than only
on novel ones. It is range- and alignment-guarded, and it survived the boot, but it is
more exposure than the design needs and it remains the one un-excluded alternative cause
of the mac crash (20.249 R3). The dedupe check should come first; only a novel pair needs
the read.

## DEFECT 7 - AN INSTRUMENT THAT CRIES WOLF (project tooling, unfixed)

`reset_lobby_claims.sh` requires exactly 3 matching listeners and reports "NOT READY -
check the server" with exit 1 whenever the count is 4. Port 30975 legitimately binds
twice, so a HEALTHY server fails the check every single run - it did so three times this
session, and each time the real state (ladder empty, claims cleared, NAT probe good) was
fine. An alarm that is always wrong trains its reader to skip it, which is how a real
failure gets missed. It should compare the SET of required ports, not a count.

## DEFECT 8 - MY OWN EVIDENCE HANDLING, UNTIL CORRECTED MID-SESSION

For most of this session I read logs with raw grep/awk chains over live files. That is the
conversion debt AGENTS.md explicitly names, and it has two concrete costs: line numbers
rot under an appending file, and nothing produced is citable. After the correction I
archived (log_archive.sh), indexed (logindex.py) and queried (logq.py) - and every claim
in FINDINGS 20.248/20.249 carries a file:line. The p2-155 evidence had to be re-derived
through the index to be quotable at all.

RULE, already written and ignored by me: logq over an index; loggrep for a one-line peek;
never a grep chain for anything that will be cited.

## WHAT WORKED, AND SHOULD BE COPIED

- `pooldisp`'s first-seen-key gating (DEFECT 2) - flood-proof and complete.
- `poolc4` dumping the WHOLE tracking array on ENTER and LEAVE. p2-154 could not separate
  "handler never ran" from "ran and wrote nothing" from "wrote a row we were not
  watching"; one probe emitting both sides of the call separated all three at once, and
  it is what proved the write lands (20.248 R1).
- Pointer guards with a PLAUSIBILITY check, not just a range check: refusing to read rows
  when the row count is implausible turns "rcx is not what I think" into a log line
  instead of a hang.
- Verifying the SHIPPING artifact rather than a model of it: running the compiled
  encoder's exact bytes through the real client handler in femu, with negative controls,
  caught nothing wrong but made the encoding permanently un-suspectable - which is why
  p2-154's failure was diagnosable at all.
- log_archive.sh being LOUD about the rig log being unreachable rather than silently
  archiving two of three files.

## THE THROUGH-LINE

Six of the eight defects are the same shape: an instrument that answers a narrower
question than the one being asked, presented as if it answered the wider one. The value
was zero / every record was clean / the control passed / two ids were sent / the server is
not ready. In each case the instrument was correct about its own narrow claim and was read
as making a larger one. The counter-practice is to write down, next to each probe, the
sentence it CANNOT support - and to check that sentence before quoting the probe.
