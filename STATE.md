# STATE - living snapshot

STATUS: live (2026-09-04 23:15 PDT, session close). Verdict + deployed + next only.
Full text: FINDINGS (20.299 is today's close; 20.292-20.298 the stack under it).
Ops facts (network move, grep hazard, BOM trap) in ENVIRONMENTS.md.

*** 20.299 (session close): P2-177 SOLO HUSK LANE - THE HUSK DID NOT FIRE ON ANY OF
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

## NEXT - ONE REBUILD UNBLOCKS BOTH LANES. Nothing else is measurable until it ships.
  *** THE REBUILD (4 changes, one build, no new fronts) ***
   R1 clear `peerWithdrawn` on acknowledgement (activity_membership_push.cpp:384 block).
      Prereq for ANY sustained-peer-row run; without it every finite cap latches off and
      cap 0 reproduces the p2(111) body storm. (20.298 R7)
   R2 log session-id <-> member-key together. Right now "which session is the rig's" is
      INFERRED; one line closes it and it gates every attribution claim. (20.298 R2)
   R3 a GATE-BYTE PROBE FIRED FROM THE CREATION PATH (pb_create/ent_make), not from the
      participant walk. Without it f38 cannot be observed when it matters. (20.299 R2)
   R4 definition.h:117's stale variant comment (pin=4 is all_mask, "it froze"). (20.298 R6)
   GATE BEFORE DEPLOY: verify_hook_rvas.py on R3's new hook; replay R3's trigger over the
   p2-177 log as a fixture BEFORE booting (the rule POSTMORTEM_2026-09-01 yielded and
   that 20.299 R2 broke).

  AFTER THE REBUILD, in order:
   1. PAIRED, sustained row: re-run p2-176 run A's contract with R1 live. The claim-state
      wall (FRONT_chain-to-a-moving-guardian.md) becomes measurable for the first time.
   2. THE ONE STATIC QUESTION, still unanswered and boot-free: WHAT WRITES BIT 4 OF
      participant_record+0x38? Approaches in the front page (constructor first; callers.py
      out from 0x1404DD470 / 0x141703910; dump_search for any nonzero +0x38 anywhere).
      NOTE: field_xref.py 0x38 is the WRONG tool (offset ubiquitous, disp8 not disp32,
      its `ff /x` hits are indirect CALLs misclassified as RMW).
   3. BLACK SCREEN: confirm the suspect cheaply - set publish_player_profile=FALSE solo
      and see whether the screen goes black. One flip, one solo launch. If it does, the
      husk's trigger may be downstream of it and the husk lane reopens with a trigger.
   4. HUSK LANE: BLOCKED on a trigger (20.299 R1) AND on R3. Do not brief it before both.

  DO NOT: re-brief the husk without a trigger and a creation-path probe; read a duplicate
  participant record as a husk (20.299 R3e - user visual refuted it); read `wire_snapshot
  peer=N` as "a row was sent" (it is havePeer); read pool=0x0 as a hang; trust a recursive
  `grep` under RE_build/ or RE_output/ (use /usr/bin/grep); write rig configs with
  PowerShell Set-Content -Encoding UTF8 (BOM); modify the client.

## HARD RULES (earned; full text in LESSONS/AGENTS)
  - THE CLIENT IS NEVER MODIFIED - the server must accomplish everything.
  - Reset the server between runs (backgrounded; it hangs AFTER succeeding).
  - Check the INPUT GATE before reading any result (withdrawals, peer bodies actually
    sent) - 20.297 R2 died of this.
  - Before a probe's field enters a conclusion, read the code that PRODUCES it.
  - ANCHOR EVERY DISASSEMBLY; census before filter; solo control before paired.
  - logindex/logq need /usr/bin/python3; launch the server from the REPO ROOT.
