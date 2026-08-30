# FRONT - END-TO-END STACK ANALYSIS (2026-08-29)

STATUS: live, header rewritten 2026-08-30. THE PROFILE PIPELINE IS NOW DONE end to end,
both directions, two machines (20.194); it carries authored content byte-exact - a name
(20.195) and account+character identity (20.198) - and a peer's profile persists in a
per-player array measured from memory (20.201).
*** THIS PAGE'S APPEARANCE ANALYSIS IS SUPERSEDED BELOW. *** Part 2d called region B "the
only remaining candidate" for appearance. That is WRONG twice over: region B is a second
NAME block, and region A - fully decoded on two accounts in 20.202 - contains a name, an
id, an enum, two -1 sentinels, an empty pair, the account+character SOIDs, a POWER float
and a constant, with NO gear hash, shader, ornament or material reference anywhere. The
membership profile block cannot carry appearance at all.
Every other candidate is closed by measurement too: the client<->client channel carries no
bulk (20.196), clients never pull a peer's character record even knowing exactly who the
peer is (20.198 R2), and the server's appearance push is self-only by construction
(20.198 R3). Appearance reaches a retail client by a mechanism this project has not
identified. Pickup doc: HANDOFF_2026-08-30_CONSUMER-HUNT.md.
Parts 1 and 3 below remain accurate. Read Parts 2 and 4 as history.

## PART 1 - THE CHAIN THAT WORKS (7 layers, all VERIFIED-BY-EXECUTION, both machines)

