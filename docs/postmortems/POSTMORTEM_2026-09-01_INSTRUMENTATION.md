# POSTMORTEM - INSTRUMENTATION, WHOLE SESSION (2026-09-01)

STATUS: closed postmortem (2026-09-01), REOPENED ONCE and closed again 2026-09-02 with an
ADDENDUM (p2-160, pubrest) at the end of this file. Subject: every instrument this session
relied on or built - across p2-154, p2-155, p2-156 and the static work between them - and
what each could and could not say. Written for a workflow-fixing session. Companion
records: FINDINGS 20.246-20.249. Sibling: POSTMORTEM_2026-09-01_THE-NIGHT-RUNNER.md.
The 2026-09-02 addendum is here rather than in a new file because its defect is the SAME
defect as DEFECT 1, one level up: a probe that could not say what its own question was.

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


---

# ADDENDUM - p2-160, THE DUMP THAT COULD NOT FIRE (2026-09-02)

STATUS: closed. Subject: the pubrest image dump across the p2-160 boot - THREE launch
cycles, two of them spent on this instrument rather than on the question. Companion record:
FINDINGS 20.258. Author: the 2026-09-02 session, about its own work.

## THE ONE-LINE SUMMARY

Three times I shipped an instrument after reviewing only the part of it I had just edited,
and three times the defect was in the part I had not looked at. The fix that finally worked
was not a cleverer gate - it was REPLAYING THE SHIPPED LOGIC OVER ALREADY-RECORDED LINES
before deploying, which I could have done after the first failed boot and did not do until
the third.

## THE COST

Three paired launch cycles. The user quit and relaunched two machines each time. Attempt 1
produced no dump at all; attempt 2 produced two dumps of which the one that mattered was
spent on a non-peer image; attempt 3 shipped only after replay confirmed correct behaviour
on both prior runs' recorded data. The user's words, which belong in the record: "do you
know how long boot tests take?" They are right, and the answer is that I was treating their
launches as the cheap resource and my review time as the expensive one, when the ratio is
the other way around by orders of magnitude.

## WHAT HAPPENED

pubrest hexdumps the staging source image. Its dump block read:

    if (restore && isEnter && srcOk) { ... }

`restore` is `is_armed_table(arg1 + 0x80)` - true only when the copy's DESTINATION is a
known participant table. In the p2-160 boot, across a full paired Tower dwell:

    pubrest calls: 24        role histogram: {unknown: 24}
    ...with a genuine peer in the source image: 8
    pubrestimg dumps: 0

Not one call classified as a restore, so the block never ran. And it could never have run:
STATE.md already recorded, from 20.255, that the restore is **obfuscated-direct and
BYPASSES 0x1403CB340** - which is the exact function this hook detours. A restore does not
arrive at this hook by construction. The dump was gated on an event that the instrument's
own placement excludes.

The publish side arrives here fine, and that is where the wanted image lives: 8 calls at
`caller_rva=0x16E62AD` (inside the message-driven publish 0x1416E6250 of 20.255) carried a
source image at 0x6AFC6A40 whose record 0 was the local identity and whose record 1 was
0x846C8338F7D022E6 - the other machine. The image we needed was in the probe's hands, with
its address logged, eight times, and the probe declined to dump it.

Fix: gate the dump on what it needs - a readable source image of a known shape
(`isEnter && srcOk && rec8[0] != 0`) - and record `role` in the dump header as an
observation instead of using it as a precondition.

## MY ERRORS, NAMED

### 1. I FIXED THE FINE STRUCTURE OF A BRANCH WHOSE GUARD WAS ALWAYS FALSE
I rewrote the dump from one shot to two, corrected which image gets which shot index, and
fixed the novelty gate that would have starved it. Every one of those edits was inside
`if (restore && ...)`. I never asked the prior question - CAN THIS BLOCK BE REACHED? -
because I was working at the layer below it. The question to ask first about any branch you
are about to improve is whether it executes, and I asked it last.

### 2. I HELD BOTH HALVES OF THE CONTRADICTION AND DID NOT JOIN THEM
This is the part that is not bad luck. In this same session I read STATE.md's line that the
restore is obfuscated-direct and bypasses 0x1403CB340, and I read the code computing `role`
from armed tables, and I quoted the first one in the boot brief's own premise section. Two
facts, one session, one file apart, and I never put them in the same sentence. A fact
recalled and a fact USED are different things; quoting a constraint into a document is not
the same as testing the design against it.

