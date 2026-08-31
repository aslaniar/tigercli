# BOOT BRIEF p2-95 (2026-08-28) - READ THE TWO GATE BYTES. Which half of the public
# switch-now condition actually fails?

STATUS: live (2026-08-28 ~22:4x). Server UNCHANGED from p2(93). Client-DLL-only,
LOGGING-ONLY. No behaviour changes anywhere.

## PURPOSE
20.154/20.155 mapped the public slice-set switch to one condition, read at two
independent sites (the phase query 0x140E22C70 @ 0x140e22ff5, and the consumer
0x140E267D0 @ 0x140e26d8a):
    byte [obj+0x2bc] == 1   AND   byte [obj+0x2c1] == 2   ->  phase 4 ('switch-now')
Anything else returns 2 or 3 ("still progressing"), which is where both clients have
been parked on every boot. Static analysis cannot say which half fails: +0x2c1 has no
disp32 writer anywhere in .text, and the predicate behind +0x2bc calls into a
NON-EXPORTED function of our own steam_api64.dll - which is also how 20.155 found that
destiny2_unpacked_full.exe carries our own hook bytes at hooked call sites and cannot
be trusted there.

Three publish hypotheses have now been spent guessing at this (member flags p2(91)/(92),
the published slice set p2(93), and the teleport block which was retired on reading).
This boot stops guessing and reads the two bytes at runtime.

WIN: `ev=phase stage=query` lines carrying public=/gate=/region=. Either branch names
the fix and there is no third:
  - public != 1        -> the client does not classify PUB56 as public, and the
                          deciding predicate is OUR OWN CODE (20.155). The fix moves
                          into the steam shim, not the wire.
  - public == 1, gate != 2 -> that byte's real value, read against the disc/ctng/cntd
                          ladder the region lines already print, names what is missing.
LOSE: no query lines, which indicts the instrument (see ABSENCE), not the map.

## GRAPHICS DELTA
Zero. No new rendered models and no rendering change: one log-only detour that calls
the original first and returns its answer untouched. Both clients load the same Tower
as p2(93)/p2(94). Boot minimized where possible - the result is read from the logs.

## FALSIFIABLE CLAIM
With the p2(95) client DLL on both machines, the boot emits `ev=phase stage=install
result=ok rva=0xE22C70` followed by at least one `ev=phase stage=query` line whose
`region=` names the public region (56), because a PUB56 `normal_z_leg` transition was
started on both machines in each of the last three boots and the phase query is what
its state machine polls.

CONTENT NEGATIVE: install=ok but ZERO query lines means the phase query is not on the
path we think it is - the RVA is right (pdata-resolved, and its two log sites fired in
p2(94)) but the transition would then be driven by a different entry point, and the map
in 20.154 needs re-reading before any fix.
SECOND CONTENT NEGATIVE: query lines that only ever carry region=48 (or 24) mean the
public transition never reaches this query at all, which moves the defect EARLIER than
the phase - to whatever constructs the public transition object.

## ABSENCE NEGATIVE
- `ev=phase stage=install` prints on EVERY attach attempt, ok or fail, with the reason.
  If neither an ok nor a fail line appears, the observer never ran: the DLL did not
  deploy or activation did not reach it - provenance failure (L13/L14), the boot tested
  nothing, and the deploy is suspect before the map is.
- `result=fail why=range` means the RVA is outside the module (wrong build / wrong
  image) and NOT that the map is wrong.
- The observer logs ONLY when its answer tuple CHANGES and stops at 64 lines. A small
  line count is the DESIGN, not a malfunction; absence of repeats proves nothing.

## CHAIN MARKS
- The gate is `[obj+0x2bc]==1 && [obj+0x2c1]==2` -> phase 4 - verified-by-reading
  (disassembly, two independent sites; 20.155 CLAIM 1).
- The fall-through returns 2 or 3, not 0 - verified-by-reading (xor/comiss/setae/add 2;
  corrects 20.154).
- rcx carries the object - verified-by-reading (`mov rbx,[rcx+0x4d8]` at 0x140e22cb8
  reads the field the constructor writes at 0x140e2b425).
- The two float args ride xmm1/xmm2 - verified-by-reading (movaps at the prologue; the
  fall-through's `comiss xmm9,xmm7` consumes one). The detour mirrors the signature.
- fn 0x140E22C70 is the owning function of both simulator log sites -
  verified-by-execution (p2(94) caller-capture + pdata_bounds).
- +0x2c1 has no disp32 writer in .text - verified-by-execution (field_xref.py, whose
  oracle passes; its disp8 blind spot is documented, so this is NOT proof of none).
- The phase query is polled while a transition is live - assumed. This is the hot-path
  risk; the observer is built for it (see below) but the assumption is untested.
- Reading +0x2bc/+0x2c1 at this entry reflects what the gate later reads - assumed
  (same object, same fields, microseconds apart, but not proven re-entrant-safe).

## ADVERSARIAL PASS: waived: solo main-session boot prep, no second reviewer available
in-session (B-checkpoint exception). The adversarial surface is the HOT PATH. Two
observers in this codebase have already caused stalls - ws_wire re-triggered the tower
stall and was stripped, and item_gate emitted 98.6% of one boot's lines. This observer
is built against that record: it calls the original first, logs ONLY when the packed
(phase, public, gate, region) tuple changes, hard-stops at 64 lines, formats nothing on
the unchanged path, and guards every field read with SEH. Steady-state cost is one
64-bit compare and a branch. If the boot stalls anyway, that is itself the finding and
the DLL rolls back with no server change.

## INSTRUMENTS:
  "ev=phase stage=query"
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
Client DLL only. Prior DLL `003baf5ff811ff79` (p2(94)) or `ae4d41f76b5202a5` (the
p2(90)-p2(93) baseline) restores via deploy_client_dll.sh. Server needs no rollback:
p2(93) `50d1f4cccbad0a56` is unchanged.
