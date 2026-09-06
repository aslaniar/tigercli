# BOOT BRIEF p2-195 - THE CONFIRMATION BOOT: the gate's second check, measured at the refusal walk

STATUS: live (2026-09-06). Client 44c400b985d60c7a deployed BOTH machines, preflight PASS.
FRONT: session-lookup-identity

## PURPOSE (what this boot learns, win or lose)

Row 5's wall was NAMED statically on 2026-09-06 with no boot (claims
connection-layer-join-delivery.md sections 11-12): the join gate matches the relayed
join's key against a walked slot's identity blob, and then REFUSES on its second check,
`[found_slot+0x1AEF8]` must be in 6..9. The matched slot is slot5 (0x4631748, bind 2 -
the session carrying the fork's identity), and walk_map read that slot at state 2 then
4, never 6, in three separate runs, while the client's OWN two sessions sit at 6.

That is an INFERENCE, not a measurement: the states were read ~2 minutes before the
gate's walk, because walk_map's change gate hashes key^slots^binds and (since the
p2-194b hot-path fix) reads states only when a line is already emitting - so a STATE
change cannot trigger a line. This boot converts the inference into a measurement.

WIN: outcome=FOUND-STATE-OUT with state=4 -> the front reduces to one server-side
question (what drives a session slot 4 -> 6) and every other row-5 lead stays closed.
LOSE: outcome=FOUND-LIVE -> section 12 is wrong, the state really is in 6..9, and the
refusal comes from deeper than the decode reaches; the next decode is 0x1417806C0's own
body. Either way the boot ends with row 5's mechanism named, not guessed.

## GRAPHICS DELTA

NONE. No rendering-path change ships. The client delta vs the last landing build is
entirely inside the milestone_trace observer: a thread-local window counter, a leave
probe that now returns immediately outside that window, and a change-gate bypass inside
it. New rendered-model count: 0. Minimization: the probe does strictly LESS work per
walker call than 572ca7c2fc02ada3, the build that lands.

## FALSIFIABLE CLAIM

Delivery contract under test (unchanged, already proven, NOT the subject): the fork
relays the peer's join verbatim on the ENGINE association; the gate walks it and its
lookup MATCHES.

THE CLAIM: on the relayed join, the walker returns a NON-NULL slot whose
`[+0x1AEF8]` is 4 (outside the gate's 6..9 window), and that slot's `[+0x1C7C0]`
bound-session id is 2.

CONTENT NEGATIVE: a walk_leave line whose outcome is FOUND-LIVE (state in 6..9), or
whose bind is not 2, falsifies section 12's slot mapping. A line with state=4 but
bind != 2 falsifies the compare-to-slot ordering while leaving the state verdict intact.

## ABSENCE NEGATIVE (L13: what ZERO instrument lines means)

Zero walk_leave lines does NOT mean "the walker did not return". Ranked:
  1. the join never arrived (check FIRST - the input gate): join_type0a's census
     `calls=` stays 0, and the server's join_relay line is absent or not result=sent.
     This is the modal negative: in 20260906_145158/145248/145403 the mac's
     join_type0a sat at calls=0 all boot.
  2. the window never opened: join_type0a enter fires but the probe is not installed -
     contradicted by preflight (64/64 install rows) and the deployed literals.
  3. budget: impossible to confuse with silence now - the probe emits
     `result=budget_exhausted` before it stops (T3.1).
Zero walk_map lines inside the window would mean the container/key guards rejected -
those emit `result=reject reason=<container|key|slots>` once per container, so that
case is named rather than silent.

## CHAIN MARKS (L16)

  L1 fork publishes the peer, both clients land          verified-by-execution (p2-180)
  L2 client builds the peer's record, identity exact     verified-by-log (20.309)
  L3 live hosted session exists                          verified-by-execution (p2-182)
  L4 peer's records enter the candidate list             verified-by-log (p2-182)
  L5a relay rides the ENGINE association                 verified-by-execution (p2-192a)
  L5b the gate's lookup MATCHES on the relayed join      verified-by-execution (p2-193a/b)
  L5c the gate has exactly two conditions, no third      verified-by-reading (claims 11.1)
  L5d the matched slot is slot5, state 4 not 6           assumed (claims 12 - THIS BOOT)
  L6 reserve -> admit -> adoption                        verified-by-reading (20.108)
  L7 ladder to connected (4,5)                           verified-by-reading
  L8 guard + receiver object                             verified-by-reading (20.279)
  L9 entity message encodes                              verified-by-femu (20.303/20.304)
  L10 entity renders and moves                           unknown

## ADVERSARIAL PASS: self (this session) - three ways this boot could mislead me

  1. THE SLOT MAP COULD HAVE MOVED. binds {0,-1,1,-1,-1,2} were measured in earlier
     runs; if the container re-binds before the gate's walk, "bind=2" may not name the
     fork's session this boot. MITIGATION: walk_leave logs bind AND the window-forced
     walk_map line names all six slots+binds+states at the same call, so the map is
     re-established in the same boot rather than carried over.
  2. A NESTED WALK COULD BE ATTRIBUTED TO THE GATE. The window is a depth counter, so
     anything the gate CALLS is inside it. The processor 0x1417806C0 also walks. But
     the processor only runs if the gate passes, so if it refuses there is exactly one
     walk; if it passes, `depth=` distinguishes them and the front is over anyway.
  3. I COULD READ A LANDING WALK AS THE GATE'S. Not possible by construction now: the
     probe emits ONLY inside join_type0a's own call, on the same thread. This is the
     defect that produced the p2-193b misreading, closed by design rather than by care.

## PRIOR ART (09-05 FAILURE 5)

  q.sh 1AEF8            -> EMPTY (the known Tier-2 false-null on hex addresses; the
                           tool's silence is a tool fact, not a world fact - T1.1)
  q.sh "session state"  -> EMPTY (same tool; re-run via /usr/bin/grep below)
  /usr/bin/grep -rn --include='*.md' -i 1aef8  -> 10 hits, all in FINDINGS_2026-08-25:
    - 20.109: "State dword at +0x1AEF8 (6..9 = live)" - the field was decoded a week
      before this front opened. VERDICT: the decode is SOUND and reused here.
    - line 4984 / 10134 / 10167: the gate's own `mov ecx,[rax+0x1AEF8]; add ecx,-6;
      cmp ecx,3; ja` range check, already transcribed. VERDICT: my section 11.1
      re-derivation AGREES instruction-for-instruction; nothing new is claimed there.
    - 20.184 RESULT 3: the stage field's writers are 0x14178CD97's cluster, driven by
      0x140C05F80, which "TRIES STAGES 0/1, 2/3, 4/5 ... THE CLIENT CYCLES STAGES 0..5
      ONLY", and it names as its own OPEN item (2) "what sets THAT stage to 6..9".
      VERDICT: STRONGEST prior art. It independently predicts exactly what this boot
      expects to measure - a session parked below 6 - and it means the follow-on decode
      already has a starting address rather than a blank page.
    - 20.185: "THE STAGE IS 2 ... the fix is CLIENT-SIDE STAGING POPULATION (WE OWN THE
      CLIENT)". RETRACTED - see DEAD-END AUDIT.

## DEAD-END AUDIT (required: PRIOR ART cites retracted work)

20.185's conclusion and the HANDOFF_2026-08-29_STAGE-TRAY lane built on it were
RETRACTED at 20.191/20.192 (premise false: NULL is the apply's normal third argument),
and its proposed fix - writing the client's staging slot - is now forbidden outright by
the governing constraint (THE CLIENT IS NEVER MODIFIED; client-side writes into game
data are admissible only as a throwaway diagnostic).

WHY THIS BOOT IS NOT THAT DEAD END: it writes nothing into game memory and proposes no
client-side fix. It READS two dwords the gate itself reads, on the gate's own call. The
follow-on work it points to is explicitly SERVER-side (what must the fork send to drive
the session's state), which is the opposite of 20.185's client-side staging premise.
20.184's factual half (the writer cluster, the 0..5 cycling) was never retracted and is
carried forward; only 20.185's fix direction is dead.

Note an honest tension to resolve in the follow-on, NOT here: 20.184 says states 6..9
belong to "a DIFFERENT object family" from the 0..5 cycling one. My measurement shows
slot0/slot2 at 6 and slot5 at 4 in the SAME walked container, so one family holds both.
20.184's framing needs refining; its addresses stand.

## STATE READERS (a direct reader per asserted state)

  the walker's returned slot            -> walk_leave `ret=` (the leave hook on
                                           0x14177A0B0, reading rax directly)
  the matched slot's gate-state         -> walk_leave `state=` (safe_read of
                                           [ret+0x1AEF8], the gate's own field/offset)
  the matched slot's bound session id   -> walk_leave `bind=` ([ret+0x1C7C0])
  all six slots' states at the walk     -> walk_map `st0..st5=`, window-forced so the
                                           change gate cannot suppress the walk
  the gate was entered at all           -> join_type0a census `calls=` + `stage=enter`
  the join actually arrived             -> pktdump `key16=` + the server's join_relay
  the game's own verdict                -> the retail line "received message for an
                                           unknown session ... sending back a refusal"

## EFFECT CLAIM (distinct from delivery)

DELIVERY (already proven, not under test): the relayed join reaches the gate on the
engine channel and its key matches a walked slot.
EFFECT: the gate's refusal is attributable to the STATE window, not the lookup - i.e.
a walk_leave line with a non-null ret and a state outside 6..9, in the same call whose
sesscmp shows match=1. Delivery succeeding while the effect fails is the expected and
already-observed shape; this boot names WHICH check consumed it.

## ABANDON OUTCOME (pre-named)

If walk_leave reports outcome=FOUND-LIVE (state in 6..9) AND join_processor still shows
calls=0, then both of the gate's decoded conditions passed and the processor still did
not run - which means the gate function I decoded is not the function refusing, and the
whole "connection-layer join gate" framing of row 5 is wrong. That ABANDONS the current
front and sends the work back to attribution: which function emits the refusal text
(the retail line's site=312), reached from where.

## WIDE NET (a probe at every decision point on the suspect chain)

  the join arrives          -> server join_relay result/channel + client pktdump
  the gate is entered       -> join_type0a stage=enter + census calls=
  condition 1: version      -> inst_nonce enter/leave (ret=0xA4F8 == pass)
  the walk happens          -> walk_map container= + the window-forced map line
  each compare              -> sesscmp (caller_rva, key, blob, match), reset per packet
  condition 2: the lookup   -> walk_leave ret= (MISS vs a slot)
  condition 3: the state    -> walk_leave state= + outcome=
  the consumer              -> join_processor census calls= (hooked at 0x1417806C0)
  the game's own verdict    -> the retail refusal line
  the probe's own silence   -> result=budget_exhausted / result=reject reason=

## FIX SURFACE: server

Nothing client-side is proposed or written. The instrument only READS. The eventual fix
is fork-side: drive the forkSession-named session's slot into the 6..9 window by sending
what the client's own sessions receive on their way to 6.

## NEGATIVE TEST (the arm that fails on the bad state, and where it RAN)

  1. probe_audit arm D (budget markers) FAILED on the pre-fix source and PASSES after:
     ran, rc=1 with 3 findings naming emit_walkleave/emit_pktdump/emit_sessstate, then
     rc=0 / "PASS (111 hook files, 0 finding(s))" after the markers landed.
  2. The change introduces NO new probe-audit finding: ran the audit against HEAD's
     version of the observer in a copied hook tree ($JOB/hooks_baseline) and diffed the
     finding sets - IDENTICAL. That is the "did I make it worse" arm, and it ran.
  3. duplicate-RVA reject: FAILS on the pre-waiver source (2 PROBLEM rows), PASSES with
     the DUAL-OK citations - ran in hook_targets.py and verify_hook_rvas.py
     (TARGETS TABLE 64/64, 0 bad).
  4. The landing arm CANNOT be run offline and is this boot's first test: the mac must
     reach the tower on 44c400b985d60c7a. Pre-named honestly rather than assumed.

## INSTRUMENTS: walk_leave, walk_map

## INSTRUMENT SOURCES:
  RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks/milestone_trace/milestone_trace_observer.cpp

## INSTRUMENT LIVENESS:
  stage=walk_leave
  result=budget_exhausted
  outcome=%s
  window=%u

## READOUT TRIGGER (the event that makes each emit, cited from a prior log)

  walk_leave: every return of the walker 0x14177A0B0 while the join window is open.
    The walker's return trigger EMITTED in prior logs - RE_output/logs/20260906_145158
    (8 lines), 20260906_145248 (10), 20260906_145403 (13) - so the hook and its
    dispatch are proven to fire. NEW AND NEVER-OBSERVED: the window gating itself, and
    therefore a walk_leave line attributed to the gate's own call. First-fire risk is
    confined to the arming, whose placement is proven STATICALLY instead (R3): the gate
    0x1416E0460 calls the walker at 0x1416E04AC, inside its own body, and join_type0a
    hooks RVA 0x16E0460 - the same function.
  walk_map: every walker entry; emits on a changed (key, slots, binds) fingerprint OR,
    now, unconditionally inside the join window. EMITTED in prior logs -
    20260906_144232 t=107520/107804 and 20260906_145403 t=134343/134637.

## OBSERVER BUDGET (the event class each budget covers)

  walk_leave: 24 emitted lines and 256 armed calls PER JOIN PACKET, not per boot - the
    counters reset when the window opens. The event class is ONE join packet's walk;
    the expected count is 1. (p2-192's defect was exactly the opposite: cumulative
    per-boot counters spent by the landing's noise before the relayed join arrived.)
  walk_map: change-gated per boot, plus every walk inside a join window.

## CALL FREQUENCY (per hook)

  walk_map / walk_leave (0x14177A0B0): HOT - 35 consumers in the connection-layer
    receive region, hundreds of calls per landing. This is why the leave side is
    window-gated: outside the gate's own call it costs one thread-local read and a
    return, which is strictly less than the proven-landing build 572ca7c2 pays.
  join_type0a (0x16E0460): RARE - exactly one call per received join (measured:
    calls=1 in p2-193a/b, calls=0 when no join arrives).

## HOOK COUNT: 64

  == verify_hook_rvas TARGETS TABLE: 64/64 entries verified, 0 bad. No hook was added
  or moved by this change; the leave probe rides the walk_map row's existing dispatch
  (ONE detour, enter+leave - the p2-194a dual-detour freeze is why).

## MODEL REVIEW (required: trailing third-branch streak on this front)

boot_outcome records p2-194a and p2-194b as consecutive third-branches - two boots in a
row that measured nothing because MY instrument broke the client. That is a model
indictment, so the assumption gets named rather than the lead re-rolled.

THE DEAD ASSUMPTION: that the readout row 5 needed could only be bought with a boot.

Both third-branches were spent building an instrument to answer "MISS or FOUND?" - and
the answer was already on disk. The p2-193a/b logs contain the gate's whole call, with
its four compares and the match, between join_type0a's enter and its leave. What was
missing was not data but the DECODE that makes the data legible: the walker's loop
order, the helper's `cmp ecx,-1` early-out, and the fact that a bound slot spends one
compare at +0x57C and at most one at +0x94E. Ten minutes of disassembly mapped the
compares to slots and named slot5. Two boots were spent buying what reading produced
for free - and the same shape appears in the BLIND-GUARD postmortem ("the static read
caught what five boots could not") and in the WRONG-QUESTION postmortem.

THE SECOND DEAD ASSUMPTION, more specific: that "st2=6" was evidence about the refusal
walk. It never was. walk_map's change gate hashes key^slots^binds, and after p2-194b
the states are read only when a line is ALREADY emitting - so a state change cannot
trigger a line, and every st= value ever logged is the state at some OTHER field's
change. The instrument could not, by construction, report what it was being read for.
Nobody checked the producer before trusting the field, which is the 09-03 rule verbatim.

WHAT CHANGES BECAUSE OF THIS REVIEW: (a) this boot is a CONFIRMATION with a pre-named
expected value, not an exploration - if it disagrees, section 12 is retracted, not
patched; (b) the follow-on question (4 -> 6) goes to STATIC decode first, with 20.184's
addresses as the starting point, and only reaches a boot when reading is exhausted;
(c) the instrument was rebuilt so its cost outside the measured event is lower than the
build that lands, because two of the last four boots died of instrument cost.

## THE READOUT (what I will grep, in order)

  1. INPUT GATE FIRST: server `join_relay` result=sent channel=engine; client pktdump
     `key16=`; join_type0a census `calls=1`. If any is absent the rest is void.
  2. `stage=walk_leave` - expect ONE line, `outcome=FOUND-STATE-OUT state=4 bind=2`.
  3. `stage=walk_map ... window=1` - all six slots with FRESH states at the same call.
  4. `stage=sesscmp` inside the window - the four compares, match=1 on the fourth.
  5. join_processor census `calls=` - expect 0 (and if not, row 5 has fallen).
  6. the retail refusal line - the game's own verdict, decoded (its session field
     renders as two reversed dword groups).
