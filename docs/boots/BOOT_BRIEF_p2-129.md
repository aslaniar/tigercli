# BOOT BRIEF p2(129) - PHASE 1: WORLD-TRACE INSTRUMENTS, SOLO LIVENESS

STATUS: live (2026-08-30). Reads with RE_output/claims/event-subscriber-hunt.md,
chunk8-wire-form.md, peer-visibility-codec-findings.md, and FINDINGS 20.201/20.202.

## WHY THIS BOOT (the three-lane context)

Three static hunts closed this week: the manifest event chain is world-transition sync
(inert for appearance), the character registry is strictly local, and region B is a second
name block. The corrected milestone path is the ENTITY layer: two guardians in one Tower =
one bubble + a player-archetype entity per peer, each client authoritative for its own
avatar. The fork's world-population carrier already emits a player-shaped record
(0x80806AC0 = the client's own player baseline, schema_capture-verified 08-16), and the
peer-visibility lane's own rule was: the decode OBSERVER must exist before the emission
flag is ever turned on again.

This boot ships exactly that observer plus the two live reads tonight's hunts left behind,
and validates them SOLO before any paired run spends them.

## THE THREE INSTRUMENTS (world_trace, one hook unit, all read-only, default-false)

1. `stage=emit` - the manifest emitter 0x1417607B0 (fn start, verified). Logs the
   eventid, record count, each record's first 8 bytes (the chunk-2 identity the client
   computes for its OWN row - hunt item 1), and the match flags. First call also fires
   the one-shot schema dump.
2. `stage=entity` / `stage=entity_done` - the entity create/decode path 0x141718080
   (fn start, verified). Its RETURN VALUE is the decode oracle the front lacked:
   ret 0 = success, 1/2 = codec-body decode failed, 3 = update-mask failure. Logs the
   record fields and the decoded body head.
3. `stage=schema*` - one-shot dump of the runtime schema registry (*0x142439C70):
   the chunk-8 power key (read live from *(int32*)(*(void**)0x14209ED00)) and the player
   archetype 0x80806AC0. Both trees are runtime-built and NOT statically dumpable (femu
   confirmed the engine faults on the static image). Raw row/slot/node/entry bytes are
   dumped beside the (INFERRED) traversal so a traversal slip is recoverable desk-side.

## PURPOSE - what this boot learns, win or lose

Phase 1 (solo) is an instrument-contract boot. Three questions:
  A. Do all three hooks attach and log (`install result=ok`, then real lines)?
  B. Does the manifest emitter fire in a SOLO session, and what chunk-2 identity does
     the client compute for ITSELF? (The server publishes chunk 2 ABSENT, so any
     nonzero id in rec0 is client-generated - the value we cannot currently author.)
  C. Do the schema trees resolve and dump? The chunk-8 tree unlocks the power writer
     offline; the player-archetype tree retires codec-findings F2 (the encoder's
     assumed field layout) before any emission boot.

## GRAPHICS DELTA

ZERO new rendered models. Three read-only detours, pass-through, capped, SEH-guarded.
No server change - the running server exe is UNCHANGED from p2(128). No behaviour change.

## FALSIFIABLE CLAIM

CLAIM: in a solo session, the emitter fires with count>=1 and rec0 carries a NONZERO
8-byte chunk-2 identity (the client's own), and both schema trees resolve to nodes with
a nonzero bound.

CONTENT NEGATIVE: rec0 = 0000000000000000 on every emit. Then the client's own chunk-2
identity is ALSO zero in a solo session (populated only on peer arrival or later) - and
the manifest's identity column is filled by a different stage than we assumed. The
schema dump still answers C regardless.

SECOND: the schema dump resolves rows but returns `result=no_node` or faults for BOTH
keys. Then the resolver arithmetic (character-record-mapping CLAIM 2, dialect A) is
wrong for the live tables - but the RAW row/slot hexdumps printed beside it are the
corrective evidence, so the boot still advances the chunk-8/power and F2 questions.

## ABSENCE NEGATIVE (L13)

- Zero `ev=wtrace stage=install` lines at all: the new DLL did not load. The literals
  `stage=emit` / `stage=entity` / `stage=schema_id` are confirmed present in the
  deployed DLL by the deploy gate, so their absence in the log indicts the deploy or
  the settings gate (`world_trace` not true in the client's settings.json).
- `stage=install result=skipped why=disarmed`: the hook armed off - a settings fault,
  not an instrument fault. Fix the settings edit per trap 18 (text edit, never a
  serialiser round-trip) and relaunch.
- Install ok but zero `stage=emit` lines after a full solo session: the manifest
  handler only fires on ROSTER CHANGES after the initial publish, or fires through the
  sibling gather (0x140D48300, the [r15+0x204]!=0 branch). Compare the server's
  membership push times against the client log before concluding.
- `stage=schema_id chunk8_key=0x00000000`: the pointer at 0x14209ED00 was null or
  unreadable at fire time - the registry is built later than the first emit. The dump
  is one-shot by design, so a retry needs a rebuild-flip or the next run.
- Entity lines: NONE expected in a solo boot (no world-population records are pushed).
  Zero is the EXPECTED solo reading for that stream - its liveness line is the install
  line, and its first real test is the Phase 3 emission boot.

LIVENESS: `ev=wtrace stage=install result=ok emitter=0x17607B0 entity=0x1718080 ...`
in the mac client log.

## CHAIN MARKS (L16)

| Link | Mark |
|---|---|
| Manifest gather 0x140D48490 collects per-player chunk-2 into 48B records | VERIFIED-BY-DISASSEMBLY (this week, instruction-cited) |
| Sole caller 0x140D47D00 feeds emitter 0x1417607B0; ABI read off the body | VERIFIED-BY-DISASSEMBLY (this week) |
| The event chain is world-transition sync, not appearance | VERIFIED-BY-READING (claims/event-subscriber-hunt.md) |
| The character registry is strictly local; region B is a name block | VERIFIED-BY-READING (claims/character-registry-route.md) |
| Tower guardians are world entities; each client authoritative for its own | VERIFIED-BY-READING (activity type table + entity-archetypes.md) |
| The player archetype hash 0x80806AC0 | VERIFIED-BY-EXECUTION (schema_capture, 08-16) |
| The chunk-8 schema table is runtime-built | VERIFIED-BY-EXECUTION (femu: engine faults on the static image) |
| The resolver arithmetic used by the dump | INFERRED (documented in character-record-mapping CLAIM 2; raw bytes dumped beside it) |
| What the client computes for its own chunk-2 identity | UNKNOWN - THIS BOOT |
| Whether the schema trees resolve live | UNKNOWN - THIS BOOT |
| Entity record decode verdicts under emission | UNKNOWN - Phase 3 boot |

## INSTRUMENTS

INSTRUMENTS:
  stage=emit
  stage=entity
  stage=schema_id
  stage=install

## LITERAL TARGETS

LITERAL TARGETS:
  Game/bin/x64/steam_api64.dll: stage=emit, stage=entity, stage=schema_id

## ADVERSARIAL PASS

ADVERSARIAL PASS: waived: read-only observation hooks on .pdata-verified function
starts (verify_hook_rvas.py PASS this session, 0 bad), no server change, no behaviour
change, every client read SEH-guarded and capped. The one write-adjacent risk (the
schema dump dereferencing runtime pointers) is fully SEH-guarded and one-shot.

## SOLO CONTROL

Solo control boot BEFORE any two-machine run (hard rule). Phase 2 (paired: the peer's
chunk-2 identity during co-location) and Phase 3 (paired, world_population emission
flipped on, settings flip, no rebuild) follow only after this boot's instruments are
proven live.
