# CONNECTION-LAYER JOIN DELIVERY — the p2-183 framing decode (static, no boot)

STATUS: live (2026-09-06 ~04:3x). Every address pdata-anchored. Answers STATE
NEXT 1-2: how to deliver the peer's join so the client's own machinery runs.

## THE DELIVERY BUG, COMPLETE (two defects, both now measured)

The p2-181 relay failed twice over:
1. **WRONG CHANNEL.** relay_join_body used wire::enqueue_message -> the
   RELIABLE QUEUE (established-packet fragments; peer_container.h "the registry
   holds ids 0..44"; registry-framed messages). The connection-layer switch
   0x1416E0940 is called from EXACTLY ONE site - 0x1416E2BDB inside the OOB
   container consumer 0x1416E2A90 (its only caller; reached via the interface
   vtable at 0x141C9AD28, slot 0). Reliable-queue messages never reach it.
   The client sends its OWN joins as OOB container datagrams (the fork receives
   them in consume_container as whole payloads) - the join lives on the OOB
   container channel in BOTH directions.
2. **WRONG DECLARED SIZE.** enqueue_message declared kJoinRequestSize=6144.
   The CLIENT'S OWN join container (p2-182 joincapture hex CA0600293E...)
   decodes bit-exact as: marker(1)=1, follows(1)=1, id(6)=0b001010=10,
   declaredSize(18)=0x600=**1536**. The relay's header declared a size 4x the
   client's own; the dispatcher's size-range check ([entry+0x14/+0x18]) would
   reject it even on the right channel.

## THE CLIENT'S RECEIVE SIDE (what a delivered join must pass)

- **The dispatcher gate** (0x1416E2A90, registry+switch): the message id must
  have a REGISTRY DESCRIPTOR (present byte, size in range) for the switch to
  be called at all; an absent descriptor skips BOTH decode and switch
  (bpl-gate at 0x1416E2B92/BB6). NOTE: the old "ids 10..29 UNREGISTERED"
  conclusion rested on absent NAME strings; a nameless descriptor still gates
  IN. Whether id 10 has a descriptor at runtime is the one open static
  question; the client's own header carrying declaredSize=1536 strongly
  suggests it does.
- **The switch table** (dword table 0x1416E0A44 is SLOT-indexed; byte map
  0x1416E0A88 id->slot): **id 0x0A -> slot 7 -> stub 0x1416E099C -> jmp
  0x1416E0460**. (First table read of this session desynced id/slot indexing;
  re-read slot-indexed - the DOOR finding's chain is VINDICATED. The finding's
  stub address 0x1416E099C is correct for id 10.)
- **The join handler 0x1416E0460** (161 lines, full disasm):
  1. `word [pkt+0] == 0x1416C1260()` - a 16-bit INSTANCE NONCE check;
     mismatch -> drop path at 0x1416E0664.
  2. `0x14177A0B0([ctx+0x28], pkt+0x10)`: walk 6 session slots; per slot
     compare the packet's 16-byte key (pkt+0x10) against the session's
     identity blob at **+0x57C or +0x94E** (helper 0x1417944C0 ->
     0x14179AF00 by-id lookup -> equality 0x141A83C00; bit-4 of [sess+4]
     selects which blob). No match -> no session -> refusal reason 4.
  3. Found session's `[+0x1AEF8]-6 <= 3` (state 6..9) -> **0x1417806C0**
     (the join processor: capacity vs [pkt+8], flags [pkt+4], candidate
     creation). p2-182 measured state 6 on TWO slots - this gate is OPEN.
- 0x1416E03B0 is id 0x0E's handler (dup-check flow), NOT the join (byte-map
  verified; correcting the first-read confusion this session).

## THE FIX (server-side, three changes to the relay)

Re-target relay_join_body from the reliable queue to the OOB datagram channel
- the same path answer_connect uses for connect-responses:
  open_container -> write_header{id=10, declaredSize=1536} -> the CAPTURED
  join body bits -> close_container -> send_transport(peer). Prefer
  forwarding the captured bytes VERBATIM (the sender's own nonce, session key
  and identity fields stay byte-correct) over re-encoding.

## OPEN (pre-named boot readouts, not blockers)

