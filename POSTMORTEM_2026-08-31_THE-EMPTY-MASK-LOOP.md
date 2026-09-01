# POSTMORTEM - THE EMPTY-MASK LOOP (2026-08-31)

STATUS: closed postmortem (2026-08-31). Written for a WORKFLOW-FIXING session, not for
the RE lane. Subject: how ~8 boots (p2-136 .. p2-143 v4, 20.212-20.218) were spent on a
front that was never a blocker, and what mechanisms would have stopped it earlier.
Companion record: FINDINGS 20.219 (the boot that closed it) and 20.220 (the static pass
that found the real path). Prior process record: POSTMORTEM_2026-08-30_MY-ERRORS.md.

## THE ONE-LINE SUMMARY

A return code was read as a state, that state was adopted as the front, and every
subsequent boot tested refinements of a cause that had never been measured. The state
was measured once, on 2026-08-31, and was false.

## WHAT WAS BELIEVED vs WHAT WAS TRUE

BELIEVED (STATE, three handoffs, FINDINGS 20.212-20.218):
  "The host client's entity-index free-slot mask is EMPTY at Tower entry every boot;
   that is why peer creation fails; the lane is to get slots into that mask."
TRUE (measured, 20.219):
  The mask holds 145-150 free slots in steady state - exactly the hysteresis midpoint of
  the client's own donate/request logic. With a peer in the Tower the host attempts ZERO
  allocations. The 44 "failed to create" lines were SELF-allocation during load, in a
  brief window before the pool->manager transfer lands. They have no relation to peers.

Cost: p2-136 .. p2-143 v4. One boot (p2-138) produced a real behaviour change. The rest
confirmed that things we built were delivered correctly, then found the outcome unchanged.

## THE NINE MECHANISMS (each is a workflow target, not a person)

### 1. A RETURN CODE WAS READ AS A STATE  *** the root cause ***
`idx_alloc` returning -1 was recorded as "the mask is empty". -1 is the function's
failure value; it is consistent with an empty mask AND with many other causes. Nobody
read the mask until p2-144. Eight boots rested on an unmeasured premise.
FIX: a brief field. For every state a brief asserts, name the instrument that reads that
state DIRECTLY. "Inferred from a return/error code" is not an instrument. If no direct
reader exists, building it is the boot.

### 2. CORRELATION ADOPTED AS MECHANISM, WITH THE CONTROL ALREADY IN HAND
The failure burst appeared near peer arrival in p2-136 and was attributed to the peer.
It fires SOLO. The project ALREADY runs a mandatory solo control boot - but only as a
crash guard; its results were never used to discriminate the failure signature.
FIX: the solo arm is a DISCRIMINATOR, not just a smoke test. Any failure signature must
be checked for presence in the solo arm before it may be attributed to a peer. Add to
boot_verdict.sh: print each failure signature's count per arm, side by side.

### 3. THE DISCONFIRMING CASE WAS RANKED THIRD, REPEATEDLY
20.211 R3 recorded "the rig never attempts peer creation" on 2026-08-30. The joiner is
the case where the alleged blocker (an empty mask) is ABSENT and the outcome is
IDENTICAL. That is the single strongest piece of evidence available against the theory,
and it sat at position 3 in two consecutive handoff hunt lists.
FIX: hunt-order rule. Any recorded case where the alleged cause is absent and the
outcome is unchanged is ranked #1 until discharged. It cannot be outranked by a new
observation.

