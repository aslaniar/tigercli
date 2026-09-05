# BOOT_BRIEF_p2-178 - THE SUSTAINED PEER ROW: DOES THE CLAIM STATE MOVE?
STATUS: live (2026-09-04, post-rebuild)

Server ed43adf1d6152744 (NEW - 4 changes). Clients f9a4c83e840b693f BOTH (NEW).
PAIRED. First entry only. gate_poke=0. THE CLIENT IS NEVER MODIFIED.

## PURPOSE
Every previous peer-row measurement was taken against a wire that had gone quiet:
`peerWithdrawn` was sticky, the client never acknowledges a peer-bearing body (20.48),
so the cap always tripped and 81% of p2-175's peer-available snapshots sent NOTHING -
which is what invalidated 20.297 R2. This boot is the first with a peer row that
genuinely STAYS on the wire, and the first that can attribute a session to a machine
without inference. The question is whether the record's CLAIM STATE moves when the row
is actually sustained.

WIN OR LOSE, THIS BOOT LEARNS:
  - the loop completes on a peer-owned record -> THE WALL IS DOWN, and the sustained row
    was the missing precondition all along.
  - the loop still churns with the row demonstrably sustained -> sustain is NOT the
    blocker either. Row content (20.298) and delivery (this boot) are both eliminated,
    and the claim state is isolated as the only remaining variable.
  - f38 goes nonzero at any create -> cond5 IS on the render path and the writing state
    is named (FRONT_chain-to-a-moving-guardian.md T1/T2/T3 collapse to one).
  - f38 never moves while creates complete -> cond5 is NOT a render precondition and the
    front page's central premise is retired. Cheaper to learn than to keep hunting.

## THE REBUILD THIS BOOT SHIPS (4 changes; server ed43adf1d6152744, client f9a4c83e840b693f)
  R1 RATE-LIMITED RE-ARM. `peerWithdrawn` was sticky forever; a naive "clear on ack" is
     WRONG (the solo body is what gets acked - that re-adds the peer instantly and
     restarts the p2(111) storm). Instead: after N acknowledged bodies the row re-arms
     ONCE, and each re-arm still pays the full retry cap before withdrawing again.
     New key `membership_peer_rearm_after_acks` (0 = off = byte-identical old path).
     BUDGET ARITHMETIC: cap 10 => ~10 peer bodies (~50 s) per arm, then 8 acks (~40 s)
     to re-arm: a ~90 s cycle, ~67 peer bodies over a 10-minute dwell. The p2(111) storm
     that blocked a Tower load was 127-146. Under it, deliberately.
  R2 SESSION <-> MEMBER-KEY JOIN. The keepalive line now carries `session=%llu` beside
     `key=0x%llX`. Before this NOTHING logged both, so "which session is the rig's" was
     INFERRED (20.298 R2 flagged its own attribution as inferred for exactly this).
  R3 CREATION-PATH GATE-BYTE PROBE (`stage=gatebyte`). p2-177's decisive read could not
     execute because pgate is driven by participant-table events, not creation - 16
     samples against 3,774 creates. The new probe reads the gate bytes AT pb_create /
     ent_make. NO NEW HOOK RVA: it reuses pgate's already-validated table pointer, so
     verify_hook_rvas has nothing new to resolve and no hook depth is added.
  R4 definition.h's stale variant-order comment corrected (pin=4 is all_mask, "the
     historical reading, and it froze" - not the comment's "packed_packed").

## SETTINGS (healthy baseline - user decision, and the reason is on the record)
  membership_peer_rearm_after_acks  8      <- NEW, the whole point of this boot
  membership_peer_retry_cap         10
  membership_peer_transport_identity TRUE
  publish_player_profile             TRUE
  membership_self_peer_row           false | same_region_advert TRUE | sweep off, pin 0
DELIBERATE DEVIATION FROM RUN A's LITERAL CONTRACT, STATED NOT HIDDEN: run A specified
both extras OFF. 20.298 already EXONERATED them as the breaking field, so re-testing row
content buys nothing; and publish_player_profile=false is the leading black-screen
suspect (false: black 2/2; true: clean 3/3). Running the extras ON keeps both clients
healthy enough to produce a VISUAL, which is what the claim-state question needs.

## INSTRUMENTS: gatebyte (NEW), pgate/ptable, pb_create, ent_make, create_loop,
## member_get, keepalive(session+key), membership_peer(rearmed/withdrawn), wire_snapshot
## LITERAL TARGETS (asserted at deploy, all three found):
##   sunrise-server.exe: result=rearmed, "session=%llu slot="
##   steam_api64.dll:    stage=gatebyte

