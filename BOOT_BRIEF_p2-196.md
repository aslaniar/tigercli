# BOOT BRIEF p2-196 - ROW 7: WHY THE CONNECTED RUNG NEVER ADVANCES FOR THE PEER

STATUS: live (2026-09-06). Client be5807eca028ddea, 68 install rows (64 + 4 new).
FRONT: connected-rung

## PURPOSE (what this boot learns, win or lose)

Row 5 closed on 2026-09-06 (the join gate is host-only; the peer is already an
established member via the membership plane). The wall is row 7: the peer's connection
record sits at ladder 4 and establishment needs 5. p2-195's resv_rec, same boot, two
records:
    rec=0 the FORK's connection  s30e8=4 s1dc0=5  mask=0x0020  touch=real
    rec=1 THE RIG's record       s30e8=3 s1dc0=4  mask=0x0000  touch=-1

The advance chain is now decoded end to end (claims/establishment-decode + the pump
disassembly): the receive pump 0x1416D56C0 reads [conn+0x1D18] (THE LADDER) and a
subtype produced by 0x1416E3140's rdx out-param, then at 0x1416D5F0A..F14:

    ladder == 4 EXACTLY  &&  subtype != 8   ->  call 0x1416BCFC0 (THE ADVANCE)

The peer sits at ladder 4, so it PASSES the ladder half. This boot measures which of the
remaining conditions actually fails, and in the same pass answers thread 2's open
question about the participant mask.

WIN: the readout names the failing condition (pump never sees the peer's connection /
subtype == 8 / advance fires but the ladder does not move) and row 7 gets a server-side
target. LOSE: the advance fires for the peer and the ladder still does not reach 5 -
which moves the question inside 0x1416BCFC0's body.

## GRAPHICS DELTA

NONE. Four new observer rows, all read-only; no rendering path is touched. New
rendered-model count: 0. Minimization: three of the four are enter-only with a single
dword read; the fourth (disown) is enter+leave on a rare path.

## FALSIFIABLE CLAIM

THE CLAIM: the connected-rung advance 0x1416BCFC0 is called for the FORK's connection
and NEVER for the peer's, and the disown never clears a bit that was set on the peer's
record (i.e. the peer's participant bit is never set in the first place).

CONTENT NEGATIVE: a rung_adv line whose conn is the peer's connection falsifies the
first half. A disown line with wasset=1 on a record whose ident is the peer's
(0xFF...) falsifies the second and revives 20.277 R2's set-then-disowned reading.

## ABSENCE NEGATIVE (L13: what ZERO lines from each instrument means)

  disown = 0 lines    -> the disown path never runs at all this boot. NOT "the bit was
     never cleared": the probe would also be silent if the hook missed. POSITIVE
     CONTROL: rec=0's mask flickers 0x0000<->0x0020 every boot in resv_rec, so the
     clear DOES run - zero disown lines therefore indicts the instrument first (U13).
  pump_lad = 0 lines  -> the pump was never entered with a readable connection. The
     pump is on the receive path and p2-195 shows heavy receive traffic, so zero here
     is an instrument verdict, not a world verdict.
  rung_adv = 0 lines  -> the advance never fired FOR ANY connection. This is the
     expected-and-informative case only if pump_lad shows the pump running; otherwise
     it is upstream silence.
  evt_sub = 0 lines   -> its out-param logger is budget-gated (24) and shares the
     generic enter budget; a budget_exhausted marker now prints when any budgeted probe
     stops, so silence is distinguishable from exhaustion.
  ALL FOUR = 0        -> suspect the install: verify_hook_rvas TARGETS TABLE and the
     census `attached=1 calls=N` lines are the discriminator.

## CHAIN MARKS (L16)

  L1 fork publishes the peer, both clients land        verified-by-execution (p2-180)
  L2 client builds the peer's record, identity exact   verified-by-log (20.309)
  L3 live hosted session exists                        verified-by-execution (p2-182)
  L4 peer's records enter the candidate list           verified-by-log (p2-182)
  L5 join gate - CLOSED, host-only, peer arrives by
     the membership plane instead                      verified-by-execution (p2-195)
  L6 peer is an established member (3 peers/2 players,
     direct channel)                                   verified-by-execution (p2-193a/b, p2-195)
  L7a peer's record reaches ladder 4                   verified-by-execution (p2-180, p2-195)
  L7b ladder 4 -> 5 requires subtype != 8 at the pump  verified-by-reading (the pump disasm)
  L7c which condition fails for the peer               unknown - THIS BOOT
  L8 guard + receiver object                           verified-by-reading (20.279/20.287)
  L9 entity message encodes                            verified-by-femu (20.302-20.304)
  L10 entity renders and moves                         unknown

## ADVERSARIAL PASS: self (this session) - how this boot could mislead me

  1. THE RECORD INDEX IS NOT THE CONNECTION POINTER. disown logs a record INDEX and
     rung_adv/pump_lad log a connection POINTER; they are different handles for the
     same family. Attribution between them must go through the ident field (disown
     logs it) and resv_rec's per-record idents, NOT by assuming index order.
  2. LADDER 4 IS ALSO THE FORK'S TRANSIENT VALUE. rec=0 passes through 4 on its way to
     5, so a rung_adv line at ladder=4 is not automatically the peer's. Read conn and
     cross it against pump_lad's (conn, ladder) history before attributing.
  3. THE SUBTYPE IS AN OUT-PARAM READ AFTER THE CALL. evt_sub's value is only valid on
     the leave side; the generic out-param logger reads it there, but its budget is
     shared with the enter census - if the line count looks wrong, check the marker
     before concluding anything about the value.

## PRIOR ART (09-05 FAILURE 5)

  q.sh 1D18 / q.sh "connected rung"  -> EMPTY both (the Tier-2 hex false-null; the tool
     returned nothing for 1AEF8 earlier today while grep found 10 hits - do not read
     q.sh silence as absence on this project until that row is fixed).
  /usr/bin/grep -rn --include='*.md' "1D18"  -> establishment-decode.md CLAIM 2 only.
    - CLAIM 2 (VERIFIED, high confidence): the 3->4 site 0x141803F2B is guarded on
      [rsi+0x3040]==3 AND [rsi+0x1D18]==5. VERDICT: STANDS, and this boot's decode
      extends it upstream to what SETS the ladder to 5.
    - "the connected rung is message-fed from the session-plane chain (0x1417E5A10 ->
      pump -> 0x1416D56C0: event type 4, subtype != 8 -> 0x1416BCFC0)". VERDICT:
      STRUCTURE CONFIRMED, ONE CORRECTION - "event type 4" is a misreading. The
      disassembly shows `mov eax,[rbx+0x1D18]` then `cmp eax,4`: the 4 is THE LADDER,
      not an event type. The gate is ladder==4 && subtype!=8.
    - THE MEASURED section: p2-180's (3,4) stall. VERDICT: STANDS and is reproduced
      unchanged in p2-195, so nothing since 09-05 has moved it.
    - Thread 2 (this session, in the same doc): the participant mask's only
      displacement writer is a CLEAR. VERDICT: stands, with its coverage caveat.
  BASE-OFFSET RECONCILIATION (new, and it removes an apparent contradiction): CLAIM 2's
  rsi is base+0xA8+idx*0x41F0, so the guard's [rsi+0x1D18] IS resv_rec's +0x1DC0
  (0xA8+0x1D18) and [rsi+0x3040] IS +0x30E8. The decode and the probe read THE SAME
  FIELDS; the two offset pairs were never in conflict.

