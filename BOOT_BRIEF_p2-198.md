# BOOT BRIEF p2-198 - THE ALLOCATION PUSH, TURNED ON: type 20 meets its handler

STATUS: prepared 2026-09-07 early (post-ingress-arc). Front: allocation-dispatch
(row 6b). Server-only change (the svc8 body dump) + settings.

## PURPOSE (what this boot learns, win or lose)

Whether the client's type-20 (allocate_entity_indices) applier - PROVEN present
in the 15-slot table (slot 10's get-type returns 20; the handler objects are
static, all 15 slots populated in dump_p2146) - APPLYs the fork's type-20 push
when the push is finally sent (entity_index_allocation has been FALSE in every
recent boot; p2-140/141 sent an older encoder's body and reached the schema
decode without downstream effects). Win: the schema decode validates, the
entity-manager init runs (branch B, distributed pool), and the client's
downstream behavior changes (mask/manager probes, the index request surfacing,
possibly the view establishment). Lose: the schema decode rejects the fork's
body (the femu validation lane answers this BEFORE the boot when it can) - and
the failing check names the encoder fix.

## GRAPHICS DELTA

Zero new rendered models expected. No client change. If the chain completes
far down (view -> entities), a peer model MAY appear - not claimed by this boot.

## FALSIFIABLE CLAIM

With entity_index_allocation=true, the fork pushes one type-20 notification per
join (schema key 0x80809445 body: BLOCK A zero-filled + BLOCK B one participant
row, memberKey low-32 = the joiner, base 0, freeSlots = the joiner's lease);
the client's applier walker 0x140E0F000 matches slot 10 (type 20) and the apply
runs - observable as downstream effects in the client's own instrumented probes
(mgr_init/mgr_fill/mgr_sync, idx_alloc, the 'player_broadcast' creation
outcomes) that differ from the p2-196/p2-197 baselines. CONTENT NEGATIVE: with
the gate off (every recent boot), the same push does not exist and the client's
type-20 applier never matches - the p2-197 archive is the negative arm.

## ABSENCE NEGATIVE (L13: what ZERO instrument lines means)

If the fork logs stage=push type=20 (sent) and the client shows NO downstream
difference (mgr/idx_alloc probes identical to p2-197, player_broadcast still
failing at the same rate): either (a) the applier's apply declined (the
vtable-slot stubs at slots 1-3 return false - the apply may be gated on
something the push lacks), or (b) the schema decode rejected the body
(validation 0x1404D6530), or (c) the walker never saw the message (the object's
type byte at the walker differed from 20 - the ingress construction question).
The svc8 upstream dump (this boot's lane 1) separates (c)-class effects: if the
client's downstream behavior includes NEW upstream traffic (a tag-0x14 index
request as type 20 upstream, or a NEW reliable-queue id), the applier RAN.

## CHAIN MARKS (L16)

- fork push exists: append_entity_index_allocation_notification, gated ....... verified-by-reading (activity_message_push.cpp:126)
- the applier table: 15 polymorphic slots, static, ALL populated .............. verified-by-execution (dump_p2146 slot read: 15 objects, vtables 0x1C26E28 family)
- slot 10 handles type 20 ..................................................... verified-by-execution (vtable slot0 = mov eax,0x14; ret at 0x141B80ED0)
- NO slot handles type 21 (the grant) ......................................... verified-by-execution (all 15 get-type constants enumerated: 123,124,9,27,160,161,100,6,8,301,20,28,150,47,51)
- the walker matches [msg u16 type] vs handler get-type, stride 8, 15 slots ... verified-by-reading (0x140E0F094-0x140E0F0AF)
- the fork's type-20 body shape: schema 0x80809445 ............................ verified-by-reading (the encoder) + femu validation lane (this session)
- the p2-140/141 precedent: a type-20 body reached the schema decode .......... verified-by-log (claims E/F)

## ADVERSARIAL PASS: self (this session) - three ways this boot could mislead me

1. The applier might apply the body and the DOWNSTREAM chain still not complete
   (the manager init branch B needs the session-widEPool object state) - the
   readout must distinguish "the applier ran" from "the chain completed"; the
   mgr/idx_alloc probes + any NEW upstream traffic do that.
2. The svc8 dump changes the fork's timing (bigger log lines) - debug level
   only, no wire change; the fork's push bytes are unaffected.
3. The client's 'player_broadcast' failure rate could drop for a reason
   unrelated to the push (timing) - the p2-196/197 baselines are the control;
   compare rates, not presence.

## PRIOR ART (09-05 FAILURE 5)

