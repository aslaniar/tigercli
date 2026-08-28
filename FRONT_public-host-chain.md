# FRONT: the public-host chain - what must be true for two clients to share one host

STATUS: live (2026-08-27 ~1x:xx, opened by the road-C decision). Owns the detail
behind STATE's "road C" line. Supersedes nothing; retires when link L4 closes.

Road C = the SERVER is the group-session host, both clients join IT, and the host
publishes one membership snapshot naming both. Chosen over A (peer-native Steam
rendezvous) and B (in-process injection) because the server half is ~80% built and
has never been switched on. See STATE "ROADS" and 20.110 for the A/B costs.

## *** CHAIN CLOSED THROUGH CO-LOCATION, 2026-08-28 ~14:0x (FINDINGS 20.140) ***

L1-L8b and co-location are ALL verified-by-execution. Both clients hold one public
Tower instance (same session-description, region and AH; both 'public AH instance
ready'), each names the other's xuid, the peer channel holds, and both machines run
0 errors / 1 rebind. This front's original question - what must be true for two
clients to share one host - is ANSWERED.

**L9 RENDER is now the sole open link and the front of the project.** It is UNBUILT,
not broken: nothing replicates another player's character records (family-0/family-3),
so the shared Tower renders empty. Everything below this line is the historical record
of how the chain was closed; read it for mechanism, not for what is open.

## STATE OF THE CHAIN, 2026-08-28 ~12:xx (read this before the table below)

L1-L8 are CLOSED verified-by-execution: one group session (members=3, players=2,
peers valid 0x7 both sides) and one shared activity host (00200003, both clients
EST-Y). The table's L8 cell is stale - the row drop it describes was fixed at
20.129 and co-location landed at 20.131.

**L8b - CLOSED 2026-08-28 by p2(88), verified-by-execution (20.133).** The shared
activity host is addressed and acknowledged: `wire_snapshot session=...00200003`,
`membership_ack` on that session, public AC `MEM-0 -> MEM-9`, `'ctng' -> 'cntd' due
to 'public AH instance ready'`, `error_connecting_to_bap` 67 -> 0 solo. It was NOT
the last link: see L8c.

**L8c (NEW, the open front): the public bubble reservation must ask for a NON-ZERO
peer slot count.** verified-by-execution as the defect (20.134): with BOTH machines
in the Tower, `Updating public bubble reservation peer request ... to '0' slots`
fired 34/34, so the peer channel still `lost all owners` (18x) and died. Membership
is necessary, not sufficient. Read the PAH tabulated-region data in the group
membership body - `Region ... PAH tabulated data now includes us` has never once
named a peer. Scope it statically before any build.

The original L8b defect text, kept because the chain marks below still cite it
(20.132):
`stage=wire_snapshot` names sessions 00200001 and 00200004 only - never 00200003,
which is the session both public activity clients joined. Consequence chain, each
step measured on the p2(87) capture: public AC `MEM-0` (0 `Acknowledged membership`
lines vs 91 on the private AC) -> `Updating public bubble reservation ... to '0'
slots` 125/125 -> the peer channel `lost all owners who want the channel to stay
open` -> `failed to connect` -> `error_connecting_to_bap` 67x.
The peer channel itself is NOT a link in this chain: it associates, secures, and
reaches `connected4`. 20.131's DTLS reading is retracted in 20.132.
The publisher exists (`activity_keepalive_push.cpp:149`, switch
`activity_public_membership` ON in the deployed settings); the gate in front of it,
`activityRole == publicTarget`, is unreachable because `bindsPublicTarget` requires
`parsed.sessionId != request.accountHandle` and a client always addresses the AH it
joins. `stage=bind result=public_target`: 0 lines, every boot. Lane = re-key that
predicate off the region-bound host row.

## THE CHAIN, LINK BY LINK (L16 marks on every link)

| # | Link | Mark | Evidence |
|---|---|---|---|
| L1 | Server binds the gameplay UDP endpoint | verified-by-execution | `ev=gameplay stage=endpoint result=ok mode=embedded port=30976` t=137; advertised 192.168.1.164 (settings server.gameplay) |
| L2 | Server allocates an activity-host session per (group, region) | verified-by-execution | `stage=activityhost result=allocated session=0x9EAA3001002000NN group=... generation=N held=N` x5 |
| L3 | Server writes the citizen advertisement (128-B join descriptor: address/port/machineId) into the type-12 region block, for BOTH sessions | verified-by-execution | `stage=peer_advert result=built own_region=48 peer_region=56 own_citizen=1 peer_citizen=1`; delivery gap closed at 20.74.4 |
| L4 | **Client sends an svc-8 activity JOIN naming the ADVERTISED host session** | **verified-by-execution (p2(78)) - CLOSED** | p2(74) measured it directly on BOTH machines: `stage=join_target result=own session==handle` bit for bit, zero `result=advertised`, zero `public_target`. The client is not refused - it never asks. Every join the client sends names its OWN allocated session: client logs `AH->9eaa300100200004`, which is this account's own `activityhost result=allocated` id |
| L5 | Server binds that link as the public half | verified-by-reading, blocked by L4 | `activity_message_route.cpp:230-246` `namesAdvertisedHost` -> `plan.bindsPublicTarget`; `bap_connection_publication.cpp:79-88` sets role publicTarget and logs `stage=bind result=public_target` |
| L6 | Client, now public, dials 30976: association -> DTLS -> peer transport connect/establish -> group join | verified-by-execution (p2(78), and 2026-08-28 on BOTH machines after the resolver + jr-observer fixes) | full stack present under `src/server/gameplay/`; ZERO datagrams have ever arrived (event census below) |
| L7 | Group host publishes the membership snapshot | verified-by-execution (p2(78)+; accepted solo on both machines) | `group_host.cpp:229 publish_snapshot()` builds host + 1 peer + 1 player, with the member-state ladder and state-replica hash |
| L8 | Widen the snapshot to host + 2 peers + 2 players | **verified-by-execution server-side (2026-08-28): 3-member snapshots published 115/135x, both records held, both players accepted - BUT each client's table keeps HOST + ITSELF (deterministic symmetric row drop, 2/2 runs) -> different spawn instances -> they cannot see each other. The drop is CLIENT-side consumer behavior; prime suspect = machineId stand-in (joinId) vs the real ids in the join request's undecoded address table. NEXT LANE.** | claims/l8-multi-peer.md + FINDINGS 20.127 addenda 1-3 |
| L9 | Both guardians RENDER for each other | not built, separate lane | nothing replicates another player's character records (family-0/family-3) - FINDINGS_2026-08-22 item 5 |

## THE EVENT CENSUS THAT NAILS L6 (last boot, both logs, debug on)

Server `ev=gameplay` appears 32 times, in FOUR stages only: `endpoint`,
`activityhost`, `advertise`, `membership result=held`. Zero `stage=receive`,
zero `dtls`, zero `association`, zero `connect`, zero `join`, zero `link`.
`stage=receive` is a debug line and debug IS enabled (the `membership result=held`
lines are debug), so this absence is measured, not filtered (L13).
=> No client has ever sent one packet to the gameplay endpoint.

## WHAT THE CLIENT ACTUALLY DOES INSTEAD (corrects the 20.69-era reading)

20.69 recorded a BLANK ah-sid and read it as the wall. On the current build the
client joins its own AH and gets a full membership ladder:

    [AC PRIVATE CURRENT CON-Y EST-N AH->0 MEM-0]   Sent join request: [AH 9EAA3001:00200004]
    [AC PRIVATE CURRENT CON-Y EST-Y AH->9eaa300100200004 MEM-1] ...
    ... MEM-4] Acknowledged membership '4'.
    ... MEM-5] Acknowledged membership '5'.

