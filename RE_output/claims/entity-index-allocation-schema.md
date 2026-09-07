# CLAIM — the client's type-20 (allocate_entity_indices) payload schema

Date: 2026-08-30 evening. Resolution chain fully static; no boot.

## Scope of authority (lesson 15)

Answers: "what shape does the client expect a host-pushed allocate_entity_indices
notification to have, per the client's own schema registry?" It does NOT say what
our fork must put in the fields semantically — that needs one paired capture or the
community doc's creation contract (§1.3-1.7).

## The resolution chain (every link marked)

| Link | Mark |
|---|---|
| Router FUN_1416E6ED0 case 20 → thunk 0x1416E6FE0 → FUN_1416F0840 | verified-by-reading (jump tables 0x1416E71E0/0x1416E7134 decoded; 20.212 R2 machinery) |
| FUN_1416F0840 → 0x1403CB3F0 (apply) → bitstream init 0x140351D90 off msg+0x88(size)/+0x8c(payload) | verified-by-reading |
| payload decode 0x1404D92A0 resolves its schema through FUN_1404C72E0 — the SAME resolver the type-12 key used | verified-by-reading |
| the key global: `[rip+0x1ac9b89]` → 0x141FA2E80 (.data, 0x1300 before the type-12 key global 0x141FA4180); pointer → 0x1427D1440 (beyond static raw .data, read from dump_healthy_inproc at base 0x7ff641bf0000 + rva 0x27D1440); first dword = **0x80809445** | verified-by-execution (read out of the dump) |
| 0x80809445 self-verifies (node+0x08 carries the key) and expands below | verified-by-execution (schema_walk --tree) |
| semantic meaning of each array | **inference**, labeled inline |

## The tree

```
0x80809445  struct, 2 fields
  [0] 0x8080944C  struct, 3 fields, 3 presence bits          <- BLOCK A
      [0] 0x8080944B: { u32-count:9bits,
                        ARRAY of 256 x u32 }                 <- 256 x 32-bit ids
      [1] 0x80809B99: ARRAY of 8 x u32                       <- 8 x 32-bit
      [2] 0x8080944A: { u32-count:9bits,
                        ARRAY of 256 x u8 }                  <- 256 x 8-bit flags
  [1] 0x80809449  struct, 2 fields, presence_bits=320        <- BLOCK B
      [0] u32-count:7bits                                    <- entry count (max 127)
      [1] 0x80809446: ARRAY of 64 x (5-bit presence each)    <- 64 ENTRIES
            each elem 0x8080944D:
              [0] u32 (present)                              <- an id/index word
              [1] 0x80809452 (present):
                    [0] 0x80809451: { count:7bits, ARRAY of 96 x u32 }
                    [1] 0x80809748: ARRAY of 3 x u32
                    [2] 0x80809450: { count:7bits, ARRAY of 96 x u8 }
```

## The reading (INFERRED — plausible, unproven)

- 64 outer entries = one per possible session participant (the fork's own member
  model tops out well below this). Each carries a 32-bit id + two 96-entry arrays
  (u32 ids + u8 flags) + a 3-entry u32 array: per-participant ALLOCATED ENTITY
  INDICES. 96 ≈ the entity count one participant can hold.
- BLOCK A (256×u32 + 256×u8 + 8×u32) = the session-wide index pool state: which
  indices exist, their types/flags.
- The 9-bit counts size the arrays' used prefix; the 7-bit counts cap at 127
  entries/96-wide blocks.
- If the reading holds, the fork cannot satisfy creation by lease masks alone:
  the host must PUSH this structure (type 20) naming, per participant, the
  allocated indices. The fork emits nothing of the kind today (20.213 static:
  no type-20/21 encoder exists server-side).

## What to do next with it

1. Decode the client's case-20 APPLY target — after 0x1404D92A0 the decoded object
   lands at msg+0x28; find who reads [msg+0x28] fields next (the consumer maps the
   arrays into the session's entity storage: the 8192-slot world object's
   lease/type tables from sobject-carrier.md claim 2.2).
2. Reconcile with the community doc's creation contract (§1.3-1.7): the archetype
   hash the creation needs may be exactly the 32-bit ids in these arrays.
3. Implement fork-side emission at join: one type-20 push per member (or per
   session), BLOCK B filled for the joining member, BLOCK A the pool snapshot.
   First capture goal: does the 58x creation failure go quiet, and does
   ent_recv/ent_create fire at all?

---

## THE FOCUSED DECODE PASS (2026-08-30 late, same session) — the wire is KEYED

### CLAIM A — the type-20 body is a schema-driven field stream, keys from globals (VERIFIED,
###          CORRECTS the earlier "keys on the wire" reading made mid-pass)
- addr: 0x1404D92A0 → 0x1404D7380 → 0x1404D7470 → 0x1404C74B0 (thunk) → 0x1404C1930
- claim: the body IS a fixed-schema bit field, not a self-describing stream. The
  schema keys come from PER-MESSAGE-TYPE GLOBALS baked in the binary (0x141BBA328,
  0x141B66030, 0x141FA2E80 — one per decode site), NOT from the wire: 0x1404c74b0 is
  a 7-instruction thunk forwarding (key-global dword, stream, two out-ptrs, flag=1)
  to 0x1404c1930, which resolves the node, sets up a schema context (0x1403f3570),
  and calls 0x1404bee90(node_struct, ctx) — the field decode driver. The caller's
  success test is whether the out param changed from its 0x811c9dc5 seed, not the
  (always-true) return value. Continue bits gate optional sub-blocks (0x140350ef0
  reads); 0x1403513b0(stream, 0x20) aligns/skips 32 bits between sections.
- evidence: full read of 0x1404c74b0 (7 instructions, `mov al,1; ret`) and
  0x1404c1930 (380 B, pdata-bounded): key→bucket arithmetic on the ARGUMENT, node
  resolution, ctx {stream, out1, out2, 0, 1} → 0x1403f3570 → 0x1404bee90; no wire
  key read anywhere in either.
- confidence: HIGH (function bounded by pdata, fully read)
- NOTE: the mid-pass "self-describing keyed stream" statement was wrong and is
  superseded here — the key globals confused the direction. The wire is fields only.

