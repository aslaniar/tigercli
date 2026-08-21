# D2 ARRIVALS CLIENT — DOMAIN BRIEF (distilled from 20+ verified agent waves)

## Target
destiny2.exe — Destiny 2 Season of Arrivals (June 2020) Windows client, 122,984,224 B,
image base 0x140000000, 11 PE sections, two .text (28.9 MB @ RVA 0x1000; 81.3 MB @
0x3CC9000). VMProtect-style encrypted at rest; all corpus exports come from the
live-captured decrypted image. Project goal: complete map of the dead server's
contract — everything the client sends or expects.

## Verified ground truth (do NOT re-derive)
- PROTOCOL STACK: SignOn HTTP POST ("SignOn?platform=%s&build=%s", hosts
  signon.deadorbit.net / signon.gravityshavings.net) -> protobuf (fields 1-7,12,14-16;
  relay dial FUN_14174B9C0, byte-order bug site FUN_1417454A0) -> BAP channel (svc 30
  start, svc 25/26 shello) -> AES-GCM frames [16B tag][ct], 12B LE nonce, codec
  dispatch 0x144A50FE0, bcrypt.dll CNG.
- DISPATCH: thunks FUN_14106F860 (class table 0x141FCF6A0) / FUN_14106F870 (type table
  0x141FCF6E0 = A+8). Type->decoder registry DAT_14280E3E0. Message IDs 0..307 (64
  client + 8 Sunrise-only names in claims/bap-dispatch.md). 8 base descriptors
  0x141C3C600+0x90k; 37 response records 0x141C3CB88+0x60k.
- QUEUEZ FAMILIES: 0=banner, 3=roster, 4=account/character/inventory, 5=investment.
  Intake: FUN_1416F0F60/FUN_1416F17A0 -> FUN_140E010C0 -> parser FUN_140E0A0B0 ->
  dispatcher FUN_140E01960 -> fresh arm FUN_140E05EB0 / diff arm FUN_140E05DA0 ->
  commit FUN_140DFD740.
- WIRE (byte-exact): family header 21B {u32 type, u64 rootSoid, u32 version
  (0xFFFFFFFF=first sync), u8 flags, u32 objectCount}; object header 20B {u32
  definitionId, u64 version, u32 payloadSize, u32 encoding}; encodings 1=tagReflection
  (FUN_1404C74D0 -> FUN_1404B9200/BF920), 2=binaryDiff, 3=raw, 4=oodle. Sizes: account
  96,280 B; character 46,928 B; instance 416 B; inventory row 32 B x350.
- FAMILY-4 STORE: slots +0x8358, count +0xDEB54, per-family stride 0x81E8, dirty flags
  +0xDED11/12.
- ENTITY PIPELINE: spawn push {u32 id, u32 type, 132B body, u32 len, payload}; 8192-slot
  lease mask (1024 B) in payload. Apply: FUN_140E0F000 (15-entry dispatch
  DAT_141FBCB60). Command registry FUN_140B47E70: 19 commands all named
  (entity-combatants.md); cmd 2 = FUN_140B456C0 slice-set transition = spawn-set
  injection point. Activity-message enum: 59 names (0=entity_slots_allocated,
  44=advance_replication_epoch, 51=bubble_host_startup_info, 52=patch_epoch).
- SCHEMAS: tagReflection entry 0x28B {rel +0x24, bits +0x28, type +0x30, present
  +0x31, childHash +0x34, count +0x38/+0x40}. Root *DAT_142439C70 runtime-built,
  live-captured: 3 nodes, 170-field main schema; stream grammar = interleaved 16B
  pairs {bitOffset,0xC0 marker,back-offset,flags} + {ordinal,...,codec,subtype}.
  Reader tables DAT_141F94F38/DAT_141F94DC0, 32 entries each (bool, biased i8-i64,
  quantized f32, vector3d, forward_and_up, entity_index w/ 6-bit salt, tagged unions,
  160B blobs). Codec is Havok-reflection-descended.