| # | Layer | Evidence from p2(110) | Mark |
|---|---|---|---|
| 1 | Boot + signon | both clients walk an IDENTICAL 24-state sequence, `bootflow:start` -> `activity:in_world`; no state skipped, no divergence | V-X |
| 2 | BAP / activity plane (TCP 30975) | both: `[AC PUBLIC TARGET CON-Y EST-Y AH->9eaa300100200003 MEM-5]` | V-X |
| 3 | Activity join | server: `join_result ah_sid=0x9EAA300100200003 status=accepted` + `bind result=public_host_row sameid=1`, BOTH clients | V-X |
| 4 | Region seeding | `session_seed result=seeded session=0x...00200003 from=0x...00200001 region=56` | V-X |
| 5 | Session membership | both: `peers valid 0x7 / players valid 0x3`, IDENTICAL peer tables at real endpoints (#0 server:30976, #1 rig:3097, #2 mac:3097) | V-X |
| 6 | Instance co-location | both: citizen join -> PUB56.56, session `7EB63346:CFB4AEE1`, "succeeded!" | V-X |
| 7 | Transport | direct client<->client DTLS: 211/205 packets on 3097<->3097, symmetric | V-X |
| 8 | Gameplay plane (UDP 30976) | 12 membership bodies; revisions 6-12 all `members=3 players=2`; BOTH `playerAdd` (id=34) received, decoded and applied as two distinct players | V-X |

CORRECTION KEPT VISIBLE: my first read of layer 8 said `players=1`, from a `head -6` that
truncated the list at revision 4. There are TWELVE bodies and the last seven carry
`players=2`. The gameplay membership plane is CORRECT. (Same class of error as 20.172's
three retractions - a filtered view asserted as a finding.)

ALSO RULED OUT while checking, so nobody re-chases them:
- `seq=10` on both player adds is NOT a collision: the log prints `request.sequence`
  (the value the CLIENT sent), not the server's allocator output. The allocator at
  group_host.cpp:900-921 correctly takes max(addSequence)+1 and the lowest free slot.
- `entries=0` on all 3038 gameplay packets is NOT "zero entities replicated":
  `entries` is `packet.ack.reportedCount`, pure ACK bookkeeping.
- `foreign=0` is NOT a peer count: it is `activityJoinedForeignSession` (20.171 R1).

## PART 2 - WHAT IS MISSING, AND IT IS ALL ONE THING

Everything above works. NO GUARDIAN RENDERS because the profile/appearance block is
unimplemented IN BOTH DIRECTIONS, in code we own.

### 2a. THE SEND SIDE - one hardcoded bit (VERIFIED-BY-READING)
`middleware/gameplay/group/session_messages.cpp`:
```c
  /** A clear flag ends a player row after its identity group. The profile block it
   *  would gate has no writer here, so no row carries one. */
  constexpr std::uint64_t kPlayerProfileAbsent = 0;
  ...  write_player_delta(...) { ... && writer.write(kPlayerProfileAbsent, kFlagWidth); }
```
That bit is `pc=0` on every group_target row on both machines (V-X, p2(110)).

### 2b. THE RECEIVE SIDE - the mirror gap (VERIFIED-BY-READING)
`server/gameplay/group/group_host.cpp:931`:
```c
  // The player block and its tail are not decoded, so the body is reported and not consumed.
```
We neither encode an outgoing profile block nor decode an incoming one.

### 2c. THE FULL INVENTORY OF WHAT OUR ENCODER NEVER PUBLISHES (VERIFIED-BY-READING)
Per membership body, `write_membership`:
```
  per MEMBER : 3 x kEntryFieldAbsent  -> "no 264-byte identity block and neither
                                          trailing delta-entry flag"
  per PLAYER : 1 x kPlayerProfileAbsent -> the appearance gate (2a)
  per BODY   : 4 x kTailGroupAbsent     -> "the four tail groups are all omitted,
                                          which leaves the consumer's own values alone"
```
Nobody has ever established what the 264-byte member identity block or the four tail
groups carry. They are absent by construction, not by measurement.

### 2d. WHY THE HARVEST LANE IS THE WRONG LANE (VERIFIED-BY-EXECUTION, 20.173)
p2(113) harvested a real profile blob. Region A decoded byte by byte is IDENTITY -
xuid, account/character SOIDs, a 1060.0f power value, -1 sentinels - with ZERO gear
hashes, shaders or ornaments. Appearance is not in region A. Region B (136B) is the
only remaining candidate and PHASE 5 established it is written ONLY from a wire delta -
i.e. it is SERVER-SOURCED. The appearance lane is server-side authoring, not client
memory harvesting.

## PART 3 - OUTLIERS (things nobody in this project has examined)

| # | Outlier | Status | Mark |
|---|---|---|---|
| O1 | `serverDefaultEntity{false}` | **CLOSED 20.174 R5: DEAD.** Three references tree-wide, all settings-parsing; nothing reads the gate. Not a lane, an empty setting | V-R |
| O11 | client->server BAP was never decryptable until 20.175 R4; `bapdecode.py` only does s2c. svc-171 (36,720B) and svc-10 (2475/4812) upstream bodies are UNREAD | new seam, tools in p2-114_grand_capture/ | V-X |
| O2 | `physicsHostSession{false}` - a whole physics-host subtree (12+ files, 186 CMake refs), wired into `gameplay_runtime.cpp` (initialize/service/reset/shutdown), never enabled. Server logs ZERO `ev=physics` all boot while both clients spend 6 s in `activity:physics_join`. | RULED OUT as the render path by its OWN doc: "It produces no wire output either way." Do not enable it hoping for guardians; it is a render-thread frame stall. | V-R |
| O3 | `activityPublicMembership` is TRUE in deployed settings, and its doc warns "a body that does not carry the local player destroys it" | live and load-bearing; interacts directly with 2a. Any profile work must not drop the local player row | V-R |
| O4 | 264-byte member identity block (3 flags/member) | never written, never decoded, contents unknown | V-R |
| O5 | four tail groups per body | never written; "leaves the consumer's own values alone" | V-R |
| O6 | `activityJoinedForeignSession` - 6 reads, 0 writes tree-wide; makes keepalive_push:281 dead code and `foreign=` a constant | real defect, NOT on the milestone path | V-R |
| O7 | `peer_advert peer_citizen=1` ONLY on the 8 `result=built` lines where regions DIFFER (48 vs 56); all 62 same-region lines report 0 | unexplained | V-X |
| O8 | a second activity soid `0x9EAA300100200004` alongside `...0001` | unexplained | V-X |
| O9 | `public_row_gate` = 94% of the entire server log | a firehose that can bury any real signal; it is exactly the condition that hid things today. Rate-limit it | V-X |
| O10 | rig black screen | USER-CONFIRMED PRE-EXISTING, reproduces SOLO, inventory opens, zero errors. A CONSTANT, not a signal | V-X |

## PART 4 - WHAT I WOULD DO NEXT, IN ORDER (updated 20.185: the writer SHIPPED, the
## wedge is found, and the remaining work is the staging detour + region B)

0. ~~The wire encoding + writer.~~ **DONE 20.178-20.179: shipped bit-exact at p2(115)**
   (178 bits, not the "150" the 20.177 summary claimed - see the correction in code).
   The boot proved: the body is delivered, acked, and decoded - counts and row verified
   in-struct by the decoder_trace instrument (20.182-20.185).
0b. ~~Why doesn't it apply?~~ **FOUND 20.183-20.185: the apply reads its profile content
   from a STAGING OBJECT whose pointer (selected by session stage; stage=2 at apply time)
   is read from slot [+0x1af60] - which no readable code ever writes.** Garbage in, row
   skipped, no crash, no log. The stage-driver's caller is VMP-virtualized - do not
   reverse it statically.
1. **Read region B's layout.** 136 bytes, apply leaf `0x1417af2d0`, one caller inside
   the L9 apply `0x141781800`. Its layout is UNREAD - this is the single largest
   unknown and it is static analysis, no boot, no risk.
1b. **The staging-population write detour** (HANDOFF_2026-08-29_STAGE-TRAY.md, job
   item 1-3): lessons review first (first WRITE detour), then populate the staging
   fields from the decoded struct at apply entry, then ONE mac run = the rung
   experiment with the mac's own harvested sheet.
2. ~~Does the present bit help or hurt?~~ **ANSWERED 20.174 R2/R3: the wire apply
   VALIDATES NOTHING.** verify=0 makes 0x1417AF6D3 skip the entire lookup3, and region B
   is an unconditional 136B memcpy. An authored block needs no correct hash. (The
   registry path DOES verify - which is what made the hash look mandatory in 20.173 R4.)
3. ~~Chase O1.~~ **CLOSED 20.174 R5: the gate is dead code, nothing reads it.**
4. ~~Does a profile block cross the wire?~~ **ANSWERED 20.175 R1/R2: NO, three
   independent ways** - zero wire-path applies on either client, zero svc-9 upstream,
   and every downstream body is ours with the bit hardcoded off. So there is no captured
   reference and the encoding cannot be copied from the wire. **OVERTURNED 20.178+:
   the block now CROSSES THE WIRE (the writer ships, the body delivers) - the refusal
   moved to the client's apply layer (see 0b).**
5. ~~The wire->delta decoder.~~ **FOUND AND CONFIRMED 20.176: `0x14173BFC0`**
   (`0x14173B920` REFUTED - a memcmp comparator). The player-row encoding is specified
   field by field and independently reproduces CLAIM 5. The profile gate is a single bit
   at entry+0x21. **And the block is NOT raw bytes** - region A is optional sub-chunks
   each prefixed by a 1-bit presence flag, with the 9-bit mask BUILT by the reader. The
   obvious guess would have corrupted the body from the gate bit onward.
   **The width tables are now READ (20.177).** The writer SHIPPED bit-exact (20.178;
   178 bits, not 150 - the summary was wrong). Remaining after pc=1 lands: the payload
   encodings of region-A chunks 2/6/7/8/9 (chunk 8 = schema engine) and region B's body.
6. NEW SEAM (20.175 R4): the client->server BAP direction now decrypts (nonce = base
   with last byte XOR 0x01). The svc-171 36,720-byte body and the svc-10 bulk
   (2475/4812 x24) are the largest UNREAD objects on our wire and have never been
   looked at by anything.
5. Only then: write the block in `write_player_delta`, using the harvested region A as
   the identity-half FORMAT REFERENCE (unvalidated - 20.173 R4).

## PART 5 - PROCESS DEBT THIS ANALYSIS INHERITED
20.172 retracts three of one session's diagnoses; 20.173 R1 records a boot lost to an
unverified hook RVA; this document corrects a fourth misread (layer 8) inside itself.
Every one had the same cause: a claim asserted from a filtered or truncated view without
the census the project's own U2 / L1-corollary-2 demand FIRST. Two gates now exist
against that class - `verify_hook_rvas.py` (addresses) and the existing bootstrap/gate
scripts. There is no gate for "you grepped with head -6"; that one is discipline.