### CLAIM B — the post-decode consumer builds a 4,096-entry index table (VERIFIED)
- addr: 0x1404D92A0 tail (0x1404d93e0-0x1404d943b)
- claim: after the item loops: validation 0x1404d6530, then a 4,096-entry × 32-byte
  table is zeroed (0x1409fd040 loop, edi=0x1000, stride 0x20) and three passes build
  it (0x1404d8ab0 → 0x1404d6430 → 0x1404da190). 4,096 = the entity-index space the
  lease experiment centered on. THIS is the consumer that turns the decoded
  allocation into the client's index table.
- evidence: the zero-loop constants and the three sequential calls, all inside the
  type-20 decoder, gated on the item loops' success flags.
- confidence: HIGH (structure), MEDIUM (per-entry 32-byte semantics)

### CLAIM D — the descriptor semantics and the full structural model (VERIFIED structure,
###          one bit-order detail open)
- addr: raw node dumps for the whole 0x80809445 tree →
  RE_output/claims/type20-node-raw-dump.txt (generated, reproducible)
- claim: the array descriptors carry DECODED-SIDE container geometry: +0x0c/+0x10 =
  container byte size (96×4=0x180 for u32 arrays, 96×1=0x60 for u8 arrays, 0x100 for
  256×u8), +0x18 = element count, +0x20/+0x24 = element byte stride (4/4/1). The wire
  side is a sequential MSB-first bitstream: presence bits per optional field/element
  (hierarchical bitmap sizes: top=325 = 320 BLOCK B + 5), count fields (7-bit/9-bit)
  preceding variable blocks, payloads at width bits each (type-5 reader: cursor read
  of `width` bits, minus a descriptor base, into the decoded container). Type→reader
  table at 0x141F94AD0+0x178 (runtime .data, dump-read): types 3/7 share 0x1409F9B00,
  5/9 share 0x1409FA080, 6/10 share 0x1409F4290, 0/1 = identity 0x140B94700.
- the bit-order question is RESOLVED (2026-08-30, final walker pass): presence bits
  are INTERLEAVED PER FIELD on the wire — read sequentially at the cursor
  (0x140350ef0: MSB-first 64-bit-window shift cursor, counters at +0x24/+0x30) at
  each field's turn in schema order, then the payload. The +0x28 "pidx" dwords are
  positions in the DECODED-side presence image (the client mirrors presence
  bit-packed into the decoded struct at those offsets) — which is why the type-12
  decoded offsets (0/992/996-999) "closed exactly" against its 1000-bit decoded
  size. ENCODER CONSEQUENCE: walk the tree in field order; per field write
  [presence bit if flagged][payload if present]; arrays = per-element presence then
  payload; the count fields are ordinary scalars. The one residual: whether an
  array's wire loop runs to the fixed node count or to the decoded count value —
  settle by emitting the full fixed count with presence bits marking used entries
  (safe under both readings).
- confidence: HIGH — the cursor function is fully read (81 bytes) and the walker's
  presence read uses it sequentially.

## Tools used (reusable)

pe_reader.py (rip target + static read) · schema_walk.py --tree (registry walk,
dumpy base 0x7ff641bf0000) · the global chain: static .data pointer at
0x141FA2E80 → dump read at rva 0x27D1440. NOTE: pe_reader RUNTIME_BASE
(0x7FF6AF7F0000) does NOT apply to dump_healthy_inproc.dmp (base 0x7ff641bf0000);
the two dumps are different sessions — do not mix pointers across them.

---

### CLAIM E — the creation failure mechanism, named end to end (VERIFIED, 2026-08-30 night)
- addr: 0x1416EE180 (creation attempt + failure log site, caller-RVA-confirmed
  rva=0x16EE3F7 = return after the 0x14035D860 enqueue) → allocator 0x14170F190 →
  free-slot allocator 0x141711D10
- claim: "failed to create 'player_broadcast' entity" fires when the index allocator
  0x14170F190 returns -1. Its gate cascade: (1) 0x141711D10 — first-set-bit allocation
  from the session object's FREE-SLOT BITMASK at +0xC118 (8192 bits), with 6-byte
  per-slot records at +0x118 (the sobject-carrier +0x114 table family: state byte set
  0→2 on allocate); -1 = mask has no free bits. (2) 0x14170B0F0 gate. (3) 0x140B47D20
  gate. (4) counter at ctx+0xC118-region ≥ 100 → rate-limit exit. (5) tick-delta ≤
  5000 → cooldown exit. The mask is populated downstream of the type-20 decode
  (validation 0x1404d6530 → three-pass table build 0x1404d8ab0/0x1404d6430/0x1404da190).
- p2(140) live: emitter fired (members=1 bytes=1823, both activity identities), client
  accepted type=20 on both, routing lookup 2688+ calls with ZERO null returns
  (rcx = the session id, exactly the envelope identity) — and 48 failures with
  ent_recv/ent_create still 0. CONCLUSION: routing is sound; the allocation is not
  reaching the free mask. Next read: 0x1404d6530 (validation gate) + the three table
  passes — what body content makes the mask populate.
- confidence: HIGH (allocator + creation site fully read; live-corroborated)

### CLAIM F — p2(141): bitmap populated, mask still empty — the gap is the population
### path, not the emission (VERIFIED, 2026-08-30 night)
- v2 emitted BLOCK A's 256×u32 as the lease free-bitmap (bits 0..4087). Live result:
  same failure signature (57 failures, same caller RVA 0x16EE3F7, routing 0 nulls,
  ent hooks 0). The body is accepted and decoded; the free mask at session+0xC118
  still reads empty at allocation time.
- CONCLUSION: BLOCK A/B do not map to the mask directly by my v1/v2 field semantics.
  The mask population runs through the decoder tail: validation 0x1404d6530 → three
  passes 0x1404d8ab0 / 0x1404d6430 / 0x1404da190 building the 4096×0x20 table — and
  one of: (a) validation 0x1404d6530 rejects our body (bits never reach the passes),
  (b) the passes consume the decoded fields differently than assumed (e.g., BLOCK A
  is not the free bitmap but an id list; the 256×u8 flags gate mask population), or
  (c) the mask is populated only for fields we zero-fill.
- NEXT READ (precise): 0x1404d6530 first — it gates everything. Then the passes, in
  call order. OPEN ITEM D (schema_walk rel-offset base) may matter here — the decoded
  struct's internal layout feeds these passes.

---

## THE MASK LIFECYCLE PASS (2026-08-30 night, session 2 — static, no boot)

