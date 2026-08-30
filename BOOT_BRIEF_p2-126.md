# BOOT BRIEF p2(126) - MAP THE PER-PLAYER ENTRY FROM MEMORY, NOT FROM ARITHMETIC

STATUS: live (2026-08-30). Reads with FINDINGS 20.198 (the client does not pull peer
records) and the 20.179 R2 chunk map.

## PURPOSE - what this boot learns, win or lose

The appearance front is now a CLIENT-SIDE question: does the client hold, per player, any
state that feeds rendering - and is any of it reachable from data we can already write?
A gather function at 0x140D48490 walks players with `imul rcx, rax, 0x1a8` and reads three
consecutive 16-byte vectors per entry into a 48-byte-stride output list. That is
transform-shaped. But the ENTRY BASE does not reconcile: 0x3c00 (the gather's own
displacement), 0x3c68 (the region-B applier's destination), and the 0x3b58 those two imply
if region B sits at entry+0x110 each produce a different, mutually contradictory layout, and
region B overruns the 0x1a8 stride under one of them.

Deriving further from second-hand offsets is how the 0x4240/0x4280 row base went wrong for
two sessions. MEASURE IT INSTEAD. The profile apply helper's FIRST argument has never been
logged; this boot logs it and dumps 0x200 bytes from it.

## GRAPHICS DELTA

ZERO new rendered models. Read-only observation added to an existing hook; no server change,
no behaviour change. Same content as p2(125).

## FALSIFIABLE CLAIM (the one contract under test)

CLAIM: the helper's first argument (`dest=`) is the per-player entry pointer, and the values
for row index 0 and row index 1 differ by exactly 0x1a8.

CONTENT NEGATIVE (pre-named): the two `dest=` values differ by something OTHER than 0x1a8.
Then rcx is not the entry pointer - most likely the state object or a sub-object - and the
entry map must be reached from the region-B applier 0x1417AF2D0's destination instead
(20.179 R3 notes it is a legitimate call target, mid-function per .pdata but genuinely
entered; it would need verify_hook_rvas judgement before hooking).

SECOND: the two `dest=` values are IDENTICAL for index 0 and index 1. Then the helper writes
both rows through one buffer and the per-player array is reached elsewhere entirely.

## THE READING METHOD - LANDMARKS WE WROTE OURSELVES

This is why the boot is cheap and unambiguous: the entry dump is read against content THIS
PROJECT PUBLISHED, so no offset has to be trusted in advance.
    "SUNRISE0" as UTF-16LE  -> 530055004E0052004900530045003000  (slot 0)
    "SUNRISE1"              -> 530055004E0052004900530045003100  (slot 1)
    slot 0 SOIDs            -> 000110000130AA9E 010110000130AA9E
    slot 1 SOIDs            -> 000111000130AA9E 030111000130AA9E
Finding those inside the dump locates region A exactly. Region B and the tail follow from
it, and whatever else occupies the 0x1a8 stride becomes visible by subtraction - including
whether the three 16-byte vectors live inside the entry or in a parallel array.

## ABSENCE NEGATIVE (L13)

- Zero `ev=ingress stage=apply` lines with `dest=`: the new build did not load. The literal
  `dest=0x%llX` is gated in the deployed DLL, so its absence indicts the deploy.
- `ev=ingress` present but zero `tag=entry` dump lines: the dump was skipped, i.e. every
  fire was outside its per-class dump budget. Budgets are per (path,index) since 20.193 R5,
  so this should not happen; if it does, that fix is wrong.
- `tag=entry` lines all `ok=0`: the destination was unreadable, which would mean rcx is not
  a pointer at all - itself an answer, and it retires the first claim immediately.
- No index=1 fire at all: the peer's row never applied, so the stride cannot be measured.
  Compare with p2(125), where both machines fired index=0 and index=1.

LIVENESS: `ev=dtrace stage=install result=ok staging_populate=0 ...` on BOTH machines.

## CHAIN MARKS (L16)

| Link | Mark |
|---|---|
| Profile pipeline carries authored content both directions | VERIFIED-BY-EXECUTION (20.194/20.195/20.198) |
| Client does NOT pull peer character records | VERIFIED-BY-EXECUTION (20.198 R2) |
| Server appearance push is self-only by construction | VERIFIED-BY-READING (20.198 R3) |
| Appearance does not cross the peer channel | VERIFIED-BY-EXECUTION (20.196) |
| A per-player array exists with stride 0x1a8 | VERIFIED-BY-DISASSEMBLY (0x140D48490, `imul rcx, rax, 0x1a8`) |
| Three 16-byte vectors per entry, gathered into 48-byte records | VERIFIED-BY-DISASSEMBLY (same function) |
| The entry BASE and interior layout | UNKNOWN and CONTRADICTORY between sources - THIS BOOT |
| Whether any entry field feeds rendering beyond placement | UNKNOWN - the question after this boot |

## INSTRUMENTS

INSTRUMENTS:
  dest=0x%llX
  ev=dtrace stage=staging

## LITERAL TARGETS

LITERAL TARGETS:
  Game/bin/x64/steam_api64.dll: dest=0x%llX, ev=dtrace stage=staging

## ADVERSARIAL PASS

ADVERSARIAL PASS: waived: read-only observation on an already-verified hook, no server change

waived: the hook (0x1417AF360) is unchanged and re-verified as a .pdata function start this
session; the only change is logging an argument that was already being received and dumping
memory it points at, SEH-guarded, under a per-class budget. Server untouched from p2(125).

## DEPLOYED FOR THIS BOOT
  server exe     `136e11e15c9acbe9` (unchanged from p2(125))
  MAC client DLL `5ce0d45a6debd0a6`
  RIG client DLL `5ce0d45a6debd0a6`
  settings       unchanged: publish_player_profile TRUE, profile_name "SUNRISE",
                 profile_identity TRUE, staging_populate FALSE both clients.

## AFTER THE BOOT - REQUIRED
`bash RE_scripts/capture_boot.sh p2-126`
