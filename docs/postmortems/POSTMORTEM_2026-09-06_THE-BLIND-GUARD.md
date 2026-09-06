# POSTMORTEM - THE BLIND GUARD: five boots' readouts refused by the instrument's own gate (2026-09-06)

STATUS: closed postmortem (2026-09-06, written during the p2-190c boot). Subject: the
sess_cmp observer chain (p2-187 -> p2-190b) - the instrument that was supposed to measure
"which container does the join gate walk" and never measured the gate at all. Written for
a workflow session; the defect was found by disassembling the COMPARED code, not by any
boot. Companion: connection-layer-join-delivery.md; sibling:
POSTMORTEM_2026-09-01_INSTRUMENTATION.md (this is DEFECT 2's family, one level deeper:
the probe's own GUARD was the filter that hid the subject).

## THE ONE-LINE SUMMARY

Five boots and the project's central instrument never measured the thing it was named
for: the gate's own compare was refused by the probe's pointer-alignment guard, because
the gate's blob pointers are misaligned BY DESIGN - and the probe's silence was then
misread three times as facts about the game.

## THE DEFECT (one predicate, five boots)

emit_sesscmp hooked the equality helper 0x141A83C00 and guarded its dereferences with
`(ptr & 7) != 0 -> return` - "not qword pointers - refuse, never dereference". Sound
advice for wild pointers. But the GATE'S OWN chain (walker 0x14177A0B0 -> per-slot
helper 0x1417944C0 -> equality) compares the key against `[rec+0x57C]` (&7=4) and
`[rec+0x94E]` (&7=6) - the identity blobs are deliberately UNALIGNED fields. So:

- every compare on the gate's chain hit the guard and was dropped WITHOUT A TRACE;
- every sesscmp line ever logged came from the helper's OTHER consumers
  (caller rvas 0x175D0B3/0x17640E3/0x1779C3A - none is the gate's chain; the gate's
  chain would show 0x17944FA/0x1794520, the two call sites inside the helper, absent
  from every census in every boot);
- the probe reported 33 firings a boot while the subject fired - unseen - right past
  its own guard.

The disassembly that exposed this took ten minutes. The alignment fact was in the
project's own decode since 20.319 ("blob at +0x57C or +0x94E") - the instrument's guard
and the decode were never read against each other.

## THE COST (what the silence was spent on)

- p2-187/p2-188b: "the blobs hold the receiving machine's own identity" - derived from
  unattributed pairs; the STATE carried "the gate's slots hold X" as if observed at the
  gate (the instrument-width handoff's warning, which fixed the caller gap and still
  could not see the gate).
