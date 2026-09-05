# FRONT - THE CHAIN FROM WHAT WORKS TO A MOVING GUARDIAN

STATUS: live (2026-09-04 23:xx, opened after 20.298). A forward walk from the last
fully-working link to the end goal: a peer's guardian RENDERED and MOVING IN SYNC on
both clients. Theories are labelled with the CONVENTION that motivates them and the
CHEAPEST instrument that would refute them. Nothing here is measured unless marked.

METHOD NOTE (the frame this page is written in): architectural priors are taken from
the RETAIL CLIENT ONLY - it is Bungie's code. The Sunrise fork is OUR reimplementation;
it is evidence of what has been TESTED, never of what Bungie intended. Inferring
"Bungie's taste" from the fork would re-derive our own assumptions and dress them as
findings. Every convention cited below is sourced to client behaviour or client code.

## THE CONVENTIONS (read off the retail client, cited where used)

  C1 OPTIONAL-CHUNK / PRESENCE-BIT ENCODING. Region A is optional sub-chunks each
     prefixed by a 1-bit presence flag, with the mask BUILT by the reader (20.176).
     Bungie encodes optionality explicitly and self-describingly. COROLLARY, and it is
     the load-bearing one: ABSENT MEANS "LEAVE THE CONSUMER'S VALUE ALONE", not "zero".
     The fork's own encoder comment says exactly that of the four tail groups.
  C2 SCHEMA-HASHED CONTRACTS. worldPopulationSchemaHash 0x80806AC0; the schemakey probe
     resolves type28/type30 against an oracle. Data contracts are versioned and hash-
     identified rather than positional-by-convention.
  C3 FIXED-WIDTH MASK REGISTRIES, SWEPT PER BIT. 32-entry participant scans, maskA/maskB,
     per-bit sweep getters (20.292/20.296). Not linked lists, not dynamic containers.
  C4 CLAIM-OR-BE-DISOWNED OWNERSHIP. The admission sweep DISOWNS any record no slot
     claims by identity (20.280). Ownership is asserted and re-asserted; unclaimed state
     is reaped. This is defensive-by-default.
  C5 VALIDATE AT THE AUTHORITY BOUNDARY, NOT ON EVERY APPLY. The wire apply validates
     nothing (verify=0 skips the lookup3; region B is an unconditional memcpy) while the
     REGISTRY path does verify (20.174 R2/R3). Trust is established once, at admission.
  C6 NAMED STATE MACHINES WITH REASONS. world_controller transitions carry a state name
     and a reason string. Lifecycle is explicit and inspectable.
  C7 PLANE SEPARATION. Membership carries IDENTITY only - region A decodes to xuid,
     SOIDs, a power float and sentinels, with NO gear/shader/ornament anywhere (20.202).
     Appearance and motion are therefore OTHER planes by construction, not by omission.

## THE CHAIN, FORWARD FROM WHAT WORKS

### LINKS THAT WORK (verified-by-execution, both machines - FRONT_e2e-stack Part 1)
  W1  boot + signon (identical 24-state sequence)
  W2  BAP / activity plane
  W3  activity join + region seeding
  W4  session membership: identical peer tables at real endpoints
  W5  instance co-location: one Tower instance, "citizen join succeeded"
  W6  transport: direct client<->client DTLS, symmetric
  W7  gameplay plane: BOTH playerAdd received, decoded, applied as TWO DISTINCT PLAYERS
  W8  *** NEW, 20.298 *** the peer's PARTICIPANT ENTRY EXISTS IN THE TABLE. On the rig,
      index 1 is not self and carries the mac's member key. maskB names it (the walk
      reaches it) and maskA bit is SET (cond3 PASSES).
      => THE MASK MACHINERY IS NOT THE BLOCKER. That is new and it narrows the front.