### CLAIM G — the free-slot mask at +0xC118 has exactly three writers in .text (VERIFIED)
- addr: init 0x14171DB20 · allocator 0x141711D10 · release 0x14170FC90
- claim: the 8192-bit free-slot bitmask (session obj +0xC118, 0x400 dwords) is written only by:
  (1) INIT 0x14171DB20 — gate 0x140b48550(0) = "current activity == 0"
      (0x140d444b0 = get-activity, sete): if TRUE → `memset(obj+0xC118, 0xFF, 0x400)`
      (0x14187e862) = ALL 8192 SLOTS FREE, then zero the 6-byte per-slot records
      (0x1000 iterations × 12 bytes at +0x11d). If FALSE (in an activity) → branch B
      (see claim H). The 6-byte record table (8192×6 = 0xC000 B) ends exactly at +0xC118.
  (2) ALLOCATOR 0x141711D10 — 0x14035ee10(mask, 0x2000) first-set-bit; -1 = fail
      (THE failure the creation logs); found bit CLEARED (and not edx); record state
      0→2 (else al+1 with 2 on wrap); builds id = [[obj+8]+8]<<4 | (i8 record+0x116)
      then <<16 | bitIndex.
  (3) RELEASE 0x14170FC90 — recursive child walk of the 0x70-stride static archetype
      table at rip+0x19a0762 (child idx at [x+0x48], -1 = leaf); sets the bit back
      ONLY if byte [x+1] == 0xff; touches ring head/tail at obj+0x...+2/+3 (0xf mask)
      and dirty flag [obj+0xcea0].
  - evidence: full .text sweep of the disp32 0xC118 (16 raw occurrences, all
    enumerated and attributed); full reads of all three functions (pdata-bounded).
  - confidence: HIGH. THE MASK IS NEVER WRITTEN BY THE TYPE-20 DECODE ITSELF —
    claim F's "mask populated downstream of the decode" is WRONG as stated: the
    decode builds the 4096×0x20 table; the mask is touched only by init/alloc/release.

### CLAIM H — type-20/21 are a REQUEST/DONATE PAIR the CLIENT also emits (VERIFIED structure)
- addr: send-20 0x1404F88C0 · send-21 0x1404F56F0 · common send 0x1404FB770
- claim: the client's entity-index pool is DISTRIBUTED with two messages through
  0x1404fb770(obj, payload, tag, size, flagptr):
  - TAG 0x14 (20): 4-BYTE payload = a count. Sent by 0x1404F88C0(obj, count).
    Sets sent-flag byte [obj+0x60299] = result and timestamp [obj+0x602a0].
  - TAG 0x15 (21): 1024-BYTE payload = a bitmap (0x400 B = 8192 bits). Sent by
    0x1404F56F0(obj, &bitmap) — 8×0x80 copy of the caller's bitmap.
  - both send via [[obj+0x6c18] vtable + 0x28] with the tag as the svc id; the
    non-fast path builds a 0x7d800 buffer and packs via 0x1404dbf90 first.
- INIT BRANCH B (activity != 0), full read of 0x14171DB20 alt path: r14 =
  [[rbp+8]+0x10] = the SESSION-WIDE pool object (its own 8192-bit mask at
  [r14+0x5FE98], sent-flag +0x60299, timestamp +0x602a0). If 0x1404f7a10(r14)
  says "mask has bits OR already sent" → nothing. Else, with local popcount esi
  vs [rbp+0xC51C] (max) and [rbp+0xC518] (min), ebp = (min+max)/2:
    - esi > max: DONATE (esi-ebp) bits — chosen deterministically by repeated
      0x14035ec60(mask, 0x2000) into a temp bitmap → send TAG 0x15 with temp →
      clear the same bits from the LOCAL mask (SSE loop).
    - esi < min: REQUEST (ebp-esi) via send TAG 0x14 with count → set sent-flag.
- meaning: THE CLIENT ASKS THE HOST FOR ENTITY INDICES WHEN ITS MASK IS EMPTY.
  An empty mask + unanswered request = exactly the p2(140)/p2(141) signature.
- confidence: HIGH on structure/offsets (all functions fully read); MEDIUM on the
  channel identity — [obj+0x6c18] vtable+0x28 not yet tied to a named wire channel;
  the numeric coincidence tag 0x14/0x15 == activity type 20/21 is UNRESOLVED.

### CLAIM I — the type-20 arrival initializes the entity manager (VERIFIED chain)
- addr: 0x1416F6746 (fragment, primary 0x1416F6640) → 0x141709800 → 0x14171D780 → 0x14171DB20
- claim: 0x141709800(parent): gate byte [[0x14059dd80()]+0x25]; tears down/creates
  the entity-manager family at parent+0x30 and initializes parent+0x270 via
  0x14171D780 (init mask → 0x14170ACB0 → 0x14171BB50 tail). The caller region
  0x1416F6640 is the type-20 handler family (FUN_1416F0840's neighborhood).
- confidence: HIGH on the chain; the exact trigger position of 0x1416F6746 inside
  the handler flow is not yet mapped (fragment, primary only 41 B, callers unread).

## WHAT THIS MEANS FOR THE ENCODER (v3 — NOT YET IMPLEMENTED)
v1/v2 pushed a schema-body type-20 at join. The mask lifecycle says the missing
piece is likely the REQUEST/RESPONSE half: the client's request (tag 0x14, 4-byte
count) must be ANSWERED with a tag-0x15 bitmap donation the client ORs into
[r14+0x5FE98] (and thence rebalanced into the local mask at init/alloc time).
OPEN before v3 is shippable:
  (a) tie [obj+0x6c18] vtable+0x28 to a named channel — does the fork's bap
      listener SEE the client's tag-0x14 requests? CHECK p2(141) server-side logs
      for inbound 4-byte count frames BEFORE any new boot.
  (b) who ORs a received tag-0x15 bitmap into the masks (the RECEIVE side of 21) —
      find the receiver and what it writes ([r14+0x5FE98] vs local +0xC118).
  (c) reconcile with the inbound type-20 schema decode (0x1404d92a0): is the big
      schema body the HOST's type-20, i.e. the fork's emission was the right
      message but the wrong CONTENT (BLOCK A must be the DONATED bitmap — the
      256×u32 = 8192 bits, matching [r14+0x5FE98]'s size), or a different message?
      NOTE: v2 filled BLOCK A bits 0..4087 — if BLOCK A is "indices the HOST
      still holds free", the polarity/direction may be inverted (donate means
      transfer OWNERSHIP, not "these are free for you").
  (d) the 0x14035ec60 bit-choice sequence (inside 0x14035E920..E954's fragment
      family) — the deterministic bit-pick order donors use.

