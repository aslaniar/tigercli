# STATE - living snapshot

STATUS: live (2026-08-30 15:1x). Verdict + deployed + next + reading order only.
FINDINGS holds the dated entry stack; front detail lives in FRONT_*.md; operational
and platform facts live in ENVIRONMENTS.md.

Updated: 2026-08-30 15:1x. *** THE BLACK SCREEN IS SOLVED IN PRINCIPLE AND REPRODUCED
BOTH WAYS. *** The membership state-hash rejection is TOTAL, not chronic: every failure
force-disconnects the group session 1:1 (268/268, 722/722, 289/289 across three logs),
which drives a permanent rejoin loop (23,908 revisions / 2,426 admits in one run at the
250 ms retry cadence) and collapses the Tower citizen join - that IS the black screen.
It tracks the PLAYER ROW: 557/557 failures across two independent runs carry players>=1,
against 21,832 published players=0 updates with zero failures. The player row's only new
content is the profile block, which build_session_state does not model at all.
ARM A (p2(131), profile OFF + client_base OFF) came back CLEAN on every measure: 0
failures, 0 disconnects, revision 9, 2 admits, peers 0x7 / players 0x3 reached, and
"Citizen join for PUB56.56 succeeded!" - a line absent from 557 baseline failures.
That also INDICTS p2(129): the historical layout hashed correctly 9/9, so the +8 shift
(session_state_client_base) was neither necessary nor sufficient. Held FALSE from here.
NEXT: p2(132) arm C - STAGED AND GATED, one line, profile TRUE against the proven-good
base. Fails -> the fix is bounded (model the profile bytes in the player entry; we
author them). Clean -> client_base TRUE was the whole regression and the checksum front
closes with the profile pipeline live. Then the render question, on a stable session for
the first time. Chunk 8 power stays blocked: the schema dump rides the manifest emitter,
which NEVER fires in fork-hosted flow (20.203 R4) - needs a new observation point.

## DEPLOYED (2026-08-30 evening, p2(130))
  server exe     `35ae2802aa7cdeb7` (unchanged binary; both flags read at runtime).
                 LIVE SETTINGS: session_state_client_base FALSE (proven good, 20.205 R4),
                 publish_player_profile TRUE (STAGED for p2(132) arm C, inert until the
                 next restart), world_population FALSE.
  clients (mac+rig) `30fe49c6914902f2` (unchanged): decoder_trace / world_trace /
                 state_diff ALL DISARMED on BOTH machines, verified byte-exact (the rig
                 edited locally, scp'd up, scp'd back, hashes compared).
  ROLLBACK: every flag above is a settings flip, no rebuild (backups *.bak_p2d13*_*).
  NOTE: settings.json is FORMAT-SENSITIVE (trap 18) - text-insert edits only, never a
        serialiser round-trip. Procedure in ENVIRONMENTS.md.

## WHERE WE ARE
Session / activity / transport / membership: DONE, symmetric, and now STABLE under arm A
(20.205 R3) - a two-player Tower session that does not collapse, for the first time.
Profile authoring: DONE, but it is the prime suspect for the hash break (20.205 R5).
Appearance/entity: world-population front UNBLOCKED (observer deployed, flag off).
Appearance closures 20.196/20.198 stand as disassembly but their NULLs are CONFOUNDED -
every one was measured on a session force-disconnecting ~1.2x/s. Re-verify when stable.

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
CLOSED BY MEASUREMENT 2026-08-30: the client<->client channel as the appearance carrier
  (20.196) | the client-side pull of a peer's character record (20.198 R2) | the
  server-side push / "add root->account resolution" (20.198 R3) | region A as an
  appearance carrier (20.202) | region B as an appearance carrier (it is a second name
  block - character-registry-route.md) | the character registry as a foreign-record
  ingest (same file) | the roster-change manifest chain as an appearance route OR as a
  live observation point in fork-hosted flow (event-subscriber-hunt.md; 20.203 R4).
RETRACTED 2026-08-30, MINE: the whole staging-population lane (20.191/20.192) - NULL is
  the apply's normal third argument at stage 4 and substituting for it SUPPRESSES the
  helper | "the client discards a peer's profile" (falsified by 20.201 R1, 14/14) | the
  black-screen idle hypothesis (falsified by 20.200 R3) | "three 16-byte vectors are a
  transform" - it is a compiler-vectorised 48-byte struct copy (20.201 R3b).
CLOSED BY p2(110)/20.170: THE WHOLE ADMISSION-FORGE LANE (20.158-20.169). Its premise was
  false and the injection poisoned the mac's OWN structures. Do not forge a peer record.
RETRACTED 2026-08-27: "Could not find tracking data" as the release (20.105) | friends
  lane as closed - slot 43 IS the string-pair setter (20.103) | counts-vs-bitmasks (20.104).
RETRACTED 2026-08-29 by 20.172: peer-player instantiation read off the wrong session |
  the "EST-N/MEM-0 wall" | the peer retry cap as the gate (it is a tuned brake).
CLOSED BY EXECUTION: friends rich-presence as the JOIN ROUTE (20.107) | type-12 wire shape
  (20.81) | delivery-gap theory (20.74.4) | gate-table<->reason-enum, which also makes the
  REASON BYTE unreliable (20.83/84) | `reason_name` (20.85/86) | `client.region_private`
  (20.82) | ws 701/702 (20.82) | steam_player_group (20.104).
RETIRED BY 20.113 (the whole class): making a peer appear by SHAPING a BAP body - member
  row sweeps, trailing fields, bitmasks, reason bytes, roster pushes. The client reads its
  session member table, not our declarations.
ROAD C CLOSED 2026-08-28: the client walks its own managed-session member table, not BAP
  membership (FRONT_public-host-chain.md, 20.113-20.144).

## PARKED: rx-decode (20.92) | reason hunts (20.86) | blind sweeps (20.49-51) | posse
   fabrication (20.87) | type-54 bubble (20.96) | client-memory profile harvest (20.173)
   | chunk 8 power (blocked on a live schema read - the dump must ride a hook that
   actually fires; see 20.203 R4).

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
