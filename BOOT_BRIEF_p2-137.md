# BOOT BRIEF p2(137) - THE MILESTONE TRACER: ONE CENSUS, NOT ANOTHER ONE-OFF

STATUS: live (2026-08-30). Reads with FINDINGS 20.209 (the static wall) and 20.208.

## WHY THIS BOOT

20.209 established statically, no boot: world_population publishes through activity type
17, whose handler FUN_1416F0F60 has exactly ONE downstream call into a chain that
sobject-carrier.md itself says ends in an event-ring commit and "writes NO entity". Our
carrier cannot create an entity, which is why p2(136)'s record was accepted and the create
at 0x141718080 logged zero calls. Tuning the 0x89 payload is pointless on the wrong pipe.
The wall: the entity receive chain has ZERO static references of any kind image-wide -
no calls, no jumps, no qword pointers, no dword RVAs beyond its own .pdata record. Its
dispatch is built at runtime, so the carrier cannot be named from the binary.

## THE INSTRUMENT - TABLE-DRIVEN, AND IT ANSWERS "NOTHING HAPPENED" OUT LOUD

Three boots have now lost their answer to an ambiguous silence (p2(130) hooked a verifier
that never runs; p2(133) budgeted its variant table on a players=0 snapshot; p2(136)
hooked a create that never runs, and logged nothing at all). This instrument is built so
that cannot happen again:
- TWELVE functions on the entity/render path traced in one pass, not one.
- Every hook logs its CALLER's return address. That is the only way to name a
  runtime-dispatched invoker (20.209), and it is the whole question for `ent_recv`.
- A HEARTBEAT THREAD prints every hook's call count every 5 s, ZEROS INCLUDED, plus an
  install census stating which detours actually attached. "Never called" and "never
  hooked" become different, visible statements.
- PER-TARGET budgets, never shared - the rule that cost 20.190/20.193 R5 two boots and
  cost p2(133) half its instrument.
- Adding a function later is ONE LINE in kTargets.
All twelve RVAs are declared as gate-visible constants so verify_hook_rvas.py resolves
every one against .pdata: 55 RVAs checked (was 43), 0 bad, VERIFY PASS.

TARGETS: ent_recv 0x1718510 (the entry, zero static refs - its caller IS the question) |
ent_header 0x1717EB0 | ent_create 0x1718080 | queue_evt 0x16F0F60 (our carrier) |
queue_down 0xE04E30 | act_router 0x16E6ED0 (fires per svc-9 message - the carrier census)
| sobj_decode 0xE739D0 | ring_commit 0xDFEC50 | registry 0x16BAB50 | schema_res 0x4C74D0 |
ent_index 0x4C16C0 | ent_encode 0x171E240.

## PURPOSE

Name the real entity carrier. If `ent_recv` fires, its caller_rva names the call site the
binary cannot show us, and the implementation follows directly. If it never fires, the
census says so explicitly and the twelve counters show exactly how far the path gets.

## GRAPHICS DELTA

ZERO new rendered models from the instrument. world_population stays armed (as p2(136)),
so the same single injected entity is attempted - no more. All hooks are read-only
pass-throughs that call the original and log.

## FALSIFIABLE CLAIM

CLAIM: with both clients in the Tower, `ev=mtrace stage=census` lines appear every 5 s on
both machines listing all twelve counters, and at least one of ent_recv / act_router /
queue_evt shows a non-zero count with a caller_rva.

CONTENT NEGATIVE (pre-named - L6):
- ALL TWELVE COUNTERS ZERO while activity messages flow: the whole traced cluster is off
  this path and the entity front needs a different map entirely. That is a real finding,
  and the census makes it unambiguous rather than a silence.
- ent_recv NON-ZERO: its caller_rva is the answer. Resolve it with pdata_bounds.py and the
  carrier is named - implementation next, no further probe.