- sgrep 141FBCB60: sobject-carrier CLAIM 3.3 ("the 15-table's registered
  question stays open - INFERRED"); this boot's slot read ANSWERS it: all 15
  populated, types enumerated, 20 present, 21 absent. The inference is resolved.
- sgrep entity_index_allocation: the fork's gate exists, built 20.212/20.213,
  default off; p2-140/141 (v1/v2 encoder) precedent in claims E/F.
- sgrep 1404D92A0 (the schema decode): claims E/F/I - reached by a type-20 body
  before; validation pass 0x1404D6530 the suspected rejector.
- q.sh verdicts: hex-term false-null known (night handoff); sgrep used.

## DEAD-END AUDIT (required: PRIOR ART cites retracted work)

- The type-21 GRANT (claims J/N: "reaches no mask"; p2-142's grant weaseled the
  login once): NOT REOPENED - this boot keeps entity_index_grant=false; the
  no-slot-for-21 enumeration explains the old finding mechanically.
- The idx_alloc/row-7b framing (RETRACTED 20.321): this boot's readout USES
  idx_alloc's probe as a downstream indicator only; no verdict rests on the
  retracted causal chain.
- CLAIM O / svc21: untouched.

## STATE READERS (a direct reader per asserted state)

- "the push left" -> the fork's own stage=push type=20 lines (existing).
- "the applier matched" -> the client's downstream probes differ from baseline
  (mgr_* / idx_alloc / player_broadcast rate) - the deployed client build's
  existing instruments; no new hooks.
- "the client asks" -> svc8 upstream dump lines (this boot's lane 1) + the
  reliable-queue delivered-id census.
- "the view happened" -> stage=view result=bound (the fork's existing line).
- "the external body is consumed" -> stage=tail lines + the client's receive
  line (from p2-197's instrument set, still deployed).

## EFFECT CLAIM (distinct from delivery)

DELIVERY: the type-20 push reaches the applier and applies. EFFECT (pre-named,
not claimed): the client's entity-index pool fills, the creation failures stop,
the view establishes, entities render. Any prefix of that chain is progress and
names the next lane; none is claimed by this boot.

## ABANDON OUTCOME (pre-named)

entity_index_allocation back to false + activity_upstream_dump per preference:
the join burst returns byte-identical to the pre-20.213 shape (the gate's own
contract). The svc8 dump is debug-level and independently revertible.

## WIDE NET (a probe at every decision point on the suspect chain)

- fork TX: stage=push type=20 (existing) + stage=index_grant NOT expected (off).
- fork RX: stage=message result=accept type=N payload=... (lane 1) - every
  upstream type, including any NEW type the client emits downstream.
- fork group: stage=message result=ok id=N (the reliable-queue census, existing).
- client: mgr_* / idx_alloc / player_broadcast / ent_* probes (existing hooks)
  + its own log lines; stage=view / stage=tail on the fork.

## FIX SURFACE: server

Server only: activity_message_route.cpp (the svc8 dump), gameplay settings
(the dump key). The client is untouched (be5807eca028ddea stays). No
SERVER-SIDE GAP section needed - the server-side gap (the never-sent type-20)
is what this boot fills.

## NEGATIVE TEST (the arm that fails on the bad state, and where it RAN)

1. THE SVC8-DUMP CHANGE, gate-off arm: with activity_upstream_dump=false the
   accept path emits the EXACT pre-change line shape (no payload= field). Where
   it ran: replay over RE_output/logs/20260906_172618_p2-197 - every
   stage=message result=accept line in that archive is the gate-off shape, and
   the rebuilt binary's gate-off branch is the same snprintf minus the loop
   (verified-by-reading the diff: the dump block is behind the gate's else).
   The malformed-input arm: service::parse_request rejects before any dump
   (the rc=1 path logs result=skip reason=parse, no payload access) - ran in
   the fork's existing parse path, exercised on every boot since p2(48b).
2. THE TYPE-20 BODY: the femu validation lane (this session, before deploy)
   runs the client's own schema decode over the fork's actual encoded bytes;
   its REJECT arm is the pre-fix state (the p2-140/141-era body semantics that
   claims F(a)/(c) pre-named). Verdict lands before the deploy; a REJECT
   fixes the encoder and re-validates before this boot runs.

## MODEL REVIEW (required: trailing third-branch streak on this front)

Front `allocation-dispatch` is NEW (streak 0; the ledger's latest fronts:
peer-entity-send (p2-197, hypothesis-wrong - resolved into this front's
design), connected-rung). No third-branch debt. THE DEAD ASSUMPTION NAMED: the
p2-140/141-era belief "accepted at ingress == applied" - the 15-slot table
proves acceptance (the walker running) is not application (a type match is
required; type 0/5 matched nothing). This boot's readout keys on APPLICATION
(downstream effects), never on the accept line alone.