- Two value-arming boots (p2-188b arm 1, p2-190b arm 3) were judged by their refusal
  lines - those verdicts STAND (the game refused them; that is the game's own output) -
  but the MECHANISM of each refusal (which blob the walked slots actually held at the
  walk) was never measured, and the per-caller data could not fill the gap because the
  gate chain was guard-blind.
- The p2-189 instrument-fix session (per-caller budgets) was correct work on the wrong
  layer: it fixed the budget drain the flat gate suffered and left the guard intact -
  the refusal-walk triples would have been refused by the guard anyway.

## WHY IT SURVIVED FIVE BOOTS (the failure shape, not the syntax)

1. The guard was inherited "safety" pattern-copying, never re-derived from the hook's
   subject. The 09-03 rule - before a probe's field enters a conclusion, read what
   produces it - was applied to the probe's OUTPUT fields but not to its REFUSAL path.
2. Refusals are silent by construction. A guard that drops a sample is indistinguishable
   from a sample that did not happen. The novelty/budget gates got blamed for every
   missing readout (three fix iterations: flat budget -> triple gate -> per-caller
   budgets); the real filter never got named.
3. The replay gate (replay_trigger.py) replays RECORDED LINES - it can verify a trigger's
   shape over what was logged, and correctly refused nothing here, but it CANNOT replay
   lines the old guard never logged. Its honest-limit is real: a filter's blindness is
   invisible to a replay of its own output.

## WHAT WORKED (the patterns that found it, keep them)

- Disassembling the COMPARED code (the helper's 0x1417944C0..0x141794540 body) and
  reading the probe against it: the two call sites' pointers are provably misaligned
  from the bytes alone. The static read caught what five boots could not.
- The caller-RVA census as an EXPECTATION test: the widening handoff predicted "the
  walker's call site must appear" - its absence across boots was treated as a novelty
  hazard, when it was a proof of the guard's blindness. An expected caller that NEVER
  appears is a placement/feasibility finding, not noise.
- The budget_exhausted marker (added this session) made the later silence EXPLAINABLE -
  it is why this postmortem can separate "budget spent" from "never reached".

## RULES YIELDED (conversion debt; land as ENFORCEMENT rows, not prose)

- R1 (template, lane-brief probe design): a probe that dereferences STRUCT FIELDS checks
  the field's ACTUAL alignment in the struct decode before writing a pointer guard -
  "qword pointer" is an assumption about the field, not about the pointer.
- R2 (rubric, 09-03 asymmetry applied to guards): a probe's reject/refuse path must be
  visible (a first-reject counter or line). A probe that can silently refuse samples
  must be able to SAY how many it refused; a silent refusal is the 09-03 class again.
- R3 (template, replay-gate scope): the replay gate proves the trigger over recorded
  data; for a probe whose subject was never logged, the PLACEMENT proof is static -
  name the call sites / pointer provenance in the brief and verify them in the binary
  (this boot's gate run carries that statement).

## ADDENDUM (2026-09-06, later the same day) - DEFECT 2: THE HASH THAT ERASED EVERY MATCH

The BLIND-GUARD fix shipped a second gate of the same family, inside the same
function: the per-caller novelty signature was `pairSig = mix(keyQ ^ blobQ)`.
`keyQ ^ blobQ` is ZERO whenever the pair MATCHES - so every matching compare
hashed to the same signature as the (0,0) init pair, and the first-seen cache
suppressed EVERY match after each caller's first. The instrument could not
see the one event this front exists to observe. (DEFECT 1's guard refused
the gate's pointers entirely; DEFECT 2's hash hid its matches.)

FOUND HOW: not by a boot - by re-reading the shipped hash against the
call-number gaps in p2-190c's own log. The refusal walk's sequence was
110476, 110477, 110478, [110479 MISSING], 110480 - a suppressed compare whose
value is unknown, at the exact walk whose readout was the front's question.
The user's challenge ("a live game can't take 20 minutes to stamp") forced
the re-derivation; the direct evidence (suppressed-by-hash) was in the code
and the gap pattern, not in any boot.

THE SECOND HIDING MODE (same fix session): even with a correct hash, the
refusal walk of a join whose key the landing already walked (the VERBATIM
relay - the same key twice per boot) was novelty-suppressed into silence,
because its (caller, key, blob) triples were all seen at the landing walk.
The walk-coupled reset fixes this structurally: the join packet's own hook
(join_type0a/pktdump) clears the first-seen caches BEFORE the gate walks
that packet, so the relayed join's walk always emits its COMPLETE compare
set, matches included.

RULES (folding into R1-R3):
- R4 (template, probe design): a novelty signature over XOR of fields has a
  zero-collision exactly on the event of interest whenever the event is
  "fields equal". Hash the FIELDS JOINTLY (rotate one into the other), and
  prove the property on a synthetic arm: (k,k) must not alias (0,0).
- R5 (template, probe design): a probe whose readout is ONE EVENT's compare
  set gates its novelty PER EVENT, not per boot - reset the seen-set on the
  event's own arrival hook, not on boot-wide state.
- The meta-rule, restated from DEFECT 1: both defects were introduced by
  instrument fixes shipped the same day they were needed. The 09-05 rule -
  a change ships with its own negative test - applies to probe gates: the
  collision arm (match vs (0,0)) was testable in one line and was not run.

## ADDENDUM 2 (2026-09-06, end of session) - DEFECT 3: THE ENTER/LEAVE ASYMMETRY ON A SHARED LOOKUP

The walker (0x14177A0B0) got an ENTER hook (walk_map, p2-189) and never a LEAVE
probe. Its return value - the found slot pointer, or 0 on a complete miss - is
the join gate's OWN lookup decision, and it was never logged across the entire
arc. Meanwhile the join gate's FOUND-path (after the walker returns) was never
decoded either: it contains a SECOND gate the project's decode did not carry -
`[slot+0x1AEF8]` must be in {6,7,8,9} (the session-state window, 6 = LIVE
HOSTED), else the SAME "unknown session" refusal text. p2-193a/b proved the
lookup MATCHES (key=forkSession vs blob=forkSession, match=1, twice) while
join_processor stayed at calls=0 - the two facts that forced this decode.

HOW IT WAS MISSED (three stacked causes, all named):
1. The enter/leave asymmetry: the leave-probe CLASS existed all along
   (retwatch/retidx/sessstate are leave probes - p2-184 built it), but the
   walker only ever got an ENTER hook. A lookup's OUTCOME is on leave.
2. The gate's found-path was never read line-by-line. 20.319 decoded the
   walker and the version gate; the five instructions between the match and
   the processor carried an entire second check, unread since 20.319.
3. The session read (sessstate) and the gate's state field were assumed to be
   the same field without checking offsets - sessstate's "state=6" was read as
   the gate's +0x1AEF8. The producer-read rule (09-03) applies to instrument
   SUBJECTS too: st2=6 came from a different function's read, not the gate's.

AND THE SESSION'S OWN BLIND SPOT, owned: when asked to verify the found-path
statically (Q3, p2-192), this session answered "nothing between the match and
the processor" from a disassembly ALREADY PRINTED in the same transcript that
contained the state-window lines. That is the 09-03 class at its purest - the
verification was asserted from the summary, not the instructions. The user's
"how did we miss this" is what surfaced it.

RULES (R6/R7, folding into the probe-design rules):
- R6 (template): a LOOKUP function gets BOTH hooks or neither - the enter line
  (the key asked) and the leave line (the decision returned). A shared lookup
  whose consumers disagree in meaning (the rich walk's match vs the gate's own
  miss) cannot be read from enter alone.
- R7 (rubric, producer-read applied to CALLER code): a gate's follow-up check
  between the lookup and the consumer is part of the lookup's contract; decode
  the caller's post-lookup instructions before declaring the path clean. The
  summary-in-the-transcript is not the disasm.

INSTRUMENT SHIPPED FOR IT: the walk_leave leave-probe (0x14177A0B0, target
count 64->65): every walker return logs (ret slot ptr | 0=MISS, the slot's
bound id +0x1C7C0, the slot's gate-state +0x1AEF8, outcome=MISS /
FOUND-LIVE / FOUND-STATE-OUT), reset per join packet.

## ADDENDUM 3 (2026-09-06, final) - DEFECTS 4 AND 5: THE INSTALL AND THE HOT PATH

DEFECT 4: the walk_leave leave-probe shipped as a SECOND target row on the SAME
RVA as walk_map (0x14177A0B0). Dual detours on one function start are an
unsupported install: the rig's client froze mid-log-line (t=198282, the
walker's hot path) in a loading loop, and the frozen process held the DLL
hostage against the backup restore. Restored from .bak_p2d7_20260906_144204;
the fix routes the leave-probe onto the walk_map row's LEAVE dispatch - ONE
detour, enter+leave.

DEFECT 5 (the same hour): the state reads added to emit_walkmap's HOT PATH (6
extra guarded reads x hundreds of walker calls) stalled the MAC's landing
transition (initial_slice_set, log stops t=154712, never reached the fork).
Fixed by moving the state reads BEHIND the change gate - read only when a line
emits (d5ed2ae3f12e42fb).

GATE GAP + RULES: (1) verify_hook_rvas/hook_targets verified the table
arithmetic (65/65 "PASS") but did not flag TWO ROWS WITH THE SAME RVA - the
duplicate-RVA reject is tooling debt. (2) R8: hot-path probes pay the original
read count - new reads go behind the gate, not into the loop. Both defects
shared one shape with DEFECTS 1-3: the change shipped without its negative
test (the duplicate-RVA case was expressible; the hot-path cost was
computable) - and the sessions's instrument fixes, stacked fast under boot
pressure, each broke a different invariant of the same function. The lesson
is not "be careful": it is that INSTRUMENT CHANGES NEED THE SAME GATES AS
SHIPPED CODE - the negative test, the cost check, the install check - and
this session ran four instrument iterations before the first one that
respected all of them simultaneously (d5ed2ae3f12e42fb).

## LEDGER

- Defect introduced: p2-187 (the observer's original guard, copied from the 09-05-era
  pointer-sanity pattern).
- Cost: ~5 boots of blind gate-side readouts (p2-187, p2-188, p2-188b, p2-189, p2-190b)
  + two value-arm boots whose value choice was made on unattributed pairs.
- Found: 2026-09-06, by disassembling 0x1417944C0 (D-026; the alignment fix shipped as
  603a909fbc4b73c6; BOOT_BRIEF_p2-190c.md is the first brief that can name the gate's
  own caller rvas in its readout).
- ADDENDUM defect introduced: the p2-190c per-caller fix itself (the XOR-of-fields
  novelty hash); found ~2 hours later by the user's challenge + the call-gap
  re-derivation (no boot spent); shipped fixed as 8252f1dad6e8a0c1 (the hash fix +
  the walk-coupled reset on the join packet's hook).
