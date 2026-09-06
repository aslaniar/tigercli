# BOOT_BRIEF_p2-187 — THE LIVE-BLOB MEASUREMENT: THE LOOKUP'S COMPARE, BOTH SIDES LIVE
STATUS: live (2026-09-06).
FRONT: session-lookup-identity

INSTRUMENTS: sess_cmp, join_type0a (pktdump), inst_nonce, join_processor, sess_state

## MODEL REVIEW (REQUIRED - the front carries 2 third-branches: p2-185, p2-186)
THE CAUSAL ASSUMPTION THAT DIES: the static chain assumed the state's
member-entry idB (entry+152) flows into the lookup's live comparison buffer
(sess+0x57C) via the client's membership/apply machinery - verified static
links at every step, but the LIVE path was never observed and my two
predictions about it were wrong twice. THAT assumption is dead: this boot
measures the comparison's two live sides directly instead of predicting
them. The dead prediction is not being patched a third time; the measurement
precedes any further identity change.

## PRIOR ART (required field)
q.sh terms: sess_cmp / 0x141A83C00 / blob / sess+0x57C. Read in full:
connection-layer-join-delivery.md (the decode chain + the copier walk);
p2-185's outcome (the +144 hash divergence, reverted); p2-186's outcome (the
+152 offset hash-VALID - both joins completed - and the lookup still failed:
the live blob is not populated from the state's entry+152 by any named
path). The helper's shape: a ONE-QWORD compare (verified-by-reading this
session, 10 real bytes, whole-instruction Detours-safe).

## PURPOSE (ONE CONTRACT)
Measure the lookup's failing comparison LIVE: every firing of the equality
helper logs BOTH first qwords - the key (what the join carries) and the blob
(what the receiver's session holds) - with a match flag. The diff names the
fix directly; a MATCH during a relayed join would be equally decisive (the
lookup's failure is then downstream).

## THE CHANGE
- server af414e390a97808b: UNCHANGED (the p2-186 identity publishing stays -
  it is hash-valid and correct at the model level).
- clients BOTH: +1 hook (sess_cmp on the equality helper 0x141A83C00,
  Probe::sesscmp, novelty-gated on the (key, blob) pair). 57 -> 58.
  verify_hook_rvas PASS (106 RVAs, 0 bad; the helper is listed NOT-CODE -
  review-not-fail: it sits in a .pdata gap, disassembled linearly this
  session, 10 real bytes, Detours whole-instruction safe).
- SERVER-SIDE GAP: none - the identity is already published (p2-186); the
  live side's writer is what is unobserved, and this boot observes it.

## READOUT TRIGGER (required field)
- stage=sesscmp: NEVER-OBSERVED (new instrument) - its firing IS the
  measurement. The helper is shared (the candidate table uses it too), so
  the novelty gate may also emit on OTHER comparisons during the landing -
  each is a distinct (key, blob) pair, all informative, budget 24.
- pktdump/inst_nonce/resv/sess_state: existing behaviors (p2-184/185/186).

## PRE-NAMED OUTCOMES
  (a) a sesscmp line with key = the relayed join's sessionId AND match=1 ->
      the comparison PASSES; the lookup's failure is DOWNSTREAM (the state
      check or the processor's own gates) - decode those.
  (b) sesscmp shows key = the join's sessionId and blob = something else
      (mismatch) -> the blob's LIVE content is the answer: if blob = 0, the
      live identity is never populated (the writer is the parameters apply);
      if blob = a different non-zero value, the live window holds a
      DIFFERENT identity (the machine's own soid or the local session id) -
      either way the fix is the fork publishing the identity through the
      path that populates THAT field.
  (c) no sesscmp lines with join_type0a firing -> the lookup never reached
      the compare (the walker's per-slot loop skipped or the ctx+0x28 lookup
      failed earlier) -> decode the lookup's skip path.
  (d) sesscmp fires only on NON-join comparisons (the candidate table's
      own) -> the join's lookup never reached the compare - the lookup's
      caller-side gate (state 6..9 etc.) failed first.

## ABANDON OUTCOME (empty-mask #7)
If (d) reproduces with join_type0a firing, the equality helper is not on the
join's lookup path in our environment - the join gate's refusal happens
before it; the road narrows to the gate's own internals with the lookup
retwatch as the next instrument. No retries.

## EFFECT CLAIM (empty-mask #5)
Not a behavior claim. The EFFECT: the first direct, live measurement of both
sides of the comparison that has blocked the join processor since p2-183.

## STATE READERS (empty-mask #1)
- the comparison's both sides: DIRECT = stage=sesscmp (dumped at the helper's
  own entry, the values the compare itself reads).
- the gate's entry: DIRECT = join_type0a enter + pktdump (existing).

## FIX SURFACE: server
No behavior change (instruments only, read-only). SERVER-SIDE GAP: the
identity's live writer is client-internal - until this boot names it, the
fork cannot publish through that path; the measurement decides the fix's
exact surface.

## WIDE NET
joincapture / join admit / join completed (server) / join_relay result=sent /
join_type0a + pktdump / sess_cmp (NEW - the compare itself) /
join_processor / admit / resv / sess_state / bootflow.

## CHAIN MARKS (L16)
  L1-L7 as banked (p2-180..184: landing, transition, identity, candidates,
       OOB delivery, nonce gate)
  L8 the session lookup matches             MEASURED THIS BOOT (both sides)
  L9 the ladder climbs to (4,5)             unknown
  L10 guard/receiver/codec/entity/render    unknown

## OBSERVER BUDGET / CALL FREQUENCY
- sess_cmp: novelty-gated on the (key, blob) pair, budget 24 distinct pairs;
  the helper is shared machinery, so non-join firings are expected and each
  distinct pair emits once.
- everything else: unchanged from p2-184..186.

## HOOK COUNT: 58 (57 + sess_cmp; hook_targets declares=58 initializers=58)
## INSTRUMENT SOURCES: RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks/milestone_trace/milestone_trace_observer.cpp
## INSTRUMENT LIVENESS
the names ("sess_cmp", "inst_nonce", "join_processor", "sess_state") must
appear in BOTH clients' attach lines.

## FALSIFIABLE CLAIM
With relay_peer_join on and both links up: at least ONE stage=sesscmp line
appears on at least ONE machine during the boot (the helper is on the join
lookup's path - measured directly). REFUTED if sess_cmp is absent while
join_type0a fires (the compare is not on the lookup's path -> outcome (d)).

## ABSENCE NEGATIVES (both kinds)
- zero sesscmp with join_type0a firing: the lookup's skip paths ran before
  the compare (outcome (d)) - the retwatch-style lookup hook is the next
  instrument.
- sesscmp lines with key = 0: the candidate table's own comparisons (not the
  join's) - distinguishable by the key's value.

## GRAPHICS DELTA (U12)
Expected new rendered models: 0 (read-only instruments; no behavior change).

## SETUP
  1. Server unchanged (af414e390a97808b running; claims cleared).
  2. Clients deployed BOTH (a3e75d564ed58832; preflight PASS recorded).
  3. rig ssh control socket up.
  4. Both clients land; NO in-game actions.

## ADVERSARIAL PASS: the novelty gates are the proven class (sess_state/pktdump
## both worked first-boot); the helper's gap-hooking is reviewed above; the
## hook set is verifier-passed (106 RVAs, 0 bad).

## DO NOT
  - do not read the machinery lines before join_relay=sent (input gate)
  - do not ship any identity change this boot (measure first - U2)
  - do not launch the server from anywhere but the repo root
  - do not modify the client beyond the declared instruments