### 4. NOVELTY BIAS IN HUNT ORDERING
Each handoff ranked the newest observation first: the periodic type-20s, the router-flags
gate, the assignment message. The type-20 lead was justified in writing by "700 is
suspiciously adjacent to our 8/4088/8192 slot arithmetic" - it is not adjacent to any of
them. Numerology outranked a measured control (see #3).
FIX: rank by load-bearing, not recency. A brief's hunt list must state, per item, WHICH
claim it would falsify. Items that falsify nothing go below items that falsify something.

### 5. "ARRIVED AND DECODED" WAS READ AS "DID WHAT WE WANTED"
Six boots proved delivery: type-0 grants reach pool_recv, type-30 reaches its handler,
type-20 routes with routable flags. Delivery was never the question. The type-30
assignment was delivered and decoded perfectly and wrote a token that gates an OUTBOUND
REPORT, not a local fill (20.217 R2 described that function as a "merge"; it is a send).
FIX: a boot whose only outcome is "the message arrived" is not a boot. Delivery proof
must ride in the SAME boot as the effect test, with the effect as the pre-named claim.

### 6. REPEATED THIRD-BRANCH OUTCOMES WERE NOT TREATED AS A MODEL INDICTMENT
20.213 explicitly named the gap: the brief pre-named "hypothesis survives" and
"hypothesis wrong", and the actual outcome was a third branch - "behaviour changed,
outcome didn't". That third branch then recurred in p2-140, 141, 143 v2/v3 and v4. Each
time it was processed as "on to the next lead" rather than "the causal model is wrong".
FIX: a counter. N consecutive third-branch outcomes on one front (suggest N=2) forces a
model review before the next boot may be briefed. Mechanical, not a judgment call.

### 7. EVERY BRIEF'S PRE-NAMED OUTCOMES CONTINUED THE LANE
Every brief in the arc pre-named outcomes of the form "survives -> proceed" / "wrong ->
next lead". None pre-named "-> ABANDON this front". Continuation was structurally
guaranteed regardless of result.
FIX (user directive, 2026-08-31, now in the template): every brief must pre-name an
outcome that ABANDONS the front, and must cast a WIDE NET - probes at every decision
point on the suspect chain, so a boot that kills the lane still points at the next one.
The template's WIDE NET section is this fix; #1 and #6 above are not yet mechanised.

### 8. THE DEFINITIVE INSTRUMENT WAS SPECIFIED AND NEVER BUILT
entity-index-allocation-schema.md line ~418 named it in writing: "the definitive
instrument: a client-side probe on the allocator 0x141711D10 ... reading the +0xC118
popcount at call time." Eight boots ran around that sentence. It was built on 2026-08-31
and closed the front in one run. This is the third instance of the 20.207 R5 pattern
("the answer was already in the repo and I generated new work instead of reading it").
FIX: a brief field - "instruments this front has already specified but not built".
bootstrap_check.sh can grep claims/*.md for "definitive instrument" / "the instrument
that would" and print them unbuilt.

### 9. QUERY ARTEFACTS PUBLISHED AS FINDINGS
On 2026-08-31 a conclusion ("the manager is never wired to a pool") was published from a
`logq | grep -v | head -20` pipeline whose `head` truncated before the counter-evidence.
The data was right; the view could not have shown the refutation. Separately, in the same
session, a bool-in-AL return (`mov al,1`) was read as a 32-bit failure code 0x80000001.
FIX: no conclusion from a truncated view. If a pipeline contains head/tail/limit, the
claim must be re-run without it before it is written down. For return values: a `ret=`
larger than the callee's declared width is a WIDTH question first, not a value.

## THE PATTERN UNDERNEATH ALL NINE

Every one of these is the same shape: a cheap proxy was accepted in place of the
expensive direct measurement, and then the proxy was refined instead of replaced.
-1 stood in for the mask. "Delivered" stood in for "worked". The newest observation stood
in for the most load-bearing one. Recency stood in for relevance.
The lane broke open the moment one direct measurement was taken.

## WHAT WENT RIGHT (keep these)

- The mtrace census printing ZEROS is why "attached but never called" was always
  distinguishable from "never hooked". Several conclusions rest on it.
- verify_hook_rvas.py caught an added-digit RVA again this arc.
- The instrument-carries-its-own-oracle pattern (p2-144's schemakey line printing the
  known type-30 key beside the unknown type-28 key) is new, cheap, and should be standard
  on any probe that reads a value we cannot check by other means.
- Static reads confirmed to the slot: the donate/request hysteresis was read offline
  (low/high/midpoint) and the live mask settled at exactly the predicted midpoint.

## HANDOFF TO THE WORKFLOW SESSION

Mechanised already: WIDE NET + abandon-outcome (brief template).
NOT yet mechanised, in priority order: #1 (direct-reader field), #6 (third-branch
counter), #2 (per-arm failure-signature table in boot_verdict.sh), #8 (unbuilt-instrument
grep in bootstrap_check.sh), #3/#4 (hunt-order rules - JUDGMENT, may resist automation;
consider a brief field that forces the author to name what each hunt item falsifies).