## DEAD-END AUDIT (PRIOR ART cites the closed row-5 front)

The join-relay road (p2-181..p2-195) is CLOSED: the connection-layer join is a
host-only message and the receiving client is a peer, so no key/channel/container/value
could pass - and peer presence was already delivered by the membership plane for at
least three boots before it. WHY THIS BOOT IS NOT THAT DEAD END: it touches none of
that machinery. The relay settings are unchanged and irrelevant here; this boot reads
four functions on the establishment path, which is a different plane, and its fix
surface (below) is a message the fork must publish, not a join to re-target.

## STATE READERS (a direct reader per asserted state)

  the peer record's ladder + mask + ident  -> resv_rec (existing: s30e8/s1dc0/mask/ident)
  the mask value the clear operates on     -> disown before= / after= (reads +0x3112
                                              on the record the callee computes)
  whether the cleared bit was ever SET     -> disown wasset= (computed on the line, from
                                              before and the callee's own bit argument)
  the ladder the PUMP sees                 -> pump_lad ladder= ([conn+0x1D18], the
                                              field the gate itself reads)
  the event subtype the gate tests         -> evt_sub's out-param value (0x1416E3140's
                                              rdx, the exact operand of `cmp ecx,8`)
  whether the advance ran                  -> rung_adv conn= + ladder=
  the record family's identity mapping     -> resv_rec ident= (cross-key for all above)

## EFFECT CLAIM (distinct from delivery)

DELIVERY (not under test, already proven): the peer is an established member with a
direct channel and a record at ladder 4.
EFFECT: the connected-rung advance runs for the fork's connection and not for the
peer's. Delivery succeeding while the effect fails IS the expected shape; this boot
names which condition consumes it.

## ABANDON OUTCOME (pre-named)

If rung_adv fires WITH the peer's connection AND the peer's s1dc0 still reads 4
afterwards in resv_rec, then the advance is not what writes the ladder and this whole
chain (pump -> gate -> 0x1416BCFC0) is the wrong mechanism. That ABANDONS the decoded
chain and sends the work to the ladder's own writers via field_xref on +0x1DC0.

## WIDE NET (a probe at every decision point on the suspect chain)

  the pump is entered                 -> pump_lad conn=
  what ladder it sees                 -> pump_lad ladder=
  the subtype it tests                -> evt_sub out-param
  the advance fires                   -> rung_adv conn= ladder=
  the record's state after            -> resv_rec s30e8/s1dc0 (existing)
  the participant mask's history      -> disown before/after/wasset
  the membership view (control)       -> the group_target dumps (existing retail lines)
  instrument silence is explainable   -> budget_exhausted markers on every budgeted probe