- COLD RUNS (0x145D0D000-0x14609C000, 0x14896A000-0x148A5E000): ~8,692 real middle-band
  functions (coldrun-naming.md); the phase10 "12,699" was a sweep artifact — 4,001
  force-created noise functions purged 8.23. Zone-active code only.
- CONTENT: all 2,202 .pkg parsed; 386/386 spawn-set class entries decoded —
  spawn_sets_full.json holds 386 sets / 8,892 points (merged 8.15, spawn_merge.py);
  class census top-60 (content/class_reference_census.json); 567 named tags
  (content/named_tags.json).

## Conventions (apply without re-deriving)
- Name hashes = TWO VOCABULARIES (do not conflate): TAG-NAME vocabulary (e.g.
  ":scenario_client" names, definition hashes) = FNV-1a-32 (basis 0x811C9DC5 =
  "unnamed" sentinel); SPAWN/BUBBLE/ACTIVITY-NAME vocabulary = FNV-1-32
  (multiply-then-xor, same basis — bubble-crossjoin.md 171/171 cache proof,
  activity campaign name-hash verification). No 64-bit variant is in use.
- Tag handles: 0x80800000 + (packageId << 13) + entryIndex.
- Wire ints are biased/quantized per the reader tables; never assume raw LE semantics
  without checking the codec byte.
- Recurring strides: 0x28 schema entry, 0x40 schema/index rows + key table, 0x60
  response record, 0x90 base descriptor, 0x30 handler object, 0xa8 message-registry
  record, 0x1100 schema capacity.
- Struct field order defies intuition (KeyTable = alternateKey FIRST). Check the
  owning source or verified spec before assuming.

## TRAP LIST — each of these was a real, gate-caught error
1. 0x7FF6.../0x7FF7... addresses in decompiles are RUNTIME pointers captured in live
   .data. Always normalize: image_va = runtime - capture_base + 0x140000000. Capture
   bases vary per boot (0x7FF6300A0000, 0x7FF6AF7F0000 observed). "Outside the image"
   findings are almost always normalization misses.
2. Bitstream primitives count BITS, not bytes (0x420 bits = 132 B).
3. Runtime-built tables read as zeros statically (DAT_14280E3E0, DAT_142808A70,
   crypto vtable DAT_1426BE2E8, schema tree). Never call them "empty" or "obfuscated" —
   file REQUEST: live-dump instead.
4. Package block records carry their own patchId; a block's bytes live in ANY patch
   file of the family (filename family_<decimal patch>.pkg).
5. Entry-table `reference` (class id, e.g. 0x80809162 spawn set) and `typeInfo` are
   DIFFERENT spaces. Class scans match on reference.
6. Descriptor qwords rendering as ASCII ("@USVWATAVAWH.") are function PROLOGUES
   (40 55 53 56... = push sequence) — code pointers, not strings.
7. Hooked functions (16 Sunrise anchors + 11 hook sites) have Detours JMPs overwriting
   their first 5-16 bytes; pattern-match failures there are BY DESIGN. Match from
   byte 16+ or use the trampoline table.
8. Evidence strings must be checked against strings_dump.txt addresses; decompiler
   output occasionally garbles long strings.
9. If the corpus lacks it, say "NOT IN CORPUS" — absence is a valid, valued finding.
   Never extrapolate wire formats from names alone.
10. PowerShell HEX-ARG TRAP (2026-08-15, activity campaign): comma-joined hex class
    args UNQUOTED (`class_scan.py 0x80809994,0x80808AAE`) are parsed by PowerShell
    as hex literals that WRAP to negative Int32 and stringify as decimal negatives —
    the scan then runs with "-2139055724,..." and silently returns 0 entries with
    EXIT=0. ALWAYS QUOTE comma-joined hex args: `"0x80809994,0x80808AAE"`.