### 3. I PRE-NAMED THE NEGATIVE AND NEVER PRICED IT
The brief's ABSENCE NEGATIVE says, verbatim: "`stage=pubrest` lines present but ZERO
`pubrestimg`: no call classified as a RESTORE with src_ok=1." That is exactly what
happened. I wrote the failure mode down, in advance, in the correct words - and treated it
as a remote edge case rather than asking how likely it was. U6 asks for the negative to be
NAMED; U9 asks for the gate's EXPECTED VALUE. I satisfied the first and skipped the second,
and the second was the one that would have stopped the boot. A pre-named negative that is
in fact the modal outcome is a design review finding, not a contingency.

### 4. MY ADVERSARIAL PASS AUDITED THE LAYER I WAS EDITING
Six findings, all real, all applied - and all about shot selection, gate starvation and
label correctness. Not one questioned the reachability of the block containing them. A
self-review that only inspects the diff will confirm the diff and miss its premise. The
pass needed one question it did not contain: what must be TRUE IN THE WORLD for this code
to run, and is it?

### 5. I USED GREP CHAINS ON A LIVE BOOT, AGAIN
For several rounds I dug through the running client's log with grep/sed pipelines, until
the user told me to use our tooling. AGENTS.md routes log digging through logq.py over a
logindex.py index; the LAST SECTION OF THIS VERY FILE already records that same failure
from 2026-09-01. Once indexed, the whole diagnosis was one query returning the role
histogram and the peer-bearing call sites. The repeat is worse than the original: the rule
was not merely written down somewhere, it was written down in the document about my own
instrumentation mistakes.

## WHAT THIS COST, AND WHAT IT DID NOT

Cost: one paired boot, and the user's time launching two machines for it.
Did NOT cost: the diagnosis. The instrument logged `role`, `src`, `caller_rva` and
`rec8_0/1` on EVERY call, so the run that failed to produce the artifact fully explained
why, and named the exact address and call site the fixed version should target. The boot
was not wasted so much as spent on the instrument instead of the question.

## WHAT WORKED, AND SHOULD BE COPIED

- The two fixes I did make were necessary and are now VERIFIED live, not just argued:
  the novelty gate would genuinely have collapsed the peer-bearing call (24 calls, all with
  f38 tuples of 00,00,00,00 and unchanging args - the peer transition is invisible in the
  fingerprint without the peer bit), and the `rec8_1 != rec8_0` peer test was vindicated
  when the mac's own pgate showed slot 1 holding the SELF identity while solo. Both would
  have been boot-killers in their own right.
- A probe that logs the CONTEXT OF ITS OWN DECISION can be debugged from a single run. Every
  input to the dump predicate was on every line, which is the only reason one failed boot
  produced a precise fix instead of another round of guessing. Copy this: log the operands
  of a gate, not just its outcome.
- Proving a behaviour switch offline BEFORE it enters a binary: the peer-row flag mask was
  mirrored into the Python encoder port and run over all 32 values - every one
  size-preserving at 4095 B, flags=0 byte-identical to the golden body, bapdecode accepting
  each. It cannot silently break the encode when a later boot uses it.
- Declining to deploy the server build that carried that switch. It was not needed for
  p2-160's contract, and 20.247 R8 is precisely the story of a change bundled to serve a
  later experiment breaking the current one.

## THE CANDIDATE RULE (for LESSONS, if it survives another session)

AN INSTRUMENT'S TRIGGER IS A CLAIM ABOUT CONTROL FLOW, AND MUST BE MARKED LIKE ANY OTHER
CHAIN LINK (U16). The brief marks the chain the boot reasons about; it does not mark the
predicate that decides whether the probe fires. Here the trigger's mark would have been
`role==restore reaches this hook: ASSUMED` - and the very next line of STATE.md refuted it.
Cheap to check, and it converts this class of failure from a spent boot into a brief edit.


---

## ATTEMPT 2 - THE PEER TEST WITH NOTHING TO ANCHOR IT

The attempt 1 fix made the dump fire. It fired twice, and the shot that mattered was spent
before the second machine had even joined:

    shot 0  peer=0  rec8_0=0x88CB5281391A82CB  rec8_1=0x0             <- correct baseline
    shot 1  peer=1  rec8_0=0x1A82CB013E294F94  rec8_1=0x88CB5281391A82CB

