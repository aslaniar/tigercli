# STATE - living snapshot

STATUS: live (2026-09-05 12:1x PDT). Verdict + deployed + next only.
Full text: FINDINGS (20.300 is newest; 20.292-20.299 under it). Session failures:
docs/postmortems/POSTMORTEM_2026-09-05_THE-REBUILD.md (4 launches lost, 3 to my defects).
Ops facts (network move, grep hazard, BOM trap) in ENVIRONMENTS.md.

*** 20.301 (STATIC, NO BOOT - READ THIS BEFORE ANY LOOP WORK): THE COND5 BIT IS NOT THE
CREATION GATE. The creation loop 0x1413086E0 never calls the cond5 reader at all - that
reader's only callers are the reconcile/RELEASE sweep. Verified: the constants are sound
(stride 0x2AC0, +0x38, bit 4), no stride-indexing site WRITES +0x38, and the loop's real
bail is GATE 2: member[+0x818] == gate1's out-value.
*** AND THAT WAS ALREADY SETTLED. *** 20.260 (2026-09-02, no boot) measured gate 2 on both
machines across three boots: gate1's out-value is THE OBSERVING MACHINE'S OWN identity and
each record's +0x818 is that member's own. "The loop is not the peer path and never could
be." 20.221 R2 said it first. I re-measured it across 20.298-20.300 and built a front page
on it. Those findings' DATA stands; their framing as "the wall" is RETRACTED.
THE REAL FRONT, unchanged since 20.221 R3: peers must ARRIVE by SERVER-MEDIATED
replication on the gameplay plane (UDP 30976). The receive cluster logs zero because
NOTHING EVER SENDS IT A PEER ENTITY - and the fork has never sent one. Client<->client is
refuted as the carrier (20.208 R5, pcap). This is fork-side work in code we own. ***

*** 20.300 (p2-178): the create is never ATTEMPTED for a foreign record (loop 15,745
passes, memidx_alloc 2). Data stands; its "wall" framing is superseded by 20.301.
First gate-byte reading at a creation call (f38=0x00). DELIVERY VOLUME ELIMINATED (11
peer bodies vs 2, identical outcome). Attribution now DIRECT. Rig hang PRE-EXISTING.
My re-arm did NOT fire - threshold 8 unreachable; ack-counting cannot drive it. ***
*** 20.299 (p2-177 solo): husk NOT reproducible on 3 triggers; H4 negative. ent_recv=0
across 3,774 local creates. publish_player_profile=false = leading black-screen suspect.
My probe was gated on an event its own placement excluded (pgate is table-driven). ***
*** 20.298 (p2-176): first ATTRIBUTED foreign-peer measurement; row CONTENT exonerated.
20.297 R2 reopened (starved: 104/128 snapshots sent nothing). ***

VERDICT TRAIL (one line each; full text in FINDINGS):
  20.298 run A: extras exonerated, wall = claim state; 2 retractions; grep-wrapper
    defect; stale variant comment; retry-cap permanence named.
  20.297 transition run - R2 REOPENED (starved); R3's never-sticks framing stands.
  20.296 receiver = converted, not constructed; C3 retired (user).
  20.295 p2-174: the client READS the row's character field; knob is SOLO-ONLY.
  20.294 eventType not the routing key; wire->image CLOSED at the queue interior.

## DEPLOYED (2026-09-04 22:0x - server LIVE on the NEW address; clients p2-171 both)
   NETWORK   *** THE MAC MOVED TO ETHERNET: 192.168.1.7 (was WiFi 192.168.1.164). ***
             Server bind/relay/advertised/transport, the mac client host, and the rig
             client host+config_url ALL repointed. reset_lobby_claims.sh and
             deploy_p2d6_gameplay.sh now DERIVE the host from settings.json.
             If the DHCP lease moves, this breaks again - a reservation would fix it.
   server    3f0496a9ebcf744c UNCHANGED (no rebuild since p2-175). Settings:
             transport_identity=FALSE, publish_player_profile=FALSE, peer_row_flags=0,
             reseed=0, sweep=false (pin 0 = packedMasks = the default),
             same_region_advert=TRUE, self_peer_row=false, c4_mark_push=false,
             world_population=true, peer_retry_cap=10 (echoed at startup).
   clients   BOTH p2-171 a96a6a70f578fc40 (hashes asserted both machines this run).
   rollback  settings .bak_p2-176_pre (pre-run-A knobs) and .bak_pre_ethernet_move
             (pre-address). Rig client settings .bak_pre_ethernet_move ON THE RIG.
   logs      RE_output/logs/20260904_220846_p2-176-runA (the run), plus
             ..._203945_p2-176-aborted-network and ..._215841_p2-176-attempt2-macspin.

## NEXT - the front is SERVER-SIDE ENTITY REPLICATION. Not the loop, not the gate byte.
  1. THE ENTITY MESSAGE ON THE GAMEPLAY PLANE (UDP 30976). The fork has never sent one.
     The receive cluster (ent_recv 0x141718510 / ent_header 0x141717EB0 / ent_create
     0x141718080) is the client's inbound path and logs ZERO in every boot - including
     across 3,774 completed LOCAL creates (20.300/20.301 R5). Establish what that plane
     expects, then write the encoder. Start from FRONT_e2e-stack PART 2's inventory of
     what our encoder marks absent (3 x kEntryFieldAbsent, 1 x kPlayerProfileAbsent,
     4 x kTailGroupAbsent) and from the group_host.cpp:931 comment (the player block and
     its tail are NOT decoded).
  2. STATIC + FEMU FIRST, NO BOOTS: what does ent_recv/ent_header/ent_create consume?
     Anchored disassembly + femu against dump_p2146.dmp answers the message shape
     offline. That names the encoder's contract before a line of fork code is written.
  3. DEAD / CANCELLED - do not restart these:
     - the +0x818 writer hunt (20.260: each record legitimately carries its OWN owner;
       reading (b) of 20.221 R4 has design evidence AGAINST it)
     - the +0x38 / cond5 writer hunt (20.301: creation never reads it)
     - "why doesn't the loop create the peer" (20.221 R2: it is not supposed to)
  4. OPEN DEBT, unchanged: the image_set hang is worked around not understood; the rig's
     initial_slice_set_loading hang is pre-existing and blocks any paired visual; the
     re-arm needs a non-ack trigger (20.300 R5) IF a sustained row is ever needed again.

  DO NOT: re-measure the creation loop; hunt writers for +0x38 or +0x818; read "the loop
  skips the peer" as a defect (it is the loop's rule executing correctly); ship a build
  change without replaying its own trigger over a recorded log; trust recursive `grep`
  under RE_build/ or RE_output/ (use /usr/bin/grep); modify the client.

## HARD RULES (earned; full text in LESSONS/AGENTS)
  - THE CLIENT IS NEVER MODIFIED - the server must accomplish everything.
  - Reset the server between runs (backgrounded; it hangs AFTER succeeding).
  - Check the INPUT GATE before reading any result (withdrawals, peer bodies actually
    sent) - 20.297 R2 died of this.
  - Before a probe's field enters a conclusion, read the code that PRODUCES it.
  - ANCHOR EVERY DISASSEMBLY; census before filter; solo control before paired.
  - logindex/logq need /usr/bin/python3; launch the server from the REPO ROOT.
