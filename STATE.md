# STATE - living snapshot

STATUS: live (2026-08-30 ~01:2x). Verdict + deployed + next + reading order only.
FINDINGS holds the dated entry stack; front detail lives in FRONT_*.md; operational
and platform facts live in ENVIRONMENTS.md.

Updated: 2026-08-30. *** THE MEMBERSHIP PROFILE PIPELINE IS DONE, AND REGION A IS FULLY
DECODED: IT CONTAINS NO APPEARANCE FIELD. *** The server authors a profile block; both
clients decode, apply and run the profile helper on each OTHER's player rows (20.194);
authored content survives byte-exact both directions - a name (20.195) and real
account+character identity (20.198); a peer's profile PERSISTS in a per-player array
measured from memory (20.201: row 0 at session+0x3b80, stride 0x1a8). All 232 bytes of
region A are now decoded on two accounts (20.202): a name, an id, an enum, two -1
sentinels, an empty pair, the account+character SOIDs, a POWER float (1060.0f at
entry+0xd0), and a constant. No gear hash, shader, ornament or material reference exists
in it. The unlock that opened the pipeline was ONE bug: region B carries FOUR presence
bits and our writer emitted ONE (20.188/20.189).
NEXT: HANDOFF_2026-08-30_CONSUMER-HUNT.md is the pickup doc. Near-term shippable win:
region A chunk 8 is the POWER value and we can write region A, so rendering a peer's
power number does not wait on the appearance question.

## DEPLOYED (2026-08-30, p2(128))
  server exe     `136e11e15c9acbe9`: region B = 4 presence bits; profile name (chunk 1)
                 and identity (chunk 7) writers. publish_player_profile TRUE,
                 profile_name "SUNRISE", profile_identity TRUE, retry-cap 2.
  MAC client DLL `0e3d78f30d3396a7`  } decoder_trace + profile_harvest + profile_ingress
  RIG client DLL `0e3d78f30d3396a7`  } with per-(path,index) budgets and the after-write
                 landmark scan. staging_populate FALSE on both - it MUST stay false
                 (20.191: substituting suppresses the profile helper).
  ROLLBACK: clear profile_identity / profile_name (settings flip, no rebuild) returns the
            block to its earlier shapes; prior binaries as *.bak_p2d6_<ts> (server) and
            steam_api64.dll.bak_p2d7_<ts> (clients).
  NOTE: settings.json is FORMAT-SENSITIVE (trap 18) - text-insert edits only, never a
        serialiser round-trip. Procedure in ENVIRONMENTS.md.

## WHERE WE ARE
Session / activity / transport / membership: DONE and symmetric. Profile authoring: DONE
and proven to carry arbitrary content. Appearance: BLOCKED, and every route this project
can currently see is closed BY MEASUREMENT (20.196-20.202) - see the handoff's WHAT IS
CLOSED. Appearance reaches a retail client by a mechanism we have not identified.
OPEN, recorded not chased: chunk 2's 0xC5-band id (the one identity field we do not
author; do NOT synthesise it - the obvious formula fits the mac and fails on the rig);
what consumes the 48-byte-record list built by the gather at 0x140D48490; the black
screen (7 paired runs, no mechanism, idle-time hypothesis FALSIFIED by p2(127)).

## HARD RULES (earned; each cost a boot or a day)
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
  appearance carrier (20.202).
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
   fabrication (20.87) | type-54 bubble (20.96) | client-memory profile harvest (20.173).

## READ FIRST (any session taking over)
  0. HANDOFF_2026-08-30_CONSUMER-HUNT.md - the pickup doc. Then FINDINGS 20.202 -> 20.187
     newest first; they supersede the 20.183-20.185 staging narrative, whose DISASSEMBLY
     stands but whose conclusions do not.
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