Record 1 holds the LOCAL identity; record 0 holds a byte-shifted view of it (`1A82CB` is a
substring of the local key's low half). My peer test was `rec8_1 != 0 && rec8_1 != rec8_0`,
which that satisfies. My stability gate - added specifically to reject torn reads - passed
it too, because the shape is STABLE and REPEATABLE rather than a one-off tear.

### THE ERROR: I DREW THE NARROW CONCLUSION FROM A LINE THAT SUPPORTED A WIDER ONE
Attempt 1's pgate had already printed `i=1 self=1` - the local player sitting in slot 1. I
READ that line, and I QUOTED it in the brief to justify the `rec8_1 != rec8_0` guard. The
conclusion I drew was "record 1 can hold self, so guard against rec8_1 == rec8_0". The
conclusion available was "record ordering is not fixed, therefore record 0 is not reliably
self, therefore THIS TEST HAS NO ANCHOR". I used the evidence to patch the symptom it
pointed at and never asked what else it invalidated.

### THE SECOND ERROR: A GUARD BUILT ON A GUESS ABOUT THE FAILURE'S NATURE
I called the attempt-1 anomaly a "torn read" and designed a stability gate around that
guess. I had the data to check it - the tuple appeared once in attempt 1, which is
consistent with a tear but equally consistent with a transient state - and I did not go
back and ask whether a repeated observation would distinguish them. Attempt 2 answered it:
the shape recurs. A mitigation designed against an unverified mechanism is a coin flip
dressed as engineering.

## ATTEMPT 3 - THE LINE-BY-LINE READ I SHOULD HAVE DONE FIRST

Reading the WHOLE function rather than my own diff surfaced five more defects, two of which
would each have cost another boot on their own:

1. **THE ANCHOR CAME FROM DUMP ORDERING - A DEADLOCK.** I learned the local identity from
   the solo baseline. If a peer is already present when the client joins, no solo image ever
   appears, so no baseline fires, so no anchor exists, so the peer shot can NEVER fire. The
   instrument would have been silent on a rejoin and I would have read that as a finding.
   The anchor now comes from pgate, which walks the live table and knows self authoritatively.
2. **ONLY TWO RECORDS WERE SCANNED.** `rec8[2]` assumes the peer lands in slot 1 - the exact
   assumption attempt 2 had just disproved from the other direction. A peer at record 2+ was
   invisible. Now eight records, best-effort past record 0.
3. **THE BASELINE WAS NOT ANCHORED EITHER.** Gated only on `!peerInImage`, so attempt 2's
   shifted image qualifies as "not a peer" and could become the baseline - after which every
   byte of the solo-vs-peer diff reads as meaning. I had fixed the peer side and left its
   mirror image untouched, which is the same error as attempt 1 at a smaller scale.
4. **THE STABILITY GATE WAS ACTIVELY HARMFUL.** Collapsed to one shared slot, an interleaved
   peer image broke the baseline's streak - replay showed the BASELINE ceasing to fire on
   attempt 1's own recorded lines. It also spent margin where margin is scarcest: the peer
   window is ~6 bodies and the genuine tuple was seen three times, so demanding a second
   sighting risks losing a short pairing outright. Removed; the anchor is strictly stronger
   and needs one sighting.
5. **`bytes=` OVERSTATED THE IMAGE** - 0x59300 reported for a 0x59260 image, because the
   loop's final `done = off + kChunk` was not clamped. Small, but it is a coverage figure,
   and a coverage figure that rounds up is worse than none.

## THE PRACTICE THAT ACTUALLY WORKED, AND ITS PRICE FOR ARRIVING LATE

Every attempt-3 fix was validated by replaying the shipped predicate over the pubrest lines
already recorded in attempts 1 and 2:

    attempt 1 lines -> shot0 (0x88CB..., 0x0) and shot1 (0x88CB..., 0x846C8338F7D022E6)
    attempt 2 lines -> shot0 only; the shifted image REJECTED

That replay is what caught defects 3 and 4 - both of which I had just written, and neither
of which I would have found by re-reading my own reasoning. The data to run it existed from
the moment attempt 1 finished. Running it cost about a minute.

RULE, and the one worth carrying out of this: WHEN A BOOT HAS ALREADY PRODUCED LINES FROM
AN INSTRUMENT, THE NEXT VERSION OF THAT INSTRUMENT IS TESTED AGAINST THOSE LINES BEFORE IT
IS DEPLOYED. A probe's trigger is executable logic over a known input format; a recorded run
is a fixture. Shipping an instrument change to a boot without replaying it against the
previous boot's own output is spending the user's launch to run a unit test.

## THE THROUGH-LINE OF THE WHOLE ADDENDUM

Attempt 1: the guard on the branch I was editing. Attempt 2: the assumption under the test I
was editing. Attempt 3 (found before shipping, by replay): the mirror of the fix I was
editing, and a mitigation whose mechanism I had guessed. Every one is the same shape - I
audited the thing I had just changed and treated everything around it as given. A diff-scoped
review confirms the diff. The scope has to be the FUNCTION, and the check has to be
EXECUTION AGAINST REAL RECORDED INPUT, not re-reading.
