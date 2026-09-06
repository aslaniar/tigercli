# BOOT_BRIEF_p2-190f — THE COMPLETE WALK READOUT (the hash fix + the walk-coupled reset)
STATUS: live (2026-09-06).
FRONT: session-lookup-identity

ONE CONTRACT: the relayed join's walk emits its COMPLETE per-slot compare
set - matches and misses - for the first time. Two client-side instrument
fixes (8252f1da + 9cd3f23b, both shipped today after the BLIND-GUARD
addendum findings); NO server change, NO value change (the relay stays
verbatim). This boot's readout is the complete walked container at the
moment the relayed join's lookup decides - which either shows the match
(row 5 falls) or names the exact slot contents the fork must satisfy.

## MODEL REVIEW (REQUIRED)
The front's dead assumptions, carried: the idB-via-membership assumption
(p2-187 brief); the caller-union reading (fixed p2-189); the alignment guard
(fixed p2-190c); and NOW the XOR-of-fields novelty hash (fixed this build -
it erased every MATCH by collision with the (0,0) signature) plus the
novelty-per-boot shape that silenced the verbatim relay's walk (its triples
were all seen at the landing walk). The "stamp timing" hypothesis is
RETRACTED as primary: p2-190e (mac spawned) still refused with an
unchanged blob set, and a live game does not run minute-scale stamps -
the slot contents are determined by events we can now see per walk.

## PRIOR ART (required field)
q.sh terms: caller_rva=0x17944FA / 0x1794520 / sesscmp / walk_map / mix.
Verdicts carried (closed, not re-tested): forkSession-verbatim REFUSED
(p2-187, landing-1, p2-190d, p2-190e - the game's own output); machine id
REFUSED (p2-188b); joinId REFUSED (p2-190b/c); the alignment guard defect
+ the hash defect - POSTMORTEM_2026-09-06_THE-BLIND-GUARD.md (+ ADDENDUM).

## PURPOSE (ONE CONTRACT)
Observe the relayed join's gate walk COMPLETELY: one sesscmp line per
slot-compare, matches included, at the walk itself. Decisive both ways:
a MATCH -> the lookup passes -> join_processor -> row 5 falls; a complete
miss-set names the walked blobs exactly, and the fork publishes to THAT
instead of iterating value arms.

## THE CHANGE
- clients BOTH 9cd3f23befe88ccf:
  1. pairSig = mix_u64(keyQ) ^ rotl(blobQ,1) - a matching pair no longer
     aliases the (0,0) signature (the synthetic collision arm v2 PASS;
     the v1 arm caught rotl(key,1)^blob aliasing for key=all-ones and was
     REJECTED pre-deploy - the 09-05 negative-test rule applied to the
     probe gate itself).
  2. THE WALK-COUPLED RESET: the join packet's own hook (join_type0a/
     pktdump, unconditional at dispatch) clears the sesscmp first-seen
     caches BEFORE the gate walks the packet - the relayed join's walk
     emits its full compare set regardless of what the landing walked.
- server UNCHANGED 7164333c337cd674; relay verbatim
  (relay_join_target_identity=false, backup .bak_p2-190c_arm3on).

## READOUT TRIGGER (required field)
- the relayed join's walk's sesscmp lines: the pktdump line (one per join
  packet, prior-log cite p2-183/189/190c) now PRECEDES a full compare set -
  NEVER-COMPLETE-BEFORE (this is the contract's first complete readout).
- join_processor enter on the relayed join: NEVER-OBSERVED (the pass).
- the refusal line (decoded reversed dwords): prior-log cite p2-190d/e.
- budget_exhausted: absence expected (32/caller with per-walk resets).

## PRE-NAMED OUTCOMES
  (a) A MATCH line at the walk and NO refusal -> row 5 FALLS: join_processor
      runs; watch reserve/admit/adoption (rows 6-8 fire on their own).
  (b) Complete miss-set + refusal -> the walked blobs at refusal are named
      IN FULL (no suppression): compare against the p2-190c boot's four-blob
      set; whatever the fork publishes must equal one of them or the binding
      decode is the next front.
  (c) Complete miss-set + NO refusal + no join_processor -> the lookup
      matched a LATER check that then refused - the refusal's reason path
      becomes the front (re-derive, do not re-arm values).
  (d) ZERO sesscmp lines at the walk despite the pktdump firing -> the
      walker does not route compares through the helper in this environment
      -> the compare is inline/obfuscated -> static decode of the walker's
      compare sites is the next move (no more instrument iterations).

## ABANDON OUTCOME (empty-mask #7)
If this boot's complete readout shows a full miss-set with all four blobs
being the recipient's own identity forms (self/asif/0/forkSession-family)
across TWO boots with different mac states, the walked container cannot
match any join we can currently name - the road narrows to decoding what
BINDS+BLOBS the container's slots actually carry (the binder/cof chain's
value sources) before any further join-side attempt.

## EFFECT CLAIM (empty-mask #5)
The first complete walk readout. Not a behavior claim - the EFFECT is the
end of value-arm iteration: every future boot's walk readout is complete
by construction.

## STATE READERS (empty-mask #1)
- the walk's compares: DIRECT = sesscmp lines between the pktdump line and
  the refusal/pass (the reset guarantees completeness).
- the game's verdict: the refusal line (greppable) or its absence.
- the walked map: DIRECT = walk_map (change-gated per (key,binds)).

