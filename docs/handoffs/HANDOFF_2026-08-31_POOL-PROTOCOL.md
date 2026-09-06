# HANDOFF 2026-08-31 - THE POOL-PROTOCOL LANE (mid-lane, instruments armed)

STATUS: SUPERSEDED by FINDINGS 20.219 (2026-08-31 15:3x) - the entity-index
front it describes is CLOSED and its central premise ("the host mask is empty")
is retracted. Its POOL FAMILY STATIC MAP stands and is still the reference.
Its hunt list is dead. Original status line follows.
STATUS: live. Supersedes HANDOFF_2026-08-30_ENTITY-FRONT.md (its hunt list is
spent: the ring consumer was deprioritized by 20.211; the entity cluster and the
peer channel stay closed). Read this + FINDINGS 20.215-20.218 before touching
the peer-rendering lane.

## THE ONE-PARAGRAPH STATE OF THE WORLD

Membership is CLOSED (two clients, one Tower, authored identity, zero session
errors - unchanged since 20.208). The wall is peer rendering, and the lane has
narrowed to the entity-index pool: the client's free-slot mask at manager+0xC118
is EMPTY on the host client at Tower entry (every boot, -1 x22-52 creation
failures) while the joiner's mask is FULL (branch-A memset; allocations 0..6
succeed, measured via the outparam instrument). We built and shipped the missing
assignment message (activity type 30, one u32, schema 0x80808683 ->
[pool+0x602b4]) - it arrives, decodes, and the one-shot sync 0x14171BB50 runs -
and the mask STILL fills empty. Two theories died by measurement this session
(type-20 teardown; router-flags gate - our messages carry flags 0x00 and route).
The best remaining lead is NEW: the client emits PERIODIC type-20 messages
(~5s, dword constant 700=0x2BC, varying flag word) nobody has answered or
explained.

## WHAT IS BANKED (verified, reusable)

- POOL FAMILY MAP (all verified-by-reading + live-corroborated):
  senders 0x1404F88C0 (type-0x14 count request) / 0x1404F56F0 (type-0x15 bitmap
  donate, 8x0x80 copy) - both via 0x1404FB770 fast path -> [pool+0x6c18]
  vtable+0x28. Pool ctor 0x1404F77D0 (arg6 = connection; subscribe via
  vtable+8; mask zero at +0x5FE98; sent-flags +0x60298/9a; assignment token
  +0x602b0/b4 = -1). Receiver 0x1404F2970 -> 0x1404DC080 (schema 0x80809857
  per claim K) -> apply 0x1404F5D60 (OR into +0x5FE98). Pool DISPATCHER
  0x1404F7DF0 = conn vtable+8 (21-entry table 0x141F92360: type 0 -> pool_recv,
  0x1E -> assignment handler 0x1404F34C0). Assignment handler: schema
  0x80808683 = one u32 -> [pool+0x602b4]. Sync 0x14171BB50: gate on
  +0x602b4 != -1, archetype-table walk (0x1430B0440, 0x70 stride), 64x8192-bit
  per-participant blocks, merge 0x1404fbad0, then RESETS +0x602b4 = -1
  (0x1404f49f0) - ONE-SHOT TOKEN.
- MEASURED: host mask empty / joiner mask full at allocator level (outparam
  instrument reads [rdx]: verdicts 1,2,3,4,5,6 on the rig vs 0xFFFFFFFF on the
  mac). The assignment value is used ONLY by the != -1 gate (eax dead after cmp).
- THE FORK NOW SPEAKS: type-0 join grants (reach pool_recv - proven), type-30
  assignment (reaches the handler - proven), type-20 (reaches the router with
  routable flags - proven). All behind settings:
  entity_index_allocation / entity_index_assignment / entity_index_grant.
- ACTIVITY NAME TABLE anchored: allocate_entity_indices=20,
  free_entity_indices=21, replicate_membership=12, send_client_heartbeat=39.
- The activity ROUTER (0x1416E6ED0, event-bus handler #14, gate `test byte
  [rbx+1],1`) input objects: {u8 type, u8 flags, u16 ?, u32 param}. Our pushes
  and internal messages BOTH carry flags=0x00. The router is NOT the blocker.

## THE HUNT, IN ORDER (desk work first - no boots needed)

1. **The periodic client type-20s** (20.218 R3): ~5s cadence, dword constant
   700 (0x2BC), varying u16 flag word, in the router stream with routable
   flags. What generates them, what consumes them, and does the constant 700
   relate to slot arithmetic? Check server-side logs for inbound type-20
   (20.212 saw only 39/47/14 inbound - if these never reach the fork they are
   CLIENT-LOCAL authority-side slot management, which reframes the lane).
2. **The sync fill semantics** (0x14171BB50 full read): is the archetype walk
   + 64-block loop a FILL of the local mask or a DONATE/RETURN walk? What are
   the fill's inputs and why are they empty on the host at sync time?
3. **The rig never attempts peer creation** (20.211 R3, still unexplained):
   if the joiner is SUPPOSED to create the peer locally, understanding that
   trigger may bypass the host path entirely.
4. **Creation contract re-read**: community doc sections 1.3-1.7
   (creation-with-baseline, archetype-by-schema-hash) against everything now
   known - it was deprioritized when the slot theory appeared; it may be the
   upstream prerequisite.
5. **Infra (anytime)**: move the server to the Ubuntu box (kills the
   terminal-restart fragility; clean one-variable test of the mac black
   screen, which stays parked).

## DEPLOYED (2026-08-31 14:3x)

- server exe a9d033e2487b9cbe - RUNNING, detached-safe (relaunch via
  `nohup bash mac-port/launch-server-macos.sh`; a terminal restart killed it
  once this session). Settings: entity_index_allocation TRUE,
  entity_index_assignment TRUE (type-30 push, value 0), entity_index_grant
  FALSE, reserve=8 / join_grant=4088 (keep).
- client DLLs 2fba6d1f30a18c78 (mac+rig) - milestone_trace 18 targets: the
  pool family hooks (pool_send_req/don, pool_recv, pool_apply, pool_dispatch,
  pool_assign), idx_alloc OUTPARAM ([rdx] verdict), act_router ARGV DUMP
  (filtered to types 20/21/30, OUTSIDE the budget). Rollbacks:
  .bak_p2d7_20260831_* series on both machines.
- BOOT HYGIENE (cost a boot this session): deploy client DLLs BEFORE the user
  boots - a running process never re-reads its image, and a fresh log can
  still be from a stale binary. Verify provenance by hook BEHAVIOR (a new
  instrument's line present), not disk hash alone. Restart the server with
  `bash RE_scripts/reset_lobby_claims.sh > /tmp/reset.log 2>&1 &` (background
  it; it hangs after succeeding). Use logindex/logq for log analysis, not
  grep chains.

## METHOD (unchanged, re-earned)

Measure, do not derive. Read the client's own bytes. Pre-name both negatives.
One instrument that prints its zeros beats three one-off hooks. Adding a
milestone_trace target is one line - the outparam/dump_rcx flags extend it
without new hooks.
