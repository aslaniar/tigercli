# BOOT BRIEF p2(125) - IDENTITY, BYTE ORDER FIXED: DOES A CLIENT ASK FOR A PEER'S RECORD?

STATUS: live (2026-08-30). Reads with FINDINGS 20.197 (why p2(124) could not answer),
20.196, 20.173.

## WHY THIS BOOT REPEATS p2(124)

p2(124) published identity with `bits::write_raw_u64` - a LOW-BYTE-FIRST raw writer - into
chunk 7, whose reader is `read_wide(0x40)`, a 64-bit VALUE read that is most-significant-bit
first. The SOIDs landed byte-reversed: `9EAA300100100100` stored where `000110000130AA9E`
was wanted. A reversed SOID has a completely different high band, so any band check in the
client discards it - which makes p2(124)'s "0 foreign roots" uninformative rather than a
negative result. Fixed with `writer.write(soid, 64)`. Nothing else changed.
CONFIRMED ALREADY (20.197 R2): the identity SELECTION is correct. slot 1 published account
`...110100` character `...110103`, and the rig's OWN local profile independently stores that
same pair - so the account walk and the selected-character walk are both right.

## PURPOSE - what this boot learns, win or lose

This is a FEASIBILITY TEST FOR THE CHARACTER-RECORD LANE, not a content rung.

20.196 established that a peer's appearance does not cross the client<->client channel, so
it must come from the server. But p2(123) measured that neither client EVER asks the server
for a peer's character record: 13 `ev=queuez stage=subscribe_in` events, and every single
`root` was the requester's own (key=0 -> 0x9EAA300100100100, key=1 -> 0x9EAA300100110100).
A peer's player row currently carries a NAME and 200 zero bytes - it names nobody, so there
is nothing for a client to ask about.

This boot publishes real identity (region A chunk 7: account SOID + character SOID) on every
player row and asks whether a client, now told WHO a peer is, requests that peer's root.
That answer decides whether the root->account resolution work (20.173) is worth building -
before it is built, not after.

## GRAPHICS DELTA

ZERO new rendered models expected. Identity is not appearance: 20.173 decoded region A byte
by byte and found no gear hashes, shaders or ornaments. Nothing new is drawn.
Minimization: bytes inside a body both clients already receive, decode and apply.

## FALSIFIABLE CLAIM (the one contract under test)

CLAIM: with each player row carrying a real account+character SOID, at least one
`ev=queuez stage=subscribe_in` appears whose `root` is NOT the requesting key's own primary
- i.e. a client asks the server for a PEER's record.
BASELINE TO BEAT: p2(123) 13 subscribe_in / 0 foreign (name only);
p2(124) 14 / 0 (identity present but byte-reversed, so uninformative).

CONTENT NEGATIVE (pre-named): identity lands correctly (the byte prediction below matches)
and STILL every subscribe_in root is the requester's own. Then the client does not request
peer records from this data at all, and the root->account resolution would have had nothing
to resolve. That RETIRES the character_record server lane as currently conceived and sends
the appearance question back to "what does the client do with a peer's identity, if
anything" - a far cheaper thing to learn now than after building the resolution.

SECOND CONTENT NEGATIVE: the identity bytes STILL do not match. Then the field is not a
plain MSB-first 64-bit value either, and chunk 7's encoding needs a direct read of
0x1416D3B20's caller rather than another guess between two conventions.

THIRD: the decoder returns ok=0. Chunk 7 adds 128 bits per row and flips mask 0x109 -> 0x129.
20.188's instrument reports it directly.

## PRE-REGISTERED BYTE PREDICTION (computed before the boot)

Chunk 7 lands verbatim at stored +0xc0 and +0xc8, so the `ev=ingress stage=dump tag=regionA
off=192` line must BEGIN with account-then-character, little-endian:
    slot 0  000110000130AA9E 010110000130AA9E
    slot 1  000111000130AA9E 030111000130AA9E
(slot 1's character is index 3, MEASURED in p2(124) from the rig's own profile - the p2(124)
brief guessed index 1 and flagged it as a caveat; it is now a measurement.)
CORROBORATION: the p2(113) harvest of the mac's OWN profile reads
`000110000130AA9E010110000130AA9E...` at off=192 - byte-identical to the slot-0 prediction.
That is independent evidence both that the offsets are right and that this pair is what a
real client stores there.
No caveat remains on the values: both halves were observed in p2(124) (byte-reversed) and
both machines' own local profiles corroborate them. The ONLY thing under test now is the
byte order and what the client does once the identity is well-formed.