So the AH join WORKS. What never changes is the classification: `PRIVATE CURRENT`
on every line, and composition advertises/searches as `[PRIVATE activity]`.
A blank `activity_host_changed: instance=PRIVATE CURRENT, ah-sid=` still appears
once, at a transition, but it is no longer the standing state.

### The peer round-trip that already happens, and dies

The peer row DOES reach the client, and the client makes a reservation for it and
then RELEASES it:

    server: stage=membership_peer result=included key=0x846C8338F7D022E6 peer_row=1
    client: [AC ... MEM-1] Sending peer-reservation release for machine 'E6:22:D0:F7:38:83:6...'
    server: stage=message result=accept type=14 name=release_peer_reservation
            handle=0x9EAA300100200004 payload=...E622D0F738836C84

That release is the closest thing to a decision point we have ever observed on
this front. Note the layer: this is the ACTIVITY-CLIENT reservation (svc-14), NOT
the session-layer reserve 0x1417692E0 that 20.109 mapped. Do not conflate them.

### Two clients are in DIFFERENT REGIONS

`own_region=48 peer_region=56`. The citizen advertisement is written only into the
region block whose index matches `citizen.regionIndex`, so a peer in another region
carries no joinable endpoint for the region the reader is in. Whether region
convergence is a precondition of L4 or a consequence of it is UNKNOWN. Do not
"fix" the region until L4's decision function is read - forcing a region is a
behaviour change and this front has already paid for guessing twice.