- act_router NON-ZERO but ent_recv ZERO: the router never routes to the entity cluster,
  which means entity replication does NOT ride svc 9 at all. STANDING HYPOTHESIS to test
  against: it rides the GAMEPLAY plane (UDP 30976) - p2(136)'s pcap's largest flow by far
  is rig <-> server:30976 at 118 KB, and 20.196 R3 showed bulk rides that channel.
- CENSUS LINES ABSENT ENTIRELY: the flag did not take or the DLL did not load. Check the
  install census before reading anything else.

## ABSENCE NEGATIVE (L13)

This instrument is built specifically so absence is never ambiguous: the heartbeat prints
zeros, and the install census prints `attached=0/1` per hook. If NO `ev=mtrace` line of
any kind appears, that is a deploy fault, not a finding.
The p2(135)/p2(136) session result must ALSO still hold or the entity data is void:
checksum failures 0, citizen join succeeded, peers 0x7 / players 0x3.

## MEASUREMENT

  mac/rig : grep -a 'ev=mtrace stage=census'   -> all twelve counters, zeros included
  mac/rig : grep -a 'ev=mtrace stage=enter'    -> caller_rva per traced call
  resolve : RE_scripts/pdata_bounds.py <caller_rva + 0x140000000>
  session : checksum=0, citizen join succeeded, players valid 0x3 must still hold

## CHAIN MARKS (L16)

| Link | Mark |
|---|---|
| The membership front is closed | VERIFIED-BY-EXECUTION (p2(135)/p2(136), both machines) |
| Our carrier cannot create an entity | VERIFIED-BY-DISASSEMBLY (20.209: FUN_1416F0F60 has one downstream call; that chain ends in the ring commit) |
| The entity chain has no static references | VERIFIED-BY-DISASSEMBLY (calls/jumps/qword/RVA all zero image-wide) |
| 0x141718080 is not on the live path | VERIFIED-BY-EXECUTION (p2(136): 0 calls while 50 creates were attempted) |
| The peer channel carries no guardian | VERIFIED-BY-EXECUTION (p2(136) pcap, profiles live, max packet 268 B) |
| Who invokes 0x141718510 | UNKNOWN - THIS BOOT |
| Whether entity replication rides UDP 30976 | HYPOTHESIS - informed by the pcap, not tested |

## DEPLOYED (p2(137))

  clients mac+rig `80f5ed1d64da66c7` (NEW - milestone_trace added; deployed via
             deploy_client_dll.sh with literal provenance asserted on BOTH).
             milestone_trace TRUE; world_trace FALSE (it also hooks 0x141718080 and two
             detours on one address is the decoder_trace/state_diff collision again);
             state_diff FALSE; decoder_trace FALSE.
  server exe `789d8d9f0ed94e9e` UNCHANGED. world_population TRUE, profile TRUE,
             client_base FALSE.
  ROLLBACK: milestone_trace FALSE restores p2(136) exactly.

## LITERAL TARGETS

LITERAL TARGETS:
  Game/bin/x64/steam_api64.dll: ev=mtrace, stage=census, ent_recv, act_router

## ADVERSARIAL PASS

ADVERSARIAL PASS: waived: twelve read-only pass-through detours on .pdata-verified
function starts (gate: 55 checked, 0 bad, VERIFY PASS), each calling the original and
logging; per-target budgets; one 5-second heartbeat thread; no server change; rollback is
one client flag. The colliding hook (world_trace) was identified and disarmed BEFORE the
boot rather than after.

## RUN SHAPE

1. (DONE) Build, gate 55 RVAs, deploy the DLL to BOTH machines with literals asserted,
   arm milestone_trace and disarm world_trace on both, archive p2(136), verify hashes.
2. mac to orbit, then Tower, SOLO. Confirm the census lines appear and the session is clean.
3. Rig joins the Tower. Hold ~60 s - the heartbeat needs a few cycles.
4. Read the census first, then any caller_rva, then resolve it with pdata_bounds.py.
