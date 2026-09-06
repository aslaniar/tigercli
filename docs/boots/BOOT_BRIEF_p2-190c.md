# BOOT_BRIEF_p2-190c — THE GATE'S OWN COMPARE, MEASURED (the alignment-guard fix)
STATUS: live (2026-09-06).
FRONT: session-lookup-identity

ONE CONTRACT: the gate's OWN per-slot compare becomes measurable. p2-190b
proved the retarget machinery end-to-end and refuted arm 3 (the joinId); the
refusal-walk's blob readout was still hidden - and the root cause is now a
STATIC FACT: emit_sesscmp's pointer guard required (ptr & 7)==0, but the
gate's own blob pointers are [rec+0x57C] (&7=4) and [rec+0x94E] (&7=6) -
every compare on the gate's chain (helper 0x1417944C0 -> equality
0x141A83C00, call sites 0x1417944F5/0x14179451B -> caller rvas
0x17944FA/0x1794520) was silently refused in EVERY boot. The walked container
has never been observed at the compare. This boot fixes the guard and reads
it. NO server change, NO value change (arm 3 stays the walk trigger).

## MODEL REVIEW (REQUIRED - the front's dead assumptions)
BANKED (p2-187 brief): the state's idB does not flow into the live blob via
the membership machinery. BANKED (p2-190b close): the retarget machinery is
wire-proven; only the VALUE was wrong. THIS BOOT's replaced assumption: that
the sess_cmp instrument measured the gate's compare at all - it did not; it
measured the helper's OTHER consumers (0x175D0B3/0x17640E3/0x1779C3A, none of
which is the gate's chain: the gate's compares would carry caller rvas
0x17944FA/0x1794520, absent from every census). Every "the walked slots hold
X" conclusion stood on walk_map binds + binder stack args, never on the
compare itself.

## PRIOR ART (required field)
q.sh terms: 0x1417944C0 / 0x17944FA / sesscmp / walk_map / 0x141A83C00.
Read: connection-layer-join-delivery.md section 3 (the gate walk decode);
p2-190b capture (the retargeted walk + the refusal naming the retarget value);
HANDOFF_2026-09-06_INSTRUMENT-WIDTH.md (the instrument-width gaps); the
helper's disasm (banked this session: entry rcx=id rdx=key; resolve
0x14179AF00; bit4 -> +0x57C first; else +0x94E). Verdicts cited as closed
premises: arm 1 refuted (p2-188b), arm 3 refuted (p2-190b), connect-family
pure transport (20.320) - the DEAD-END AUDIT of p2-190 stands; this boot
re-tests none of them.

## PURPOSE (ONE CONTRACT)
At the relayed join's refusal walk: read the walked records' COMPARED BLOBS
per slot - (key, blobA=[rec+0x57C], blobB=[rec+0x94E], match) per slot with
caller rvas 0x17944FA/0x1794520. The blob set IS the answer: it names the
retarget arm the gate can actually match (arm 5 = the measured value), or
proves arm 2, or shows the slots empty at refusal time.

## THE CHANGE
- clients BOTH 603a909fbc4b73c6: emit_sesscmp's pointer guard accepts any
  user-space pointer (was qword-aligned-only - the defect); per-caller budget
  16->32, seen-cache 8->16, total bound 192->384. No new hooks (64/64;
  verify_hook_rvas PASS 112 RVAs 0 bad).
- server UNCHANGED 7164333c337cd674; relay_join_target_identity=true (arm 3's
  value drives the same walk - its refusal is the measurement window).

## READOUT TRIGGER (required field)
- caller_rva=0x17944FA / 0x1794520 sesscmp lines: NEVER-OBSERVED (the guard
  refused their pointers in every prior boot; the call sites are verified in
  the static disasm - the placement proof). Their FIRST appearance is the
  contract's event.
- the refusal line + walk_map at the walk: PRIOR-LOG CITE p2-190b (fires on
  every retargeted refusal).
- budget_exhausted: marker semantics unchanged (absence expected).