### CLAIM J — the v1/v2 premise is DEAD: the type-20 schema decode CANNOT fill the mask
###          (VERIFIED, 2026-08-30 night, session 2)
- addr: full decode tail read: item loop 0x1404d7380/0x1404d7470 · validation
  0x1404d6530+0x1404d6580 · passes 0x1404d8ab0/0x1404d6430/0x1404da190
- claim: the inbound type-20 decode (schema 0x80809445) writes NO mask anywhere:
  - each item's decoded out-value (FNV-seeded 0x811c9dc5) is matched against a
    16-byte-entry registry at ctx+0 (count at ctx+0, entries ctx+4 stride 0x10,
    flag byte entry+15); unknown id = item fails; match sets the entry flag.
  - validation (0x1404d6530, also called from 0x1403CD61F) walks the presence
    bitmap of ctx+0x808's object; EMPTY mask = passes trivially; any present
    entry failing the array/[node+0x68] width check (<=0x3f) returns FALSE —
    and the decoder then returns SUCCESS (bl still 1) with all three passes
    SKIPPED (0x1404d93ec je 0x1404d9445). SILENT SUCCESS = the exact p2(140/141)
    signature candidate.
  - the three passes build a 4096x0x20 STACK table, hash-map-annotate SCHEMA
    REGISTRY NODES (node+0x6e flags, node+0xc), and the table is DISCARDED.
  - sub-item decode 0x1404d7470 mirrors the same registry-flag mechanism.
- corollary: no body CONTENT for type-20 can populate the free mask. v1/v2 were
  aimed at a mechanism that terminates without touching it. STOP tuning BLOCK A/B.
- confidence: HIGH (every function in the tail fully read, pdata-bounded).

### CLAIM K — the live path: activity type 21 carries a 1024-byte bitmap grant
###          (VERIFIED structure, 2026-08-30 night, session 2)
- router (FULL map decoded, byte-exact from tables 0x1416E71E0/0x1416E7134):
  wire type = byte index + 1 (the claim-doc "case 20" = byte index 19). Handlers:
  1->0x1417090C0, 2->0x1417085C0, 3->0x141708EC0(no, 4->0x141708730), 5->0x1416F3620,
  6->0x1416F35A0, 11->0x1416F4250, 12->0x1416F4450, 13->0x1416F43E0, 14->0x1416F3BF0,
  16->0x1416F4750, 17->0x1416F0F60, 18->0x1416F1320, 19->0x1416F17A0, 20->0x1416F0840
  (slot_grant_request, CONFIRMED by the mac client log naming it),
  21->0x1416F04C0, 22->0x1416FC600, 42->0x1416F3A70, 43->0x1416F39E0, 57->0x1416F26D0,
  58->0x1416F28B0, 59->0x1416F22E0, 63->0x1416F1C70, 64->0x1416F2580, 65->0x1416F1B20,
  70->0x1416F31E0, 71->0x1416F3CE0, 72->0x1416F5AF0, 73->0x1416F47F0, 74->0x1416F3710,
  76->0x1416F4950, 77->0x1416F2BF0, 78->0x1416F5180, 79->0x1416F4E20, 80->0x1416F4B10,
  81->0x1416F2580, 82->0x1416F4CC0, 83->0x1416F4FD0, 91->0x1416F5C50, 92->0x1416F5EB0,
  93->0x1416F5D10.
- wire-21 chain: 0x1416F04C0 -> 0x1416E8DC0 -> 0x14170CFB0 -> the entity manager:
  0x14170CFB0 zeroes two 0x400-B buffers, then 0x14035ecf0([msg+4], 0x2000) tests
  the 8192-bit field AT DECODED OBJECT +4 — the payload carries a bitmap at +4.
- the donation APPLY: 0x1404F5D60(pool, &bitmap) ORs the 0x400-B bitmap into the
  pool mask [pool+0x5FE98], sets word [pool+0x60299] |= 0x100 and byte
  [pool+0x60298]=1, wakes a waiter via 0x1403BCEE0. Schema for this message =
  0x80809857 (key global 0x141FAA250, dump-read) = ONE field, type 24 (raw blob):
  the bitmap rides as raw bytes.
- the pool REQUEST (client->host): 0x1404F88C0 sends tag-0x14 with a 4-byte count
  when branch-B init finds pool empty and not-yet-sent; sets sent-flag +0x60299.
  The DONATION (host->client): 0x1404F56F0 sends tag-0x15 with the 1024-B bitmap.
  Both through 0x1404FB770 -> [[obj+0x6c18] vtable+0x28].
- local-mask restore on init: 0x14170ACB0 (called right after init in the
  0x14171D780 chain) rebuilds bits from the LIVE-ARCHETYPE 0x70-stride table
  (rip+0x19a56f5; entries whose +1 state byte +3 passes and (+0x68)>>3 bit set)
  into scratch [mgr+0xCAA0], then merges into [mgr+0xC118] (SSE loop).
- p2(141) live logs corroborate: fork's type-20 accepted ("msg=slot_grant_request",
  accepted=1, mac client log t=300935/t=334305), failures begin AFTER decode
  (t=305951+), and NO inbound pool request ever reached the fork on BAP
  (server log has zero candidate frames).

