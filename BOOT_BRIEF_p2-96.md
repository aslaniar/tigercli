# BOOT BRIEF p2-96 (2026-08-28) - TWO CENSUSES, ONE BOOT: what does the group-host pump
# actually receive, and is the public transition ever polled?

STATUS: live (2026-08-28 ~23:2x). BOTH halves are LOGGING-ONLY - no behaviour change on
either side. Server switches unchanged from p2(93).

## PURPOSE
Two independent unknowns gate everything left, and neither needs a behaviour change to
answer. They are bundled because both are pure observation, so this is still one contract.

HALF A - THE MESSAGE-ID CENSUS (server). The group-host pump dispatches eleven ids and
lets everything else fall through to migration::consume, which answers host-handoff ids
only and drops the rest without a word. We therefore do not know what the clients send
us. The load-bearing unknown is the type-0x0A (10) ADMISSION JOIN named by the
roster-caller lane (RE_output/claims/blockers-research-2026-08-28.md #2): it is absent
from SessionMessageId entirely. Whether it reaches this pump decides the admission route
- server relay (route A) vs DLL-side reserve/admit injection (route B) - and admission is
what populates the client's netmgr member records, which the roster needs and which the
public world swap may also depend on. `peerConnect` (11) is in the enum but is NOT
dispatched either; the census names it too.

HALF B - THE POLLER CENSUS (client). 20.156 proved the phase query is never called for a
public transition, by design: the constructor calls it only for types {2,4,5,6,7} and
normal_z_leg is type 3. Two other callers accept type 3 - fn 0x140E244C0 (type <= 5) and
fn 0x140E25A30 (type <= 7) - and NEITHER ran for region 56 in p2(95). Both also bail on
`byte [obj+0x200] != 0`. This observes both at entry.

WIN: `stage=msg_census` lines enumerate every id the pump sees with dispatched=0/1, and
`stage=poll` lines say whether a type=3 object ever enters either poller and with what
guard byte. Every combination is informative; see the negatives.
LOSE: neither census emits, which indicts the instruments (see ABSENCE), not the map.

## GRAPHICS DELTA
Zero. No new rendered models and no rendering change on either side: one server log line
per distinct message id, and two client detours that call the original first and return
its result untouched. Both clients load the same Tower as p2(93)-p2(95). Boot minimized
where possible - the entire result is read from the logs.

## FALSIFIABLE CLAIM
A paired boot emits at least one `ev=gameplay stage=msg_census` line per distinct id the
pump receives (the pump demonstrably runs - p2(90) logged stage=properties, stage=player
and stage=parameters from inside it), and `ev=phase stage=install result=ok` on both
clients naming all three RVAs.

CONTENT NEGATIVE (half A): if `stage=msg_census id=10` never appears while the clients
are co-located, the admission join does NOT reach this server. That CLOSES route A for
admission and makes route B (DLL-side reserve/admit injection) the only path - a real
result, and the one that most changes the plan.
CONTENT NEGATIVE (half B): if no `stage=poll` line ever carries type=3, the public
transition object never enters either poller, and the defect is upstream of both - in
whatever should schedule the z-leg, not in the pollers' guards.
SECOND CONTENT NEGATIVE (half B): a `stage=poll type=3 gate=<non-zero>` line names the
guard byte as the cause outright and makes `[obj+0x200]` the next target.

## ABSENCE NEGATIVE
- `stage=msg_census` fires on the FIRST message of every id, so at minimum the ids p2(90)
  already logged (31 properties, 34 player-add, 39 parameters) must appear. If ZERO
  census lines appear, the instrument did not ship - provenance failure (L14), and the
  server deploy is suspect before any conclusion about ids.
- `ev=phase stage=install` prints on every attach attempt with its reason. No line at all
  = the client DLL did not deploy or activation never reached it. `result=fail
  why=range_poll` = an RVA is outside the module (wrong build), NOT a wrong map.
- Both censuses are ONE LINE PER DISTINCT VALUE by design (ids: per id; pollers: per
  changed tuple, cap 64). Low line counts are the design; absence of repeats proves
  nothing.

## CHAIN MARKS
- The pump dispatches exactly eleven ids and everything else reaches migration::consume -
  verified-by-reading (group_host.cpp dispatch chain; the census helper mirrors it by
  hand and must be updated with it).
- id 10 is absent from SessionMessageId - verified-by-reading (the enum lists 11,12,13,
  15,16,17,18,26,29,30).
- The `public-session-reservations` parameter is requested and answered - verified-by-
  execution (p2(90) t=590207, both lines), which corroborates the research doc's #4.
- type-13 never fires in a co-located boot - verified-by-execution (0 hits, p2(90) index).
- normal_z_leg is type 3 and the constructor skips its phase query - verified-by-reading
  + verified-by-execution (type table 0x141C27960; p2(95) runtime, both machines).
- Pollers A and B accept type 3 and neither ran for region 56 - verified-by-reading
  (guards) + verified-by-execution (p2(95): zero poll activity for the public region).
- Both pollers take the object in rcx - verified-by-reading (A does `mov rsi,rcx`; B
  reads `[rcx+0x209]`).
- The pollers return a value in rax - ASSUMED. The observers declare a u64 return and
  pass it through, which is safe if the real return is void (the caller ignores rax) and
  correct if it is a bool or int.
- Admission failure explains the un-polled z-leg - assumed. This is the session's leading
  hypothesis, NOT a finding, and half B is what tests its client half.

## ADVERSARIAL PASS: waived: solo main-session boot prep, no second reviewer available
in-session (B-checkpoint exception). The adversarial surface is again the HOT PATH, on
the client half: two pollers on the transition state machine may run per tick. Both
observers call the original first, log only on a changed tuple, share a 64-line cap with
the phase probe, format nothing on the unchanged path, and SEH-guard every field read -
the same construction that ran clean in p2(95) (3 lines, no stall). The server half is
bounded by construction: one line per distinct id, at most 256 lines ever.

## INSTRUMENTS:
  "ev=gameplay stage=msg_census"
  "ev=gameplay stage=msg_unhandled"
  "ev=phase stage=poll"
  "ev=phase stage=install"

## SWITCH POSITIONS FOR THIS BOOT (all unchanged from p2(93))
  activity_slice_set_follows_region  TRUE
  activity_region_survives_churn     TRUE
  activity_host_region_bound         TRUE
  activity_public_row_membership_bodies 65535
  activity_member_setup_flags        FALSE
  join_roster_observer               FALSE  both clients
  slice_set                          56     both clients

## ROLLBACK
Both halves are observation; neither needs a functional rollback. Server: p2(93)
`50d1f4cccbad0a56` is the prior binary. Client: p2(95) `4cb3887f6ecd669c`, or the
`ae4d41f76b5202a5` baseline, via deploy_client_dll.sh.