## FIX SURFACE: server
No server change this boot. SERVER-SIDE GAP: none for this contract (the
relay is verbatim; the readout is the deliverable). The NEXT server change,
if the readout names a publishable blob, is the retarget value.

## WIDE NET
joincapture / join_relay / join_type0a + pktdump / inst_nonce / walk_map /
sesscmp (all callers) / join_processor / join_reserve / admit / resv /
sess_state / add_candidates / bootflow / the refusal line / stage=identity.

## INPUT GATE (hard rule)
Do not read walk lines before the server's join_relay result=sent peers=1.

## OBSERVER BUDGET / CALL FREQUENCY
- sesscmp: 32/caller x 12 slots, seen-sets RESET on every join packet's
  arrival (the walk-coupled reset) - the relayed join's walk always emits
  fresh; the global hard bound 384.
- every other target: unchanged.

## HOOK COUNT: 64 (unchanged; verify_hook_rvas PASS 112 RVAs 0 bad)
## INSTRUMENT SOURCES: RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks/milestone_trace/milestone_trace_observer.cpp
## INSTRUMENT LIVENESS
- "budget_exhausted" / "stage=walk_map" literals verified IN the deployed
  binaries (9cd3f23befe88ccf, BOTH machines; preflight PASS 13/0/0).
- the walk-coupled reset's effect is the contract itself: the relayed
  join's walk MUST emit its compare set this boot (its absence = outcome
  (d), loud).

## FALSIFIABLE CLAIM
With the verbatim relay and both links up: between the pktdump line and the
refusal/pass, at least 3 sesscmp lines emit on the mac naming (caller,
key, blob) for the relayed join's walk - the complete set. REFUTED if the
pktdump fires and the window holds ZERO sesscmp lines (the reset or the
hash is still broken -> outcome (d)).

## ABSENCE NEGATIVES (both kinds)
- zero sesscmp in the pktdump->refusal window with pktdump firing: the
  instrument is still hiding (outcome (d)) - fix before any further boot.
- zero walk_map with the relay firing: the walker not on the relayed join's
  path (the p2-187 (d) class).

## GRAPHICS DELTA (U12)
None. The mac's spawn state is NOT a gate for this readout anymore (the
reset makes the walk verbose regardless); spawn if possible for the
strongest state, but a black-screen mac does not void this boot.

## SETUP
- server 7164333c337cd674 RUNNING (verbatim relay; settings
  .bak_p2-190c_arm3on; claims=0).
- clients BOTH 9cd3f23befe88ccf (mac bak_p2d7_20260906_133657-era; rig
  bak_p2d7_20260906_133707); preflight PASS 13/0/0.
- rollback: client .bak_p2d7_*; settings .bak_p2-190c_arm3on.
- ARming order (unchanged, proven): mac alone first -> link bound -> rig
  second -> the relay fires verbatim.

## CHAIN MARKS (L16)
- the relay delivers verbatim: VERIFIED-BY-EXECUTION (p2-190d/e).
- the refusal names the relayed key: VERIFIED-BY-EXECUTION (every boot).
- the gate chain's compares exist and are hookable: VERIFIED-BY-READING
  (the helper disasm; the two call sites' pointers are misaligned by
  design - the alignment fix).
- the prior reads were incomplete: VERIFIED-BY-READING (the hash collision
  + the novelty suppression - THE BLIND-GUARD postmortem ADDENDUM).
- this boot proves: the COMPLETE walk compare set. NOT YET (this boot).

## DEAD-END AUDIT (the closed findings this brief cites as premises, not roads)
- the verbatim relay (forkSession key): REFUSED in 4 boots (p2-187, landing-1, p2-190d, p2-190e) - the game's own output. This boot does NOT re-test the value as a fix; it tests the READOUT of the refusing walk. The value re-test becomes meaningful only when the readout shows what the slots hold.
- arm 1 (machine id): refuted p2-188b by the refusal; arm 3 (joinId): refuted p2-190b/c by the direct compare. Not re-armed.
- the "stamp timing" hypothesis: RETRACTED this session (p2-190e: spawned mac, unchanged blob set, refused) - cited as retracted, not re-walked.
- the alignment guard + the hash collision: both instrument defects (THE BLIND-GUARD postmortem + ADDENDUM) - fixed, cited as the reason the prior reads were incomplete. The escape this boot buys: a readout that cannot be incomplete by construction.

## ADVERSARIAL PASS: ses_f882ff186ffeIGc0ofsy65C5k1
The hash fix carries its own negative test (the synthetic collision arm,
which FAILED the first candidate and forced the v2 mix - the 09-05 rule
applied to a probe gate). The walk-coupled reset's negative: the p2-190d/e
logs (silent refusal walks) replay through the OLD logic as zero-fires in
the relayed window - the NEW logic must emit; that is the boot's own
falsifiable claim. Hook table unchanged (64/64, verifier PASS). No server
change to prove.

## DO NOT
- change the retarget value this boot (verbatim stays - the readout is the
  point, and the fork-session key is the one with boots of refusal history).
- iterate instrument shapes beyond this boot's readout (two defects found
  and fixed; the third strike would be a process failure, not an unlucky
  one - U7).
- read walk lines before join_relay result=sent.
- sleep in shell chains (background + notify).