## V3 IMPLEMENTATION SHAPE (next lane phase — NOT yet started)
Emit activity type 21 (schema 0x80809857, single type-24 raw field) per member at
join: payload = 4-byte prefix + 1024-byte bitmap with the member's grant range set
(bits 0..4087 under the 4088/8 lease), riding the fork's existing activity push.
OPEN before code:
  1. exact decoded-object layout around the bitmap ([msg+4] implies a 4-byte
     field BEFORE the blob — likely the type-24 field is preceded by a count or
     the decoded struct has a header; confirm against 0x14170CFB0's full body);
  2. wire byte order of the type-24 blob vs the client's dword-LSB bit tests
     (0x1404DBF90 encoder treatment of type-24: memcpy vs bit-packed);
  3. whether the fork's svc-9 activity push framing reaches 0x1416F04C0
     (type-20 did reach its router, so type-21 should — verify routing identity
     in the first boot's client log, handle_message type=21);
  4. KEEP the type-20 slot_grant_request push for now (harmless, annotates
     registry nodes); gate type-21 behind its own settings switch.

### CLAIM L — the walker's type dispatch and the type-24 wire shape (VERIFIED, session 2)
- addr: walker 0x1404BEE90 (dispatch at 0x1404BEFF6); dispatch table 0x141F94AD0
  (base+type*8, dump-read); type-24 reader 0x1409FB2B0
- claim:
  1. The field-decode driver dispatches per field as
     `reader[record+0x30](rcx=decoded_write_addr, edx=bit_off=[r12+0x28]+base(+1 if
     presence), r8=&record+0x38, r9=stream)` — through TABLE 0x141F94AD0+type*8.
     Presence flag (record+0x31) gates a wire-cursor bit read + presence-image
     seek (0x1403FCF70) BEFORE the dispatch; presence=0 fields skip both.
  2. dispatch[24] = 0x1409FB2B0 = read a 6-bit TAG (0x1403513B0(stream,6)) and
     RE-DISPATCH through the SAME table at dispatch[tag] with unchanged args.
     The +0x178 offset table (0x141F94C48) used by claim-D's reader census is
     the SAME table viewed at its reader-table offset — there is ONE 64-entry
     polymorphic table; type 24 is "6-bit tag prefix, then the tagged body".
  3. dispatch[0] = dispatch[1] = 0x140B94700 = literally `ret` — tags 0/1 are
     no-ops. The bitmap does NOT ride tag 0/1.
  4. Schema node 0x80809857 raw (dump): count=1, key, +0x0c=4, +0x10=0x10,
     total_bits(+0x14)=0; field record: pidx=0, presence=0, type=24, sub=-1,
     width=0. The 8192-bit size appears NOWHERE in the node — the blob length
     must be carried by the TAG BODY (e.g. a length-prefixed blob reader) or the
     tag value itself. Candidate length-prefixed reader seen: 0x1409F5840
     (tag 22: presence bit + 32-bit length + 0x1404CDFA0 blob read).
- REMAINING before v3 code: the exact tag the client's ENCODER writes for the
  pool bitmap, and that tag's body framing. Plan: femu.py the client's encoder
  (0x1404C78C0: resolve+walk encode, reached from 0x1404DBF90) with a crafted
  msg object for key 0x80809857 — verification-by-execution, no boot.
- confidence: HIGH on 1-3 (fully read); MEDIUM on the tag identification.

### CLAIM M — femu verification of the encode side (PARTIAL, session 2)
- addr: packer 0x1404DBF90 → bitstream init 0x140351D90 → leading bit 0x14034C2A0
  → encode entry 0x1404C3390 → encode walker 0x1404BD820 (mirror of decode walker)
- tool: RE_output/scratch/femu_type24_encode.py — femu.py Rig driven multi-call,
  with TWO new reusable graft techniques:
  1. REGISTRY GRAFT: the schema registry is runtime heap, absent from the static
     image. Graft the dump's chain (global 0x142439C70 → reg obj → table → bucket
     entry → slot → node) into the emu at the dump's own VAs; write the global at
     EMU image base 0x140000000+0x2439C70 (NOT the dump base — first attempt failed
     on exactly this).
  2. STALE-POINTER REBASE: the unpacked file is a process dump; .data holds
     pointers from the ORIGINAL session (preferred base 0x7FF6AF7F0000). 64,095
     qwords rebased to 0x140000000+(v-orig) so indirect calls stay in-image.
  Auto-graft loop: on fault, map the faulting 4K page from the dump, retry.
- results (key 0x80809857, node grafted and self-verified):
  - stream init + leading-bit calls: clean (stream = {buf, end, cap, cursor};
    cursor advanced 0→1 by the leading bit ✓).
  - variant A (msg obj = raw 1024-byte bitmap at +0): walker RETURNS, rax=0x3FFE,
    but the stream cursor stays 1 — THE ENCODER WROTE NOTHING. The type-24 field
    is SKIPPED by the encode walker for a width-0 record.
  - variants B/C (len-prefixed objects): read-unmapped crashes in the walker's
    object reads (wrong object shape, as expected for a guess).
- interpretation (MEDIUM confidence): the donation bitmap is probably NOT
  schema-walker-encoded. The real sender (0x1404F56F0) passes the raw 1024-byte
  buffer + size 0x400 to 0x1404FB770, whose FAST path (test byte[arg5],1) sends
  DIRECTLY via [[obj+0x6c18] vtable+0x28] without the schema pack — the schema
  pack (0x1404DBF90) is the SLOW path. So the wire body for tag 0x15 is likely
  the RAW 8192-bit bitmap, and the 0x80809857 schema exists for the RECEIVE side
  only (its decode produces the same 0x400-byte image, 0x1404F5D60 ORs it).
  REMAINING to confirm: which arg of 0x1404FB770 is the fast/slow selector, and
  the exact framing the fast path puts on the wire (header before the bitmap).
  Next read: 0x1404FB770's stack-arg plumbing (arg5/6/7) + the connection
  vtable+0x28 send; and the encode walker's type-24 branch (why width-0 skips).

### CLAIM N — p2(142): the type-21 grant is accepted but does not reach the mask (LIVE)
- runs: solo raw-shape x2 (first with a derived 8184-bit mask [BUG: requestedCount,
  not the lease], then the corrected lease mask byte-identical to the type-0 body),
  then the flat flip staged.
- results (both raw runs, mac client log): ingress ACCEPTS the body —
  "handle_message ... type=21 ... accepted=1" ~5-6s BEFORE the failure burst —
  then 47-51 "failed to create 'player_broadcast'" in one ~100s bucket, same
  caller RVA 0x16EE3F7, then silence (the flaky-gate pattern, unchanged since
  p2(138) which predates ANY type-20/21 emission). ent_recv/ent_create hooks
  stay 0 — they are the RETIRED cluster (20.210), uninformative by design.
- reading: outcome (b) of BOOT_BRIEF_p2-142 — the body decodes at ingress but
  the local free mask (+0xC118) is still empty at creation time. The gap is
  somewhere in: ingress decode shape -> case-21 handler (FUN_1416F04C0 ->
  0x1416E8DC0 -> 0x14170CFB0) -> pool/claim path -> the +0xC118 refill.
  Note the fork's own entity_slots.h calls type 21 "slot_return" (client->
  host release) — the DIRECTION of the client's case-21 consumer (host->client
  grant, claims K) vs the fork's release parser is an UNRESOLVED tension; both
  may be true on different channels (svc8 inbound vs the [obj+0x6c18] vtable).
