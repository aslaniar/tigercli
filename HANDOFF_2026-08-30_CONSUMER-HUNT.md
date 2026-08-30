# HANDOFF 2026-08-30 - THE APPEARANCE CONSUMER HUNT

STATUS: live (2026-08-30 evening, updated in place). READ WITH FINDINGS 20.203/20.204,
which supersede this file's hunt list in three places: (1) the black screen is NAMED -
membership checksum rejection -> force-disconnect at peer arrival; (2) the manifest
emitter never fires in fork-hosted flow, so hunt items 1-2 are parked pending a hook
that actually executes; (3) the live pickup point is 20.204 R3 - capture the replica at
the APPLY (rcx-0x858 post-apply, decoder_trace disarmed), diff offline, fix the hash
exactly. The appearance-route closures below all stand; "region B as a candidate" is
now doubly dead (it is a second name block - character-registry-route.md).

## THE ONE-PARAGRAPH STATE OF THE WORLD

The membership profile pipeline is DONE. The server authors a profile block, both clients
decode it, apply it, and run the profile helper on each other's player rows; arbitrary
authored content survives the wire byte-exact in both directions - a name (20.195) and real
per-player account+character identity (20.198) - and a peer's profile PERSISTS in the
client at a per-player array we have now measured from memory (20.201: row 0 at
session+0x3b80, stride 0x1a8). None of that renders a guardian, and we now know why:
REGION A CONTAINS NO APPEARANCE FIELD AT ALL. All 232 bytes are decoded, both accounts,
every chunk (20.202). Appearance reaches a retail client by a mechanism this project has
not identified, and the four candidates we pursued are each closed by measurement.

## WHAT IS CLOSED - DO NOT REOPEN WITHOUT NEW EVIDENCE

1. **The peer channel** (20.196). Client<->client is 98.7% 42-byte heartbeats, lifetime
   maximum packet 234 B, no burst at co-location. It carries no bulk. Measured from a pcap
   this project already held.
2. **The client-side pull** (20.198 R2). Given a peer's well-formed identity in the correct
   SOID band, clients still issue ZERO foreign-root subscriptions - 14 subscribe_in, all
   self, across three boots of escalating identity quality. Telling a client who its peer is
   does not make it ask.
3. **The server-side push** (20.198 R3). queuez_banner_push takes
   `state::account_snapshot(after.accountKey)` - the CONNECTION's own account - and matches a
   character inside it. Self-only by construction, not by oversight. "Add root->account
   resolution" is dead: there is no foreign root to resolve and the code would never run.
4. **Region A as the carrier** (20.202). Fully decoded: a name, an id, an enum, two -1
   sentinels, an empty pair, the account+character SOIDs, a power float, a constant. Not one
   gear hash, shader, ornament or material reference, on two accounts.
5. **The staging-population lane** (20.191/20.192, MINE). The apply's NULL third argument is
   NORMAL at stage 4; substituting for it SUPPRESSED the helper for 8 consecutive applies.
   The detour survives in the tree, DISARMED, default false.

## WHAT IS PROVEN AND USABLE

- Wire path end to end, both directions, two machines (20.194).
- Arbitrary content byte-exact: name cipher inverted and verified against the client
  (20.195), identity in chunk 7 (20.198). `RE_scripts/name_codec.py --selftest` is the
  offline oracle.
- The per-player array: base session+0x3b80, stride 0x1a8, region A at entry+0x00..0xe7,
  chunk 2 at entry+0x80, region B at entry+0x110 (20.201).
- **A POWER VALUE, decoded**: region A chunk 8 carries `00808444` = 1060.0f at entry+0xd0,
  followed by 8 bytes of 0xFF sentinels (20.202 R2). We can WRITE region A. So rendering a
  peer's power/light number is reachable on the pipeline that already works - it does not
  wait on the appearance question at all, and it is the most concrete near-term win on the
  board.

## THE HUNT, IN ORDER

1. **Where does chunk 2's id come from?** It is an 8-byte 0xC5/0xC6-band SOID-family value
   at entry+0x80 with 32 zero bytes after it, and it is the ONE identity field we do not
   author. A gather at 0x140D48490 walks every player and copies that 48-byte region into a
   counted list. We publish chunk 2 ABSENT, and its destination is only zeroed by the
   chunk-2 reader - which does not run when the chunk is absent - so a PEER's slot holds
   zero where the local player's holds a real id, and the gather emits a zero for the peer.
   DO NOT SYNTHESISE THE ID: `(0xC5<<56)|(accountSoid>>8)` fits the mac exactly and FAILS on
   the rig, which stores the mac's account band. Find its source first (20.202 R3).
2. **What consumes the gather's output list?** It writes 48-byte records with a running
   count into a caller-supplied buffer. Whoever reads that list is the nearest thing to a
   named consumer this project has found.
3. **Does any client route accept another account's character record?** The original
   question. Everything in WHAT IS CLOSED says the answer is "not by the routes we know",
   so this is a client-side RE question about routes we do NOT know.
4. **The power number** (see above) - not part of the hunt, just the thing worth shipping
   while the hunt runs.

## METHOD THAT WORKED - REUSE IT

The client's heap is SELF-LABELLING because we choose what the server publishes. Publish a
distinctive value, scan for it, and read the layout off real memory. That found the
per-player array in one boot after three sessions of contradictory offset arithmetic
(0x3b58/0x3c00/0x3c68 - all three wrong). Prefer it over deriving offsets, always.
Corollary paid for twice tonight: scan AFTER the write, and budget observers PER EVENT
CLASS - a shared cap gets spent by the wrong event and the null reads as a finding.

## HONEST CAVEATS

- The slot->account mapping in `profile_identity` is a TEST-RIG mapping by player slot
  order; no machineId->accountKey association exists anywhere in this server. Fine for two
  distinct real accounts, not a production mapping.
- The black screen is UNEXPLAINED. The idle-time hypothesis was falsified by p2(127)
  (87.1 s idle, both machines clean). Seven paired runs, no mechanism, no error line ever
  accompanies it. Do not spend a boot on it; note it if it returns.
- 20.183-20.185's staging narrative is retracted but its DISASSEMBLY stands; read the
  entries with 20.191/20.192 beside them.
