# HANDOFF 2026-08-30 (evening) - THE ENTITY FRONT

STATUS: live. Supersedes HANDOFF_2026-08-30_CONSUMER-HUNT.md, whose hunt list is spent:
its items 1-2 were parked on a dead emitter, and its central premise (that the profile
pipeline was the road to a rendered peer) is now settled - the pipeline WORKS and renders
nothing, because region A carries no appearance field at all.

## THE ONE-PARAGRAPH STATE OF THE WORLD

The membership milestone is CLOSED. Two clients hold one Tower instance with authored
identity live and zero errors on both machines: 0 checksum failures, 0 force-disconnects,
citizen join SUCCEEDED, revision 9-20 against a 23,908 baseline, peers 0x7 / players 0x3.
That took two measured fixes to the replica model - the name's key16(L) terminator and the
tail's dword at +0x0c - both read off the CLIENT's own decode of a body we published.
What remains is peer rendering, and it is now isolated: the rig (a pure client, no server)
holds that clean session, has zero errors of any kind, and still shows only its own
guardian. Every earlier appearance measurement was taken on a session that was
force-disconnecting ~1.2x/s; that confound is gone, and the results survive it.

## WHAT IS CLOSED - DO NOT REOPEN WITHOUT NEW EVIDENCE

1. **The membership state hash.** Fixed and verified twice (20.206, 20.207, 20.208 R1).
   The HISTORICAL player-table base (15192) is correct; `session_state_client_base` stays
   FALSE - p2(129)'s +8 shift was neither necessary nor sufficient.
2. **The checksum as the black screen** (20.208 R2). Zero failures, zero disconnects, and
   the mac still went black. 20.203 R1 is corrected.
3. **The peer channel as the appearance carrier** (20.208 R5). The capture 20.196 R5 asked
   for, taken WITH profiles applying - its own named re-open condition. 1,394 packets,
   106,691 B, largest packet 268 B, 10s buckets flat with no burst at co-location, while
   the largest flow in the capture is rig <-> server:30976 at 118 KB. Provisional closure
   is now a real one.
4. **The entity-replication cluster** 0x141718510 / 0x141717EB0 / 0x141718080 (20.210).
   attached=1, calls=0, SOLO AND PAIRED, while the guardian renders. Wrong subsystem, not
   a wrong observation point. Do not hook it again, and treat sobject-carrier.md's
   "entity replication codec cluster" identification as unproven for players.
5. **world_population's carrier** (20.209, confirmed live in 20.210). Activity type 17
   decodes our record with the correct decoder (rcx=0x141FBF268, r8=0x89) and commits it
   to an event ring. It was never on a path to an entity. Do not tune the 0x89 payload -
   a correct record on the wrong carrier still creates nothing.

## WHAT IS PROVEN AND USABLE

- A stable two-player Tower session with authored identity, on both machines.
- The profile pipeline end to end, byte-exact, verified against the client's own decode:
  name (plain UTF-16 + key16(L) terminator), account+character SOIDs as host qwords at
  region A +0xc0/+0xc8, region B as 136 zero bytes, tail = 0,0,0x01000000,1.
- `milestone_trace` - 8 functions, caller RVAs, and a census that prints ZEROS. THIS IS
  THE MODEL FOR EVERY FUTURE INSTRUMENT: add a target in one line rather than writing
  another one-off hook. Three boots this session were lost to one-off hooks on functions
  that never ran, and to silences that could not be told apart from "never installed".

## THE HUNT, IN ORDER

1. **The event ring's consumer.** ring_commit runs 147 solo -> 624 paired, the ONLY
   counter that moves sharply with a peer. sobject-carrier.md records what that commit
   does: {type, seq, count, payload-tail, timestamp} into session +0x130, then it
   NOTIFIES THE +0x81e0 OBJECT. Sweep +0x130 and +0x81e0 with field_xref.py FIRST - no
   boot. That consumer is the nearest named thing to a peer-data sink this project has.
2. **Where player entities actually come from.** The guardian renders, so entities ARE
   created - just not through the retired cluster and not from svc 9. Standing hypothesis,
   evidence-backed but untested: the GAMEPLAY plane (UDP 30976), which carries the
   capture's largest flow by far and which 20.196 R3 already showed is where bulk rides.
3. **The mac black screen** - PARKED, and not on the critical path. It correlates with the
   machine that also hosts the server, across every paired run in the project; the rig has
   never gone black once. Cheap to attack later, irrelevant to peer rendering.

## METHOD THAT WORKED - REUSE IT

Measure, do not derive. Every fix that landed this session came from reading the client's
own bytes (its decode of our body, its logged hashes); every fix that failed came from
deriving a layout out of summary documents. The corollary that cost the most: READ THE
REGISTRY AND THE RUNNING HOOKS BEFORE BUILDING AN INSTRUMENT. Three times the answer was
already on disk - name_codec.py --try-both, field_xref.py, and the live ev=ingress hook.

## HONEST CAVEATS

- The slot->account mapping in `profile_identity` is a TEST-RIG mapping by player slot
  order. Fine for two real accounts, not a production mapping.
- `sobject-carrier.md` contains a contradiction that cost a boot: it names activity type
  17 "the RESOLVED entity carrier" while its own section 0.3 says that chain "writes NO
  entity". The disassembly and two runs side with 0.3. Read that document with care.
- The unpacked image contains no dispatch table for the entity cluster - not a call, jump,
  qword or RVA anywhere. Runtime-built structures are simply absent from it, so "no static
  xrefs" in that image is weaker evidence than it looks.