## ABSENCE NEGATIVE (L13)

- Zero `stage=install` on either machine: that DLL did not load.
- `staging_populate=1` anywhere: detour armed, boot void (20.191).
- Zero `ev=queuez stage=subscribe_in` AT ALL: the subscription path did not run this boot;
  the claim is untested, not refuted. p2(123) had 13. Compare before concluding anything.
- Zero `tag=regionA off=192` dump lines from a WIRE caller: the per-(path,index) dump budget
  did not cover the wire class - it should, since 20.193 R5.
- Both clients present but only ONE key appears in subscribe_in: the other client never
  subscribed at all, so its half of the claim is unmeasured.

LIVENESS: `ev=dtrace stage=install result=ok staging_populate=0 ...` on BOTH machines.

## CHAIN MARKS (L16)

| Link | Mark |
|---|---|
| Profile block applies both directions, peer rows included | VERIFIED-BY-EXECUTION (20.194) |
| Content (a name) survives the wire byte-exact | VERIFIED-BY-EXECUTION (20.195) |
| Appearance does NOT cross the client<->client channel | VERIFIED-BY-EXECUTION (20.196, 98.7% 42-byte heartbeats, 234 B lifetime max) |
| Clients never request a peer's root (with name-only rows) | VERIFIED-BY-EXECUTION (p2(123): 13 subscribe_in, 0 foreign) |
| Chunk 7 = two verbatim 64-bit words at +0xc0/+0xc8 | VERIFIED-BY-DISASSEMBLY (20.179 R2) + corroborated by the p2(113) harvest |
| Identity reaches the client's stored buffer | UNKNOWN - THIS BOOT |
| A client asks for a PEER's record once it knows the peer | UNKNOWN - THIS BOOT, the whole point |
| root->account resolution missing server-side | VERIFIED-BY-READING (20.173) - the thing this boot decides whether to build |
| Render / co-presence | UNKNOWN (parked) |

## INSTRUMENTS

INSTRUMENTS:
  ev=dtrace stage=decoded
  path=%s

## LITERAL TARGETS

LITERAL TARGETS:
  Game/bin/x64/steam_api64.dll: ev=dtrace stage=decoded, path=%s

## ADVERSARIAL PASS

ADVERSARIAL PASS: waived: content-only server change, rollback is a settings clear

waived: no new hook RVAs, no client change (same DLL as p2(122)/p2(123)). The diagnostic
needs NO new instrument - `ev=queuez stage=subscribe_in` already logs family, root and key.
Clearing `profile_identity` leaves chunk 7 absent and reproduces the p2(123) bytes exactly,
with no rebuild.

## THE TEST-RIG CAVEAT, STATED PLAINLY

No machineId->accountKey association exists anywhere in this server, so the player SLOT
picks the account by ORDER. On a two-account rig with two distinct real SOIDs that is
deterministic and sufficient for the question (does a client chase a FOREIGN root?), but it
is NOT a production mapping and must not be read as one. If a row is ever attributed to the
wrong account the identity is wrong-but-valid, which is exactly why this is gated behind a
default-false setting. Building the real association is part of the work this boot gates.
An unprovisioned slot leaves both SOIDs zero, which writes chunk 7 ABSENT rather than
publishing a wrong identity.

## DEPLOYED FOR THIS BOOT
  server exe     `136e11e15c9acbe9` - chunk 7 written as a 64-bit VALUE (MSB-first), the
                 p2(124) byte-order fix; all seven deploy gates passed, failures=0.
  MAC client DLL `cadb28325fb3e7cf` (unchanged)
  RIG client DLL `cadb28325fb3e7cf` (unchanged)
  settings       publish_player_profile TRUE, profile_name "SUNRISE",
                 profile_identity TRUE; clients staging_populate FALSE.
                 settings.json edited by TEXT INSERTION only (trap 18); backup
                 settings.json.bak_claude_p2d124 (settings unchanged this boot).

## AFTER THE BOOT - REQUIRED
`bash RE_scripts/capture_boot.sh p2-125`
