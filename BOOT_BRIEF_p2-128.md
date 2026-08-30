# BOOT BRIEF p2(128) - SCAN AFTER THE WRITE: DOES THE PEER'S PROFILE PERSIST?

STATUS: live (2026-08-30). Reads with 20.199 (p2(126): the helper's first argument is the
SESSION OBJECT, not an entry pointer) and 20.198.

## WHY THIS BOOT REPEATS p2(127)

p2(127) found the published name in client memory at session+0x3b80 - the first time this
project has located its own authored content in the client by SEARCH rather than by offset
arithmetic, and near none of the three contradictory disassembly candidates
(0x3b58/0x3c00/0x3c68), which is why they never reconciled.
But it hit on 1 scan in 24. TWO INSTRUMENT FAULTS, both mine, are the leading explanation
and both are now fixed:
  1. The scan ran BEFORE the pass-through call, so it could only ever see what a PREVIOUS
     call left behind. "Does the profile persist" cannot be asked from before the write.
     It now runs AFTER the original returns.
  2. The window was 0x10000; widened to 0x40000 so a SECOND row stored further out is
     reachable. The spacing between rows is the measurement this lane actually wants.
Nothing else changed: same server, same content, same hook, read-only.

## PURPOSE - what this boot learns, win or lose

One question: DOES A PEER'S PROFILE PERSIST IN THE CLIENT?

Everything upstream is settled. The server authors a profile block; both clients decode it,
apply it, and run the profile helper on each other's rows (20.194); arbitrary content
survives the wire byte-exact - a name (20.195) and real per-player identity (20.198). The
client does not pull peer character records even when told exactly who the peer is
(20.198 R2), the server's one appearance push is self-only by construction (20.198 R3), and
appearance does not cross the client<->client channel at all (20.196).

So the remaining question is what the client DOES with a peer's profile once it has it.
p2(127) found our published name in client memory once, at session+0x3b80, on 1 scan in 24 -
but every scan ran before the write, so it could only see stale state. Scanning immediately
after the write answers it: if the name is reliably there, the client keeps per-player
profile state and the next question is which of its fields feed the renderer. If it is
reliably NOT there, the client discards a peer's profile, and that - not any server gap -
is the appearance wall.

## GRAPHICS DELTA

ZERO new rendered models. Read-only observation added to an existing hook; no server change,
no behaviour change. Same content as p2(125).

## FALSIFIABLE CLAIM (the one contract under test)

CLAIM: scanning AFTER the helper writes finds the published name reliably - on most or all
WIRE fires rather than 1 in 24 - and at two or more offsets whose spacing is the per-player
stride.

CONTENT NEGATIVE (pre-named, and this is the one that matters): the scan STILL reports
`hits=none` on most fires even when run immediately after the write. Then the client accepts
a peer's profile and does not retain it in this object - and that, not any server gap, is
why nothing renders from it. That reading was explicitly refused in 20.200 R2 off a single
hit; a clean after-write negative is what would earn it.

SECOND: hits are reliable but there is only ever ONE, at a stable offset, regardless of
which row index fired. Then both rows are written through one slot and the client keeps no
per-player profile array at all.

THIRD: two or more hits with a spacing that is NOT 0x1a8. Then the profile array is not the
array the gather function walks, and the three 16-byte vectors are a parallel structure
decoupled from anything we can write.

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

- Zero `ev=ingress stage=scan` lines: the new build did not load. The literal `stage=scan`
  is confirmed present in both deployed DLLs, so its absence indicts the deploy.
- Scans present but ALL from local-path fires: the wire path did not run; compare against
  p2(127), where both machines fired WIRE index=0 and index=1.
- `hits=<fault>`: the scan window left mapped memory. The offsets printed before the fault
  are still valid; the window needs shrinking, not the method abandoning.
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
| The helper's first argument | VERIFIED-BY-EXECUTION: the SESSION OBJECT, identical for both rows (20.199) |
| The published name reaches client memory at session+0x3b80 | VERIFIED-BY-EXECUTION (20.200 R1, one hit) |
| Whether it PERSISTS there | UNKNOWN - THIS BOOT, scanning after the write |
| The black-screen idle hypothesis | FALSIFIED (20.200 R3): 87.1 s idle rendered clean on both machines |
| Whether any entry field feeds rendering beyond placement | UNKNOWN - the question after this boot |

## INSTRUMENTS

INSTRUMENTS:
  stage=scan
  pattern=SUNRISE

## LITERAL TARGETS

LITERAL TARGETS:
  Game/bin/x64/steam_api64.dll: stage=scan, pattern=SUNRISE

## ADVERSARIAL PASS

ADVERSARIAL PASS: waived: read-only observation on an already-verified hook, no server change

waived: the hook (0x1417AF360) is unchanged and re-verified as a .pdata function start this
session; the only change is logging an argument that was already being received and dumping
memory it points at, SEH-guarded, under a per-class budget. Server untouched from p2(125).

## DEPLOYED FOR THIS BOOT
  server exe     `136e11e15c9acbe9` (unchanged from p2(125))
  MAC client DLL `0e3d78f30d3396a7`
  RIG client DLL `0e3d78f30d3396a7`
  settings       unchanged: publish_player_profile TRUE, profile_name "SUNRISE",
                 profile_identity TRUE, staging_populate FALSE both clients.

## AFTER THE BOOT - REQUIRED
`bash RE_scripts/capture_boot.sh p2-128`
