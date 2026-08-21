# RE MAP STATUS — 2026-08-14 (the exhaustive "what's left" ledger)

Purpose: single source of truth for mapping coverage before any rebuild work starts.
Status values: CLOSED (nothing left worth discovering) / PARTIAL (named gaps remain) /
OPEN (untouched) / DEAD (server-side, unrecoverable — reimplement only).

## A. Client protocol stack (the wire contract)

| Subsystem | Status | What remains | How to get it |
|---|---|---|---|
| SignOn HTTP + protobuf | CLOSED | — | — |
| Relay dial + byte-order bug | CLOSED (mechanism) | — | — |
| BAP envelope + dispatch | CLOSED | response entries ≥48 directional only | live registry read (opportunistic) |
| Secure channel (AES-GCM) | CLOSED | seal internals at 0x144A50FE0 decoded only superficially | 1 decompile if ever needed |
| Family 0 (banner) | PARTIAL | registration blob B base structurally solved (edx=0); diff arms mapped | 1 createFunction (cosmetic) |
| Family 3 (roster) | PARTIAL | registration sweep base (blob A, `lea edx,[r9+3]` x3 = families 3/4/5); wire CLOSED | 1 createFunction |
| Family 4 (account/char/inv) | CLOSED (byte-exact) | char-progression 0x10 offset discrepancy vs Sunrise | 1 re-read of both layouts |
| Family 5 (investment) | CLOSED | — | — |
| Family 7 | PARTIAL | register site known (FUN_140be49d0); payload shapes unexplored | 1 GLM lane |
| Web-service opcodes | PARTIAL | 47/200 server shapes known; client compare sites unmapped (table-driven) | live dump of 0x14280E3E0 + family-5 getter bodies (needs game up) |
| Activity messages (svc-8) | PARTIAL | wire + apply machinery CLOSED; per-message payload semantics = 59 names, ~5 decoded | P1 entity-schema lane + per-type digs |
| Entity sobject archetypes | OPEN | the payload field layouts per archetype (Vex goblin vs Cabal) — nobody has this | schema-entry dump + GLM dig (the never-run P1) |
| Activity-state commands | PARTIAL | 1 of 19 commands named (index 2 = slice-set); 18 unnamed | 1 Ghidra batch (FUN_140b4xxx family) + 1 dig |
| Vendors | OPEN | storefront opcode + defs; hint: "300_vnd" named tag exists | opcode lane after registry dump |
| Matchmaking (svc 42/43) | OPEN | skeleton only | dispatch entries exist; 1 dig |
| Social/clans/friends | OPEN | types 44/45 + friends services in dispatch | 1 dig (low priority) |
| Upload/ticket-drop | CLOSED | — | — |

## B. Content layer (the on-disk world)

| Item | Status | What remains | How |
|---|---|---|---|
| .pkg container format | CLOSED | — | — |
| Named-tag tables | CLOSED | 567 names / 10 classes extracted; coverage is what it is (199 pkgs carry them) | — |
| Class census (references) | CLOSED | 2.8M entries, top-60 classes enumerated | — |
| Spawn-set inventory | CLOSED | 386 sets, all destinations/raids/dungeons/gambit | — |
| Spawn-set payloads | BLOCKED-1KEY | blocks are AES-GCM(3)-encrypted; key table runtime-built; derivation formula known (primary = bootstrapToken + identityConstant) | one live read of the 48-byte key table (game up, 5 min) → then full extraction |
| Scenario/bubble/slice tables | PARTIAL | Sunrise readers exist (scenario_walk etc.); our own walker not built | port after keys |
| Item/investment defs | PARTIAL | Sunrise reads item/progression tables; class ids in census | port item_definition_reader |
| Activity definitions | OPEN | the biggest unmapped content class | after keys + scenario port |

## C. Binary-level

| Item | Status | Notes |
|---|---|---|
| Unpacked image | CLOSED | 94%+ plaintext; Ghidra project complete |
| Cold runs (4.7 MB) | OPEN | never decrypt in menu/destination/orbit; crucible private match + raid override untested; low marginal value |
| Sunrise symbolization | DONE-ENOUGH | PDB built; stub naming optional (source already names hooks) |
| Dispatch registry dumps | CLOSED | both runtime tables captured |

## D. Dead (reimplement, never discover)
Combat sim (damage/health/abilities), enemy AI, mission state machines, loot RNG,
anti-cheat. These lived on Bungie's servers. Ground truth options: live-D2 capture
(high risk, separate project), community behavioral docs, D1 priors.

## E. Rebuild-readiness gates (what unblocks what)

- **Standalone server (S0)**: NO open RE items. Blocked only on engineering.
- **Persistence DB (S1)**: family maps CLOSED. Item defs partial → port readers.
- **Static world (S2)**: ONE runtime read (key table) → spawn payload extraction →
  emit via closed recipe. This is the critical path.
- **Combat (S3)**: entity archetype schemas (P1 lane) + DEAD sim work.
- **Missions (S4)**: activity-state commands (18 unnamed) + activity defs + DEAD sim.

## F. Recommended completion order (cheapest-first to fully-closed map)
1. Key-table live read + spawn-set payload extraction (S2 unblock)
2. Entity archetype schemas (the last big OPEN client-side unknown)
3. Activity-state command registry (18 names)
4. Web-service opcode client sites (live registry dump while playing anyway)
5. Family 7 + vendors (small digs)
6. Cold-run warming attempts (crucible/raid) — optional
7. Family-3/0 registration createFunction (cosmetic closure)

After 1-5 the client-side map is as exhaustive as static+RPM analysis allows;
everything beyond that is either DEAD (reimplement) or content extraction at scale.
