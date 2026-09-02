# POSTMORTEM - THE WRONG QUESTION: ~10 BOOTS ON A GATE, WHILE OUR OWN DATA SAID SUPPLY

STATUS: closed postmortem (2026-09-02). Subject: the strategic error behind the
20.220-20.259 arc, found by re-reading three retired fronts against p2-161's result.
Companion records: FINDINGS 20.258, 20.259. Siblings: the p2-160 addendum in
POSTMORTEM_2026-09-01_INSTRUMENTATION.md (the instrument errors of the same session).

## THE ONE-LINE SUMMARY

For roughly ten boots the project asked "WHICH FLAG UNLOCKS THE PEER?" when its own
measurement, recorded forty findings earlier in this very file, already said NOTHING EVER
ASKS TO CREATE A PEER ENTITY. The gate was never shut. There was nothing behind it.

## THE SENTENCE THAT CONTAINED THE ANSWER

FINDINGS 20.219 RESULT 4, written 2026-08-31, closing the entity-index front:

    "CONCLUSION: ~145 slots sit free and the client NEVER ASKS. Creation is not reached.
     Slot supply was never the blocker. THE ENTITY-INDEX FRONT IS CLOSED."

Both halves are in one paragraph. The first half - **the client never asks; creation is
not reached** - is the most important measurement this project has taken. The second half
closed the front that contained it.

The reasoning was: "is there room for a peer entity?" -> yes, 145 free slots -> supply is
not the blocker -> front closed. That answers a SUB-QUESTION. The question that mattered
was "does anything ever ASK for a peer entity?", and the same probe answered it: no, zero
attempts across the entire paired window. An unasked question is not a satisfied one.
"Supply is not the blocker" is true and irrelevant; "creation is never initiated" is the
whole problem, and it was written down as a supporting detail.

## WHAT p2-161 COST TO RE-DISCOVER

p2-161 forced bit 4 of the peer's +0x38, every condition the probe tracks passed for 294
consecutive walks, and nothing rendered and nothing was constructed (20.259). That is the
same fact from the other end: you cannot unlock your way to an entity that was never
created. The boots between 20.220 and 20.259 - the c4 front, the tracking cluster, the
contactable byte, the gate-byte writer hunt, the femu byte map - were all searches for the
lock on a door with no room behind it.

## THE SECOND ERROR: A RETRACTION THAT BURIED THE POSITIVE SIGNAL

This is worse than the first, because the project had already made the client TRY.

FINDINGS 20.208 RESULT 6 (2026-08-30), titled "WE PROVOKED THE ENTITY PATH FOR THE FIRST
TIME": arming world_population made the server push `type=7` (the sobject record) and
`type=52` (epoch); the client accepted both and then attempted `failed to create
'player_broadcast' entity` 50 times - "against ZERO such lines in every previous run
(p2-131/132/133/135 archives all read 0). **Our injection is what makes the client try to
build a player entity at all.**"

FINDINGS 20.213 RESULT 1 (p2-138) sharpened it: changing a SERVER setting (the lease size)
changed whether the client attempts creation at all - 58 attempts, fired ON
membership_replication (type-12) pushes, 21 ticks after a type-12 body. "The attempt gate
is keyed to the free pool. FIRST TIME THE ATTEMPT HAS EVER FIRED SOLO." Its RESULT 2
localised the failure precisely: creation dies BETWEEN "roster member exists" and the index
request. Its VERDICT even named the next front: the archetype must resolve before creation,
and **our fork's type-12 body may need per-member entity/archetype fields it does not carry
today** - a server-side hypothesis, exactly the shape the project needs.

Then 20.219 RESULT 5 reclassified those failures as "Self-allocation during load... They
have no relation to peers - they fire SOLO and stop once the mask fills."

That reclassification does not address its own counter-evidence. If the failures were an
unrelated startup race they would appear in every run; 20.208 R6 records FOUR prior runs
with ZERO of them, and 20.213 R1 records them appearing and disappearing as a SERVER
SETTING changed. A startup race does not switch on when you edit the server's lease size.
The reinterpretation may still be partly right - the failures DO fire solo - but "fires
solo" was treated as proof of "unrelated to peers", when the honest reading is that our
injection provokes a creation attempt whose failure is not peer-specific. Those are very
different conclusions, and the front was closed on the stronger one.

