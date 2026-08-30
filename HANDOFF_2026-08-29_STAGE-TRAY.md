# HANDOFF 2026-08-29 - THE STAGE TRAY (opencode session, the write-detour job)

STATUS: live (2026-08-29 ~23:5x). Read with FINDINGS 20.185 -> 20.178 (newest first).
Supersedes HANDOFF_2026-08-29_PROFILE-WRITER.md (its job shipped; the hunt moved past it).

## THE ONE-PARAGRAPH STATE OF THE WORLD

The flag-on membership body is delivered, acked, and decoded CORRECTLY: the client's
decoder fills the update struct (members=2, players=1, the row present at ~+0x4240 - the
20.176 R1 delta base 0x4280 pointed at the inter-row gap). The row then dies in the APPLY
(0x141781800): the apply does not read profile content from the decoded struct - it reads
it from a STAGING OBJECT whose pointer arrives as the apply's third argument, selected by
session stage ([+0x1aef8]: 1 -> [+0x1af08], 2 -> [+0x1af60], else a NULLed local). At
apply time the stage is 2 and the stage-2 slot holds CHANGING GARBAGE - no readable code
ever writes [+0x1af60] (field_xref: zero writers in readable .text; the population is
either VMP-hidden or vestigial). The apply reads gate/header/mask/regionA/tail from
garbage, concludes no-profile, and skips the row. No crash, no log, no pc. Our server
bytes were never the problem.

## WHAT NOT TO REDO (each is closed with evidence)

1. Do not re-litigate the transport: delivery + ack PROVEN (20.182 R1, 91 sendqueue
   cleared lines). The "client never acks" reading of 20.178 was a capture-window
   artifact + an unverified assumption - the lesson is in the findings.
2. Size gate: dead (p2(114) accepted 14-fragment bodies; the refused body was 12).
   Fragment count: dead (12 == 12). Region-A exit: dead (20.180 R2/R3 verified pass).
   Hash gate: dead on the wire path (verify=0, instruction-exact, 20.181 R2).
3. 20.177's "total 150 bits": wrong, the field list sums to 178 (incl. gate). Code and
   smoke record the correction - do not re-derive the writer from the summary.
4. Do not hook 0x1417AF2D0 blindly - it IS a legitimate call target (20.179 R3 softened
   the old "never hook" note) but it remains mid-function; verify before any detour.
5. Do not spend a boot on the rig/mac black screens (pre-existing constants) or on
   stage-machine static reversal (the stage-driver's caller is VMP-virtualized - wall).

## THE INSTRUMENT STATE (all settings-gated, default false)

  server exe   `e41d5a92b07d20ab` (fork 25cae4e): minimal writer + svc/dtls skip+miss
               debug lines. publish_player_profile TRUE; retry-cap 2.
  MAC DLL      `fdb3d90b785ad59f`: + decoder_trace (decoder 0x173BFC0 + apply 0x1781800
               entry traces, stage/counts/row0/nz-map dumps) - decoder_trace TRUE.
  RIG DLL      `45ef17f93b901db9` (no trace instruments, unchanged).
  captures     RE_output/captures/p2-115_flagon_wedge/; the flag-on server log is
               sunrise.log.old (rotated); the rung/boot logs are in sunrise.log.
  boot count   through p2(115); next number p2(116).

## THE JOB, IN ORDER

1. **LESSONS REVIEW - our first WRITE detour.** Every prior internal detour was
   read-only; the p2(102)+ poisonings were write detours done carelessly. Write the
   review: what we write, where, when, the disarm switch, and the rollback. Get it
   past the gate before building.
2. **The staging-population detour.** At apply entry (0x141781800, already hooked by
   decoder_trace), populate the staging fields from the DECODED struct (rdx = the
   struct, verified correct): staging[+0x19] = 1 (gate), [+0x1c] = decoded hdr1
   (0 is fine - wire verify=0), [+0x20] = decoded mask (0x109 for the minimal block),
   [+0x28] = region A pointer (struct + row base + 0x30), [+0x198] = tail pointer.
   The row base is ~struct+0x4240 (CONFIRM the exact base first - 20.184 R1's caveat).
3. **One mac run** (solo, ~2 min). Outcome A: pc=1 lands -> the wire path is proven
   end to end; proceed to the mac's own harvested real sheet (rung 2). Outcome B: still
   silent -> the apply's early section has another gate; read 0x1417806C0's full body
   with the staging insight (the r8=timestamp reading is now suspect - re-derive).
4. **The rung ladder after pc=1**: real name (cipher done), then the harvested sheet,
   then region B (UNREAD - 136B, the appearance candidate) and chunk 8 (schema engine).
5. **The render** is the last unproven link (co-presence class parked 20.110/20.111).

## THE HONEST CAVEATS

- The stage-2 slot has no readable writer: the population is VMP-hidden or vestigial.
  The detour assumes the staging object's SHAPE is right even if its lifecycle is
  unpopulated - if the apply rejects a well-formed staging object, the shape is wrong
  and 0x1417806C0's full body is the next read.
- The logged "stage=2" may be the VARIANT field (setter writes stage/variant adjacently
  and r14d's source is unresolved) - the rung experiment does not depend on resolving it.
- The harvested sheet is UNVALIDATED (its commit hash covers the previous cached copy).
- The struct is REUSED across messages: the nz map mixes fresh and stale bytes. The
  row0 dump's zeros-before-+0x20 may be a fresh empty decode OR a stale gap.