## SETUP (my job; user launches both games)
  1. Server restart so the new settings load; assert peer_retry_cap + rearm in the echo.
  2. reset_lobby_claims.sh; claims = 0.
  3. Rotate BOTH client logs to zero (p2-177's stale log must not be read as this run).
  4. Assert both client hashes f9a4c83e840b693f; assert gate_poke=0.
  5. ssh control socket up for the rig log pull.

## THE RUN
PAIRED Tower, FIRST ENTRY ONLY. Both machines land, then dwell ~8 minutes - longer than
usual ON PURPOSE: the re-arm cycle is ~90 s, so a short dwell would show at most one
arm. No orbit trips, no character switches.

## GRAPHICS DELTA (THE TEST ITSELF)
Expected new rendered models: 0 or 1 per machine. Baseline is one guardian each (self).
A SECOND guardian on either machine is the positive. Minimisation: no client-side write,
no new hook, one new settings key; the graphics delta IS the deliverable.

## FALSIFIABLE CLAIM
With the peer row sustained across at least two re-arm cycles (>= 2 `result=rearmed`
lines and peer bodies published after each), the creation loop COMPLETES a peer-owned
record: pb_create stops repeating identical-arg creates on the same slot for a record
whose member_get owner is the OTHER machine's key.

CONTENT NEGATIVE (what refutes it): >= 2 re-arms occur, peer bodies demonstrably follow
each, and pb_create still repeats identical-arg creates on a peer-owned record. That
eliminates DELIVERY as the blocker and isolates the claim state.

## ABSENCE NEGATIVE (L13 - what zero lines MEAN)
  - zero `result=rearmed`: EITHER the knob did not load (check the settings echo FIRST)
    OR no withdrawal ever happened (check `result=withdrawn`). These are opposite
    findings and must not be conflated - read withdrawn before concluding.
  - zero `stage=gatebyte`: the probe returns early when no table is cached. MEASURED
    BLIND SPOT, replayed over p2-177 BEFORE shipping: the first create fires ~3.3 s
    before the first pgate (t=74388 vs t=77670), so early creates emit nothing. Zero
    gatebyte lines therefore means "pgate never ran", NOT "the byte stayed zero".
  - gatebyte lines that all read f38=0x00: that IS a real measurement (the probe fired),
    and it is the T1-refuting outcome. Distinguish it from the case above by presence.
  - zero `session=` on keepalive: the R2 change did not ship; every attribution claim
    this boot makes reverts to INFERRED and must be labelled so.

## CHAIN MARKS (L16)
  S1 the peer row reaches the wire                verified-by-execution (20.298: 82
       adverts built, all peer_citizen=1)
  S2 it is SUSTAINED across re-arm cycles         unknown (THIS BOOT - R1 is new code)
  S3 session <-> machine attribution is DIRECT    unknown (THIS BOOT - R2 is new code)
  S4 the peer's participant entry exists          verified-by-execution (20.298: rig
       slot 1 = mac's key, maskA set)
  S5 the gate byte at create time                 unknown (THIS BOOT - R3 is new code)
  S6 the loop COMPLETES a peer record             unknown (THE WALL)
  S7 a second guardian renders                    unknown
  S8 it MOVES in sync                             not built (peer channel carries no
       bulk, 20.196 - a separate problem, see FRONT_chain-to-a-moving-guardian)

## ADVERSARIAL PASS: waived: no reviewer run. MITIGATION APPLIED INSTEAD, and it worked:
the R3 trigger was REPLAYED over the p2-177 log before shipping (the rule
POSTMORTEM_2026-09-01 yielded and that 20.299 R2 broke). The replay caught TWO real
defects pre-boot - a single-global change-gate that would have emitted on every create
for every record and burned the budget in seconds, and the ~3.3 s pre-pgate blind spot
now documented in the ABSENCE NEGATIVE. Both fixed before the binary shipped.

## DO NOT
  - do not read `wire_snapshot peer=N` as "a row was sent" (it logs havePeer)
  - do not read zero gatebyte lines as "the byte stayed zero" (see ABSENCE NEGATIVE)
  - do not conflate "no rearm because no withdrawal" with "no rearm because knob off"
  - do not enable gate_poke; do not modify the client
  - do not add a transition rider - first entry only
  - do not shorten the dwell below ~8 min (one re-arm cycle is ~90 s)
