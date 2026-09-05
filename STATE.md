# STATE - living snapshot

STATUS: live (2026-09-05 1x:xx PDT). Verdict + deployed + next only.
Full text: FINDINGS (20.307 is newest; 20.292-20.306 under it). Session failures:
docs/postmortems/POSTMORTEM_2026-09-05_THE-REBUILD.md (4 launches lost, 3 to my defects).
Ops facts (network move, grep hazard, BOM trap) in ENVIRONMENTS.md. Instrument
defects: docs/TOOLING_AUDIT_2026-09-05.md.
TOOLING 20.307 (2026-09-05, no boot): enforcement waves 0-1 SHIPPED - pre-commit hook
INSTALLED; gate_boot v3 brief-tie fields ENFORCED (the next boot brief MUST carry
PRIOR ART / STATE READERS / READOUT TRIGGER / EFFECT CLAIM / ABANDON+WIDE-NET / FIX
SURFACE; instrument briefs also OBSERVER BUDGET / CALL FREQUENCY / HOOK COUNT /
INSTRUMENT LIVENESS - template updated); record each boot's outcome at boot close via
RE_scripts/boot_outcome.py (>=2 third-branches on a front refuse the next boot without
MODEL REVIEW). Wave 2 next: replay_trigger.py (M1), preflight.py + instruments.json,
boot_verdict v2 (docs/plans/boot-gate-v3.md + TOOLING_AUDIT shortest path).

*** 20.302 (STATIC + FEMU, NO BOOT): THE ENT_* RECEIVE CLUSTER IS DECODED. Four
receive interfaces (0x141718510 ent_recv / 0x141718AE0 / 0x1417183C0 /
0x141718CB0), all at vtable slot 10 of the four blocks the ctor 0x1416BB1E0
installs; one 0x84-byte record shape; the header grammar (ent_header
0x141717EB0) femu-validated bit-exact; the anchor codec 0x1404C16C0 fully
decoded (index13+salt4[+high2], 22-bit handle); wire = MSB-first bits in
big-endian u64 words (femu-proven). Descriptor tables read from the p2-146
dump: entity indices are SMALL INTEGERS (live set 0..6), descriptor 0 carries
kind=2 - the creation loop's own kind. THE CONTRACT IS WRITTEN:
RE_output/claims/ent-receive-contract.md - the fork encoder's source of truth.
Dispatch-INTO the cluster (who calls slot 10) = complete-encoding scan done,
only VMP/cross-function-register candidates remain; the contract does not
need it. 20.303 (lane): THE CARRIER LAYER IS NAMED - the "network extract"
pair (0x1416C8250/0x1416C8240) feeds a decode chain (0x1416EACB0 -> 0x1417115D0
-> 0x1417117D0) operating the SAME entity storage as ent_create; router census
complete (93 wire bytes, 44 handlers; type 17 excluded, type 22 = the receive
tick's own gate fn). 20.304 (lane): PAYLOAD BODIES DECODED + FEMU-VALIDATED -
kind 2 (the player/guardian) = RAW 8 BYTES (64 bits, no presence, no
transforms; bit-exact vs the real dump codec object); kind 1 = 55 bits, kind 3
= 0 bits; 23 per-kind keys from the dump; two decode dialects (W1 walker + a
NEW 0x1404BA530 dialect, table 0x141F95980, extended types 18-46 carry the
wire). THE ENCODER'S PAYLOAD HALF IS SPEC-COMPLETE FOR THE GUARDIAN KIND. ***

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

## NEXT - the front is GETTING THE RIG TO LAND (20.306), then the transition contract.
  1. (offline) Census the archives: peer-body flow vs withdrawal vs the rig's load
     stages + empty-manager spin onset in p2-176/178/179 vs p2-175 (H-land: churn
     during load hollows the manager; stable bodies load fine).
  2. (settings-only boot) retry_cap back to 2 -> rig should land on the CURRENT
     stack (behavioral confirmation of 20.306 R2; isolates cap causality).
  3. (fork code) LANDED-GATE: withhold peer rows until the client shows post-load
     acks, then sustain - serves both the rig landing and the replication front's
     sustained-row requirement; then the p2-179 transition contract is runnable.
  4. The entity-message encoder stays spec-complete except the outer wire type
     (20.303 R4); contract + payloads done (20.302/20.304 - guardian payload =
     8 raw bytes). The establishment-ladder decode (20.305 R5, minus the BABOON
     evidence) remains the parallel static front.
  5. TOOL DEBT: tar-over-ssh corrupted the 6.7 GB dump pull deterministically
     (+7249 B, identical wrong hash twice; 20.305 R4). The rig-side generated-
     script scan (_rig_vptr_scan.py pattern) is the workaround and the better
     instrument - generalize it before the next dump question.
  6. DEAD / CANCELLED - do not restart: the +0x818 and +0x38 writer hunts; the
     creation-loop framing; the queue-event/sobject_message entity carrier
     (ring-only, excluded); type-17 as carrier.
  DO NOT: re-measure the creation loop; hunt writers for +0x38 or +0x818; read "the
  loop skips the peer" as a defect (it is the loop's rule executing correctly); trust
  the local copy of dump_p2-179-hang.dmp as evidence (hash mismatch); cite today's
  BABOON as evidence about the hang (dump-precipitated, 20.306 R1); read the hang as
  a client bug in isolation (it tracks the sustained row, 20.306 R2); ship a build
  change without replaying its own trigger over a recorded log (no replay tool yet -
  Wave 2 builds it); trust recursive `grep` under RE_build/ or RE_output/ (use
  /usr/bin/grep or RE_scripts/sgrep.sh); modify the client.
   7. OPEN DEBT, updated: the image_set hang is worked around not understood; the
      re-arm needs a non-ack trigger (20.300 R5) IF a sustained row is ever needed
      again (the landed-gate may obsolete it).

## HARD RULES (earned; full text in LESSONS/AGENTS)
  - THE CLIENT IS NEVER MODIFIED - the server must accomplish everything.
  - Reset the server between runs (backgrounded; it hangs AFTER succeeding).
  - Check the INPUT GATE before reading any result (withdrawals, peer bodies actually
    sent) - 20.297 R2 died of this.
  - Before a probe's field enters a conclusion, read the code that PRODUCES it.
  - ANCHOR EVERY DISASSEMBLY; census before filter; solo control before paired.
  - logindex/logq need /usr/bin/python3; launch the server from the REPO ROOT.
