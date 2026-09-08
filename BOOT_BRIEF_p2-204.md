# BOOT BRIEF p2-204 - THE VERIFIED-CORRECT TYPE-51 ECHO + THE FULL LIVE STACK

STATUS: prepared 2026-09-07 (post 20.329 + the p2-203 confounder postmortem +
lane #4's FALSIFY-THE-FRONT). Server-only; clients stay be5807eca028ddea on BOTH
machines; HOOK COUNT 0. NO CONTROL BOOT: the p2-202/p2-203 archives ARE the
baseline (the mechanical census diff compares against them - 20.297 R2 input
gate: withdrawals/pushes actually sent, on the same client builds).

front: bubble-startup

## PURPOSE (what this boot learns, win or lose)

p2-203 delivered the type-51 echo 4x but was CONFOUNDED: the identity capture
was keyed by account slot, both machines' early ads landed on slot 0, and the
rig's push echoed the mac's token. This boot ships the keying fix -
capture keyed by the "steamid:<digits>" member id, push loaded by the JOIN's
wire memberKey (the only machine-truthful name the push has) - plus the
boot-end dump check that measures whether the echo was byte-right at all.
ALL LIVE LEVERS RUN (user directive: no control boot): bubble-startup echo,
external-body entity send (delivery proven p2-197, consumption silent p2-198-203),
entity-index allocation + assignment, world-population static baseline (S2-0,
carrier 7 - a SECOND entity-delivery carrier on the same entity system).
Win: ANY new client line past the p2-203 census; the ent_recv instance census
going 0 -> >0 (boot-end dump); a verified byte-match between the sent echo and
the client's own identity row. Lose (pre-named): verified-correct echo + full
stack + silence = the type-51 apply half is inert (lane #4 already says it
cannot flip the gate bytes: FUN_140B928D0 = ring-push/telemetry recorder) and
row 8 concentrates on the VMP job-gate byte [unmixed+0xCD5] - which lane #4
proved is client-internal-only. The boot stays DECISION-GRADE under every
branch: the dump check resolves the echo question by measurement.

## GRAPHICS DELTA

Zero new rendered models expected. Server-only (the keying fix + log lines +
settings). Clients unchanged (be5807eca028ddea both). No client hooks.

## FALSIFIABLE CLAIM

1. KEYING FIX (fixture-proven pre-ship): with captures stored per steamid
   digits and pushes loaded per the join's memberKey, NO push can ever return
   another machine's token. Fixture (RE_output/map/fixtures/
   identity_keying_20260907.py) ran on the RECORDED p2-203 log: OLD keying
   wrong-attributes 2 pushes (rig@213781 got the mac's token, mac@289923 got
   the rig's); NEW keying wrong-attributes = 0. PASS.
2. Every type-51 push logs `lookup_key=0x<memberKey> result=stored|no_identity`
   with the SENT echo hex; every capture logs `key=0x<digits> account=N
   machine=0x<id>`. The digit<->memberKey pairing is MEASURED this boot, not
   assumed (the two namespaces have no proven formula - 20.329 + the p2-203
   matrix).
3. CONTENT NEGATIVE: if EVERY push shows result=no_identity AND the capture
   lines show key=0x<digits>, the digit<->memberKey equivalence is refuted for
   this session's join form and the matrix in the log names the pair - a
   measured iteration, not an instrument failure (the readout distinguishes).

## EFFECT CLAIM (distinct from delivery)

DELIVERY: the type-51 frame rides the proven svc9 notification path.
EFFECT (pre-named, not claimed): the client decodes (femu-proven W8), the
validator's memcmp passes iff echo == the client's own DAT_1426BDCC8 row-2
window (the dump check), and the apply half (FUN_140B928D0) runs - lane #4:
it records ring/telemetry state only; it CANNOT flip AF1/AF2/AF3 or
[unmixed+0xCD5]. Downstream movement (entity lines, receive-block
construction) is the win, not the expectation.

## ABSENCE NEGATIVE (L13)

If the client shows no new line past the p2-203 census AND the dump check
proves the echo was byte-right: the apply half is verified inert for our
state - row 8 = the VMP job-gate, client-internal-only (lane #4 verdict),
and the project's next question is architectural (which fork-side lever CAN
reach the entity system - or whether the receive blocks are gated on a
client state we must trigger another way). If the echo was WRONG (dump
mismatch): the keying/matrix arm - the boot's data names the digit<->memberKey
pair and the next fix is one line.

## CHAIN MARKS (L16)

- the type-51 wire form ................... verified-by-emu (W8: femu-validated, every validator window)
- the identity capture (descriptor steamid) verified-by-log (p2-203: both machines' live tokens; the raw dumps carry the 0x56 form)
- the keying fix .......................... verified-by-replay (fixture on the p2-203 log: wrongs 2 -> 0)
- the echo-readout tool ................... verified-by-dump (identity_dumpcheck.py: positive control on dump_p2146 matched the rig's row at 0x7FF7593BDD38, the lane-6g pre-annotation)
- the push frame path ..................... verified-by-execution (p2-203: delivered; p2-197/199: external+queue-event paths ack-verified)
- the row-2 identity layout ............... verified-by-dump (type54-and-receiver-gate.md CLAIM 6g: stride 0x70, window +0x02..+0x57, version 06 @+0x55)

## ADVERSARIAL PASS: self - four ways this boot could mislead me

1. THE JOIN'S WIRE MEMBERKEY FORM: the activity memberKey carries TWO forms
   per machine (real account key 0xE4DD/0x846C AND the per-boot machine id
   0x8629/0xD022 - both observed as activity memberKeys in p2-203, t=184947/
   213840/294942/308086). Whichever form the join request carries, the push
   logs lookup_key and the capture stores only under digits - so a form
   mismatch = no_identity + a measured pair, never a wrong echo.
2. THE RIG'S TIMING FACT (p2-203 measured): the rig's first advertisement
   arrived at t=289601, AFTER its first join (t=213779). Expect the rig's
   FIRST-join push to fail closed (result=no_identity, PRE-NAMED - that is a
   correct outcome of the fix, not a failure); the rig's SECOND burst (its
   re-join to ...0003-style session) is the rig arm, and the mac's first
   burst is the earliest arm (mac ads precede its joins in every archive).
3. THE DUMP COULD COME TOO LATE (p2-203: clients left the tower before the
   dump). THE DUMP TRIGGER IS THIS BOOT'S OPERATOR INSTRUCTION: capture the
   mac client's full dump AS SOON AS both clients are in-world and the push
   lines are visible (~60-90s after joins), NOT at end of session. Rig-side
   dump optional (the row check needs one client; the mac is the primary
   arm).
4. THE FULL STACK CHANGES THE CENSUS BASELINE: world-population + type-30 +
   type-51 + external bodies add server-side byte volume vs p2-203. The
   census diff is CLIENT-line mechanical shape (logq shape census) - the
   client-side line set, not byte counts; server-side deltas are attributed
   per family by their own log lines (index_allocation push / assignment /
   bubble_startup push / world pop push).

## PRIOR ART (09-05 FAILURE 5 - q.sh each central term)

- q.sh "bubble_startup | type-51": type51-bubble-startup-spec.md W1-W8 (closed
  wire map) + 20.328 R3/R4 + 20.329 (the confounded boot) - none closed the
  keying question; the front is streak 1 confounded, not 2 failed.
- q.sh "identity capture | memberKey": 20.319 (the two identity forms),
  20.90 (asif_ relabel), the p2-203 matrix (this session's measurement).
- q.sh "receiver | job-gate": lane #4's claims 6f/6g (the VMP boundary
  [unmixed+0xCD5], the apply half = telemetry recorder, DAT_1426BDCC8 row 2
  layout) - type54-and-receiver-gate.md.
- the fixture + identity_dumpcheck results (this session, both PASS on
  recorded/dump data).

## DEAD-END AUDIT

- Account-slot keying: MEASURED broken (p2-203 + the fixture: 2 wrong
  echoes) - replaced by digits/memberKey keying; not re-armed.
- view/type-9/grant arms: closed by measurement (20.326/20.327/20.324) -
  their settings stay OFF this boot (entity_index_grant=false,
  activity_start_host_push=false, activity_view_initiate=false).
- The relay/retarget/ladder family (rows 5-7): closed (20.195/20.196/20.321);
  no relay settings changed.

## STATE READERS (a direct reader per asserted state)

- "the identity was captured" -> `ev=identity stage=capture result=stored key=0x<digits> account=N machine=0x<id>`.
- "the push went out with the right identity" -> `stage=bubble_startup push ... lookup_key=0x<memberKey> result=stored bytes=443 echo=<hex>`.
- "the push had no identity" -> `stage=bubble_startup push ... result=no_identity` (fail-closed, pre-named arms).
- "the echo was byte-right" -> `python3 RE_scripts/identity_dumpcheck.py --log <archive server log> --dump <mac full dump>` (MATCHES).
- "the client moved" -> ANY new client line past the p2-203 archive's shape census (logq --shape --ev diff).
- "the receiver opened" -> ent_recv instance census > 0 in the same boot-end dump (dump_search on the 4 ent vtables, 20.328's method).

## WIDE NET (probes at every decision point)

All existing instruments (HOOK COUNT 0): the capture lines, the push lines,
the client census diff vs the p2-203 archive, the ent/mgr/pool instruments,
boot_verdict's both-machine comparison, the row-2 dump readout. No client
hooks - the boot's decisiveness comes from the dump + the log matrix.

## FIX SURFACE: server (the entire surface, one rebuild)

1. activity_identity_store.{h,cpp}: keyed by u64 (digits/memberKey) instead
   of AccountKey - the p2-203 cross-attribution is structurally impossible.
2. matchmaking_route.cpp capture: parses "steamid:<digits>", stores under the
   digits, logs key/account/machine; parse failure fails closed (logged).
3. activity_message_push.{h,cpp}: the type-51 push loads by the JOIN's wire
   memberKey (activity.entitySlotMutation.memberKey); logs lookup_key +
   result + the sent echo hex (the derived-lines rule: what was SENT).
4. append_join_notifications no longer takes accountKey (unused).
5. settings (this boot, user directive): entity_index_assignment=true,
   world_population=true; bubble_startup/external_body/allocation already on.
NO SERVER-SIDE GAP: the wire items this boot sends ARE the handshakes under
test (type-51 echo + the two entity carriers); the client renders peers on
server input alone, which is the whole premise (THE CLIENT IS NEVER MODIFIED).

## ABANDON OUTCOME (pre-named)

- activity_bubble_startup=false: no type-51 anywhere; the burst returns to
  the p2-203-minus-echo shape. 
- entity_index_assignment=false / world_population=false: the two new
  carriers drop out; the burst returns to the p2-203 shape. All flips are
  settings-only (backup .bak_p2-204_pre_full); the rebuild stays deployed
  (the keying fix + log lines are the permanent part).

## NEGATIVE TEST (the arm that fails on the bad state, and where it RAN)

1. THE KEYING (the p2-203 defect): fixture identity_keying_20260907.py PASS
   on the recorded p2-203 log - OLD conflates (2 wrong echoes), NEW cannot
   (0). This is the negative test for THIS boot's fix, on pre-boot data.
2. THE READOUT TOOL: identity_dumpcheck.py positive control on dump_p2146 -
   the rig's row read at the lane-6g address and the synthetic echo MATCHED
   byte-exact. A wrong address or window would have failed this arm.
3. THE WIRE FORM: W8 femu-validated (prior session, unchanged encoder).
4. THE BOOT'S OWN NEGATIVE: if all pushes are no_identity while captures
   store under digits - the digit<->memberKey equivalence is refuted and the
   matrix is measured (the log names both sides per machine). Pre-named, not
   a surprise.

## MODEL REVIEW (required: front history + the lane verdict)

Front bubble-startup streak = 1 (p2-203 CONFOUNDED - the pre-named adversarial
item fired; no third-branch). THE DEAD ASSUMPTION NAMED (this session):
"the account slot can attribute a client" - REFUTED by the p2-203 matrix and
the fixture (both machines' early ads on one slot). THE LANE VERDICT
ACCEPTED: lane #4 FALSIFY-THE-FRONT - no wire message can construct the
receive blocks (the only VMP gate is [unmixed+0xCD5], client-internal); the
type-51 apply half is a telemetry recorder. CONSEQUENCE: this boot's win
condition is the VERIFIED-CORRECT ECHO (the p2-203 gap) + any client
movement; its pre-named lose arm is "echo right + silence" = the row-8
question moves to architecture (which client state the fork can trigger that
the gate depends on), with the echo question CLOSED by measurement either
way. No further type-51 boot without a model review after this one.