NET EFFECT: the project's only known lever for making the client attempt to build a player
entity - a SERVER-SIDE lever, reachable from the wire, discovered twice - was retired as
noise, and the next ten boots went looking for a flag.

## THE RE-READ: WHICH RETIREMENTS WERE PREMATURE

  20.219 ENTITY-INDEX / SLOT SUPPLY - **PREMATURE, RE-OPEN.** Its own RESULT 4 is the
    supply finding. Its RESULT 5 retracted the positive signal without meeting 20.208 R6's
    control or 20.213 R1's settings correlation. What is genuinely closed: slot supply as a
    SCARCITY problem (there are ~145 free). What is wide open and was never asked: what
    makes the client initiate creation for a peer.
  20.202 REGION A APPEARANCE FIELDS - **CORRECTLY CLOSED, UNAFFECTED.** All 232 bytes are
    accounted for field-by-field on two accounts: name, id, enum, sentinels, SOIDs, a power
    float, a constant. No gear, shader or geometry reference. This rests on decoded data,
    not on the gate assumption, and it stays closed.
  20.196 / 20.208 R5 PEER CHANNEL AS APPEARANCE CARRIER - **CORRECTLY CLOSED FOR WHAT IT
    TESTED; DO NOT EXTEND IT.** The measurement is sound: 42-76 byte packets, largest ever
    268 B, dead flat with no burst at co-location - no bulk capacity, so a packaged guardian
    does not cross it. But it tested APPEARANCE (bulk gear). It says nothing about
    continuous POSITION/STATE updates, which are small, frequent and flat - the exact shape
    it measured. 20.196 R2 even describes the channel as "shaped for liveness, not for
    bulk". If it is ever cited as "the peer channel is irrelevant to rendering", that is an
    overreach the finding does not support.

## HOW THE FRAMING SURVIVED SO LONG

1. **A sub-question's answer was recorded as the front's verdict.** Once "THE ENTITY-INDEX
   FRONT IS CLOSED" was in STATE's DEAD ENDS list, the sentence three lines above it -
   "the client NEVER ASKS" - stopped being read. STATE's dead-end list is load-bearing and
   is trusted by every subsequent session, including this one; a wrong entry there costs
   weeks, not hours.
2. **Elimination has no natural end.** Without a positive reference, "the writer is not
   here either" can be produced indefinitely, and each negative feels like progress because
   it is genuinely new information. Nothing in the process asked whether the SEARCH SPACE
   was right, only whether the last search was clean.
3. **The gate framing was never itself a marked claim.** Chain marks were applied
   diligently to every link WITHIN the framing (U16) and never to the framing itself. "A
   flag gates the render" was assumed in every brief from 20.220 onward and marked in none.
4. **The contradiction was visible and was not looked at.** pgate printed FAIL-cond5 for
   the LOCAL, RENDERING player in every boot since it was written - 603 samples in p2-150
   alone. A rendering entity failing the render gate is a refutation of the framing, printed
   hundreds of times per boot, read as a peer problem every time.

## WHAT TO DO DIFFERENTLY (candidate rules)

  A. **A FRONT IS CLOSED BY ANSWERING ITS QUESTION, NOT A SUB-QUESTION.** When a boot's
     verdict closes a front, the closing sentence must restate the front's ORIGINAL
     question and answer that. 20.219 would have failed this instantly: the front was
     "why is no peer entity created", the answer given was "there is enough room".
  B. **A RETRACTION MUST MEET THE EVIDENCE IT RETRACTS.** 20.219 R5 reversed 20.208 R6 and
     20.213 R1 without citing either. A retraction that does not name and address the
     control it overturns is an opinion.
  C. **THE WORKING CASE IS A CONTROL AND MUST BE READ EVERY BOOT.** The local player renders.
     Any gate it fails is not the render gate. This one line, applied to pgate's own output,
     would have ended the +0x38 front before it started.
  D. **MARK THE FRAMING, NOT ONLY THE LINKS.** Every brief's CHAIN MARKS should carry the
     front's premise as link zero, with a mark. "The render is gated on a flag: ASSUMED"
     would have invited the test that finally happened at p2-161.

## THE THROUGH-LINE

The instrument postmortem for this session says I audited the diff and treated everything
around it as given. This is the same error at project scale: each boot audited its own
front and treated the FRAMING as given. Both were fixed the same way in the end - by
running the working case and the broken case side by side and looking at what actually
differs, rather than reasoning forward from a premise nobody had marked.