## PRE-NAMED OUTCOMES
  (a) The refusal walk's triples show a walked slot whose blob == the
      retargeted key (match=1) yet the refusal still fired -> the match is
      real but a LATER gate check refuses -> decode the post-compare path
      (the refusal's own reason path), not another value arm.
  (b) The walked blobs hold a CONSISTENT identity form != the joinId (e.g.
      the member key 0xE4DDDA60E08629C3-family or the machine id) -> arm 5 =
      that form, retarget value := the recipient's blob value; one value
      change, machinery unchanged.
  (c) The walked blobs are ALL the recipient's OWN identity forms and none
      matches any peer-naming form -> the binding never carries the peer ->
      the binding publisher (the copier walk open site) is the fix surface.
  (d) ZERO 0x17944FA/0x1794520 lines across the whole boot -> the helper's
      equality call sites are not reached in our environment (the resolve
      path short-circuits earlier) -> the gate decode gets re-derived; no
      value arm, no instrument retry.

## ABANDON OUTCOME (empty-mask #7)
If the 0x17944FA/0x1794520 lines appear but show all-zero blobs or blobs
identical to the recipient's own identity across BOTH boots' landing and
refusal walks, the walked records' identity window is a static self-stamp:
the front narrows to what populates it (the copier walk 0x1416E2350 decode,
no further boots until it is decoded).

## EFFECT CLAIM (empty-mask #5)
Not a behavior claim. The EFFECT: the walked container's blob values at the
refusal, measured directly for the first time - the input that decides the
next retarget arm without another value-arming guess.

## STATE READERS (empty-mask #1)
- the gate's per-slot compares: DIRECT = sesscmp caller_rva=0x17944FA/
  0x1794520 (key + blobA/blobB + match).
- the walked slot map at refusal: DIRECT = walk_map (change-gated per key).
- the game's own verdict: the refusal line (greppable).

## FIX SURFACE: server
No server change this boot (the retarget stays arm 3 as the walk trigger).
SERVER-SIDE GAP: none - no wire change is needed for this contract; the
NEXT fix (the retarget value) is server-side and is decided by this boot's
readout.

## WIDE NET
joincapture / join_relay_target retarget= / join_type0a / pktdump /
inst_nonce / walk_map / sesscmp (ALL callers incl. the gate chain) /
join_processor / join_reserve / admit / resv / sess_state / add_candidates /
bootflow / the refusal line / stage=identity (the member-key rows).

## INPUT GATE (hard rule)
Do not read gate-side lines before join_relay_target result=sent
retarget=<non-zero> for the relayed join.

## OBSERVER BUDGET / CALL FREQUENCY
- sesscmp: 32 triples/caller (12 slots), seen-cache 16/caller, hard bound
  384. The gate chain's callers (0x17944FA/0x1794520) are NEW caller slots -
  their budgets start clean. The p2-189 replay acceptance of the per-caller
  shape still passes on recorded data; the misaligned-pointer path could not
  be replayed (the old guard never logged it) - its placement proof is the
  static call-site verification, stated honestly.
- every other target: unchanged from p2-189.

## HOOK COUNT: 64 (unchanged; hook_targets declares=64 initializers=64)
## INSTRUMENT SOURCES: RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks/milestone_trace/milestone_trace_observer.cpp
## INSTRUMENT LIVENESS
- "sess_cmp" attach lines in BOTH clients; the literals budget_exhausted /
  stage=walk_map verified IN the deployed binaries (deploy_client_dll.sh).
- NEW liveness mark: caller_rva=0x17944FA or 0x1794520 appearing = the fix
  is live AND the gate chain reached the equality. ABSENT across the whole
  boot = pre-named outcome (d).

## FALSIFIABLE CLAIM
With the relay retargeting (arm 3) and the mac's link bound: at the relayed
join's refusal walk, at least ONE sesscmp line with caller_rva=0x17944FA or
0x1794520 appears on the mac. REFUTED if walk_map fires (the walk happened)
while both gate-chain caller rvas stay absent through the whole refusal
window - then the compare does not route through the equality helper
(outcome (d)).

## ABSENCE NEGATIVES (both kinds)
- zero gate-chain sesscmp lines with the refusal firing: outcome (d) - the
  helper's compare sites are not on the executed path; re-derive the gate.
- zero walk_map with the refusal firing: the walker did not run (the p2-187
  (d) class) - re-derive the lookup path.

## GRAPHICS DELTA (U12)
None. The mac's subclass-swap spawn worked at p2-190b (no render-black);
if it recurs, the readout is taken from the mac's LOG (its instruments fire
regardless of rendering) and the boot is not voided.

## SETUP
- server: 7164333c337cd674 RUNNING since the 11:53 restart (initialize ok,
  ports bound, claims=0); settings relay_join_target_identity=true.
- clients: BOTH deployed 603a909fbc4b73c6 (mac bak_p2d7_20260906_124740; rig
  bak_p2d7_20260906_124758); preflight PASS 13/0/0 (manifest recorded).
- rollback: client .bak_p2d7_20260906_*; server .bak_p2d6_20260906_111620;
  settings .bak_p2-190_arm3.

## CHAIN MARKS (L16)
- retarget rides the wire to the recipient: VERIFIED-BY-EXECUTION (p2-190b).
- the refusal names the retargeted value: VERIFIED-BY-EXECUTION (p2-190b).
- the gate walks the retargeted key: VERIFIED-BY-EXECUTION (p2-190b walk_map).
- the gate's OWN compares were never instrumented on any prior boot (guard
  code + helper disasm + caller census): VERIFIED-BY-READING
  (this session; caller rvas 0x17944FA/0x1794520 absent from every census).
- this boot proves: the walked blobs at the refusal. NOT YET (this boot).

## INSTRUMENTS:
  "budget_exhausted"
  "stage=walk_map"

## ADVERSARIAL PASS: ses_f882ff186ffeIGc0ofsy65C5k1
The fix is one predicate change verified against the disasm (the two call
sites' pointers are provably misaligned - 0x57C&7=4, 0x94E&7=6). The
replay-acceptance ran on recorded data (fires>0, per-caller shape holds);
its known limit (the never-logged misaligned firings cannot be replayed) is
stated in the brief, and the static placement proof substitutes. No new hook
targets; the hook table is unchanged (64/64). The negative test for the fix
is the boot itself: the old build's logs lack 0x17944FA lines - the new
build's must have them (pre-named, outcome (d) if not).

## DO NOT
- change the retarget value this boot (arm 3 stays as the walk trigger).
- spend a boot on any value arm not named by this boot's readout.
- re-decode the connect-family handlers or the parameters road (closed).
- read gate-side lines before join_relay_target result=sent.
- sleep in shell chains.