- The packet record's word[+0] nonce provenance (client-side OOB parse; not
  decoded). If verbatim forwarding still dies at the nonce check, the readout
  is: join_type0a enter fires, join_processor does not - then decode the OOB
  parse (the 0x141C9AD28-vtable object's receive loop).
- Whether the receiving client's registry holds id 10 (descriptor present).
  If the OOB join arrives and join_type0a stays silent -> fail mode (c):
  the registry gate is the blocker -> next decode = the registrar/bulk
  writer for the 10..29 family.
- Session-key provenance: the key is compared against the receiver's OWN
  session identity blobs (+0x57C/+0x94E). A join forwarded verbatim names the
  SENDER's session identity; if the receiver's live sessions carry different
  blobs, the lookup fails (reason 4). Readout: join_type0a fires + refusal;
  then the fork must map the join's session identity to the receiver's.

## THE BLOB DECODE (session-identity provenance, 2026-09-06) — COMPLETE, NO BOOT

- **The packet record = the DECODED JOINREQUEST STRUCT.** All five fields
  verified numerically against the fork's own decode of the same container:
  word[+0]=protocolVersion (0xA4F8), dword[+4]=minimumBuild (86657),
  dword[+8]=maximumBuild (86657), qword[+0x10]=sessionId (0xE42264D36E73148E
  LE bytes 8E14736ED36422E4 - byte-exact vs the fork's admit log for the same
  join), qword[+0x18]=joinId (0xEE1FED3B37C9B483 LE = 83B4C9373BED1FEE -
  byte-exact). The p2-184 key16 mystery resolved: it is sessionId+joinId.
- **The "nonce" = the protocol version check, and it PASSES.** (p2-183's
  nonce-mismatch diagnosis retracted; retraction stands.)
- **The session lookup = a ONE-QWORD compare.** 0x141A83C00 disassembled:
  `mov rcx,[rcx]; cmp rcx,[rdx]; sete al` - ONLY the first qword. The
  lookup therefore compares THE JOIN'S SESSIONID vs the session blob's first
  qword. The joinId half is irrelevant to the lookup.
- **The blob = the session APPLY (0x1416C5280) copying the applied
  parameters/state source's +0xC8..+0xD8 window into the session object.**
  (Earlier suspicion that this window = the per-entry characterSoid at
  kCharacterSoidOffset=200 was a COINCIDENCE of offsets - that constant is
  relative to a PLAYER ENTRY's regionA, not this source; retracted before
  writing.)
- **THE ROOT CAUSE (verified in the fork's own source): the fork's
  publish_join_parameters sends a parameter update with releasedMask and NO
  VALUES ("This host has no values, so it releases a slot the peer never
  filled"). The client's session identity blob is populated by the APPLY from
  parameter values the fork never sends. The join's sessionId therefore
  matches nothing in the receiver's blob -> the lookup fails -> the silent
  refusal.** In retail the host publishes real parameter values; the session
  identity lives among them.
- **THE FIX (fork-side, no client change): publish the session identity as a
  parameter VALUE.** The parameter registry is a named key/value store of 25
  parameters (world-controller-goal-data, activity-host, remote-join-data,
  remote-join-result, ...) - the fork's parameter_registry.cpp holds the
  names and the update grammar. Remaining decode (still no boot): which
  parameter's value lands at the applied source's +0xC8 window, and the
  parameter-update body grammar for carrying that value.

## THE COPIER WALK (the offset re-derivation pass, 2026-09-06) — DECODED TO A BOUNDED WALL

- The copier 0x1416E2350's walk arithmetic (fully decoded this pass):
  - Field address = the ACCUMULATED position + entry[+8] (unsigned byte) +
    entry[+9] (SIGNED byte); after each field, both src and dest advance by
    size (x count for LEN-typed fields; a count=0 LEN field is skipped
    entirely - no copy, no advance).
  - The member-array recursion (0x1416E2430): per element i, dest/src =
    the walker's position + i * stride, recursing with the SUB-TABLE
    ([rbx+0x18]) - the root's field 6 carries THE STRIDE 184, count 32,
    sub-table 0x141CA68E0 (verified: the root descriptor's entry has
    size=184 count=32 - ms-start-gate3's "size=8" for field 6 was a misread
    of the entry's bytes).
- The member descriptor (0x141CA68E0) as it sits in the static image:
  fields 1 (NetAddr, 96), 2 (machineId, 16), 3 (joinId, 8), 8 (idB, 8),
  9 (4), 10 (playerSlot, 4), 11/12 (flags, 1/1) - ALL with count=0. count=0
  means the copier would SKIP every field - so the static table is the
  TEMPLATE and the runtime registry carries the real counts, set at registry
  construction (the registrar 0x1416E2C50's writes) or per-session.
- The walk's own sequential sum of the member fields (with count=1 assumed)
  lands idB at entry+136-relative positions that STILL do not sum to the
  validated 184 stride without assumptions about the element base anchor
  (the fork's model absorbed a +56 shift: the client's member element base
  is state+8+idx*184 per the readers, while the fork's model entries sit at
  state+64+idx*184 - the reconciler shift is real but the recursion's base
  anchor at runtime is not yet pinned).
- p2-185's empirical anchor (the hash divergence) proves only that
  model-entry+144 is NOT the client's field-8 landing; the true offset is
  inside the walk above, and the decisive missing fact is the RUNTIME count
  and base anchoring of the member-array walk - obtainable two ways, both
  named: (1) decode the registrar 0x1416E2C50's writes (the runtime counts
  per field), or (2) one instrument boot dumping the decoded member rows
  (the apply's source) at the moment the state lands.

## PROVENANCE

bin destiny2_unpacked_full.exe: 0x1416E2A90 (dispatcher, full), 0x1416E0940
(switch head + stubs, linear 0x1416E0940..0x1416E0A40), 0x1416E0460 (join
gate handler, full), 0x1416E03B0 (id-0x0E handler, full), 0x14177A0B0 +
0x1417944C0/0x141794511 (lookup + compare, full), 0x1416C1260 (nonce getter,
partial); switch table + byte map read via pe_reader (slot-indexed, verified
twice after a desync); fork source: peer_transport.cpp (relay_join_body,
consume_container, answer_connect/establish), peer_container.h/.cpp,
established_packet.h, join_messages.h; capture: p2-182 server log
joincapture hex CA0600293E... (bit-decoded: marker/follows/id=10/size=0x600).

## 9. THE 20.319 STATIC ARC (2026-09-06, no boot) — the parameter path is BLOCKED
## on the OOB plane; the blob window is VINDICATED; two identity forms distinguished

### 1. The client's message registry + the OOB switch id map (complete, first read)

- The registrar (name-table refs 0x1416E164A..0x1416E1B1F, a .pdata GAP after
  0x1416E15FE) initializes per-message DESCRIPTOR BLOCKS of 0x40 bytes:
  +0x00 present byte, +0x08 name ptr, +0x10 min size, +0x14 max size,
  +0x18 size again, +0x20/+0x28/+0x30/+0x38 four handler slots.
- parameters-update block at reg+0x980: name=0x141C9E6B8, max=0xAC20=44064
  (= the fork's kParameterUpdateSize EXACTLY); parameters-request at +0x9C0
  max=0xAC18=44056 (= kParameterRequestSize). Join-request at +0x280, max
  0x1800=6144 (bits) — the client's own container declared 1536 (bytes?).
  Handler slots (parameters-update): +0x20=0x1416DEAC0 (thunk → 0x1417A28F0),
  +0x28=0x1416DA610 (obfuscated), +0x30=0x1416DCDA0 (thunk → 0x1417A24D0),
  +0x38=0x14021900 (shared with parameters-request).
- THE OOB RECEIVE SWITCH byte map (0x1416E0A88) re-read slot-indexed:
  handled ids = 0,1,2,3,4,5,6,7,9,0xA,0xB,0xD,0xE,0x10,0x1B,0x1C,0x1D,0x2A.
  **id 0x26 (38, parameters-update) maps to slot 16 = the default stub
  0x1416E0A40, which is a bare `ret` — SILENT DROP.** id 12 (join-complete)
  is likewise dropped on the OOB plane. CONSEQUENCE: parameters-update can
  never reach the client through the OOB plane; the client's reliable-plane
  receive is the VM-OBFUSCATED ring (0x1416DA0C0/0x1416D99F0/0x1405A5040 all
  share the 0x1472B4425/0x146260781 checksum-guard prologue). The
  parameters-apply road is statically CLOSED for the fork.
- Cross-check of fork ids vs the map: 10=join ✓ handled, 11=peer-connect ✓
  handled (0x1416E0E10), 13=join-abort ✓ (0x1416E02B0), 14=join-refuse ✓
  (0x1416E03B0), 16=leave-ack ✓ (0x1416E0830), 29=time-sync ✓ (0x1416E13A0),
  27/28/42 handled (0x1416DFD50/0x1416DFE90/0x1416E08A0), 5/6/7/9 → the
  transport module (0x1417D3010/0x1417D4590/0x1417D27B0/0x1417D1A90).

### 2. The blob window VINDICATED (the claim's +0xC8 decode confirmed)

- The apply 0x1416C5280's tail (which disasm_fn's output TRUNCATED at
  0x1416C5B89 — its "exact end" heuristic stopped early; the linear sweep
  shows the function runs to 0x1416C6071) contains, at 0x1416C5C73..:
    [rbx+0xC8] → [rdi+0x57C]   ← the blob's FIRST QWORD (what 0x141A83C00
    [rbx+0xCC] → [rdi+0x580]     compares) = the source's sessionId half
    [rbx+0xD0] → [rdi+0x584]   ← the joinId half
    [rbx+0xD4] → [rdi+0x588]
    [rbx+0xD8] → [rdi+0x58C]
  The claim's "+0xC8..+0xD8 window → +0x57C" was right; my first grep missed
  it because it ran over the truncated output. TOOL DEBT: disasm_fn printed
  "; pdata end of function reached" for a 3569-byte function after ~2300
  bytes — a confident TRUNCATION, exactly the 09-03 instrument class.
- The apply's source = the obfuscated getter 0x1405A5040's object; its
  +0xC8/+0xD0 = the machine's OWN soid. The apply stamps the session
  object's blob at creation from that singleton.

### 3. The gate's walk, fully decoded (walker 0x14177A0B0 + helper 0x1417944C0)

- The walker: 6 slots at [ctx+0x28 .. +0x50]; per slot, slot ptr non-null →
  read dword [slot+0x1C7C0] → call 0x1417944C0(slot, key, thatId).
- The helper: 0x14179AF00(id) → session record; **bit 4 of [rec+4] SET →
  compare the key against [rec+0x57C] FIRST (equality 0x141A83C00, one
  qword); on miss OR bit-4-clear → compare [rec+0x94E].** (Refines the
  claim's select description: both blobs are tried, 0x57C first.)
- 0x14179B270 confirms the record's identity block: +0x57C..+0x5F0 primary,
  +0x94E..+0x9C0 secondary (only when [rec+4]&0xC0==0xC0).

### 4. peer-connect (id 11) is the SAME GATE (new, boot-relevant)

0x1416E0E10: version check (0x1416C1260) → **the same ctx+0x28 walker
0x14177A0B0 with the body's key at [rbx+4]** → found: processor 0x1417839E0;
NOT found: reason-4 refusal + the movdqa log block. Every connection-layer
message naming the fork's session dies at the ONE wall.

### 5. THE IDENTITY-FORM DISTINCTION (from the p2-187 + 191812 logs)

- The client holds (at least) TWO identity forms: the REAL ACCOUNT KEY
  (activity identity with field6!=0: mac=0xD3DABDA3AF16F99E,
  rig=0x846C8338F7D022E6 — STABLE across the arc) and the JOIN identity
  machine id (activity identity with field6=0: rig=0xD022E6014726E889,
  per-boot, sharing the real key's low 24 bits — the p2-166/167 relation:
  machineId>>40 == memberKey&0xFFFFFF, group_host net_addr_for_member).
- sesscmp blob values seen (mac): 0, 0xA8C849F15BE5891F, 0xC127C9FCC1F56597,
  0xD3DABDA3AF16F99E (real account key), 0x0D432248EC9E1A1B (the fork's
  sessionId — MATCH=1 at t=132645+, the landing-created session), and
  0xACBE7AA8CBE8B2D4 (the mac's joinId, match=1 with itself at t=132775+).
  The rig's blobs: 0, 0x1A3408BC21EDD5C9, 0xC477C7F91F2A0C54,
  0x846C8338F7D022E6 (rig's real key), 0xD3DABDA3AF16F99E (the MAC's key —
  the rig holds a slot naming the mac; the mac holds NO rig-key slot —
  asymmetric).
- The join identity machine id appeared as a blob NOWHERE.
- TIMING (novelty-gate hazard, the 09-03 class): the mac's join-key
  comparisons at t=131641..132908 (incl. the match=1 against the fork's
  sessionId) PREDATE the relayed join's refusal (t=206768) and are the mac's
  OWN join machinery. The refusal's walk emitted NO new pairs — the gate's
  slot-blob set at refusal time is NOT directly observable from this log.
  The refusal is the hard fact; the slot contents are the open measurement.

### 6. THE NEXT DECODE (named, clean code — not obfuscated)

The connect-family handlers the OOB switch routes ids 5/6/7/9 to
(0x1417D3010/0x1417D4590/0x1417D27B0/0x1417D1A90): what they bind into the
RECEIVING connection's context ([ctx+0x1C7C0] and the slot sessions) — the
real session-to-connection binding publisher. The fork's answer_connect
already speaks this family.

### 7. THE SHIPPED SERVER CHANGE (this arc, settings-gated, default OFF)

- `relay_join_target_identity` (settings/gameplay): the relay's per-recipient
  copy of the join retargets the sessionId field (absolute bit 109 of the
  container, byte-exact vs the fork's own admit decode of the p2-182 capture
  — session 0x7F7EAE4DD8A942DB and joinId 0x338F19050FD86611 re-derived from
  the raw bits at exactly the implemented offsets) to the recipient's join
  identity machine id (arm 1; the comment records the account-key arm 2 and
  the binding-decode alternative). Peer ids recorded per endpoint at
  answer_join; unknown peer or parse failure = verbatim fallback;
  `stage=join_relay_target` logs each rewrite.
- The default keeps the deployed byte-verbatim behavior. Flipping it on is
  ONE setting change + server restart; the readout is the greppable refusal
  line plus sesscmp's new (key,blob) pairs.

### 8. THE ARM-1 BOOT (p2-188 + p2-188b, 2026-09-06 late): MECHANISM PROVEN, VALUE REFUTED

- p2-188 (first landing): the relay went VERBATIM (retargeted=0) — the mac's
  join identity decode failed AGAIN (machine=0, 2nd consecutive boot). Offline
  decode of the capture found the cause: **the identity table's two NetAddr
  pairs legitimately diverge — the mac's first pair names its CACHED
  PRE-NETWORK-MOVE address (192.168.1.164) while the second names the current
  192.168.1.7; the rig's agree.** The decoder's equality rule refused the mac.
  The parse itself is correct: mac machineId 0x16F99E012A801F92 >> 40 ==
  the real account key's low 24 bits (0xD3DABDA3AF16F99E & 0xFFFFFF) — the
  measured relation holds. FIX SHIPPED: the decoder returns both pairs
  (address/address2) and the consumer's self-check accepts EITHER matching
  the datagram source. Client DLL redeployed to BOTH machines
  (9100743cacc30cae — shared sources; preflight PASS 13/0/0).
- p2-188b (second landing): the full chain verified — mac identity
  selfcheck=ok via the second pair (addr .164 / addr2 .7 both logged);
  rig identity selfcheck=ok; the rig's join relayed with
  **stage=join_relay_target result=sent machine=0x16F99E01172E8FCB,
  retargeted=1** — and the mac's client REFUSED, with the refusal's session
  field = the RETARGET VALUE (machine_rev rendering CB8F2E17:019EF916).
  **OUTCOME (b), PRE-NAMED: arm 1 (the join machine id) is DEAD as a value.**
  join_processor: ZERO events (the refusal correctly precedes it).
  The mac's sesscmp blob census this boot: 0, the fork's sessionId (match=1,
  the landing session), the machine id (match=1, some container), the REAL
  account key 0xD3DABDA3AF16F99E, and two new identities
  (0xF1355488131A3F56, 0x8E4B5C1BE4FBBA92) — the blobs exist in SOME
  container but the gate's walk still refused; WHICH container the gate
  walks needs the caller-discriminated sess_cmp (STATE NEXT 4).
- Per the brief's ABANDON clause: relay_join_target_identity reverted to
  false (byte-verbatim relay restored, no rebuild needed); the next decode is
  the connect-family handlers (ids 5/6/7/9) — the binding publisher — before
  arm 2 (the real account key). D-018 closed: mechanism proven, value refuted.

## 10. THE 20.320 DECODE + THE WIDE BINDING CAPTURE (p2-189, 2026-09-06) —
## THE BINDING ARCHITECTURE IS MEASURED END TO END; THE FIX KEY IS THE RECIPIENT'S JOINID

### The connect-family decode (OOB ids 5/6/7/9: request/response/refuse/closed)

- The four handlers (0x1417D3010 request / 0x1417D4590 response /
  0x1417D27B0 refuse / 0x1417D1A90 closed) are PURE TRANSPORT: they manage a
  62-slot transport-connection table (0x41F0 stride, singleton accessor
  0x1417CF0E0, ADDRESS-matched at conn+0xA8 by finder 0x1417C38A0; state at
  +0x1D18 (2 = handshaking), +0x3040 (3); channel/sequence pairs at
  +0x1D10/+0x1D14; sub-object getter 0x1416C0830 = conn+0x1D28; endpoint
  object at +0x3150). The response handler validates the three echoed fields
  and applies the peer channel/sequence pair (0x1416D7CB0) and the local pair
  (0x1416BFBB0). **No handler touches session state; the bodies carry no
  session identity.**
- **OOB id 8 (establish) is in the client's DEFAULT-DROP slot** (the byte
  map's slot 16 = a bare `ret`) — the establish step never crosses the OOB
  plane in either direction; establishment is inferred from the response.

### The session-to-connection binding, decoded to the binder chokepoints

- The binding field [machineCtx+0x1C7C0] — the exact field the join gate's
  walker reads — has EXACTLY TWO store sites in .text, both clean
  pdata-backed functions:
  - **binder 1 (0x141772440)**: [ctx+0x1C7C0] = 0x141795A40(ctx-index rcx=4,
    flags, …); create-or-find with a CLEAN index-keyed finder (0x141792370);
    on hit updates the record via 0x14179AF00 (+0x0=arg1, +0x30=arg4,
    +0x34=arg3, +0x38=arg6, flag bits → +0x4 bit1, +0x2C bits 0/1). Also
    mirrors the index at [ctx+0x858]. Called from the init-time context
    manager (0x14175E520, clean) AND from the VM-obfuscated runtime ring
    (0x140B5ECD0 → … → 0x140C26C60 → thunk 0x1417723C0).
  - **binder 2 (0x141773200)**: [ctx+0x1C7C0] = 0x1417951A0(sessionId,
    flags, …) — the SESSION-ID-KEYED form; its finder 0x1417A1ED0 is
    VM-obfuscated. Called from the context manager and the runtime ring.
- The session create-or-find pair (0x141795A40 index-keyed / 0x1417951A0
  session-id-keyed) grants SMALL INTEGER indexes — the records the walker's
  by-id lookup (0x14179AF00) resolves.

### The p2-189 boot (the wide binding capture: 6 new hooks + widened sess_cmp)

All six instruments fired on BOTH machines (hook count 58 → 64,
307586da4bb7e0ac; preflight PASS 13/0/0; D-020 closed survived):

- **walk_map (the gate's walked map, captured at the relayed join's walk):**
  `key=0xC66E077AA815237A bind0=0 bind1=-1 bind2=1 bind3=-1 bind4=-1
  bind5=2` — IDENTICAL ON BOTH MACHINES (rig t=99344 / mac t=109700). The
  gate walks six slots bound to SMALL-INDEX sessions {0, none, 1, none,
  none, 2}. (Cosmetic: the log line's stage tag is `walkmap`, the census
  name `walk_map` — greps must match both.)
- **binder2's stack args name the binding key — THE MACHINE'S OWN JOINID**:
  mac a6=0x59ED107102C1F335 (= the mac's joinId on the admit line), rig
  a6=0x587CDBAF44D4D2AB (= the rig's joinId). binder2/cof_soid create the
  session NAMED BY THE JOINID and bind it (index 2 → slot5).
- **binder ctx pointers = the walked slots**: binder1 call1 rcx=0x45A2C18 =
  walk_map's slot0; binder2 rcx=0x4631748 = walk_map's slot5. The binding
  chain is fully attributable.
- cof_index granted indexes 0 then 1 (called with rcx=4 — a kind code);
  cof_soid granted index 2 for the joinId-keyed lookup.
- **apply_stamp fired ONCE** (early boot, dst=0x143050D60 — a STATIC config
  object, soidA=0): the session-apply is NOT the writer of the session
  records' blobs in the landing state. The landing-session's blob writer
  (the record whose blob held the fork's sessionId in p2-187/188b) remains
  an open site.
- **sess_cmp widened WORKS** (every line carries caller_rva; two consumers
  visible: 0x17640E3 and 0x175D0B3) — but the flat 64-triple budget was
  spent by the landing's own comparisons BEFORE the relayed join, so the
  gate's own triples for the relayed key are missing. THE INSTRUMENT FIX:
  per-caller sub-budgets (e.g. 16/caller, first-seen-key per caller), or
  caller_filter for the walker's call site. This is the one defect the
  boot found in its own instruments (the pre-named "budget per event
  class" rule, violated by a flat budget again).
- The relayed join was refused under the fork's sessionId (byte-verbatim,
  retarget OFF) — the baseline reproduced WITH the map being recorded.
- The mac hit the parked co-presence render-black variant (client alive,
  no fade_release in the second segment — sharper marker than previously
  recorded); the rig spawned fine on the identical build. Banked as
  observation; not attributed to the instruments.

### THE CONSEQUENCE (the front's fix, now concrete)

- The gate's walked slots hold the client's OWN small-index sessions — one
  of them NAMED BY THE MACHINE'S OWN JOINID (the binder2/cof_soid path).
- p2-187's blob census already measured a record whose blob = the machine's
  own joinId (key=joinId vs blob=joinId, match=1, p2-187 t=132775+).
- THEREFORE: **the relayed join's sessionId must equal the RECIPIENT'S
  CURRENT JOINID** — the value under which the recipient's own binding
  names its session. The fork HOLDS that value (every client's join carries
  it; the membership machinery refuses updates that do not echo it, so the
  fork always holds the live value). This is retarget **arm 3**, and it is
  the first arm whose key value is PROVEN to exist inside the gate's walked
  records on both machines (binder2/cof_soid + the p2-187 blob census).
- Arm 1 (join machine id) is dead; arm 2 (the real account key) is the
  fallback; arm 3 (the joinId) is the evidence-backed move. The retarget
  mechanism (rewrite_join_session_id) already implements the rewrite — arm
  3 is a one-line value change + the per-caller sesscmp budget fix.
- OPEN: which wire message drives the runtime binder (inside the
  obfuscated ring) — decidable by correlating binder firings with the
  fork's published message stream in the next capture, or by the
  caller-discriminated instrument on the binder itself.

---

## 11. THE GATE READ TO EXHAUSTION (2026-09-06 evening + 09-06 late, STATIC, NO BOOT)

Provenance: `disasm_fn.py 1416E0460`, `disasm_fn.py 14177A0B0`,
`lane_svc43_disasm_range.py 1417944C0 1417945A0`. Every instruction below is
printed output, not a summary — the 09-06 postmortem's ADDENDUM 2 records this
session's predecessor asserting "nothing between the match and the processor"
from a summary while the disassembly in its own transcript said otherwise. This
section exists so that never has to be taken on trust again.

### 11.1 THE GATE (0x1416E0460), the complete decision path

    0x1416E0495  call 0x1416C1260           ; the protocol version constant
    0x1416E049A  cmp  word [r14], ax        ; r14 = the packet
    0x1416E049E  jne  0x1416E0664           ; version mismatch -> drop (NOT the refusal)
    0x1416E04A4  mov  rcx, [rdi + 0x28]     ; rdi = the ARRIVING CONNECTION's context
    0x1416E04A8  lea  rdx, [r14 + 0x10]     ; the key = packet + 0x10
    0x1416E04AC  call 0x14177A0B0           ; THE WALKER
    0x1416E04B1  test rax, rax
    0x1416E04B4  je   0x1416E04D7           ; MISS            -> refusal
    0x1416E04B6  mov  ecx, [rax + 0x1AEF8]  ; the returned SLOT's state
    0x1416E04BC  add  ecx, -6
    0x1416E04BF  cmp  ecx, 3
    0x1416E04C2  ja   0x1416E04D7           ; state NOT in 6..9 -> the SAME refusal
    0x1416E04C4  mov  r8, r14               ; the packet
    0x1416E04C7  mov  rdx, r15
    0x1416E04CA  mov  rcx, rax              ; the found slot
    0x1416E04CD  call 0x1417806C0           ; THE PROCESSOR
    0x1416E04D2  jmp  0x1416E0792

VERIFIED, and this is now closed: **there are exactly TWO conditions between
the walker and the processor** — `rax != 0` and `[rax+0x1AEF8] - 6 <=u 3`.
Nothing else. Both failures branch to the same block at 0x1416E04D7, which is
why "unknown session" prints for a state-window failure as well as a miss.
The comparison is UNSIGNED (`ja`), so the passing set is exactly {6,7,8,9}.
The walker's return is used directly as a pointer — `emit_walkleave`'s reading
of rax as the slot, and of `+0x1AEF8` off it, is the gate's own arithmetic.

### 11.2 THE WALKER (0x14177A0B0), complete — 0x66 bytes, no hidden paths

    rcx = the container, rdx = the key, ebx = 0, rdi = the container
    loop:  rax = [rdi]                      ; the slot pointer
           test rax,rax / je next           ; a NULL slot is skipped
           ecx = [rax + 0x1C7C0]            ; THE SLOT'S BOUND SESSION ID (a dword)
           rdx = the key
           call 0x1417944C0                 ; the per-slot compare helper
           test al,al / jne found
    next:  ebx++ ; rdi += 8 ; cmp ebx,6 ; jb loop
           return 0                         ; MISS
    found: return [r14 + ebx*8]             ; THE SLOT POINTER at the matched index

### 11.3 THE PER-SLOT HELPER (0x1417944C0), complete

    helper(ecx = the slot's bound session id, rdx = the key):
      if (ecx == -1) return 0               ; AN UNBOUND SLOT IS NEVER COMPARED
      rdi = 0x14179AF00(ecx)                ; the by-id lookup -> the session RECORD
      if (bit 4 of [rdi+4]) {
          if (equality(key, rdi + 0x57C)) return 1     ; call site 0x17944FA
      }
      return equality(key, rdi + 0x94E) ? 1 : <the +0x57C result>   ; site 0x1794520

(`disasm_fn` truncates this one at 0x1417944D4 — its .pdata entry is a chunk of
a larger function. That is the known Tier-2 truncation row; the linear range
disassembler is the path.)

### 11.4 THE STRUCTURAL FACT NOBODY HAD SEPARATED — TWO OBJECTS, NOT ONE

**The match is on the RECORD. The state check is on the SLOT.** They are
different objects, joined only by the bound session id:

    slot --[+0x1C7C0]--> a session id --0x14179AF00--> a RECORD --[+0x57C / +0x94E]--> the blob
     |
     +--[+0x1AEF8]--> the state the gate demands be 6..9

So the gate finds the slot whose *bound session's record* carries the join's
sessionId, and then requires *that slot* to be live. A match on the record and
a failing state on the slot are entirely compatible — and both print the same
refusal. The project's "three structures not to conflate" warning applies here
directly; `sess_cmp` observes the RECORD's blob and has never been able to name
the SLOT it came from.

CONSEQUENCE FOR THE BINDS: measured binds are {0,-1,1,-1,-1,2}, and a -1 bind
short-circuits before any compare. So only THREE of the six slots are ever
compared, and each compares against one or two blobs depending on bit 4 —
which is exactly why the observed walks emit 4 compares, not 6 or 12.

### 11.5 AN INSTRUMENT GAP THIS DECODE EXPOSES (name it before it costs a boot)

`emit_walkmap`'s change gate hashes `key ^ slots ^ binds` — and after the
p2-194b hot-path fix the STATES are read only when a line is already being
emitted. **A state change therefore cannot trigger a walk_map line.** Every
`st<i>=` value ever logged is the state at the moment some *other* field
changed, not at the walk being reported. That is precisely explanation (a) for
the p2-193b contradiction — "st2=6" was never evidence about the refusal walk —
and it means the enter probe must bypass its change gate inside the join
window, or the leave probe's state read is the only trustworthy one.

### 11.6 WHAT THIS LEAVES

The gate is now decoded to exhaustion; no third check exists. The whole of
row 5 reduces to ONE measurement — what the walker returned on the gate's own
call for the relayed join:

  ret == 0                    -> MISS: the matched compares seen in p2-193a/b
                                 belonged to another of the walker's 35
                                 consumers, and the gate's own container does
                                 not hold a record naming the fork's session.
  ret != 0, state in 6..9     -> the processor MUST have been called; if
                                 join_processor still reads 0 the hook or its
                                 attribution is wrong, not the game.
  ret != 0, state outside     -> the fork-side fix is sequencing: make the
                                 forkSession-named session's SLOT reach 6.

---

## 12. THE MATCHED SLOT IS SLOT5, AND ITS STATE IS 4 (2026-09-06, NO BOOT)

Derived from RECORDED logs (p2-193a: 20260906_143105/143129; p2-193b:
20260906_144232; plus 145158/145403) read against section 11's decode. No boot
was spent. This is the answer to the question p2-194 was going to buy.

### 12.1 THE WALK, MAPPED COMPARE-BY-COMPARE

The whole gate call fits in one window of the mac's log (p2-193b, t=227718..720):

    enter fn=join_type0a call=1 caller_rva=0x16E2BE0     <- the gate is entered ONCE a boot
    pktdump  nonce=0xA4F8 key16=D2085640FCBA383A...
    enter/leave fn=inst_nonce ret=0xA4F8                 <- the version check PASSES
    sesscmp call=67947 caller=0x17944FA blob=0xBECC274CA684E9DB match=0
    sesscmp call=67948 caller=0x1794520 blob=0x0000000000000000 match=0
    sesscmp call=67949 caller=0x17944FA blob=0x2726D84C40069020 match=0
    [call 67950 - novelty-suppressed]
    sesscmp call=67951 caller=0x17944FA blob=0x3A38BAFC405608D2 match=1   <- THE MATCH
    retail "join-request: received message for an unknown session ... a refusal"
    leave fn=join_type0a call=1 ret=0x3F

Two facts fall straight out and neither needed a new instrument:

**(a) The match is the GATE'S OWN walk.** It sits between join_type0a's enter
and leave. The p2-193b ambiguity - "was this the gate's walk or one of the
walker's other 34 consumers?" - is ANSWERED, from data already recorded.

**(b) The matched slot is SLOT5.** Section 11.3: a bind of -1 is never
compared, and a bound slot spends one compare at +0x57C (site 0x17944FA) and at
most one at +0x94E (site 0x1794520). The measured binds are
{0,-1,1,-1,-1,2}, so exactly three slots are walked, in index order:

    slot0 (bind 0) -> 67947 (+0x57C) + 67948 (+0x94E)   no match
    slot2 (bind 1) -> 67949 (+0x57C) + 67950 (+0x94E, suppressed)  no match
    slot5 (bind 2) -> 67951 (+0x57C)  MATCH

67951's caller is the +0x57C site, and a slot visits +0x57C at most once - so
it cannot be slot2's second blob. The match is slot5's first. Independent
confirmation: sessstate's c854 field tracks the eventual session index
(0x45A2C18 c854=0 -> sid 0; 0x45DBD60 c854=1 -> sid 1; 0x4631748 c854=2), and
bind5 = 2. Slot5 IS 0x4631748.

### 12.2 SLOT5'S STATE IS 2, THEN 4, AND NEVER 6

    20260906_144232  t=107520  st0=6  st2=6  st5=2
    20260906_144232  t=107804  st0=6  st2=6  st5=4
    20260906_145158  t=134343  st0=6  st2=6  st5=2
    20260906_145158  t=134637  st0=6  st2=6  st5=4
    20260906_145403  t=134343  st0=6  st2=6  st5=2
    20260906_145403  t=134637  st0=6  st2=6  st5=4

Reproducible in every run: the client's OWN two sessions sit at 6 (LIVE
HOSTED); the session carrying the fork's identity climbs 2 -> 4 in about 300 ms
and then STOPS. The gate requires 6..9 (`add ecx,-6 / cmp ecx,3 / ja`,
unsigned), so 4 refuses - and it refuses with the SAME "unknown session" text
as a miss, which is why five boots read a state failure as a lookup failure.

### 12.3 WHAT THIS RETRACTS

The p2-193b reading "the matched slot is slot2 (0x45DBD60, st2=6), which is
INSIDE the window, so the state check should pass" is WRONG. It inferred the
matched slot from which record held the forkSession blob rather than from the
walk order, and it picked the wrong one. The correct mapping was available in
the same log. The contradiction that made p2-194 look necessary - "match=1 and
state=6 and yet calls=0" - dissolves: the matched slot was never at 6.

### 12.4 THE CONFIDENCE, STATED HONESTLY

The state values above were read at t=107520/107804; the gate's walk is at
t=227718. Nothing measured slot5's state AT the refusal, because walk_map's
change gate hashes key^slots^binds and cannot fire on a state change (11.5).
So this is a strong inference, not a measurement: three runs agree that slot5
rests at 4, and no mechanism is known that would carry it to 6 and back.

THE BUILD NOW DEPLOYED (44c400b985d60c7a) closes exactly that gap: inside the
join gate's own call the change gate is bypassed, so walk_map re-reads and
reports all six states at the refusal walk, and walk_leave names the returned
slot with its bind and state. One boot converts 12.2 from inference to
measurement, and it is a CONFIRMATION boot, not an exploratory one.

### 12.5 THE FRONT AFTER THIS

Row 5's wall is no longer "which container" or "which key" or "MISS vs
STATE-OUT". It is one question with a server-side answer:

  **WHAT DRIVES A SESSION SLOT FROM STATE 4 TO STATE 6, AND WHAT MUST THE FORK
  SEND TO DRIVE THE forkSession-NAMED ONE THERE?**

The positive control is in the same log: the client's own two sessions make the
whole climb to 6 organically (p2-182 measured this on both machines). So the
progression mechanism exists, runs locally, and is reachable - the fork simply
never triggers it for the session it names. That is fork-side work on the
gameplay plane, in code we own, and it is the next decode: find the writer of
[slot+0x1AEF8] and the transition 4 -> 6.

---

## 13. MEASURED (p2-195, 2026-09-06 ~16:29) - SECTION 12 CONFIRMED BYTE-FOR-BYTE

One paired boot, client 44c400b985d60c7a, archive RE_output/logs/20260906_162912_p2-195.
Every value section 12 pre-named was measured exactly. The inference is retired; this
is now a measurement.

### 13.1 THE READOUT

    t=240902 enter fn=join_type0a call=1 caller_rva=0x16E2BE0
    t=240903 pktdump nonce=0xA4F8 key16=F3238901C0161CE7BB7AD63EF25A5E09
    t=240904 leave  fn=inst_nonce ret=0xA4F8                    <- version check PASSES
    t=240904 walk_map call=82 window=1 key=0xE71C16C0018923F3
             bind0=0  st0=6   slot0=0x45A2C18
             bind1=-1 st1=0   slot1=0x45BF4B8
             bind2=1  st2=6   slot2=0x45DBD60
             bind3=-1 st3=0   slot3=0x45F8600
             bind4=-1 st4=0   slot4=0x4614EA8
             bind5=2  st5=4   slot5=0x4631748                   <- THE FORK'S SESSION
    t=240904 sesscmp 0x17944FA blob=0x6D51976ADE26AE2E match=0   slot0 +0x57C
    t=240905 sesscmp 0x1794520 blob=0x0000000000000000 match=0   slot0 +0x94E
    t=240905 sesscmp 0x17944FA blob=0x4039673F805FDAE4 match=0   slot2 +0x57C
    t=240905 sesscmp 0x17944FA blob=0xE71C16C0018923F3 match=1   slot5 +0x57C  MATCH
    t=240906 walk_leave ret=0x4631748 bind=2 state=4 depth=1 outcome=FOUND-STATE-OUT
    t=240906 retail site=301 "join-request: received message for an unknown session
             F3238901:C0161CE7 ... sending back a refusal"

  join_processor (0x1417806C0) calls=0 - the consumer is never reached.

### 13.2 WHAT IS NOW PROVEN RATHER THAN INFERRED

- The gate MATCHES the relayed join and refuses on its SECOND check. Not a lookup
  failure, not a container failure, not a key failure - all three are closed.
- The matched slot is slot5 = 0x4631748, bind 2. Section 12's compare-to-slot mapping
  by walk order was correct; p2-193b's "the matched slot is slot2 at st=6" is retracted.
- The matched slot's state is 4 AT THE REFUSAL WALK, in the same call, read by the
  window-forced walk_map (window=1) and independently by walk_leave off the walker's own
  return value. The two-minute gap section 12.4 flagged as its honest limit is closed.
- depth=1 on the walk_leave line: the walk is the GATE'S OWN, not a nested or concurrent
  consumer's. The p2-193b attribution ambiguity is closed by construction, not argument.
- Exactly ONE walk_leave line for the whole boot. The armed window behaves as designed:
  silent everywhere else (walk_leave=0 for the entire solo period before the join).

### 13.3 THE INSTRUMENT VERDICT

The mac LANDED on 44c400b985d60c7a (initial_slice_set x10, character select, tower)
where d5ed2ae3f12e42fb never reached the tower at all. The R8 defect diagnosed by
reading - the leave probe's budget checked against EMITS while the novelty gate returned
before that counter could move - was the landing regression, and removing the probe's
cost outside the join window fixed it. Two boots (p2-194a/b) had been spent on that
defect; no boot was needed to find it.

The one budget_exhausted line in the boot belongs to an unrelated consumer
(sess_cmp caller 0x1779C3A, t=241942) AFTER the gate window - the gate's own chain
emitted its complete compare set.

### 13.4 THE FRONT, RESTATED

Row 5 is one state transition from falling. The fork's session is created, bound into
the gate's walked container at slot5, and carries the identity the join names - the
whole delivery chain works. It sits at state 4; the gate requires 6..9.

  **WHAT DRIVES A SESSION SLOT FROM 4 TO 6, AND WHAT MUST THE FORK SEND TO DRIVE THE
  forkSession-NAMED ONE THERE?**

Starting evidence for the decode (do not re-derive): 20.184 RESULT 3 - the stage
writers are 0x14178CD97's cluster, driven by 0x140C05F80, which tries stages 0/1, 2/3,
4/5 across 0x1C8A0-stride object pairs until the setter returns true, and the client
"CYCLES STAGES 0..5 ONLY". That matches this measurement exactly: the fork's session is
parked at the top of the client-driven range (4) and something ELSE must carry it to 6.
The positive control is in the same log: slot0 and slot2 are at 6, in the same
container, on the same boot - so whatever makes 6 happen is reachable and observable.
NOTE the tension to resolve: 20.184 calls 6..9 "a DIFFERENT object family", but slot0,
slot2 and slot5 are all in the one walked container. Its addresses stand; its framing
needs a pass.

---

## 14. THE STATE LADDER DECODED - AND THE JOIN-RELAY ROAD CLOSES ON ITS OWN QUESTION
## (2026-09-06, STATIC + recorded logs, NO new boot)

### 14.1 THE STATES HAVE NAMES, AND THE CLIENT PRINTS THEM

field_xref on +0x1AEF8: 497 accesses, SIX writes, and only two can write an
arbitrary value:
    0x0140914bbf  mov [rsp+0x1AEF8], eax    <- SIB base=rsp: a STACK write in a
                                               huge frame. NOT the field.
    0x0141768036  mov dword [rbx+0x1AEF8], -1
    0x0141774f41  mov dword [rbx+0x1AEF8], -1
    0x01417756cd  mov dword [rdi+0x1AEF8], 0
    0x014178cd98  mov [rdi+0x1AEF8], esi     <- 20.184's named cluster
    0x01417b37de  mov [r14+0x1AEF8], r15d    <- NOT named by 20.184

The second register writer (enclosing chunk 0x1417B36CA..0x1417B37F6) is the
STATE-TRANSITION function, and it LOGS the transition: it formats the old state
([r14+0x1AEF8], read at 0x1417b3780) and the new state (r15d) through the
name function 0x14177A280, and emits. It then computes `lea ecx,[r15-4] /
cmp ecx,5 / setbe al` - "is the NEW state in 4..9" - and compares that against
a saved boolean, i.e. an in-range-ness edge that drives a notification.

So the ladder was never a mystery: the client prints it in plain English, and
the p2-195 log carries every transition of the boot:

    t=58024  [fireteam:...]     'none' -> 'host-established'
    t=82048  [posse:...]        'none' -> 'host-established'
    t=118144 [group_target:...] 'none' -> 'peer-creating'
    t=118190 [group_target:F3238901:C0161CE7] 'peer-creating' -> 'peer-joining'
    t=118628 [group_target:F3238901:C0161CE7] 'peer-joining' -> 'peer-established'

Cross-matched against the sessstate probe on the same boot (0x45A2C18 -> 6 at
t=58025; 0x45DBD60 -> 6 at t=82061; slot5 at 4):

    **state 6 = 'host-established'      state 4 = 'peer-established'**

    host path: none -> host-established (6)
    peer path: none -> peer-creating -> peer-joining -> peer-established (4)

### 14.2 WHAT THE GATE'S 6..9 WINDOW ACTUALLY MEANS

`[found_slot+0x1AEF8]` in {6,7,8,9} is not an arbitrary readiness threshold. It
is the HOST half of the ladder. The gate is answering a join REQUEST - a machine
asking to be admitted to a session - and it requires that the session named be
one THIS MACHINE HOSTS. A peer cannot admit anyone; only the host can.

The mac is a PEER in the fork's group_target session (it logs "Creating CLIENT
managed session", "joining Steam Lobby as client", and tops out at
peer-established). It will never be that session's host.

**THEREFORE THE RELAY CANNOT SUCCEED, AND NOT FOR ANY REASON WE WERE HUNTING.**
Not the channel, not the key, not the container, not the retarget value - all of
which we closed by measurement. A connection-layer type-0x0A join is a HOST-ONLY
message, and we were delivering it to a peer. The 4 -> 6 question posed at the
end of section 13 is the WRONG question: driving the mac's peer session to
'host-established' would be asserting a falsehood about the topology, and the
fork - which really is the host - is where such a request belongs.

### 14.3 AND THE RELAY WAS NEVER NEEDED FOR PEER PRESENCE

The membership plane has ALREADY put the rig into the mac's group session. From
the same p2-195 log (t=241625, after the rig reached the tower):

    [group_target:F3238901:C0161CE7] update_number: 11, leader_peer_index: #0,
      host_peer_index: #0
    peers valid: 0x7 (THREE peers), players valid: 0x3 (TWO players)
    peer # 2 a=[192.168.1.136:3097] s=_established o=1 j=[095E5AF2-3ED67ABB]
    channel 192.168.1.136:3097 ... state change connecting -> established
    [group_target:...] player-properties accepted for player #1

THE CONTROL (run before claiming novelty): these counts are NOT new to this boot.
peers 0x7 / players 0x3 and the `peer # 2 a=[192.168.1.136...]` row appear
identically in 20260906_143105 (p2-193a) and 20260906_144232 (p2-193b). The
membership plane has been delivering the rig as an ESTABLISHED PEER, with a
direct mac<->rig channel, for at least three boots - through every one of the
join-relay experiments, whose refusals therefore never blocked anything.

### 14.4 WHERE THE WALL ACTUALLY IS

With the rig established as a peer and a channel up, the entity road is still
COMPLETELY SILENT on the same boot:

    ent_recv   calls=0        ent_create calls=0
    ent_gate   calls=0        ent_make   calls=56  (local only)

So the wall is not session membership, not the join gate, and not the state
ladder. The peer is present at the session layer and NO ENTITY TRAFFIC FOLLOWS.

That is exactly what 20.301 said on 2026-09-05 and it has been true the whole
time: "peers must ARRIVE by SERVER-MEDIATED replication on the gameplay plane
(UDP 30976). The receive cluster logs zero because NOTHING EVER SENDS IT A PEER
ENTITY - and the fork has never sent one. This is fork-side work in code we own."

### 14.5 THE FRONT

CLOSED (on its own question, not a sub-question): "what must the fork send so
the receiving client's join gate admits the peer?" Answer: NOTHING CAN. The gate
is host-only by construction, the client is a peer, and the peer is already
admitted by a different plane that has been working for boots. The whole
p2-181..p2-195 relay road is closed - its machinery, decodes and measurements
stand as the record of how it was closed.

OPEN, and it is the one 20.301 named: THE FORK MUST SEND AN ENTITY. The contract
is already spec-complete and femu-validated (20.302 ent_* receive cluster,
20.303 the carrier, 20.304 the payload bodies - kind 2, the guardian, is RAW 8
BYTES). The single remaining unknown is the OUTER WIRE TYPE (20.303 R4).
