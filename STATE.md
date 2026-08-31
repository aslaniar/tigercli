# STATE - living snapshot

STATUS: live (2026-08-30 ~18:0x). Verdict + deployed + next + reading order only.
FINDINGS holds the dated entry stack; front detail lives in FRONT_*.md; operational
and platform facts live in ENVIRONMENTS.md.

Updated: 2026-08-30 ~18:0x. *** THE MEMBERSHIP FRONT IS CLOSED. TWO PLAYERS, ONE TOWER
INSTANCE, STABLE, WITH AUTHORED IDENTITY LIVE, ZERO ERRORS ON BOTH MACHINES. *** The
state-hash rejection was the profile block: the client stores 396 bytes of it inside the
hashed player entry and build_session_state modelled none of them. Fixed in two measured
steps - the name's key16(L) terminator (20.206) and the tail's dword at +0x0c (20.207),
both read off the CLIENT's own decode of a body we published, not derived. Result: 0
checksum failures, 0 force-disconnects, citizen join SUCCEEDED, revision 9-20 against a
23,908 baseline, peers 0x7 / players 0x3.
*** 20.203 R1 IS CORRECTED: the checksum was NOT the black screen. *** With zero failures
and zero disconnects the mac still went black, and p2(136) separated the two: the mac
(which also HOSTS the server) goes black; the rig (pure client) never has, in any run.
Not on the critical path - the rig proves a client holds a clean paired session and
renders.
THE REMAINING WALL IS PEER RENDERING, and it is now isolated on a machine with nothing
else wrong. Closed this session: the peer channel carries no guardian even with profiles
live (20.208 R5, the pcap 20.196 asked for); and the entity-replication cluster
0x141718510/0x1717EB0/0x1718080 is RETIRED - attached=1, calls=0, solo AND paired, while
the guardian renders (20.210).
NEXT: the EVENT RING. Our type-7 record is decoded by the right decoder and committed to
a ring; ring_commit runs 147 solo -> 624 paired, the only counter that moves with a peer.
sobject-carrier.md says that commit writes {type,seq,count,tail,timestamp} to session
+0x130 and NOTIFIES THE +0x81e0 OBJECT. Sweep that consumer statically first
(field_xref.py on +0x130 / +0x81e0) - no boot.

## DEPLOYED (2026-08-30 ~18:0x, p2(137))
  server exe     `789d8d9f0ed94e9e` via deploy_p2d6_gameplay.sh (seven harness gates).
                 SETTINGS: publish_player_profile TRUE, session_state_client_base FALSE
                 (the historical base is the correct one - 20.205 R4 / 20.206 R5),
                 profile_state_variant 0, world_population TRUE.
  clients mac+rig `3ff651086721e1ad`: milestone_trace TRUE; world_trace / state_diff /
                 decoder_trace ALL FALSE (world_trace collides with the tracer on
                 0x1718080; decoder_trace and state_diff both own apply-adjacent
                 addresses). Rig settings pushed and read back byte-exact.
  ROLLBACK: publish_player_profile FALSE is arm A, measured clean at the session layer;
            milestone_trace FALSE restores p2(136).
  NOTE: settings.json is FORMAT-SENSITIVE (trap 18) - text-insert edits only.
  NOTE: NEVER hot-copy the server exe. deploy_p2d6_gameplay.sh restamps the content cache
        to the candidate's PE identity; a raw cp leaves cache and exe mismatched and the
        server dies at content_swap (cost a recovery this session).

## WHERE WE ARE
Session / activity / transport / membership / identity: DONE, symmetric, STABLE, verified
on both machines with the profile live. That milestone is closed.
Peer rendering: the one open front. Every appearance route this project pursued is closed
by measurement, and the closures are no longer confounded - the rig holds a clean paired
session and still renders no peer. The entity cluster is retired (20.210); the event ring
and its +0x81e0 consumer are the next target, statically first.
Instruments: milestone_trace (8 functions, caller RVAs, census printing ZEROS) is the
model to extend - add a target in one line rather than writing another one-off hook.

