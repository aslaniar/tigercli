# STATE - living snapshot

STATUS: live (2026-09-05 11:4x PDT). Verdict + deployed + next only.
Full text: FINDINGS (20.300 is newest; 20.292-20.299 under it). Session failures:
docs/postmortems/POSTMORTEM_2026-09-05_THE-REBUILD.md (4 launches lost, 3 to my defects).
Ops facts (network move, grep hazard, BOM trap) in ENVIRONMENTS.md.

*** 20.300 (p2-178): THE CREATE IS NEVER ATTEMPTED FOR A FOREIGN RECORD. The rig's loop
ran 15,745 times, its gates ran 300k-580k times, and memidx_alloc/idx_publish/pb_create
fired TWICE all session - neither for the peer. So the wall is NOT "builds and fails"; it
is a BAIL BETWEEN GATE EVALUATION AND ALLOCATION, upstream of creation. This CORRECTS
20.298's framing. First gate-byte reading ever taken AT a creation call: the mac's record
in the rig's table reads maskA=1, f38=0x00. DELIVERY VOLUME ELIMINATED (11 peer bodies vs
2 - identical hang, identical counts). Attribution is now DIRECT (rig = session ...108).
The rig hang is PRE-EXISTING (identical on the old client). MY R1 RE-ARM DID NOT FIRE:
threshold 8 was unreachable - exactly one ack follows a withdrawal, because the client
never acks a peer-bearing body. Ack-counting cannot drive a re-arm; a different trigger
(time or revision churn) is needed. ***

*** 20.299: P2-177 SOLO HUSK LANE - THE HUSK DID NOT FIRE ON ANY OF
THREE TRIGGERS (landing / orbit round-trip / character switch). H4 NEGATIVE: it has NO
KNOWN TRIGGER, and that must be solved before the lane is briefed again. 3,774 creates
COMPLETED solo with ent_recv AND ent_header at ZERO throughout - corroborating 20.296's
remote-only receiver behaviourally for the first time. Solo re-entry was CLEAN where
20.297's paired re-entry hung forever: the differing variable is the PEER RECORD.
MY INSTRUMENT DEFECT: the brief's decisive read could never have executed - pgate is
gated on participant-table events, not creation (16 samples all run vs 3,774 creates;
ZERO during the character switch). Any gate-byte observation needs a probe fired from
the CREATION path = a rebuild. publish_player_profile=FALSE is now the LEADING
BLACK-SCREEN SUSPECT (false: black 2/2; true: clean 3/3) - inverting 20.298 R4's
"no established cause". ***

*** 20.298: P2-176 RUN A - THE FIRST ATTRIBUTED FOREIGN-PEER
MEASUREMENT. On the rig, the creation loop engaged a record PROVEN to be the mac's
(rec=0x1FED8C24EC0 owner=0x34B6F79FCF627275 x 11,491; rig's own key is
0x846C8338F7D022E6) and CREATED NOTHING - pb_create's 2 calls are a different caller
and kind. The in-world session SUSTAINED its peer row (60 peer=1, no withdrawal; the
two withdrawals are on region=-1 sibling links) and every advert carried a citizen.
So with the post-20.53 extras OFF the loop still does not complete: THE EXTRAS
(transport identity, profile block) ARE EXONERATED AS THE BREAKING FIELD. The wall is
the record's CLAIM STATE, not the row's content - where 20.219's front already points.
Neither machine produced a visual (mac black-screened in-world; rig hung in
initial_slice_set_loading) - the LOG half is the deliverable. ***

*** RETRACTIONS THIS SESSION (both mine or inherited, both load-bearing):
  - 20.297 R2's outcome (c) is REOPENED: p2-175's peer row was permanently withdrawn
    after 2 unacked bodies; 104 of 128 peer-available snapshots sent NOTHING. It was a
    STARVED measurement, not a negative. `wire_snapshot peer=N` logs havePeer
    ("available"), NOT publishPeer ("sent") - the trap that hid it.
  - "the empty-manager spin" is NOT a hang signature. mgr_sync ROTATES managers and one
    is empty every pass (rig: 11,492 healthy vs 11,492 empty - a dead-even split).
    20.297 R1's "same empty manager 0x46EF040" carries a healthy pool here. pool=0x0
    diagnoses nothing. THE MAC'S BLACK SCREEN HAS NO ESTABLISHED CAUSE. ***

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

## NEXT - the front moved UPSTREAM of creation. No boot is needed for the top item.
  1. *** THE STATIC QUESTION, still unanswered, still free: WHAT WRITES BIT 4 OF
     participant_record+0x38? *** If nothing in the binary writes it, the cond5 theory is
     dead and FRONT_chain-to-a-moving-guardian.md gets rewritten. Approaches, best first:
     the 0x2AC0-stride record's CONSTRUCTOR (a constructor names its own flags);
     callers.py out from the readers 0x1404DD470 / guard 0x141703910; dump_search for any
     nonzero +0x38 anywhere in dump_p2146.dmp. NOT field_xref 0x38 (offset ubiquitous,
     disp8 not disp32, its ff/x hits are indirect CALLs misclassified as RMW).
  2. NEW AND BETTER-POSED (20.300 R1): WHERE DOES THE LOOP BAIL? It reaches its gates
     (gate1 301,904 calls, returning 0x1) but reaches memidx_alloc only twice. The bail
     sits between gate evaluation and allocation. Static: read create_loop 0x13086E0's
     body between the gate calls and the allocator call.
  3. THE RE-ARM NEEDS A DIFFERENT TRIGGER (20.300 R5). Ack-counting cannot work - the
     ack signal carries no information about the peer. Consider elapsed time or revision
     churn. Do NOT just lower the threshold to 1: that re-arms on the solo body's ack,
     which is what the original sticky flag deliberately avoided.
  4. OPEN DEBT: the image_set hang is WORKED AROUND, NOT UNDERSTOOD (hook disabled; front
     parked). If it was the game function and not our detour, the condition still exists.
  5. The rig's initial_slice_set_loading hang is pre-existing and now the single biggest
     blocker to any paired visual. Likely the SAME event as the never-completing loop.

  DO NOT: read "the loop churns" as "creates are attempted" (20.300 R1); tune the re-arm
  threshold and re-boot; ship a build change without replaying its own trigger over a
  recorded log (3 of 4 changes in the last build skipped it - see the postmortem);
  trust recursive `grep` under RE_build/ or RE_output/ (use /usr/bin/grep); modify client.

## HARD RULES (earned; full text in LESSONS/AGENTS)
  - THE CLIENT IS NEVER MODIFIED - the server must accomplish everything.
  - Reset the server between runs (backgrounded; it hangs AFTER succeeding).
  - Check the INPUT GATE before reading any result (withdrawals, peer bodies actually
    sent) - 20.297 R2 died of this.
  - Before a probe's field enters a conclusion, read the code that PRODUCES it.
  - ANCHOR EVERY DISASSEMBLY; census before filter; solo control before paired.
  - logindex/logq need /usr/bin/python3; launch the server from the REPO ROOT.