- live probes still untried: flat framing (settings-only, staged), and the
  client-side probe on the allocator 0x141711D10 / the case-21 consumer
  0x14170CFB0 reading the +0xC118 popcount at call time. RETIRED 2026-09-06
  evening: specified against the wrong subject - idx_alloc is NOT in the
  peer-render path (see the final section of this document).
- confidence: HIGH on the live facts; the mechanism gap is UNRESOLVED.

### CLAIM O — ROOT CAUSE: the client's index request rides BAP SERVICE 21 and the fork
###          answers it EMPTY (VERIFIED live, p2-142 flat run + fork source)
- live (server log, both solo joins): "ev=transport stage=frame conn=1 type=1
  bytes=219" → "bap stage=crypt dir=open bytes=197" → "ev=bap svc=21 rsp=22
  result=ok" — the client sends a BAP SERVICE 21 request exactly once per join,
  and the fork replies an EMPTY svc22 body.
- fork source: bap_service_routing.cpp maps RequestService::purchasedOffers →
  "svc=21 rsp=22 result=ok" with BodyCodec::empty. The handbook's svc21 name
  (purchasedOffers) is WRONG for this frame — the timing (once per join, gated
  with the entity-manager init) and the whole static chain (claims E-M) say
  this is the entity-index pool request the client sends when its free mask is
  empty and not-yet-requested (0x1404F88C0: tag 0x14... the tag number rides the
  BAP SERVICE field; request=svc21 observed live).
- probe chain (p2-142 flat run, mac client log): idx21_handler calls=0 (the
  activity-router case-21 NEVER runs for our svc9 pushes — the router is
  registered via 0x14040F500(ecx=0xE,...) and its dispatch is gated on
  msg+1 bit0: `test byte [rbx+1],1; jne epilogue`), idx_alloc calls=51 (= the
  51 failures), idx21_consumer calls=0. The activity-type-20/21 pushes we
  built ride svc9 and are ACCEPTED at the apply layer (0x140E0F000) but never
  reach the entity-index handlers. THE FIX IS THE BAP-SVC21 HANDLER, not the
  activity push.
- the response the client needs: svc22 body = the grant bitmap that
  0x1404F5D60 ORs into the pool mask (+0x5FE98) — decoded through schema
  0x80809857 (one type-24 raw-blob field). The encoder already exists:
  entity_index_grant::encode/encode_flat.
- confidence: HIGH (live frames + fork source + full static chain).

### CLAIM P — p2(142) CLOSED: the raw svc22 grant WEASELS the login; rollback live
- the corrected pre-join svc22 grant (raw 1029 B, lease=synthesized 0..4087)
  WEASELED the client at login — the body kills the signon-phase apply. Rolled
  back per the brief: entity_index_grant=false (settings only), server
  relaunched 10:14, legacy empty svc22 reply restored, login expected clean.
- ROOT PROCESS FAILURE: the response framing was never decode-verified. The
  encode side alone cannot pick the framing — the svc22 body must survive the
  client's own decode (0x1404DC080, schema 0x80809857, the type-24 polymorphic
  reader: [6-bit tag][tag body], dispatch[0]/[1] are literal `ret`).
- PICKUP POINT (next session, no boot needed): femu-decode loop. Build a
  bitstream over candidate bodies (raw 1029 / flat 1024 / [tag T][body] for
  T in a small sweep) and call 0x1404DC080 offline (the femu registry graft +
  stale-pointer rebase from femu_type24_encode.py are reusable). The body that
  decodes clean AND yields the 0x400-byte image at the expected offset IS the
  wire format; only then flip entity_index_grant back on.
- open sub-question: the svc21 request body (197-B frame) is still unread —
  log its hex at the codec before assuming a count request.

### CLAIM Q — CORRECTION of claim O: svc21 is purchased offers; the pool protocol
###          rides the GAMEPLAY PLANE (UDP 30976) (live-evidence, 2026-08-31)
- the svc21 request body (logged live, 191 B) = consecutive 3-byte hash records
  (0x42C4AA, AB, AC, ... then E6-E8, FA-FB, 0x42C598-9A) — an owned-item/offer
  catalog, NOT an index request. The handbook's "purchased offers" name for
  svc21 stands. The fork's empty reply was fine.
- with the probes live across three boots: idx21_handler=0, idx21_consumer=0,
  idx_alloc == the failure count. The client's entity-index pool request NEVER
  touches the BAP svc21/22 pair or the svc9 activity router (msg+1 bit0 gates
  the router dispatch; both our push and any inbound activity-21 skip it).
- the remaining carrier: the [obj+0x6c18] connection vtable the pool senders
  use (0x1404FB770) = the GAMEPLAY PLANE (UDP 30976) — the same plane whose
  join the fork already serves ("ev=gameplay stage=join result=completed",
  session/machine ids 0xC85E-family) and whose capture 20.196 R3 already showed
  carrying the largest flow. The pool request/donate messages (claim H's
  4-byte count / 1024-byte bitmap, tags 0x14/0x15) are GAMEPLAY-PLANE messages
  the fork does not implement yet.