### THE WALL, STATED AS ONE MEASURED FACT
  participant record stride 0x2AC0; the gate byte is +0x38; cond5 requires bit 4 SET.
  ACROSS EVERY SAMPLE EVER TAKEN, ON EVERY MACHINE, IN EVERY BOOT: f38 = 0x00.
  31,188 samples (mac) + 3 (rig) tonight alone. Zero exceptions. The local player's own
  record included.
  Consequence chain (each step already measured):
    bit 4 clear -> cond5 fails -> the guard is never reached -> THE CLAIM NEVER HAPPENS
    -> the admission sweep disowns the record (C4) -> the creation loop re-engages it
    forever (11,491x on the rig for the mac's record, 20.298 R1) -> no entity persists
    -> no body renders.

### THE STRUCTURAL ASYMMETRY NOBODY HAS EXPLAINED
  The LOCAL player also has f38=0x00 and also fails cond5 - and renders fine.
  Therefore the local player does NOT reach the world through this gate.
  READING (taste-led, C5+C7): an authoritative client owns its own player directly and
  never "receives" it, so it needs no claim. The participant table + cond5 gate is the
  REMOTE-replication path. This is the normal shape for a peer-hosted simulation and it
  means THE LOCAL PLAYER IS NOT A CONTROL FOR THIS GATE - it never had to pass it.
  (This also corrects the instinct, twice acted on in this project, to use the local
  player as the positive control for peer machinery.)

### THREE STRUCTURES THAT HAVE BEEN BLURRED - DO NOT CONFLATE
  S1 RESERVATION RECORD  - rec+0x3112 birth-set word / rec+0x3114 claim word (20.280,
     20.286, 20.287). The admission/claim accounting.
  S2 PARTICIPANT SLOT/RECORD - stride 0x2AC0; +0x38 gate byte (cond5); +0xEC the peer's
     86-byte card as actually landed (20.283); +0x142 the card the guard reads (20.280).
  S3 ENTITY / POOL OBJECTS - what pb_create builds and the receive vptrs attach to.
  20.286's "the bit is stamped at record creation" is about S1. cond5 is about S2. They
  are different fields in different structures and a finding about one does not transfer.

## THE THEORIES, RANKED BY (probability x cheapness to refute)

### T1 *** LEADING *** THE TAIL GROUPS ARE THE WRITER, AND WE MARK THEM ABSENT
  CLAIM: participant flags (including +0x38) are carried by the four per-body TAIL GROUPS
  and/or the 264-byte per-member identity block. The fork marks all of them absent:
      per MEMBER : 3 x kEntryFieldAbsent   per BODY : 4 x kTailGroupAbsent
  The fork's OWN comment on the tail groups reads "which leaves the consumer's own values
  alone" - i.e. absent = keep current. The participant's flags therefore sit at their
  construction default, 0x00, for the entire session, on every machine, forever.
  WHY IT FITS: C1 exactly - a presence-flagged delta protocol where absent means unchanged.
  It also EXPLAINS THE UNIVERSALITY that every other theory struggles with: f38=0x00 for
  self and peer alike, every boot, because nothing has EVER written that byte from the wire.
  AND IT SURVIVES 20.298: run A exonerated transport-identity and the profile block, which
  live in the PLAYER ROW. The tail groups and the member identity block are a DIFFERENT
  part of the body and were never under test. The exoneration does not reach them.
  REFUTED BY: decoding a tail group and finding it carries no participant flags; or
  finding a non-wire writer of +0x38 that should have fired.
  CHEAPEST TEST: STATIC. The four tail groups and the 264-byte block are never written and
  their contents are unknown "by construction, not by measurement" (O4/O5). Read the
  client's DECODER for them. No boot.

### T2 THE GATE BYTE IS OWNED BY THE PEER-CONNECTION PLANE, NOT THE MEMBERSHIP PLANE
  CLAIM: bit 4 means "this participant's owning connection is established and has asserted
  ownership of its objects", written by the peer-transport/ownership layer.
  WHY IT FITS: C7 (plane separation) and D2's actual topology - each machine is the
  authority for its own player. A membership row says who EXISTS; it should not be able to
  assert that a remote machine's simulation is live. Bungie would not let roster data grant
  simulation authority.
  TENSION: the peer channel IS established and symmetric (W6) yet carries no bulk (20.196).
  If T2 were the whole story the byte should already be set. So T2 likely needs a
  sub-condition: an ownership assertion that our peers never send because nothing tells
  them to.
  REFUTED BY: the writer of +0x38 living in membership-apply code rather than transport.
  CHEAPEST TEST: STATIC - name the writer. See "THE ONE QUESTION" below.

### T3 THE PHYSICS/SIMULATION JOIN IS THE MISSING PLANE
  CLAIM: a participant becomes simulable at physics join; the gate byte is set there.
  WHY IT FITS: C6/C7. The client's own state machine runs
  initial_slice_set_loading -> physics_join -> in_world, spending ~6 s in physics_join,
  while the server logs ZERO ev=physics all boot. A whole physics-host subtree
  (12+ files, 186 CMake refs) has never been enabled.
  IMPORTANT DISTINCTION THE CORPUS MAY HAVE CONFLATED: O2 ruled this out on the grounds
  that OUR physics subtree "produces no wire output either way". That is a statement about
  the FORK. It is NOT the same claim as "the CLIENT expects no physics-plane input". The
  second was never tested. Tonight the rig hung IN initial_slice_set_loading, one state
  before physics_join, which keeps this alive.
  REFUTED BY: reading physics_join's client code and finding it consumes no inbound
  message class we fail to send.
  CHEAPEST TEST: STATIC, then femu. No boot.

### T4 CIRCULAR BOOTSTRAP (receiver <-> claim)
  CLAIM: the byte is set on first entity receipt; ent_recv never fires; so nothing ever
  sets it. A chicken-and-egg broken only by an explicit bootstrap event.
  WHY IT FITS: 20.296 - the receive vptrs are installed BY the mask lifecycle, i.e. the
  receiver is downstream of the same machinery the claim gates.
  WHY I RANK IT LOWER: C4/C5. Bungie's designs establish trust at an admission boundary
  precisely so the steady-state path cannot deadlock. A pure circularity with no bootstrap
  would be a design error, and this code is retail-shipped and worked for millions.
  Its existence would more likely indicate WE are missing the bootstrap message.
  REFUTED BY: finding the bootstrap. (Note: that is the same artifact T1/T2/T3 predict.)

### T5 (RULED OUT AS PRIMARY) THE MASKS
  maskA is SET on the rig's peer entry and maskB names it. The masks work. Any theory
  that blames mask population is contradicted by 20.298's own data. Recorded so it is
  not re-chased - this has consumed boots before (POSTMORTEM_2026-08-31_THE-EMPTY-MASK-LOOP).


## *** THE HUSK: THE POSITIVE CONTROL THIS PROJECT HAS BEEN MISSING (folded in
## 2026-09-04 late, from the user's clarification + FINDINGS 20.135) ***

THE SEQUENCE (user-reported, on record since 20.135): the client lands in the Tower ->
THE SCREEN GOES BLACK -> it recovers -> a SECOND GUARDIAN is present, and THE ONE THE
PLAYER CONTROLS IS THE NEW ONE. The original body is left behind INERT. User, verbatim:
"it went black and then the duplicate spawned in, and that's the one i have control
over." And: "it's always been like that" - the sequence PREDATES the public-membership
lane entirely.

THE FACT THAT MAKES IT VALUABLE: **IT FIRES SOLO.** p2(88) run 3 produced the full
sequence with the RIG NOT BOOTED AT ALL, confirmed independently server-side (every
`stage=identity result=ok tag=8` in that window carries the mac's 0xC0A801A4; the rig's
0xC0A80188 does not appear until later). It is NOT a co-presence effect and NOT a peer
body. It is the local player's own previous body, orphaned.

WHAT IT PROVES, AND IT REFRAMES THE WHOLE FRONT:
  THIS CLIENT WILL RENDER A CHARACTER BODY THAT NOTHING IS DRIVING.
  Visible, ownerless, motionless - which is exactly the end state we want for a peer
  body, minus a motion source.
  => The wall is NOT "the client refuses to build bodies for non-self". It plainly will.
  => THE WALL IS: THE CLIENT BUILDS BODIES THROUGH A PATH THE PEER RECORD NEVER REACHES.
     Respawn/container-rebind reaches entity creation AND COMPLETES IT. The membership
     path engages the creation loop 11,491 times and never completes (20.298 R1).
     Same destination, two roads, one arrives.

WHY THIS IS THE BEST INSTRUMENT ON THE BOARD:
  - it is SOLO: one machine, no rig, no pairing, no lobby claims, no network coupling -
    which is exactly the class of failure that cost four of five launches on 2026-09-04;
  - the deployed p2-171 client ALREADY carries every probe needed (pb_create, ent_make,
    pgate/ptable, mgr_*). No new instrument, no rebuild, no hook-depth risk;
  - it produces a SUCCESSFUL body creation to diff against the failing peer path.

THE DECISIVE READING - IT SETTLES T1 EITHER WAY:
  Watch f38 on the participant table across the husk event.
    f38 becomes NONZERO on the husk's record  -> cond5 IS on the render path, the byte
      IS writable in practice, and the state that wrote it is NAMED. T1/T2/T3 collapse
      to "which path did that, and why does membership not take it".
    f38 stays 0x00 while a body renders anyway -> COND5 IS NOT ON THE RENDER PATH AT
      ALL, and this front page's central premise is WRONG. That is worth knowing before
      another boot is spent on the +0x38 writer hunt.

STILL UNCOLLECTED, COSTS NOTHING (20.135's own discriminator, open since 2026-08-28):
  WHERE DOES THE HUSK STAND?
    (a) WORLD-CONTAINER REBIND -> at the position held BEFORE the screen went black.
    (b) DOUBLE SPAWN            -> at the SPAWN POINT.
  One user observation eliminates one reading. Ask for it every time the sequence fires.

CONNECTION TO THE 2026-09-04 BLACK SCREEN (correcting 20.298's "no established cause"):
  "black screen on landing" is PHASE ONE of this documented sequence. On 2026-09-04 it
  went black and never recovered - plausibly the same mechanism ARRESTED PARTWAY rather
  than a new environmental fault. 20.298 called it unexplained; that was written without
  20.135 in hand. Not proven, but it is now a named candidate rather than a mystery.

## THE ONE QUESTION THIS FRONT REDUCES TO
  WHAT WRITES BIT 4 OF PARTICIPANT_RECORD + 0x38 ?
  Every theory above is a different answer to it, and naming the writer discriminates
  between ALL of them at once. It is static, boot-free, and nobody has run it.
  INSTRUMENT NOTE (learned the hard way tonight): `field_xref.py 0x38` is the WRONG tool.
  0x38 is a ubiquitous small offset, the useful encodings are disp8 not disp32, and the
  20 disp32 hits are mostly `call qword [reg+0x38]` misclassified as RMW. The right
  approaches, in order:
    (a) find the ALLOCATOR/INITIALISER of the 0x2AC0-stride record and read its field
        setup - a constructor names its own flags;
    (b) walk out from the KNOWN readers (cond5's reader 0x1404DD470, the guard
        0x141703910) via callers.py and look for the sibling that sets what they test;
    (c) dump_search the p2-146 dump for a 0x2AC0-strided table and check whether ANY
        record anywhere ever carried a nonzero +0x38 - a single nonzero instance would
        prove the byte is writable in practice and name the state that did it.

## THE TAIL: "MOVING IN SYNC" IS A SEPARATE PROBLEM, NOT A SEPARATE WALL
## (CORRECTED 2026-09-04 late - the husk is ONE event exhibiting both; see THE HUSK below)
  Rendering a body and syncing its motion are different problems and the second is not
  merely downstream. Even with a body:
    M1 motion must be authored by the owning machine (C7, peer authority)
    M2 it must travel the client<->client channel - which is ESTABLISHED but CARRIES NO
       BULK (20.196). A rendered but motionless clone is the predicted intermediate state,
       and 20.53 saw exactly that ("a body that presumably does not move").
    M3 the fork has no relay for it and no concept of simulation ownership.
  PLANNING CONSEQUENCE: do not treat "guardian renders" as one milestone from here. It is
  RENDER (this front) then MOTION (unopened). Budget accordingly.

## WHAT WOULD MAKE THIS PAGE WRONG
  - a nonzero f38 anywhere in any dump (kills the "never written" premise of T1)
  - the +0x38 writer living in membership-apply (kills T2, strengthens T1)
  - physics_join consuming nothing inbound (kills T3)
  - the local player passing cond5 in some state (kills the asymmetry reading, and would
    restore the local player as a usable control)
