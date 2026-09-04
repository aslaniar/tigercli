# POSTMORTEM 2026-09-03 — READING THE INSTRUMENT

STATUS: closed postmortem (2026-09-03). Read before interpreting ANY probe output, and
before writing a finding whose evidence is a log line rather than a mechanism.

## THE THESIS, IN ONE SENTENCE

Every mechanical gate in this project fired correctly this session and caught real defects;
every error that reached the user came from the space the gates do not cover — deciding what
an instrument's output MEANS — and six of the seven were the same failure: concluding from a
field without first establishing what the field measures.

This session closed W1 and W3 and moved the front to entity construction. It also produced
six wrong claims, three of which I stated to the user with confidence before retracting.
The work was good. The reading of it was not, and the reading is the part that steers boots.

## PART 1 — THE SEVEN ERRORS

### E1. A BOOT THAT NEVER HAPPENED (cost: ~1 boot of analysis, one false FINDINGS entry)
I read the 2026-09-03 16:44 archive as a new paired boot whose slot_dump instrument had
failed silently. It was p2-165's session STILL RUNNING, snapshotted by the deploy script's
auto-archive hook. Two facts available before I wrote a word: both archives carry the
IDENTICAL `slot_card=1078`, and the widened DLL's mtime is 16:44:47 — SIX SECONDS AFTER the
archive it supposedly produced.
ROOT: I treated an archive directory's existence as evidence of a boot. An archive is a
COPY OF A FILE, not a run. U14 (assert artifact provenance) exists for exactly this and I
did not apply it to the artifact class it most obviously covers.
RULE: before an archive is treated as a boot, check (a) the deployed binary's mtime against
the archive's, and (b) at least one instrument counter against the previous archive. An
identical counter means the same session.

### E2. THE %zX THEORY (cost: a code change shipped with a false premise in its comment)
Built entirely on E1. I hypothesised the format specifier `%02zX` failed in the CRT, and
wrote that hypothesis into the source as a fact. It was disproven twice over: a replay
cross-compiled with the fork's exact toolchain under the same Wine emitted all three chunks
correctly, and the shipped DLL's disassembly carries three unrolled emit sites.
ROOT: a mechanism invented to explain an observation that was itself wrong (E1), then
recorded as established because it was written in a comment rather than in FINDINGS where a
reviewer would meet it.
RULE: a hypothesis put into a source comment is a CLAIM and inherits the same burden as a
FINDINGS entry. If it has not been tested, the comment says "suspected", or it does not go in.

### E3. THE SCAN WHOSE POSITIVE CONTROL FAILED (cost: reinforced E2)
My xref scan reported ZERO references to the slot_dump format string — and zero to
slot_card, which the same log proves emitted 1,078 times. I reported the slot_dump zero and
did not stop at the contradiction. The scan matched only REX prefix 0x48 and missed 0x4C.
ROOT: this is 20.209 R2 / U13 in its purest form — a tool's coverage limit read as a
world-fact — with the aggravating factor that the control was IN THE SAME OUTPUT.
RULE: a scan that cannot find its positive control has not produced a negative. It has
produced nothing. Every scan states its control and its control's result in the same breath.

### E4. THE WIDENING WRITTEN BEFORE THE CENSUS (cost: a build + revert; no boot)
p2-167 logged six fail-closed refusals where the peer key arrived in an unexpected form. I
called that a defect and wrote, built and gated a widening to accept the second form. The
census I ran AFTERWARDS showed that form appears in ONE boot of three, only inside the 26 s
before that client's transport reset. It is what the roster publishes while a session is
coming apart. The refusal was correct; my fix would have published a peer card for a peer
that was leaving. Reverted before deployment.
ROOT: I read six log lines I did not want as a defect. The project's CENSUS BEFORE FILTER
rule was in my head as a rule about scans, and I did not apply it to log lines.
RULE: CENSUS BEFORE FILTER APPLIES TO LOG LINES. Before "fix" is written for an unexpected
output, count that output across every boot that could have produced it.

### E5. THE FIELD I NEVER CHECKED (cost: three wrong statements about W2 in one session)
The `gatebit` probe prints `value=`. I read `value=0` as "the gate bit is clear" — three
separate times, including in a status summary to the user — and then asserted that W2 "has
never been instrumented". Both wrong. `value` is a CONTAINER COUNTER; the bit's requirement
is the derived `bitreq`; and the bit's actual home is the word the reservation dump has
been printing all along as `mask`. W2 was measured every boot this session, under a name
that did not say so.
ROOT: I read a field name and assumed its semantics instead of reading the six instructions
that produce it. When I finally read them, the answer took under a minute.
RULE: before a field's VALUE is used in a conclusion, its PRODUCER is read. A probe's field
name is a label its author chose, not a specification.
SECOND-ORDER: the corrected probe now states W2 on one line (`reqA/setA/reqB/setB`) rather
than requiring a join across two probes and a remembered findings entry. An instrument that
needs three sources to interpret WILL be misread; that is a property of the instrument.

