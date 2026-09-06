# BOOT_BRIEF_p2-180 — THE DUTY-CYCLED SUSTAINED ROW: THE RIG LANDS

STATUS: live (2026-09-05, drafted post-20.307). Supersedes BOOT_BRIEF_p2-179.md's
run plan (same session; p2-179's contract is INTACT and rides this boot as the
pre-named secondary phase).

## PRIOR ART (required field)
q.sh terms: retry_cap / duty / landing. Read in full: 20.297 (the transition
run), 20.300 R3/R5/R6, 20.305, 20.306 (the two corrections), 20.307 (the
census - THIS boot's mechanism), 20.222, 20.296, 20.302-20.304 (the contract),
STATE NEXT. The mechanism this boot tests was measured, not guessed: the
client completes its re-landing ~12-18 s after the last peer-row-driven
composition change; at body cadence (1.4-5 s) it never gets that window
(p2-176/178/179: 46-101 bodies, 17k-77k-hit engagement floods, no
fade_release; p2-175: 2 bodies, a 20-hit burst, landed 1.9 s after).
DEAD-END AUDIT: the pacing approach builds on a live mechanism question
(20.307), not an escaped dead end - the refuted alternative (cap=0,
20.307 R4c) is cited with its refutation inline.

## PURPOSE (ONE CONTRACT)
With the peer row duty-cycled to one publication per 30 s, the rig's second
landing COMPLETES (bootflow fade_release ISSUED) while the row stays
sustained. PRIMARY readout: the rig's bootflow reaches fade_release issued.

## THE CHANGE (server build + one settings key; clients UNCHANGED)
  - server: 791ffd907cb1636b (the duty-cycle gate in
    activity_membership_push.cpp: paced publication, retry budget disabled in
    the duty regime, 'result=paced' log line). Deployed via
    deploy_p2d6_gameplay.sh; settings.json gained
    membership_peer_duty_cycle_ms = 30000 (text edit, TRAP-18 procedure,
    .bak_p2-180_preduty saved).
  - clients: 3cc844c4cdd2fd63 BOTH - UNCHANGED, NOT redeployed (the client
    sources did not change; one variable per boot).
  - everything else byte-identical: cap=10 stays (ignored in the duty regime
    by the code guard), rearm stays 8 (inert), all other knobs unchanged.

## INSTRUMENTS (all existing; no new hooks; no client change)
  - server log: 'result=paced' (THE GATE'S LIVENESS LINE - fires only when
    the duty key loaded), 'result=included' (publication times - the gaps
    must be >= 30 s), 'result=withdrawn' (must stay 0 - the budget is off).
  - rig client log: bootflow stages (fade_release issued = the contract),
    member_get(owner=mac) census (the flood must be gone: dozens, not
    17k-77k), pb_create census.
  - mac client log: same census (the duty cycle applies to both machines'
    sessions - periodic re-landing churn on BOTH is EXPECTED, see graphics).

## READOUT TRIGGER (required field)
  - result=paced: emitted on every body build inside the 30 s window; the
    trigger = the gate loaded (duty key parsed). NEVER-OBSERVED (first fire
    risk): absence means either the key did not load or no peer body was
    due - distinguished by the included lines and the rig's hang returning.
  - rig bootflow fade_release issued: fired in p2-175's rig (t=128344) -
    read the line from the p2-175 archive as the positive control.
  - included gaps >= 30 s: checkable against p2-178's recorded timeline
    (REPLAYED this session: RE_output/scratch/dutycycle_replay.py - 46 pubs
    -> 8 over the same 225 s span, all gaps >= 30 s, exit 0).

## THE RUN
  1. asserts: server hash 791ffd907cb1636b; client hashes 3cc844c4cdd2fd63
     both; settings echo duty=30000 (grep the file; the startup echo does
     not print it).
  2. Paired Tower, mac first, mac stays put.
  3. RIG lands (or not - that IS the readout). Dwell ~4 min.
  4. If (and only if) the primary passes: the SECONDARY phase, pre-named
     from p2-179's brief - the rig transitions (orbit + re-enter) and we
     take rig_full_dump.sh p2-180-transition for the four-vptr scan. The
     dump is taken during a QUIET phase (the last server line is 'paced',
     not 'included') so the client is mid-landing-stable, not mid-change.
  5. log_archive --label p2-180-duty; logindex all three.

## PRE-NAMED OUTCOMES
  (a) rig lands + paced/included alternation >= 30 s + withdrawn=0 ->
      THE MECHANISM CONFIRMED. Proceed to the secondary phase (transition +
      dump). The receiver question finally gets its measurement.
  (b) rig still hangs, paced lines present, included gaps >= 30 s -> the
      quiet window needs MORE than 30 s. Measure the rig's actual
      region-native -> next-attempt interval from the log, re-run the
      replay with that window, boot again at the larger value.
  (c) no paced lines AND the hang returns -> the duty key did not load
      (settings/parse) - a defect in this boot's own plumbing, void run.
  (d) withdrawn lines appear -> a code defect (the budget must be off in
      the duty regime) - void run, fix before any conclusion.
  (e) rig lands but the PEER ROW never reaches it (no member_get on the
      mac's record at all) -> the pacing starved the row entirely -> the
      window semantics need re-reading (first-publish immediate is asserted
      by the replay; check the live log for the first included).

## GRAPHICS DELTA (U12)
Expected new rendered models: 0 or 1 (a second guardian remains the positive
for the render question, unclaimed by this boot). NEW ARTIFACT, expected and
pre-named: BOTH machines may visibly re-enter (ship animation) every ~30 s -
each paced publication is a composition change, which is the (A)-design's
known cost. It is not a defect; if it blocks play, the follow-up is a bigger
window or the revision-freeze design (noted for later, not this boot).

## CHAIN MARKS (L16)
  L1 paired Tower co-location                     verified-by-execution (20.140)
  L2 the client re-lands on a composition change  verified-by-execution (p2-175:
                                                   zeroed at 110156, re-landed 128344)
  L3 the landing completes ~12-18s after the last change
                                                  verified-by-log (20.307 R2:
                                                  p2-175 issued 1.9s after its burst)
  L4 body cadence starves that window             verified-by-log (20.307 R2: three
                                                   boots, 46-101 bodies, no issue)
  L5 the duty-cycled row (one per 30s) restores the quiet window
                                                  unknown (THIS BOOT - the contract)
  L6 the rig lands with the row sustained         unknown (THIS BOOT)
  L7 a transition produces a receiver-bearing object
                                                  unknown (the secondary phase;
                                                   20.297 outcome (c) stands until
                                                   measured with the dump)
  L8 a peer entity is created / renders           unknown (encoder blocked on the
                                                   outer wire type; 20.53 positive
                                                   control only)

## WIDE NET (user directive)
The suspect chain's decision points, each probed or pre-named:
  - settings load (the duty key parsed): probed by result=paced absence +
    the settings grep assert.
  - gate decision per body: probed by result=paced / result=included lines.
  - the withdrawal machinery: probed by result=withdrawn (must stay 0).
  - client digest: probed by the rig bootflow stages + member_get census.
  - the mac digest: probed by the mac bootflow + its own paced/included lines.
  - the composition change itself: probed by the client's composition zeroed
    stage (existing bootflow line).

## ABANDON OUTCOME (empty-mask #7)
If outcome (b) holds at multiple window sizes (30 s and a re-measured 60 s
both starve the landing), the quiet-window model DIES and this front
abandons the pacing approach: the re-landing would have to be duration-bound
by something other than composition-change quiet, and the front returns to
decoding the client's re-landing state machine (static) rather than pacing
the wire. No further pacing boots after that.

## STATE READERS (empty-mask #1)
  - the row's publication state: DIRECT reader = the server's own
    result=included/paced/withdrawn lines (the emitter logs its decision).
  - the rig's landing state: DIRECT reader = the rig client's bootflow
    stage=fade_release line (the emitter of the state itself).
  - the rig's record engagement: DIRECT reader = the member_get enter lines
    (the hooked function's own args: rec/owner).
  - the client's composition resets: DIRECT reader = the client's
    stage=composition bootflow line.
  No inferred-from-return-code claims; every reader above is the emitter.

## EFFECT CLAIM (empty-mask #5)
Delivery (bodies sent, rows included) is NOT the claim. The pre-named EFFECT:
the rig's bootflow ISSUES fade_release while the row is sustained - i.e., the
client re-enters and holds the world with a duty-cycled peer present. If only
delivery improves (rows paced, rig still loading), the claim is REFUTED and
outcome (b) fires.

## FIX SURFACE: server
The change is server-only (the push path + one settings key). No client
change, so no SERVER-SIDE GAP section is required.

## FRONT: rig-paired-landing (2026-09-05)
Outcome ledger: record at boot close via RE_scripts/boot_outcome.py. Prior
boots on this front: p2-176 (third-branch: hung, cause unknown-at-the-time),
p2-178 (hung), p2-179 (hung, void per input gate) - this boot is the first
with a mechanism-level change, so the ledger's third-branch rule is satisfied
by the MODEL REVIEW being embedded in 20.307's census (the causal assumption
that died: "the hang is pre-existing" - corrected at 20.306 R2).

## OBSERVER BUDGET / CALL FREQUENCY
  - server log lines: n/a (server-side only; included/paced at body cadence).
  - hooks: n/a (no hook changes; the deployed p2-178 clients are untouched).

## HOOK COUNT: unchanged (the p2-178 client build's count; no new hooks this
## build - the server exe carries no hooks). INSTRUMENT LIVENESS: n/a (no
## new literals in any client binary; the server's own paced/included lines
## are the liveness).

## ADVERSARIAL PASS: waived - the mechanism is census-measured (20.307), the
replay is green (dutycycle_replay.py exit 0), and the pre-named tree covers
the gate's own plumbing ((c)/(d)). The one unreviewed assumption: 30 s is
enough quiet on the current stack - outcome (b) is its dedicated detector.

## FALSIFIABLE CLAIM
With the peer row published at most once per 30 s, the rig's bootflow issues
fade_release within 60 s of its second region-native line, while the server
log shows >= 2 included publications with >= 30 s gaps and zero withdrawals.
REFUTED by outcome (b)/(e).

## ABSENCE NEGATIVES
  - zero paced lines + hang returns: the key did not load (outcome (c)) -
    check the settings file parse FIRST, then the deployed exe's strings.
  - zero included lines: the row never published - the gate is miswired or
    havePeer is false (peer_reason lines name it).
  - withdrawn > 0: outcome (d), void.
  - rig lands but zero member_get(owner=mac): outcome (e).

## SETUP (my job; user only launches the games)
  1. Server already deployed + restarted with duty=30000 (verify: settings
     grep + the paced line on the first bodies).
  2. Assert server 791ffd90..., clients 3cc844c4... both.
  3. rig ssh control socket up.

## ADVERSARIAL PASS: the mechanism is census-measured (20.307), the replay is
## green, and the pre-named outcome tree covers the gate's own plumbing
## defects ((c)/(d)). Waived; the one unreviewed assumption: that 30 s is
## enough quiet on the CURRENT stack - outcome (b) is its dedicated detector.

## DO NOT
  - do not read the bootflow verdict before checking paced/included/withdrawn
    (input gates result)
  - do not redeploy or touch the client DLL (it did not change; one variable)
  - do not take the transition dump before the primary passes
  - do not tune the duty window mid-boot; one variable per boot
  - do not launch the server from anywhere but the repo root
  - do not modify the client, in any form, for any reason