## HARD RULES (earned; each cost a boot or a day)
  - RESET THE SERVER BETWEEN RUNS (reset_lobby_claims.sh). The 2026-08-30 solo landing
    loop was a 12-hour-old server's accumulated state; every historical landing was on
    a fresh one. The recovery procedure in ENVIRONMENTS.md works - practice it.
  - NO .text patching; NO interface slot bound by a guessed ordinal. Census FIRST.
  - EVERY hook RVA goes through `RE_scripts/verify_hook_rvas.py` before a boot. A
    module-range check passes on a WRONG address and the detour never fires (20.173 R1).
  - Bundle OBSERVATION freely; bundle BEHAVIOUR only behind a switch flippable without a
    rebuild. p2(62) changed six bindings, froze, and its cause is now unknowable.
  - CENSUS BEFORE FILTER, always. Multiple retractions came from asserting a mechanism
    off a filtered or truncated view.
  - BUDGET OBSERVERS PER EVENT CLASS. A shared cap gets spent by the wrong event and the
    resulting null reads as a finding (20.190, 20.193 R5 - it cost two boots).
  - SCAN AFTER THE WRITE. p2(127) asked "does it persist" from before the write and got
    1 hit in 24 (20.200 R2).
  - PREFER LANDMARKS OVER ARITHMETIC. We choose what the server publishes, so the client's
    heap is self-labelling. Searching for a published value found the per-player array in
    one boot after three sessions of contradictory offset derivation (20.201 R2).
  - Wire fields have TWO conventions and the FIELD decides, not the C++ type: raw fields
    keep byte order, VALUE fields are MSB-first. Mixing them shipped byte-reversed SOIDs
    (20.197 R1).
  - One long-running or ssh-touching action per shell call; they hang AFTER succeeding and
    an interrupt leaves the server dead (recovery procedure in ENVIRONMENTS.md).
  - Solo control boot before any two-machine run; never return fabricated ids to client
    enumeration loops (p2(63)).

## DEAD ENDS - DO NOT RESUME (mechanism in the cited FINDINGS)
RETIRED 2026-08-30 by p2(137)/20.210: the entity-replication cluster 0x141718510 /
  0x141717EB0 / 0x141718080 - attached=1, calls=0, solo AND paired, while the guardian
  renders. Wrong subsystem, not a wrong observation point. Do not hook it again.
CLOSED BY MEASUREMENT 2026-08-30: the client<->client channel as the appearance carrier
  (20.196, and 20.208 R5 discharged its own re-open condition with profiles live: max
  packet 268 B, flat buckets) | the client-side pull of a peer's record (20.198 R2) | the
  server-side push (20.198 R3) | region A as an appearance carrier - fully decoded, no
  gear/shader/ornament field (20.202) | region B (a second name block) | the character
  registry as a foreign-record ingest | the roster-change manifest chain (20.203 R4).
RETRACTED 2026-08-30: 20.203 R1's "the checksum IS the black screen" (20.208 R2 - zero
  failures, still black) | the p2(129) +8 table shift (20.205 R4 - the historical base
  hashes correctly 9/9) | the staging-population lane (20.191/20.192) | "the client
  discards a peer's profile" | the black-screen idle hypothesis | "three 16-byte vectors
  are a transform".
CLOSED BY p2(110)/20.170: THE ADMISSION-FORGE LANE. Do not forge a peer record.
RETRACTED 2026-08-27/29: "Could not find tracking data" as the release | friends lane as
  closed | counts-vs-bitmasks | peer-player instantiation off the wrong session | the
  "EST-N/MEM-0 wall" | the peer retry cap as the gate.
CLOSED BY EXECUTION: friends rich-presence as the JOIN ROUTE | type-12 wire shape | the
  delivery-gap theory | gate-table<->reason-enum (which also makes the REASON BYTE
  unreliable) | `reason_name` | `client.region_private` | ws 701/702 | steam_player_group.
RETIRED BY 20.113: making a peer appear by SHAPING a BAP body. The client reads its own
  session member table, not our declarations.
ROAD C CLOSED 2026-08-28: FRONT_public-host-chain.md, 20.113-20.144.

## PARKED: rx-decode (20.92) | reason hunts (20.86) | blind sweeps | posse fabrication |
   type-54 bubble | client-memory profile harvest | chunk 8 power (needs a hook that
   fires) | the mac black screen (host-machine-correlated, 20.208 R3 - NOT on the
   critical path).

## READ FIRST (any session taking over)
  0. HANDOFF_2026-08-30_CONSUMER-HUNT.md (background) + FINDINGS 20.203/20.204
     (tonight: the checksum mechanism, the state_diff instrument, the exact next
     boot shape in 20.204 R3 - that staged recipe IS the pickup point).
  1. AGENTS.md (router) + its conditional triggers. Boot work ALSO loads LESSONS.md
     PRE-BOOT CHECKLIST and runs `gate_boot.py` on the brief.
  2. FRONT_e2e-stack.md for the layer map; FINDINGS 20.107 for what has never been touched.
  3. ENVIRONMENTS.md before ANY deploy, capture or settings edit - it carries trap 18
     (settings.json format sensitivity), the NIC-is-not-a-constant rule, and the
     server-recovery procedure.
  4. Contract refs in RE_output/claims/: l9-profile-layout.md, profile-builder.md,
     msg12-schema-decoded.md. steamfriends-vtable-audit.md is LARGELY RETRACTED.
  5. Captures contain NUL bytes - grep with `grep -a`, and prefer
     `logindex.py` + a query over grep chains for anything beyond a one-line peek.
