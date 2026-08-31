# BOOT BRIEF p2-94 (2026-08-28) - THE PHASE LANE: name the code that advances a
# slice-set transition phase, and the writer that feeds it from the wire.

STATUS: live (2026-08-28 ~21:3x). Server UNCHANGED from p2(93) - this is a
client-DLL-only, LOGGING-ONLY boot. No behaviour changes anywhere.

## PURPOSE
Two publish hypotheses have now been spent guessing at the public slice-set switch:
p2(91)/p2(92) (member setup flags) and p2(93) (the published slice set). Both were
clean, pre-named negatives. U7 says escalate to the instrument rather than take a
third swing, and that is this boot.

Measured state after p2(93): the server now publishes `region=56 slice=56` (verified,
25 roster lines) and BOTH clients still stop at exactly the same place - citizen join
to PUB56.56 succeeds, `Finished precaching slice-set 'PUB56.56'`, and then no
slice-set-switch task and no transition completion, on either machine. A PRIVATE or
ORBIT transition self-simulates its phase (`:simulator: ... advancing simulated phase
directly to 'switch-now'`) and completes with no server agreement at all; the PUBLIC
`normal_z_leg` has no simulator arm and waits for an input we have not identified.

This boot does not try to fix that. It arms caller-capture (LESSONS 18c) on five
transition-manager log lines that DO fire, so each yields a module-relative RVA. Those
five bracket the entire decision: where the phase is set, where it is read, what runs
when a precache finishes, what assigns the switch task, and what closes a transition.

WIN: `ev=retail stage=caller target=...` lines appear for the new targets on at least
one machine. Each RVA then resolves through pdata_bounds.py to its owning function,
and the disassembly names the phase variable plus every writer of it - including the
network-fed one. That converts the remaining question from guesswork into a map.
LOSE: no caller lines for the new targets, which indicts the instrument (see ABSENCE),
not the theory.

## GRAPHICS DELTA
Zero. No new rendered models, no rendering change of any kind: the only edit is five
added strings in a log-funnel observer's target table. Both clients load the same
Tower they loaded in p2(93). Clients may boot minimized where possible - the entire
result is read from the logs.

## FALSIFIABLE CLAIM
With the p2(94) client DLL on both machines, the boot emits
`ev=retail stage=caller target=<t> rva=0x... abs=0x... base=0x...` for at least
`Transition to private slice-set`, `Finished precaching slice-set` and
`is being assigned the slice-set-switch task`, because all three of those lines were
observed firing on both machines in p2(93).

CONTENT NEGATIVE: if caller lines appear for the OLD targets (e.g. `Adding player`,
`Could not find tracking data`) but NOT for the new ones, the target strings do not
match the native text - a substring/format mismatch in this brief's assumptions, not a
property of the game. Fix the strings against the p2(93) captured text and re-run; no
conclusion about the phase may be drawn.
SECOND CONTENT NEGATIVE: if the RVAs for `Transition to private slice-set` and
`Transition to Orbit slice-set` are IDENTICAL, the two simulator arms share one call
site and the split was unnecessary - harmless, and it still tells us the arm is
parameterised rather than duplicated, which narrows the disassembly.

## ABSENCE NEGATIVE
- `ev=retail stage=caller` lines are the whole instrument. p2(90) produced them for
  `Could not find tracking data` on BOTH machines, so the mechanism is known-good.
  If ZERO caller lines of ANY target appear this boot, the observer did not attach or
  the DLL did not deploy - provenance failure (L13/L14), the boot tested nothing, and
  the deploy is suspect before the target strings are.
- If `ev=hook stage=attach ... name=retail_log*` does not appear, the hook never
  installed and no absence of caller lines means anything.
- Caller capture is rate-limited to ONE report per (target, RVA). A target that fires
  from two sites reports only the first. Absence of a SECOND rva for a target is
  therefore not evidence that only one site exists.

## CHAIN MARKS
- Both clients reach `Finished precaching slice-set 'PUB56.56'` and stop there -
  verified-by-execution (p2(93) boot, both logs, identical).
- `region=56 slice=56` is now published and did not move the outcome -
  verified-by-execution (p2(93), 25 roster lines; second content negative of that brief
  fired exactly as pre-named).
- PRIVATE/ORBIT transitions self-simulate their phase, PUBLIC does not -
  verified-by-reading (`:simulator:` lines present for PRV24/PRV48 on both machines
  across p2(90) and p2(93), absent for PUB56 on both).
- The transition token is already correct and is NOT the gap - verified-by-reading
  (server publishes token=2; the client's PUB56 leg is `token advanced to 002`).
- The teleport block is a MIRROR of a client-authoritative message-22 report, not a
  host command channel - verified-by-reading (upstream struct docs "mirrored between
  activity messages 22 and 12"; upstream comment "It goes out only when the client's
  own authoritative-data message supplies one"; zero message-22 teleport intake in any
  boot on record). Its "de-instantiates the world" warning applies to the UNSET
  sentinel reaching the wire as zero (logical -1), which the encoder already clamps -
  it is not a warning against publishing a valid teleport. NOT pursued; see 20.153.
- Caller capture yields a usable RVA for these five lines - assumed (this boot's test;
  the mechanism is verified-by-execution for other targets, the strings are not).
- The owning functions will expose the phase variable - assumed (the disassembly step
  is downstream of this boot and may itself stall; the fallback is widening the target
  table, not another publish guess).

## ADVERSARIAL PASS: waived: solo main-session boot prep, no second reviewer available
in-session (B-checkpoint exception). The adversarial surface is that this boot cannot
produce a false positive - a caller line is an address or it is absent, and both
content negatives above name what a wrong result would mean.

## INSTRUMENTS:
  "Transition to Orbit slice-set"
  "Transition to private slice-set"
  "slice-set-switch task is not possible yet"
  "is being assigned the slice-set-switch task"
  "Finished precaching slice-set"
  "Stopping transition of type"

## SWITCH POSITIONS FOR THIS BOOT (all unchanged from p2(93))
  activity_slice_set_follows_region  TRUE   (p2(93), left on - it is correct even
                                             though it was not sufficient)
  activity_region_survives_churn     TRUE   (p2(90), required)
  activity_host_region_bound         TRUE
  activity_public_row_membership_bodies 65535
  activity_member_setup_flags        FALSE  (retired, 20.152/20.153)
  join_roster_observer               FALSE  both clients
  slice_set                          56     both clients

## ROLLBACK
Client DLL only. Prior DLL `ae4d41f76b5202a5` (p2(90)-p2(93) baseline) restores the
previous state on either machine via deploy_client_dll.sh. Server needs no rollback:
p2(93) `50d1f4cccbad0a56` is unchanged by this boot.