11. CLIENT SETTINGS TRAP (2026-08-15, S0 acceptance saga — cost six diagnostic boots):
    the game-side client settings.json must be edited as a BYTE-LEVEL two-value change
    from a known-good backup: locate the exact byte ranges of `"enabled": false` and
    `config_guid`'s value inside the external_server block, replace in place, write
    back raw. NEVER reserialize (json.dump / Set-Content / reformat) — the DLL's strict
    settings parser aborts at init on formatting/BOM/line-ending changes: the boot dies
    PRE-LOG, PRE-NETWORK, with zero evidence anywhere (no file logs even with
    file_sink=true). Reserialized files also grew 45 KB → 72 KB. The known-good backup
    is settings.json.bak_s0accept (45,180 B, no BOM). Server-side settings docs keep
    their own rules: no-BOM, under the 64-KB cap (settings_runtime.cpp:22).
12. WINDOWS SHELL RULE (2026-08-15): anything longer than one line, or containing
    quotes inside quotes, goes in a FILE (RE_output/claims/*.py or *.cmd) and the
    file is run. Inline `python -X utf8 -c` = single-line, quote-free snippets only.
    PowerShell = the orchestration shell (Start-Process -Verb RunAs,
    Get-NetTCPConnection, Get-Process, Copy-Item). Do NOT layer `bash -c` under
    PowerShell for anything complex. Inline content was the ONLY mangling source
    all session; the file-form pattern has been ~20/20 clean.
17. EXTERNAL-MODE CONTRACT TRAP (2026-08-15): the standalone server must mirror the
    in-process DLL's FULL local-answer contract, including the "empty success"
    (200 + empty body) for every unmapped content route — a 404 where the game
    expects "empty success" changes the game's behavior downstream (the patchable-
    package registration falls back to the config-as-manifest and fails). Any
    future server route addition requires an in-process source diff FIRST: grep
    externalServer.enabled across the fork + port each gated site's in-process
    behavior before the game touches it.

## Corpus map (frozen; the only permitted sources)
- RE_output/export/phase3..phase10/ — decompiles, xrefs, tables (phase10 = cold runs)
- RE_output/export/strings_dump.txt, functions.csv, decompiled_archive.txt
- RE_output/claims/*.md — the completed maps. family4-decoders.md FINAL is the
  structural gold standard; family3-roster.md is the closest imitation example.
- RE_output/content/ — spawn sets, class entries, census, named tags, schema tree.
- Sunrise source RE_build/Sunrise-fork/Sunrise/src/ (the ACTIVE fork, 0.2.1+; the
  Sunrise-021 tree = the prior context only). The fork is the deliverable home: the
  standalone server (sunrise-server.exe), the external-server DLL hooks (incl. the
  package_validator_iv -87 fix), and the S1/S2 state machine.

## Claims discipline (non-negotiable)
- Schema: "## CLAIM / - addr / - claim / - evidence / - confidence" and
  "## REQUEST / - want:" for anything needing Ghidra or live reads.
- Every claim carries an address; evidence = quoted corpus text. No address, no claim.
- WRITE EARLY AND OFTEN — a full wave was once lost by writing only at the end.
- Finish with a FINAL section: map/table + open questions.
- You have NO Ghidra, NO bash, NO web. Corpus text only. REQUEST what you cannot reach.

## TRAP 18 (2026-08-15): settings.json REFORMATTING KILLS THE LAUNCH
json.dump() reformatting of the game's settings.json (semantically identical, different
whitespace) makes destiny2.exe fail at launch with Bungie's "problem reading game
content" error. The DLL's parser is format-sensitive (or the file identity matters).
RULE: settings.json edits must be byte-exact � copy from a known-good backup, or
in-place minimal edits. NEVER reformat via json.dump.

## DOCTRINE 2026-08-15 (the dump-at-failure rule, adopted from the user directive)
DUMP-PAIR DIFF: any future black-screen-class event = dump the process (full_dump.py,
MiniDumpWriteDump via the game's own dbghelp) + diff against the latest healthy dump
(diff_minidumps.py). The state IS the evidence: the delta names the bug or its reader.
Capture-first, name-the-code-second. The first pair: dump_healthy_inproc.dmp (5.7 GB,
the character select) vs dump_failing_external.dmp (3.7 GB, the black screen) — the
verdict = the same registration pipeline + the same validator, the healthy returns 1
(the pass), the failing returns -87. The mode-dependent divergence = the validator's
inputs (the expected @+0x168 vs the thunk). NOTE: the .data region = the image base +
0x1F00000 (the globals @ 0x141Fxxxxx -> the runtime base + 0x1Fxxxxx).


## TRAP 19 (2026-08-15): THE WINDBG IS PERMANENTLY DEAD
Attaching ANY debugger (WinDbgX included) to destiny2.exe = VMProtect's anti-debug
self-destruct: GetContextState fails with 0x8007001F, the breakpoint arms but the game
CRASHES ITSELF after login (the fault RIP = 0x7FF681E641F9, identical across two dumps).
The ReadProcessMemory path (never blocked) is the only live-read avenue; WPM works too
but see TRAP 21.

## TRAP 20 (2026-08-15): THE POISONED PHR
The game's Patch Hash Resource cache (dcv build\cache_phr_0000f7ea.dat) can be an
ABORTED WRITE (type byte 0x02 @0x25 + a zero tail) left by a failed registration -
installing it poisons the IN-PROCESS boot (black screen at registration). The FRESH
type-1 PHR (a complete write) is BENIGN. The aborted one stays archived as .bak, never
installed. The PHR's content is irrelevant to the EXTERNAL mode (proven: the fresh PHR
present + external = still -87 + no rewrite).

## TRAP 21 (2026-08-15): THE IV BUFFER IS POOL MEMORY UNTIL +29s - AND THE RESULT
REGISTER DEFAULTS TO 1
- The kind0 IV buffer (base+0x1F44CE0) = async-task POOL memory during early boot (its
  bytes transition through garbage twice). ANY external write before the game's own
  ~+29s write CRASHES the game ~9s later (WER: c0000005 @0x180092440, not the trap-19
  signature). The game's own write -> the validator's read = MICROSECONDS apart (the
  same function); no external write can interpose on that race - a 5ms poll catches
  both in one window. THE ONLY working fix = the in-process fork hook at the validator's
  entry (package_validator_iv, the -87 fix).
- DAT_14267aa50 (the result register) STARTS at 1 (optimistic default); a live "1"
  reading != a validator PASS unless the registration state (DAT_141f916fc) has
  advanced to 3. -87 (0xFFFFFFA9) is the only definite failure value.
- The module-snapshot (find_module_base) can throw error 299 (loader lock) during early
  startup - RETRY with backoff; never treat it as fatal.

## TRAP 22 (2026-08-15): THE SINGLE-INSTANCE GUARD
Multiple destiny2.exe launches while one instance runs = EVERY new process silently
waits pre-window (no UI, no log, ~idle CPU) - "the game won't open" with zero errors.
ALWAYS verify no destiny2.exe is running before a boot; kill all instances + launch
exactly once. (Cost one whole confusing hour: 5 stacked processes, one crash.)

## TRAP 23 (2026-08-15): DUMP-SCANS BEAT TARGETED CAPTURES; TASK NODES != VALIDATOR
RECORDS
- Scanning the full-memory dumps for a known 4-byte constant found the whole expected-
  side array (2,199 hits) in minutes; a purpose-built live watcher (task_watch_records.bin)
  captured 2,263 frames that turned out to be 32-byte SCHEDULER NODES - not the
  validator records (frame-format assumption failure). For "where does value X live",
  scan the dump first; build a capture harness second.
- The 632-byte registration-record array (with expected @+0x168 = 0x281141FD and kind
  byte @+0x16C = 0) is built AT/AFTER the validation - it does NOT exist in the live
  process pre-registration (zero scan hits before the -87). Persisted-state reads from
  the dumps != live-window targets.

## TRAP 24 (2026-08-15): THE SERVER REJECTS NON-UUID config_guid OVERRIDES
The fork's validate_served_guid() (server_main.cpp:265) refuses to start when the
configured configGuid override is not UUID-canonical (the d2legacy string =
"invalid_override"). Any GUID experiment must respect the server's canonical-id gate
AND the game-side gate (which is MODE-driven, not GUID-driven - the healthy dump
proves the in-process boot runs the registration too, it just passes it).