### E6. THE STABLE ADDRESS (cost: one confident wrong statement to the user)
I reported that an image address identical across two boots indicated persistent or pooled
state, and called it significant. It is a STACK TEMPORARY — the function allocates it with a
stack probe on entry. The address repeats because the same code path reaches the same stack
depth. I stated the inference before reading the allocation.
ROOT: an inference from a coincidence-shaped observation, delivered as a finding.
RULE: "this address is stable across runs" is not evidence of anything until the allocation
is read. Stack, pool, and static all produce it.

### E7. THE INHERITED LABEL (cost: none this session; would have cost a front)
Our probe printed `ALL-PASS-would-construct`. I used "construct" in reasoning for most of
the session. When finally read, the guard's return feeds ONE accumulator whose only consumer
is a diagnostic string builder — a passing gate constructs nothing. The objective survived
(the guard CLAIMS as a side effect) but the reason was wrong, and anyone inheriting the
string would have inherited the error.
ROOT: the same class as 20.219 in POSTMORTEM_2026-09-02_THE-WRONG-QUESTION: a label written
by an earlier session, carried forward without ever meeting its evidence.
RULE: a verdict string is a CLAIM. Before it appears in reasoning, the code path it names is
read once. Corrected to `ALL-PASS-would-claim`.

## PART 2 — PROCESS FAILURES (not interpretation; just discipline)

- **Foreground ssh, twice.** ENVIRONMENTS documents that ssh over the ControlMaster hangs
  AFTER succeeding and prescribes backgrounding. I did it in the foreground anyway, twice,
  and the user had to tell me both times. Then I killed a large in-flight transfer, which
  wedged the multiplexed master and made an intact 12.4 MB log look like a broken one. The
  diagnosis that worked was purely LOCAL (`ps`, `ls`) and cannot hang — that should have
  been the first move, not the fourth.
- **Grep chains over logq.** The router says logq over a logindex, and raw grep chains are
  conversion debt. I built grep chains through 40 MB logs until the user said "use our
  tools". The index took 20 seconds and answered the question cleanly.
- **Explanations that did not land.** The user twice said the explanation made no sense, and
  once asked explicitly for no hex jargon — after which I produced more of it. When a reader
  says they do not follow, the defect is in the explanation; adding detail makes it worse.

## PART 3 — WHAT WORKED, AND WHY IT MATTERS MORE THAN THE FAILURES

Every mechanical gate fired, and each one caught a real defect:
 - `gate_boot --literals` rejected a mistranscribed instrument string before a boot.
 - `verify_hook_rvas` rejected a call-site constant misnamed as a hook address — AND its
   rejection message ("FRAGMENT offset=0x11c of 0x1404f77d0") is what CONFIRMED the address
   was the pool ctor's publish site. A gate that explains itself does double duty.
 - The membership wire test failed loud on the field re-pin because its bit offset was
   hand-counted. That failure produced the right fix: one shared constant, with the test
   deriving its offset from it, so writer and oracle can no longer drift.
 - `negative_audit` flagged a stale scan-negative that p2-167 had falsified by measurement.
 - TOOLS' check-before-you-fork rule stopped me building a probe that already existed and
   had already emitted the exact field the front needed.
 - An OFFLINE REPLAY over a previous boot's recorded values validated a new probe column and
   caught a real defect in it (two containers, one global) BEFORE deployment — the p2-160
   lesson working exactly as intended.

THE ASYMMETRY IS THE POINT: the gates caught every mechanical error and zero interpretive
ones, because interpretation is not gateable. The failures above are all in the gap, and
five of the seven share one shape — a conclusion drawn from an instrument's output without
first establishing what the instrument measures.

## PART 4 — THE ONE RULE THIS SESSION EARNED

**BEFORE A PROBE'S OUTPUT ENTERS A CONCLUSION, READ WHAT PRODUCES IT.**
Not the field name, not the comment above it, not what the previous session called it — the
code that computes the value. E5 and E7 are the same error at two layers. E1, E3 and E6 are
the same error applied to artifacts, scans and addresses. The cost of the read is a minute;
the cost of skipping it this session was three retracted claims to the user and one built
and reverted fix.

ONE-IN-ONE-OUT: this supersedes nothing. It is a NEW rule and it converts to a gate only
partially — `negative_audit` covers the scan case (E3), nothing covers E5/E7. Those stay
prose and stay JUDGMENT, which is the honest label.

## WHAT THIS SESSION ACTUALLY DELIVERED (for the record, and it is not small)
W1 CLOSED and W3 DOWN, both by measurement. Three real server-side defects found and fixed:
the peer card sourced from the wrong endpoint entirely, landing one field early, and a race
that meant one of two players never got sent one. The cascade proven end to end: the claim
now sticks and the peer's record stops being disowned. The front moved to entity
construction with the upstream chain verified rather than assumed.
