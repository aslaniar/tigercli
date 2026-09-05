# STATE - living snapshot

STATUS: live (2026-09-04 19:57 PDT, session close). Verdict + deployed + next only.
Full text: FINDINGS (20.292-20.297 are today's stack); ops facts in ENVIRONMENTS.md.

*** 20.297 (session close): THE TRANSITION RUN - a participant transition (mac leave +
re-enter; fresh type-7 push consumed on BOTH machines) produced ZERO receiver activity
(ent_recv/header/create = 0) - outcome (c). STRUCTURAL FIND: the NEVER-STICKS CHURN
(pb_create N times on the same slot, identical args, ~16 ticks) is the client's GENERAL
signature for "a record the creation loop engages but cannot complete" - measured long
before the crafted rows (20.211 R3's 50x player_broadcast). In 20.53 a create STUCK once
and rendered. The variable is the ROW'S CONTENT SHAPE. The mac's re-entry hang
reproduces the crafted-record hang's empty-manager spin exactly (mgr pool=0x0).
NEXT: the 20.53 ROW BISECTION - settings-only, no rebuilds, readout in the logs. ***
*** 20.296: THE RECEIVER IS CONVERTED, NOT CONSTRUCTED - installer 0x1416CACD0's four
callers are ALL mask-table-driven reconcile/release paths (the claim sweep's family; it
reads the 20.292 container/table anchors directly). 20.223's zero instances = no
participant transition had ever occurred in a dumped session. The C3 crafted-self
program RETIRED (user decision): the ceiling is a self-owned record; its durable yield
is "the client READS the row's character field" (20.295: V-1 non-loaded character HUNG
the instantiation, V-2 active character landed clean). ***
*** 20.294: THE WIRE->IMAGE ROAD CLOSED - the fork's own carrier (svc-9 type 17,
eventType 17) was consumed IDENTICALLY to eventType-7 (sobj_decode, same caller/slot);
the image plane never reached. eventType is not the routing key. 20.292's structural
map stands (the resolver object contains the mask table at +0x6C38; masks at
container+0x5FE80/84; the obfuscated region's `mov eax,0x6c38` = the anchor offset).
20.290 corrected: p2-172 DID run (its client defect was real, parked). image_set's
"fed only by the handler" premise FALSE (the publish path writes a SOID into the cache
- any future image_set reading must name caller_rva first). ***

VERDICT TRAIL (one line each; full text in FINDINGS):
  20.297 transition run outcome (c) + never-sticks = general signature + the bisection
    plan. 20.296 receiver = converted, not constructed; C3 retired (user).
  20.295 p2-174: reads the character field; knob is SOLO-ONLY (paired displaces real
    peer rows); 20.64-freeze did not recur; no black screen (16:0x run).
  20.294 p2-173: eventType not the routing key; wire->image CLOSED at the queue
    interior; 20.290 corrected; image_set premise FALSE.
  20.293 carrier named (svc-9/type-17 = the fork's existing family). 20.292 R7 YES
    (resolver contains the mask table) - structure, not a road.
  20.290 corrected (p2-172 ran); 20.289 revert rules stand; 20.284-20.288 stand.

## DEPLOYED (2026-09-04 19:36 - server LIVE; clients p2-171 both)
   server    3f0496a9ebcf744c (crafted-row knobs + carrier knob wired). Settings:
             world_population=true, membership_self_peer_row=FALSE (knob retired),
             same_region_advert=true, pool_c4_mark_push=false, reseed off, transport
             identity ON, roster participation ON. gate_poke=0 clients.
   clients   BOTH p2-171 a96a6a70f578fc40 (rolled back 12:40, hashes asserted). The
             2e91f94-lineage builds are RETIRED (crash at Tower instantiation - the
             parked p2-172 defect) until a hook-depth audit.
   rollback  p2-171 exe .bak_p2d6_20260903_210009 + PAIRED build_data.bin; settings
             .bak_p2-173_pre. Logs: RE_output/logs/20260904_195444_p2-175-transition
             (indexed p2175_{mac,server,rig}.db).

## NEXT (the bisection ladder leads; each run = settings flip + restart + one solo
##       mac launch; readout = pb_create sticks vs churns, in the logs)
  1. RUN A - MINIMAL ROW: transport identity OFF, publish_player_profile OFF,
     peer_row_flags 0, mask variant off, reseed off -> the 20.53 shape, fresh revision.
     Sticks+clone -> bisect the extras ON one at a time until the churn returns (the
     breaking field is NAMED). Sticks, no clone -> presentation layer. Churns even
     minimal -> compare a FIRST-ENTRY boot (today's churn appeared only on RE-entry).
  2. After the bisection: if a field fix makes the churn stick, retest the receiver
     conversion with a claimed peer record + transition (20.296 R2's open question).
  3. DOC/AUDIT: `negative_audit.py` over the corpus. 4. The trailing-sweep re-run rider
     (20.53's voided trailing verdicts) on the first boot with a genuinely foreign peer.
  5. TOOL DEBT: no mac-side dump tooling (the receiver check on the mac is
     unanswerable); ssh control socket reopens with: ssh -M -S ~/.ssh/cm-rig
     -o ControlPersist=8h -N -f rasla@192.168.1.136. logindex/logq need
     /usr/bin/python3. Launch the server from the REPO ROOT only (relative paths).
  DO NOT: emit against the image; poke cond5; chase the queue interior statically
  (eventType measured not-routing); re-enable the crafted knob for paired runs
  (displaces real peer rows); unanchored disassembly; launch from the wrong cwd.

## HARD RULES (earned; full text in LESSONS/AGENTS)
  - THE CLIENT IS NEVER MODIFIED - the server must accomplish everything.
  - Reset the server between runs (backgrounded; it hangs AFTER succeeding).
  - No live client before a DLL deploy; server reverts restore the PAIRED
    build_data.bin; every hook RVA through verify_hook_rvas.py.
  - ANCHOR EVERY DISASSEMBLY (pdata_bounds first); search RELOCATED, not static.
  - Census before filter; solo control before paired unless explicitly waived.
  - logindex/logq need /usr/bin/python3; capture liveness needs a probe packet.