## FIX SURFACE: server

Nothing client-side is written; all four probes only read. The expected fix is a
message the fork must publish so the peer's connection receives the event whose subtype
is not 8 - i.e. fork-side work on the session plane, in code we own.

## NEGATIVE TEST (the arm that fails on the bad state, and where it RAN)

  1. THE TABLE-SIZE ARM FIRED FOR REAL: adding four rows without bumping kTargetsSize
     reproduced the 09-05 FAILURE 2 shape (RVA-0 login crash), and hook_targets.py
     REFUSED it - "declares 64 but the initializer has 68 entries ... the installer
     would detour RVA 0". Fixed to 68; re-run PASSES 68/68, 0 bad. That is a gate
     observed failing on the bad state and passing on the good one, this session.
  2. probe_audit arm B FAILED on the new pump_lad signature (transformed ^ raw with no
     zero-guard) and PASSES after the guard was added: rc=1 -> rc=0, 0 findings.
  3. verify_hook_rvas: all four new RVAs resolve to .pdata function STARTS
     (118 checked, 0 bad) - a detour on a non-start installs cleanly and fires never.
  4. No duplicate RVAs introduced (the p2-194a freeze class): hook_targets clean.

## INSTRUMENTS: disown, pump_lad, evt_sub, rung_adv

## INSTRUMENT SOURCES:
  RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks/milestone_trace/milestone_trace_observer.cpp

## INSTRUMENT LIVENESS:
  stage=disown
  stage=pump_lad
  stage=rung_adv
  wasset=%d

## READOUT TRIGGER (the event that makes each emit, cited from a prior log)

  disown:   every call of 0x1417C4810, the mask clear. NEVER-OBSERVED as a hook, but
    its EFFECT is observed every boot: resv_rec shows rec=0's mask flickering
    0x0000<->0x0020 in 20260906_162912_p2-195 and in the p2-190 baseline, which is this
    clear running. Placement proof is static (R3): 0x1417C4810 is the sole
    displacement writer of +0x3112 and its args are edx=bit, r8d=record index, read
    directly from the disassembly.
  pump_lad: every entry of 0x1416D56C0. NEVER-OBSERVED as a hook; the function is on
    the receive path that p2-195 exercises heavily (the join arrives through it).
  evt_sub:  every call of 0x1416E3140 (2 call sites, both inside the pump).
    NEVER-OBSERVED.
  rung_adv: every call of 0x1416BCFC0 (3 call sites). NEVER-OBSERVED - and its absence
    for the peer is precisely the hypothesis.
  ALL FOUR ARE FIRST-FIRE RISK. That is declared here rather than assumed away: the
  census `attached=1 calls=N` line for each row is the liveness discriminator, and
  rec=0's known-live disown is the one guaranteed positive control in the set.

## OBSERVER BUDGET (the event class each budget covers)

  disown   32 emitted lines per BOOT; event class = one mask-clear. Expected count is
           small (5 call sites on the disown path); budget_exhausted marker on stop.
  pump_lad change-gated on (conn, ladder), NOT counted - the event class is a NEW
           (connection, ladder) pair, so a hot pump costs one atomic exchange per call
           and emits only on transitions.
  evt_sub  24 (the generic enter/out-param budget).
  rung_adv 16 per boot; event class = one advance. Marker on stop.

## CALL FREQUENCY (per hook)

  disown   0x17C4810 - RARE. 5 call sites, all on the reservation/disown path.
  pump_lad 0x16D56C0 - RECEIVE-PATH, potentially hot: 2 call sites but on the packet
           pump. MITIGATION: one guarded dword read plus a change gate; no allocation,
           no loop, no accessor call. This is deliberately cheaper per call than
           walk_map's 13 guarded reads, which ships in the build that lands.
  evt_sub  0x16E3140 - same frequency as the pump (2 sites, both inside it); the
           out-param read is the template's existing budgeted path.
  rung_adv 0x16BCFC0 - RARE by construction: it only runs when ladder==4 && subtype!=8.
  NONE of the four is the 35-consumer hot path that required the p2-195 join window.

## HOOK COUNT: 68

  == verify_hook_rvas TARGETS TABLE: 68/68 entries verified, 0 bad (64 + the four new
  rows). No existing row moved; no RVA is duplicated.

## THE READOUT (what I will grep, in order)

  1. INPUT GATE FIRST: both clients land; the rig reaches the tower; the group_target
     dumps show peer #2 established. If the rig never joins, everything below is void.
  2. census `attached=1 calls=N` for disown / pump_lad / evt_sub / rung_adv - liveness
     before interpretation.
  3. `stage=disown` - especially wasset= on any ident=0xFF... record. This answers
     thread 2 outright.
  4. `stage=pump_lad` - is there ever a line whose conn is the peer's connection?
  5. `stage=rung_adv` - which conn values, and at what ladder.
  6. `stage=leave fn=evt_sub ... ret=` / the out-param line - the subtype values seen.
  7. `stage=resv_rec` - the peer's s1dc0 before and after; unchanged at 4 is the
     baseline this boot is trying to explain.