## THE ONE QUESTION L4 REDUCES TO

What makes the client choose a FOREIGN advertised host session as its AH target
instead of its own? Everything downstream of that choice is built and read.

Instrument (LESSONS 18c, already deployed and proven 4/4 last boot): the retail
log funnel's `_ReturnAddress()` names the emitting function as a module-relative
RVA. The lines that bracket the decision are all present in the current capture,
so their callers are obtainable with NO new mechanism - only new target strings:

  "Sending peer-reservation release"   the release decision (highest value)
  "initiate_search"                    the PRIVATE/PUBLIC classifier
  "matchmaking gatherer advertising"   the advertiser's privacy source
  "activity_host_changed"              the AH-change consumer
  "waiting to connect to AH"           the AC->AH connect gate
  "join request to AH"                 the target chooser

With .pdata bounds + an E8 xref scan (the 20.106 method), those RVAs open the
decision's call graph with no further boots.

## HYGIENE FIXED WHILE WRITING THIS

`client.region_private`: mac carried `true`, rig has no such key (defaults false).
Divergent since at least 20.82. The hook forces solo loads only when its filtered
return site is reached, and that site has not been reached in any recent boot (no
`stage=region result=forced|public` line, budget 8, both machines) - so the flag
has been inert, not causal (that is 20.82's finding and it still holds). Set to
false on the mac so the two machines are comparable. Settings-only, no rebuild.

## WHAT p2(74) SETTLED (20.111) - and what it opened

SETTLED: L4 is the client's own choice, on both roles. Six deciding functions are
named by RVA and .pdata bounds; the chooser is fn 0x140C0CF30 (6938 B).

*** L6 AND L7 ARE DONE (p2(78), 20.118). *** Forcing the TOWER's region public
(slice set 56, settings-only) made the client dial the gameplay endpoint for the
first time: 64 datagrams, DTLS, establish, group join, membership built, player
added, `join result=completed`. Client side: reserve fired for a second machine at
member state 10 = ESTABLISHED, peers valid went 0x1 -> 0x3, the activity client took
the PUBLIC TARGET role, and the tracking-data warning and peer-reservation release
(20.112) did not fire at all.

The chain from 20.114 is now open from step 2 to step 7. What remains is TWO bounded
changes in code we own:

1. **Application-ready gate (handbook 18.5).** We queue membership and parameters at
   admit. Before the peer is application-ready the transport ACKS reliable records
   WITHOUT DISPATCHING them, so our retry logic is satisfied while the client never
   receives them - and it re-joins every ~21.7 s with a fresh join id (13 admits,
   present in the SOLO boot too). We have no app-ready concept anywhere under
   server/gameplay/. 18.6's corollary applies: an acknowledgement is not proof of
   dispatch. DO THIS FIRST - a stable single peer is the control for step 2.
2. **L8: one session, many peers.** DONE IN CODE (20.124), awaiting execution. Both clients
   named the SAME group session, and the old `claim()` rebound its single record to whichever
   endpoint joined last, so they stole it from each other and every snapshot stayed members=2
   players=1. Now: records keyed (session, endpoint), per-recipient complete snapshots with a
   composition-change refresh (the consumer clears and rebuilds its table from each snapshot),
   endpoint-disambiguated transport, byte-identity regression vs the proven solo encoder, and
   measured + static_asserted body bounds. See claims/l8-multi-peer.md.

DEPRIORITISED, now likely symptoms rather than causes: the `[rdi+0xC]` PRIVATE/PUBLIC
writer, the target chooser at 0x140C0CF30, and the empty-but-present matchmaking
configuration (20.115) - the client reached the Tower's public route without the
search surviving at all.

RENDER DEATH (parked, render lane): follows CO-PRESENCE, not entry order - the mac
entered first and died when the rig arrived; 20.110 saw the reverse. Game stays
alive and logging; no client-side trace exists.
