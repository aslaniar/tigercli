# HANDOFF 2026-09-03 — THE CREATION FRONT

STATUS: SUPERSEDED 2026-09-03 23:0x PDT by FINDINGS 20.291 - the image/mask-delivery
front this handoff points at is PARKED (its premise is unevidenced; the message is not
fork-emittable). Its PROVEN list (W1/W3/cond5/walk-skips-self) still stands and is still
the right starting evidence. Read 20.291 before acting on anything below.
STATUS (original): live (2026-09-03). Supersedes HANDOFF_2026-08-31_GATE-FEEDERS.md for front
selection; that file's gate table and elimination list remain readable history.
**20.287 CORRECTION (same day): the "birth-set" framing below is superseded — the required
bit OR-accumulates at CLAIM time, and the front is now "deliver the participant image so
the sweep's claim arms for the peer's slot." Read FINDINGS 20.287 before anything below;
its measurements (populations disjoint, setA/setB=0 on the peer) all stand.**

## THE ONE-PARAGRAPH VERSION

Two clients reach the Tower in one session on a private server. Everything about the peer's
DATA now works: identity, membership, transport endpoint, and the 86-byte card the client's
admission guard reads. Neither player can see the other, because neither client ever builds
an entity for the peer. Tonight established why the obvious path cannot work: the bit the
guard requires is stamped at record CREATION from the container the record is born into, and
no downstream action grants it. Everything fixed so far concerns a record's CONTENTS. The
blocker is its CREATION. That is this front.

## WHAT IS PROVEN (do not re-derive)

- **The card reaches the guard's field.** 1,559 samples carrying the RIG's endpoint inside
  the MAC's participant slot - an address the mac cannot compose locally, so the bytes are
  ours by construction. (20.284)
- **The peer's reservation record climbs to the top of its state ladder.** The 3/4 stall of
  20.277 is not a wall. (20.284 R4, reconfirmed p2-170/p2-171)
- **The gate that guards the walk (cond5) is a pure data read** - six instructions, no
  branches, no second path. Only the byte can change the outcome. (20.285 R1)
- **The walk SKIPS SELF.** The local player is never evaluated by it and cannot be used as
  the control. (20.285 R2)
- **A passing gate CONSTRUCTS NOTHING.** The guard's return feeds one AND-accumulator whose
  only consumer is a diagnostic string builder. It claims as a SIDE EFFECT; the verdict
  string is corrected to `would-claim`. (20.285 R4)
- **The guard's required bit is BIRTH-SET.** Records carrying it never climb; records that
  climb never carry it; on the rig the same peer identity occupies both populations at once.
  1,190 guard calls against a correct card never moved it. (20.286 R3)

## THE QUESTION THIS FRONT OWNS

**What determines which container a peer's reservation record is created in?**

The guard's required bit is `container-at-creation + 6`, so the container choice IS the bit.
There is no other lever: the bit cannot be set after the fact, and the poke reaches only
cond5, which is downstream. If the server can influence which container a peer's record is
born into, the wall falls. If it cannot, this front reports that and the project needs a
different route to a rendered peer.

Secondary, and possibly the same mechanism: **entity construction**. Two untested
server-side levers are on record - 20.208 R6 (world_population -> type-7 sobject + type-52
epoch) and 20.213 R1 (lease size fired the attempt on type-12 pushes). Nothing measured says
whether record-creation and entity-creation are one mechanism or two. TREAT CREATION AS ONE
FRONT until evidence splits it; a boundary assumed now is a boundary that will be defended
later for no reason.

## WHERE TO START (static, no boot needed)

1. The two record populations are visible in any p2-171 `resv_rec` line. Find the CREATOR of
   a reservation record and read what selects its container. Anchor: the record stride is
   0x41F0 and the guard's word is at +0x3112; `field_xref.py` with the ALIAS TRAP in mind
   (TOOLS.md - a field reached through a sub-object base spells a different displacement).
2. `callers.py` on the creator once found; the container argument's provenance is the answer.
3. Only then consider a boot, and only to confirm a named mechanism.

## WHAT NOT TO DO (each of these is already paid for)

- **Do not poke cond5 again for this question.** Nothing downstream of cond5 reaches a
  birth-set bit. p2-170 ran that experiment: 1,190 guard calls, bit unmoved. (20.286 R4)
- **Do not plan "make the guard claim the record so the bit follows".** Same test, same
  result.
- **Do not resume the image-copier hunt.** Three boots of direct instrumentation on the
  copier show neither machine ever copies INTO the live table, and every source image's gate
  bytes are clear. The earlier "a restore happened" conclusion was an inference from address
  spacing and does not survive direct measurement. (20.285 R6, 20.286 R4)
- **Do not modify the client.** The governing constraint is in AGENTS.md and it outranks
  convenience. The poke is a throwaway diagnostic only, reverted at boot end.

## TOOLING NOTES EARNED TODAY

- `resv_rec` now answers W2 on one line: `reqA/setA/reqB/setB`. TWO requirements because a
  machine can pin two containers; `set=-1` means "requirement not pinned yet", which is NOT
  the same as the bit being clear.
- `pubrest` classifies publish vs restore correctly now; its registry is seeded from the pool
  ctor's call site because the participant walk fills it ~9 s too late otherwise.
- The image copier probe ALREADY EXISTED before I nearly rebuilt it. Check TOOLS.md.
- Two ControlMaster processes on one socket path wedge every rig ssh and look exactly like a
  broken log. Diagnose LOCALLY first (`ps`, `ls` cannot hang). ENVIRONMENTS has the recovery.

## READ BEFORE INTERPRETING ANYTHING

`docs/postmortems/POSTMORTEM_2026-09-03_READING-THE-INSTRUMENT.md`. Seven errors in one
session, five sharing one shape: a conclusion drawn from an instrument's field without first
reading the code that produces it. W2 was measured every boot for a week under a name that
did not say so, and misread three times in one session by the same person who fixed it.
Every mechanical gate in this project fired correctly; the failures were all in the gap the
gates do not cover.

## OPEN, LOWER PRIORITY

- The mac's black render screen, every boot, still unexplained. It has not affected logging.
- The peer identity published by the roster changes to a machine-id form while a session is
  failing (20.284 R7). The fail-closed refusal is correct; the CAUSE is unread.
- The gate byte's provenance (what writes record+0x38 bit 4 in retail). Parked, not closed.