- NEXT LANE: the 30976 gameplay-plane protocol — enumerate the plane's message
  types server-side (the fork's own gameplay endpoint is the parser reference),
  find the index-request/donate message shapes, answer them. The wide-net rule
  applies: capture the whole plane's traffic classification, not one message.
- confidence: HIGH that svc21/activity-router are exonerated; MEDIUM-HIGH on
  the 30976 attribution (the [obj+0x6c18] vtable is not yet tied to the UDP
  socket by direct evidence — the tie is the next static read).

---

## CLAIM O IS PROBABLY WRONG - THE svc21 BODY IS NOT AN ENTITY-INDEX REQUEST
## (2026-09-06, STATIC, from ~130 archived server logs; NO boot)

CLAIM O reads: "the client's index request rides BAP SERVICE 21 and the fork
answers it EMPTY (VERIFIED live)". The delivery half is verified and stands. The
IDENTIFICATION half does not survive reading the body, which has been captured in
about 130 archives - including tonight's p2-196 - while the claim says the shape
"is still unread".

### THE BODY, DECODED

Byte-identical in every archive and on both machines, 191 bytes:

    12 3a  aac442 abc442 acc442 adc442 aec442 afc442 b0c442
           e6c442 e7c442 e8c442  fac442 fbc442  98c542 99c542 9ac542 ...

    0x12 -> protobuf field 2, wiretype 2 (length-delimited)
    0x3a -> 58 bytes
    contents: a PACKED REPEATED VARINT list, decoding to

      1090090 1090091 1090092 1090093 1090094 1090095 1090096
      1090150 1090151 1090152   1090170 1090171   1090200 1090201 1090202 ...

    deltas: 1,1,1,1,1,1, 54, 1,1, 18, 1, 29, 1,1 - sorted runs with gaps, all
    inside a narrow band 1090090..1090202.

### WHY THAT REFUTES THE IDENTIFICATION

1. ENTITY INDICES ARE SMALL INTEGERS. 20.302 measured the live set as 0..6, and
   the descriptor tables index them as small integers. A sorted list of ~19 ids
   in the 1.09-million band is not an entity-index pool request under any
   reading of the entity namespace.
2. THE FORK'S OWN ROUTING ALREADY NAMES IT: bap_service_routing maps svc21 to
   RequestService::purchasedOffers. A packed list of large sorted catalogue-ish
   ids is exactly the shape a purchased-offers / catalogue query has, and an
   EMPTY svc22 reply is a correct answer to it for an account that owns nothing.
3. CLAIM O'S OWN SUPPORTING DETAIL IS CONTRADICTED. It says the request arrives
   "exactly once per join". In p2-196 it arrives THREE times; in
   20260906_155138 it arrives ELEVEN times. Whatever drives it is not the join.

### WHAT THIS SAVES

The next step CLAIM O implies - build an entity-index GRANT body and answer
svc21 with it - would be answering a question nobody asked, and the fork's source
already carries the scaffolding to do exactly that (BodyCodec::entityIndexGrantResponse,
settings entity_index_grant / entity_index_grant_flat). That work is now
DE-PRIORITISED pending a correct identification of the real index request.

### WHAT STANDS, AND WHAT THE REAL FRONT IS

STANDS (20.218 / p2-143, verified-by-log): the fork's activity messages DO route
to the client - "OUR MESSAGES ROUTE (flags=0x00) ... ASSIGNMENT+ORDERING ALL
CONFIRMED WORKING" - and the assignment -> recreate -> sync chain executes.

## RETRACTED 2026-09-06 EVENING (session after the night handoff): idx_alloc IS
## NOT THE PEER-RENDER BLOCKER - row 7b as written is a poisoned claim (STATIC,
## NO BOOT; every leg verified at the bytes this session)

The prior framing ("idx_alloc returns -1 and the empty local mask IS the
blocker; no index -> no entity -> ent_recv=0") does not survive verification:

1. IDENTITY CONFIRMED (my own disasm, 0x141711D10, pdata-exact): writes -1 to
   the out-param [rdx] up front; scans the +0xC118 mask (0x2000 bits, first-set
   via 0x14035EE10); on success CLEARS the found bit, bumps the 6-byte record
   state at [mgr + (i*3)*2 + 0x118], packs ((([mgr+8]+8)<<4 | rec+0x116)<<16 |
   bitIndex) into [rbx]; on failure logs via [mgr+8]+0x10 and returns -1.
   It IS a real free-slot allocator over the session object's 8192-slot pool.
   The function is what we said it was.
2. IT IS NOT IN THE PEER-RENDER PATH. callers.py: exactly ONE direct caller,
   0x14170F190 (ent_make); ent_make's only caller is 0x1416EE180 (CLAIM E's
   creation-attempt site) on the LOCAL creation loop
   (0x1413086E0 -> 0x1416EE180 -> 0x14170F190). 20.300 (p2-178) already
   measured the create is never ATTEMPTED for a foreign record. CLAIM G's full
   .text census: +0xC118 has exactly three writers (init 0x14171DB20 /
   allocator / release 0x14170FC90) - none in the receive cluster. The receive
   path (ent_recv -> ent_create 0x141718080) structurally cannot reach it.
3. THE ENT_CREATE ID VALIDATION IS SOFT (my disasm of 0x141718080): the
   +0xC520 lease-bit check (`bt; jae`) and the descriptor-id check
   (`cmp r9d,[desc+8]; jne`) both bail to 0x14171810d, which is NOT an abort -
   it falls through to the presence-mask test, and header bit0 set decodes the
   record FROM THE WIRE regardless; only the bit0-clear template path needs
   the descriptor (rsi=0 after a failed validation). This corrects
   ent-receive-contract.md section 5 step 1's "must have the bit" as a gate.
4. THE FAILING CALL IS BENIGN FOR SPAWN: the local player renders in every
   boot while idx_alloc fails 54x (p2-196). ent_make(kind=2) allocates a LOCAL
   activity-entity slot (the 'player_broadcast' family); a peer entity's index
   arrives ON THE WIRE (contract sections 4-5: the id is decoded from the
   bitstream via the "entity-index" key).

WHAT THIS RETRACTS: this document's prior "STANDS ... the real front" framing
and the row-7b "idx_alloc is THE BLOCKER" lines on FRONT_peer-render-chain.md
and STATE.md NEXT. The -1 is REAL and reproducible, but its subject is the
SESSION entity-slot pool (system A, CLAIMS E-H: the distributed tag-0x14/0x15
request/donate pool, in-activity init leaves the local mask empty) - NOT the
sobject entity system (system B: ent_recv/ent_create, world manager, small-int
ids 0..6, lease bitmap +0xC520, table A descriptors), which is the peer path.

THE ALLOCATOR-PROBE SPEC IS RETIRED (bootstrap empty-mask #8): it was
specified against the wrong subject. The +0xC118 pool question (why the
in-activity local mask is empty; who answers the client's tag-0x14 request;
which channel [[obj+0x6c18] vtable+0x28] is) remains a REAL, SEPARATE, OPEN
system - but no current verdict depends on it, and building its probe now
would spend a boot on a system the front does not touch.

THE CORRECTED FRONT (back to 20.221 R3 / 20.301, now sharper): the fork must
SEND a peer entity on the sobject system. The contract (20.302-20.304) is
spec-complete except ONE unknown: the outer wire type (dispatch into vtable
slot 10; 20.303's carrier decode chain 0x1416EACB0 -> 0x1417115D0 ->
0x1417117D0 operates the SAME entity storage). The id question is OPEN-SOFT:
the bit0-payload path decodes without a lease bit or descriptor, so a grant
may not be needed at all - ent_create's step-5 gate 0x1417114C0 and the apply
path decide. That question is answerable by FEMU with no boot (ent_create
against dump state, synthetic reader carrying a bit0-set kind-2 body).

---

## THE ROUTER DECODED LINE-BY-LINE (2026-09-07 early, static, NO boot) - the gate
## is INVERTED from CLAIM O's reading, and the fork's messages are pushes by construction

The dispatcher 0x1416E6ED0 (877 B, pdata-exact), read whole:
    rbx = rcx                          ; the MESSAGE OBJECT
    dil = 1
    call 0x1416FC5E0                   ; session getter (0x1416FC600 family)
    edx = [rax+0x560E0]                ; the session's record index (the extract chain's +0x560E0)
    call 0x1404C0440(&stack, edx)
    test byte [rbx+1], 1
    jne  0x1416E7118                   ; bit0 SET -> SKIP the switch entirely (the epilogue)
    eax = (s8)[rbx] - 1                ; THE TYPE BYTE at object+0; wire byte = name index + 1
    cmp eax, 0x5c ; ja epilogue        ; else DISPATCH by the jump tables 0x1416E71E0/0x1416E7134
So: bit0 CLEAR dispatches the case handlers; bit0 SET skips them. The prior
"dispatch is gated on msg+1 bit0" reading had the polarity backwards; the OBSERVED
fact stands unchanged (idx20/idx21 handlers = 0 with the fork's pushes).

THE STRUCTURAL FACT that supersedes the polarity question: 0x140E10C10 (the
registry gate -> the 15-table apply) has EXACTLY ONE caller - 0x1416F17A0 =
router case 19 (incident/push). The fork's pushes demonstrably reach 0x140E0F000
(the handle_message hook logs them, type=0/5, accepted=1) - so the fork's
notifications are dispatched AS CASE 19 (the push wrapper), and the 15-table's
registered set is {15,50} in our dumps: types 20/21 arrive inside a push and are
silently dropped THERE, before any type-specific case could matter.

THE REGISTRATION RECORD (dump_p2146): one qword == the router fnptr in .data at
rva 0x26BE9F8; record = {router, ->0x141BE00C8 (.rdata, reads empty), heap
cookie, 0x80000046}. The router is a REGISTERED BAP handler (registered by the
init callback 0x1416F7DA0 via 0x1416F6470 -> 0x14040F500(0xE, DAT_142037968);
that callback also toggles the enable bytes at 0x142037AE9/B0C, the
0x142037AF0 neighborhood).

THE ONE MISSING LINK (the next lane's first step, well-scoped): the client's
svc9 ingress -> the message OBJECT construction - where [+0] (the type byte) and
[+1] (the flags byte the switch tests) come from on the wire. The fork's DOWN
envelope is [disc=1][u64be asid][u32be type][u32be len][payload] with NO flags
byte (handle_message_observer.cpp, verified two ways), so [+1] is constructed
client-side. Path: 0x140412A30 registered the router into a handler table; the
table's walker is the BAP dispatch; its object builder names the +1 semantics.

THE V2 FORK MOVE, ONCE THE +1 SEMANTICS ARE KNOWN: either (a) shape the push so
the object dispatches to case 20/21 directly (if +1 is wire-derivable), or
(b) accept the push path and find what REGISTERS types 20/21 in the 15-table
(the table is runtime-built; our dumps hold {15,50}; the static registration
DAT_142037968 already names 17,18,19,20,21 - queue-event/state-refresh/incident/
ALLOCATE/FREE - so the handlers EXIST and the registration that surfaces them is
the target). Either way the downstream chain is already verified:
case 20 -> 0x1416F0840 shim -> 0x1403CB3F0 -> 0x1404D92A0 (the schema decode)
-> the entity-manager init (CLAIM I) -> the distributed pool -> the client's
tag-0x14 request -> the fork's type-21 answer -> the mask fills -> entities can
exist -> AND the view establishment (group id 40, never once sent by any client
in any archive; the fork's bind_view/echo has never executed) becomes possible -
the view being the client's replication registration ("a mismatch produces no
replicated entities at all").

## INGRESS ARC (same session, continued): the UPSTREAM side is fully mapped; the
## DOWN-side object construction is VMP-built

UPSTREAM (client -> server, svc8 RequestService::activityMessage): the fork
PARSES these (BodyCodec::activityMessageRequest -> activity_message::process)
and logs accept/skip with types. CENSUS ACROSS ALL ARCHIVES: type 47
(connection_quality_report) x1914, type 39 (send_client_heartbeat, 3447 B -
the client's per-tick state upload) x928, type 14 (peer reservation release)
x386, type 15 x29. **NO type 20, NO type 21, NO type 40 (view) has EVER
arrived upstream in any archive.** The client never asks for indices and never
establishes its view - consistent with the client never reaching replication-
participant state.

DOWN (server -> client, svc9 notifications): the wire envelope is
[disc=1][u64be asid][u32be type][u32be len][payload] - NO flags byte (verified
two ways in handle_message_observer.cpp). The router's message OBJECT (+0 type
byte, +1 flags byte) is therefore constructed by the client's BAP ingress -
which is in the VM-OBFUSCATED transport ring: the registration global
0x1426BE9F8 (= the dump's live router-ptr location, rva 0x26BE9F8) has ZERO
rip-relative readers and ZERO absolute-moffs readers in .text; the setter
0x140412A30 is a bare pointer store. The reader is VMP. Static object-
construction decode is CLOSED for this arc.

THE REGISTRATION TABLE (static 0x141C9FA48): records are RUNTIME-RELOCATED
{handler, secondary} pairs (first pair -> 0x1416E6010 (router neighborhood) /
0x140E0DC10) followed by name strings - the record format needs the relocated
arithmetic pass before further reads. The ids named in the earlier census
(1, 8, 13, 17, 18, 19, 20, 21, 39) say the type-20/21 handlers ARE registered
somewhere in the client's tables; the dispatch just never reaches them.

NEXT LANE (well-scoped, in order):
1. Log the svc8 upstream bodies fork-side (one snprintf of the first N bytes
   behind the existing accept/skip lines) + one boot: the heartbeat's bytes
   give the client's activity-message object->wire serialization, and any
   flags byte it carries, without touching the client.
2. femu the DOWN construction is closed (VMP); instead decide the +1 byte
   empirically from (1)'s symmetric encoding, or find the 15-table's
   REGISTRATION call (who inserts {15,50} - if the activity's own setup
   registers pushed types, completing that setup may register 20/21).
3. Whichever opens: the goal state is "the client's type-20 handler runs"
   (downstream: schema decode -> manager init branch B -> the tag-0x14
   request -> our type-21 answer -> mask fills), and then the view
   establishment + external-handler registration become reachable.
