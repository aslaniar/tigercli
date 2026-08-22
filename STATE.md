# STATE - living snapshot (the single source of "where we are")

Updated: 2026-08-21 ~20:0x. THE TWO BUGS (disabled weapons + inventory
model loop): 14.18's root cause ("gear socket-entry-lists never built")
did NOT survive disk re-verification - see FINDINGS 14.19. The served
cache is faithful to the raw blobs (weapons' entryList=0 is what the blob
says; subclasses are bucket 16 with catalog indices, not "1..1000");
equipped-gear details are healthy; upstream never solved this front.
Leading unproven theory: the unconditional `socketEntryContentsResolved=true`
on gear instances resolved against EMPTY list row 0 (FINDINGS 14.19).
Next = zero-boot read of resolve_socket_states + bounds emission, then a
one-variable boot (flip the flag on empty lists) or a wire capture first.
New tool: RE_scripts/probe_cache_v24.py (correct v24 layout) +
probe_native_entry_indices.py; checksum recipe verified.

PREVIOUS (2026-08-21 ~18:1x): graphics/UI closed enough to develop; ship
+ Sunrise UI work via gated-draw config; menu HOME key; pick-crash =
DXMT cold-compile quirk mitigated by cache warmth. Deployed: 7b70ba68-
generation DLL, current runtime settings (ui on, warp probe, renderer on,
hud_always=false), fresh server per boot. Git convergence parked at
integration @ 88be8bb+.

## POST-PORT CLEANUP (2026-08-21 ~13:00-13:40) — perf + FPS HUD + two new bugs

- **LAUNCH-TIME FIX (real, landed)**: the `ability_gate`/`gate_trace` hooks
  (pure research instrumentation for the flag-map/veteran-hunt investigation,
  zero gameplay effect - verified line-by-line, every path calls the original
  unconditionally then only logs) fire on hot per-tick engine paths and were
  logging 20k+ lines/boot once `file_sink`+`debug` got turned on for today's
  bug-diagnosis work. That log volume was the dominant cost in several
  multi-second boot stalls. Fix = stopped calling `install()` for both in
  `client_hook_activation.cpp` (code untouched, trivially re-enabled by
  uncommenting two lines) + settings reverted to `file_sink=false`,
  levels=`warn`. Landed in Sunrise-fork commit 6a63d9a.
- **SHADER CACHE (applied, NOT YET CONFIRMED)**: found zero MoltenVK cache
  env var anywhere in Whisky's launch environment - Whisky's own
  `shaderCacheEnabled` bottle setting almost certainly only governs DXVK's
  cache, irrelevant since this bottle uses wine's native winemetal.dll path,
  not DXVK. Every launch was very likely doing a cold shader/pipeline compile
  from scratch. Set `MVK_CONFIG_SHADER_CACHE_PATH` via `launchctl setenv`
  (same mechanism as the HUD fix below) pointing at
  `~/Library/Caches/MoltenVK/Sunrise/moltenvk_cache.mvk`; relaunched Whisky to
  pick it up. A kill-test after 15s showed no cache file written yet, but
  MoltenVK typically flushes its cache on clean shutdown, not mid-run, so
  this is inconclusive rather than a negative result. NEXT SESSION: verify
  the cache file actually populates after a normal quit, and if it's still
  empty, check whether Whisky's Swift launcher constructs a fresh environment
  for its child process instead of inheriting the ambient one (would mean
  `launchctl setenv` never reaches wine64 at all for anything not on
  Whisky's own explicit list — test by checking a KNOWN-good var like
  MTL_HUD_ENABLED is still landing after any future Whisky update).
- **FPS COUNTER (confirmed working)**: enabled via Apple's native Metal HUD -
  `launchctl setenv MTL_HUD_ENABLED 1` (system-wide, standard mechanism for
  any Metal/MoltenVK app including Finder-launched ones) + the Whisky
  bottle's own `metalConfig.metalHud` flipped true in Metadata.plist directly
  (`WhiskyCmd run ... --command` confirmed `MTL_HUD_ENABLED=1` reaches the
  launch env). **Gotcha that cost real time**: Whisky.app was already running
  from earlier in the session when `launchctl setenv` was first called - env
  vars are inherited at process launch, not dynamically, so the already-
  running Whisky never picked up the new value. Fix = `killall Whisky` +
  relaunch. User confirmed the HUD is visible. Rule for next time ANY
  `launchctl setenv` is used for this project: always kill+relaunch Whisky
  right after, don't assume it's live.
- **NEW BUG A - Mercury (public destination) spawn resolves empty, then
  crashes**: with `region_private=true` (the destination-hang fix from
  earlier), Mercury freeroam now actually loads (both slice-set transitions
  correctly show `PRV`, not `PUB` - the fix works exactly as designed) and
  reaches `state:in_world: Starting activity`. ~12s later the client logs
  `world_controller: successfully changed world to:` with **nothing after the
  colon** (compare the working line's `...to: mercury_freeroam`), immediately
  followed by the BAP connection getting killed
  (`_connection_failure_suicide`), both sessions disbanding, and a full
  client shutdown. Root-caused to a DIFFERENT, DOWNSTREAM step from
  `region_private`: `region_private` only fakes the "is this bubble public"
  answer for one specific call site (`client/hooks/bootflow/region_private.cpp`,
  read in full - confirmed side-effect-free, targeted, correct); it does
  NOT touch spawn-point or bubble selection. Something in THAT later step
  resolves to an empty destination for Mercury specifically (a real, complex,
  multi-bubble patrol zone) where it apparently didn't for the Tower (a
  simple single-space social destination). LEAD: the fork already has a
  built, unused-so-far `ForcedDestination` system
  (`state/activity/forced/activity_forced_destination.{h,cpp}` + a whole
  server-side debug UI panel, `server/ui/activity_override/
  activity_override_panel.cpp`, with explicit bubble/slice/spawn pickers) -
  `region_private.cpp` itself already references it
  (`state::activity::forced::override_active()` is one of the two conditions
  that trigger the private fake-out). This strongly reads as the fork's own
  intended answer for "automatic resolution doesn't work for this
  destination, name one explicitly" - NOT YET WIRED UP or tested for
  Mercury. NEXT SESSION: read `activity_override_panel.cpp` fully to learn
  how a ForcedDestination actually gets set (settings.json field? admin HTTP
  call? in-process UI only?), then try forcing a known-good Mercury
  bubble/slice/spawn combination and see whether the empty-destination crash
  goes away.
- **GIT-SYNC GAP FOUND AND FIXED**: the crypto key-derivation fix
  (`derive_envelope_wrap_keys`, state_runtime.cpp - the actual fix for the
  BAP handshake/"Centipede" bug) had NEVER been copied to the git-tracked
  Sunrise-fork repo at all - it only ever existed in the untracked
  Sunrise-fork-inventory Mac build tree. Copied + committed properly
  (Sunrise-fork b84f8de). All six of today's source fixes are now confirmed
  committed to Sunrise-fork: 65df13f, 9ba95c8, 701c7d5, 3935ca7, b84f8de,
  6a63d9a. The NEW sunrise-server CMake target/CMakeLists.txt correctly does
  NOT need porting to Sunrise-fork - that repo mirrors the PC/MSVC .vcxproj
  build and was never meant to carry Mac-only build tooling; see
  MAC_VS_PC_DIVERGENCE.md.
- **NEW BUG B - the ship still doesn't render**: very likely the SAME root
  cause already mapped in FINDINGS 14.6/6 as "the character-forever-loading
  bug" - `networking:simulation:entity: failed to create 'player_broadcast'
  entity`, repeating continuously since Tower load, tied to the fork's own
  documented, pre-existing "entity front" gap (`lane_entity_scope.md`'s W1-W8
  plan - zero entity schema/data published server-side yet, days-scale
  unfinished work, not Mac-specific and not new). The user could not
  previously reach a destination where they'd notice this (blocked by the
  hyperspace hang); now that `region_private` lets them load in, it's simply
  visible. Likely the SAME underlying gap as Bug A above (public/complex
  destinations needing entity/world-population data the fork doesn't yet
  serve) - investigate together, starting with the `ForcedDestination`/
  entity-front material already mapped, before assuming two separate causes.

## THE MAC PORT — CLOSED (2026-08-21, superseding everything below in this section)

WHAT'S RUNNING NOW (both deployed, both verified stable):
- Client: `Game/bin/x64/steam_api64.dll`, hash `c7ae81cd...`. Launched via a
  DEDICATED Whisky bottle ("Sunrise", `whisky create Sunrise`) — NOT the old
  hand-rolled `mac-port/launch-sunrise-macos.sh` env (it was missing ~15 wine
  env vars + a DllOverrides entry Whisky sets automatically; that was the
  real fix for the graphics chive, not a Metal/macOS-27 regression as
  previously suspected — that whole isolation ledger in INCIDENT_20260821_1002
  is now known moot, left for the record only).
- Server: `RE_output/s1_accept/sunrise-server.exe`, hash `abf2d9af...` — a
  NET-NEW Mac (MinGW/llvm-mingw) cross-compile; the exe that ran all prior
  session was a pre-built Windows/MSVC binary with no Mac build path at all.
  Runs under GPTK cask wine-7.7 in its own dedicated prefix
  (`~/Library/Application Support/SunriseServer/pfx`), launched via
  `mac-port/launch-server-macos.sh`. Client and server do NOT need to share a
  wine engine or bottle — only their TCP ports need to agree (30975 bap_port,
  8443 https_port, both configured identically on both sides).
- THE HYBRID ARCHITECTURE (as actually landed, not just planned): config-
  manifest GET + SignOn POST answered fully in-process by the client DLL
  (`client::hooks::network::http::route_descriptor` always tries the
  in-process consumer now, no more external-forward branch); BAP/discovery/
  admin genuinely external to the real standalone server on 30975/3074/3075/
  8099. The one designed unknown from the original lane brief ("BAP session
  validation shape") resolved to: derive ONLY the SignOn envelope's wrap keys
  (`encryptionKey`/`authenticationKey`) deterministically from the shared
  `bootstrap_token` (both sides already configure the identical value); the
  actual session nonce/key stay genuinely per-boot random (the client learns
  them by decrypting the server's hello). `state/runtime/state_runtime.cpp`,
  `derive_envelope_wrap_keys`.
- THE NEW `sunrise-server` CMake TARGET (net-new Mac tooling, lives in
  `RE_build/Sunrise-fork-inventory/Sunrise/CMakeLists.txt`, NOT yet ported to
  the git-tracked `Sunrise-fork`/committed): file membership derived from the
  client DLL's own (proven-working, 565-file) list minus client/UI/steam-hook
  dirs, plus ~15 server-exclusive files. Needed `LANGUAGES CXX C RC` (C, for
  the embedded sqlite3.c — silently uncompiled otherwise) and an explicit
  `-Wl,--stack,8388608` (the client DLL rides destiny2.exe's own host-process
  stack; a standalone exe only gets the linker default, which stack-overflowed
  on `state::initialize()`'s large stack struct).
- THE BUILD-IDENTITY RESTAMP PROCEDURE (will recur on every future server
  rebuild): a rebuilt exe's new PE timestamp+size invalidates
  `RE_output/s1_accept/Sunrise/cache/build_data.bin`'s stored identity header
  (offsets 12/16, `#pragma pack(push,1)`, `cache/records/format.h`) — no live
  rescan fallback exists for this cache (unlike content_manifest), so it hard
  z-fails content_swap. Patch offsets 12 (imageTimestamp) + 16 (imageSize),
  u32 LE, straight from the server's own freshly-logged "expected_ts"/
  "expected_size" fields (`cache_identity_patch.cpp`'s `restamp_equipment_hash`
  is the WRONG tool — it only touches the eq-hash at offset 20 and explicitly
  assumes ts/size are stable). A proper rebuild-aware restamp tool does not
  exist yet — worth writing before the next server rebuild.
- A separate, PRE-EXISTING, NON-FATAL warning persists every boot:
  `cached_eq` vs `expected_eq` mismatch in that same build_data identity
  check. This is a DIFFERENT mechanism (`configured_equipment_identity.cpp`,
  keyed to account gear/abilities, not the exe build) that the PC-track
  sections below already document extensively as "the eqHash gate." Never
  conflate the two — they share a log-line shape but are unrelated systems.

NEXT SESSION, IF THE SERVER GETS REBUILT AGAIN: re-run the build_data.bin
identity patch (the exact two-field procedure above) before the next boot,
using that boot's own logged expected_ts/expected_size — do not reuse today's
literal values, they are tied to today's specific binary.

SOURCE-CONTROL DEBT: today's two source changes (the SignOn hybrid + manifest
gate fixes were already committed by a prior session; TODAY added the
state_runtime.cpp key-derivation change and the new sunrise-server CMake
target) live only in `RE_build/Sunrise-fork-inventory` (uncommitted, no git).
Port to `RE_build/Sunrise-fork` and commit if that repo is meant to stay the
canonical history.

## Where we are (the one-line map)

The external-mode private server WORKS (S1 accepted, the world walkable, the
Tower loads). THE SWAP FRONT = CLOSED (boot Q: the equip's panel updates
live). THE CLEANUP FRONT (both fixes = deployed, the validation = PENDING the
boot): (1) THE PURPLE DIAMONDS (13.7) = the acquired-state restore (the
enum + the mask ternary + the Attunement forcedActive) — the harness gate
covered=20 acquired_active=20, zero ready lanes; (2) THE 3-SWAP STALL (13.8) =
the refuse-on-push-failure arm (frames staged first, persist LAST, revert +
the plain-pair refusal on any failure) — the full stage-then-commit = the
named OPEN item if the refusal alone doesn't clear the stall. THE NEXT FRONTS
(on request): the veteran fold (the trigger ∈ 47..953's 388 suppressed; the
next fold = restore the second half → ~194 kept); the verb layer; the entity
front; the vendor-open boot; the equip front's OPENs (the per-item picks
7846599; the 637bddc invalidation).

## Where we are (the one-line map)

The external-mode private server WORKS (S1 accepted, the world walkable, the
Tower loads). THE SWAP FRONT: the ability swap COMMITS (the item upsert); the
SUBCLASS EQUIP's panel display = the front. THE MAP (FINDINGS 12.26-12.27 +
13.1-13.2, all static): (a) the panel's live-update engine = the socket-node
sink FUN_1412f3660, with TWO doors — the notify gate (FUN_1412f0a70: the
changed def == DAT_141fb5928) AND the def-change repoint (FUN_140f40e80: the
panel's own inspected def ≠ the incoming record's def → the sink); (b)
DAT_141fb5928's writer = the panel's selection-changed event (mode 4 =
select, 6 = deselect), raised ONLY by the panel UI's own selection/preview
actions + the flow state machine + the activity-transition UI — the equip's
completion CANNOT raise it (xref proof); (c) the repoint's roots = the
player-class resolve callback FUN_140dc3960 (the "can't spawn... player_
globals" callback) + the +0x800 flag driver FUN_140fd13b0 + the panel's
refresh commits — none reachable from the family-4 apply chain statically;
(d) the character-side equipped-diff chain pokes the character-screen tiles,
not the panel; (e) THE UPSTREAM TRUTH: the equip flow EXISTS upstream; its
403 = the statusPair PROMISING before.family4Version+1 + ONE character object
@ +1 + the refreshes + the ability-bucket invalidation. THE REVISED THEORY:
the panel stays stale because the equip never delivered the upstream contract
(D1: all five boots carried the default reply value) AND the panel's re-render
depends on the CLIENT'S OWN reaction to the completed state change — the
player-class resolve / the flow-machine re-select — which the static map
cannot verify and the boot discriminates live. THE FIX = LANDED (13.3): the
promised reply (576edd7), the character upsert + the +1 discipline (5afca25),
the clicked row + the reset removal (61f1b62), the harness (8922e0d — EXIT 0
both, 81/81 + the clicked-row byte proof), the mojibake (2f94b39); builds =
server exe 1CA70C62... + DLL 3DA28DFD... (the kind hook included); OPEN-1
(the D5 reorder), OPEN-2 (the per-item picks), OPEN-3 (the invalidation =
structurally N/A). THE BOOT (the census-intent, PENDING THE USER'S GO): the
deploy (the cache re-stamp with the THEN-CURRENT DB hash — the live eqHash
0x9414... ≠ the DB's 0x034A... as of X's copy; the boot-L procedure) + the
kind-hook DLL + the A→B/B→A cross-swap equip; the falsifiable claim: kind=1,
the transaction completes, the panel switches; THE NEGATIVE = instrument
FUN_140dc3960 + FUN_140fd13b0 + FUN_140b47250's callers (a one-hook census
each). THE CONTINGENCY: a client-side Sunrise-DLL driver of the panel's
event/repoint (a new front, pre-mapped). The veteran fold (restore 47..953's
second half → ~194 kept) = the standing rider.

## THE DEPLOYED STACK (2026-08-19 ~20:5x, the BOOT-P deploy — UNCHANGED)

- The server exe = the boot-P build (7e94a2b the nonce fix on 216ca08 the
  reset→select two-frame, on the serial-port stack): SHA-256 = the
  INCIDENT_20260819_210002 acceptance stack (the incident = the re-hash). LIVE =
  PID 39444 on 443/8099/30975 (the boot = clean: six domains match, build_data
  cache ok, initialize ok). The .bak chain: .bak_bootO (the WEASEL build),
  .bak_bootN (the serial-port build), .bak_bootM, .bak_bootL.
- The DLL = UNCHANGED since boot L (6ef4ea030638cbda, the count=13 strip build).
  THE NEXT DLL = the kind-hook build (the count=14 batch, per the kind lane's §4
  spec) — LANE K's deliverable; it does NOT ride until Phase 3.
- THE CACHE = the v24 build with the boot-P identity (the exe's ts/size + the
  DB-derived eqHash — the identity-gate diagnostic (b4cbabf) now logs both
  identities on any mismatch; the deploy procedure = the bootL_eqhash_exact.py
  port's value (4-for-4 confirmed as the DB-load's C++ truth); NOTE the live
  /restamp verb stamps the RUNTIME snapshot's hash, which can differ from the
  DB-load's — the diagnostic is the arbiter).
- The DB = the post-boot-P state (the serials + the equip hand-offs live: the
  mutation_serial + flags + next_inventory_serial columns migrated in); the
  flags = the account 12,300 with 388 suppressed in 47..953 (the veteran fold).

## THE BOOT LOG (the swap-front boots)

- BOOT 12 (the first 801 port): the commits = ok, the push = FAILED (the banner's
  prepare — the catalog's 9 rows lacked the alternative selections).
- BOOT 13 (the 486-row catalog): the ability swap → the WEASEL (the nonce
  double-advance — the '_connection_failure_bad_signature'; FIXED).
- BOOT 14 (the nonce fix): the node picks = worked; the subclass equip → the
  PORPOISE (the cross-list stale picks — the equip's banner prepare; FIXED by the
  pick-reset).
- BOOT 15 (the equip reset): the character-creation regression (the roster encode
  on the persisted {6,8,10,21,2} — the bundle-member combination the bucket
  builder rejects; FIXED by the default-selection fallback).
- BOOT 16 (the fallback): the boot = clean (the Tower = loaded); the swaps = the
  same behavior — the ability swap = the rollback, the subclass = the state
  applies (the reopen shows it). CORRECTION (the ruling): this undersold a
  SESSION-KILLING CRASH — the same boot's subclass-equip increment landed at
  family-4 version 4 against the client's expected 2 (the two 801 bumps never
  delivered frames) → the out-of-order rejection → the kick → the
  '_connection_failure_suicide' → a 255+ s wedged cleanup (the game ran until
  the user closed it ~10:2x). The mechanism + arithmetic = FINDINGS 11.8.
- BOOT A (the fixed server + the census DLL + the staged fold, ~12:0x): the
  version discipline = VALIDATED — four 801s + the equip delivered +1 frames,
  ALL ACCEPTED (no kick, no suicide); the swap's UI = still cue-then-revert
  (the same behavior). THE HARVEST (FINDINGS 11.11): the correspondence =
  CONFIRMED (the platform pair → 583/581 exactly); the dictionary's shift map
  = validated live; the swap's requirement evaluations = named; the stamp
  chain = fires post-equip; the rollback executor = NOT the reverter. THE
  REVERT'S SOURCE = the subclass item's socket state (the 36-slot array in the
  item record) — published only in the boot snapshot; the fork republishes the
  item upsert on the 801. THE NEXT FIX = the item upsert on the 801 frame.
  THE USER'S POST-TOUR REPORT (FINDINGS 11.12) + THE ESCALATION RULING
  (FINDINGS 11.13): the SHIP = (d) the durable DB's post-equip loadout (the
  discriminator = the harness rebuild + diff); the TOWER-GATING = the
  session-layer knot (the activity-session AH-id wait — the S3 work item; the
  swap exonerated as the release); the census DLL + the re-stamps =
  exonerated; the repush guard = exonerated (the version-0 arm).
- BOOT B (the item upsert, 6692c07): THE ABILITY SWAP = COMMITS (the user's
  "ABILITY SWAP WORKS!!!!!!" — the item frames 189-190 B delivered + the
  display sticks). The recap = GONE → the veteran ∈ the kept half (the fold
  direction settled). The ship = back. The subclass equip's refresh = the
  remaining gap (the pop-ups + the exit/re-entry).
- BOOT C (the equip's item republish, 4bf7632): the 403's frame = the
  character + the item (2 objects, the harness 42/42). THE USER: unchanged —
  the pop-ups + the re-entry + the subclass icons disappear + one tree swap
  per inventory visit (the grenades/jump/class picks = fine).
- BOOT D (the in-place family-0 refresh, 9f52ba5): the banner = the
  record-only upsert (flags 0, no release — the fork's shape; the
  release-and-re-add = the "tears down the ship/banner binding" pattern).
  THE USER: ~2 swaps then the selector stopped responding; the UI = no
  difference. THE WIRE = clean (the frames accepted, the connection alive
  throughout — the stall = the client's UI).
- BOOT E (the head-block flags revert 1..13 → 2): THE USER: "everything
  remained the same" — the pop-ups + the icons + the re-entry = UNCHANGED
  with the 1..13 = 2 (the hypothesis = refuted). THE ESCALATION = the
  user's call (FINDINGS 11.16; the package = STATE + the fresh incident).
- BOOT F (the complete-fork-shape equip, c2637b3): the full transaction
  delivered (the family-4 pair + the family-0 in-place + the family-3
  roster + the delayed arm), the behavior = unchanged — the ruling's
  contingency (the fold-zero test folds into the veteran hunt).
- BOOT G (the veteran candidates suppressed — flag1682 + the elite-4, the
  Layer-2 /suppress debut): the ship broke + the tower black-screened (the
  swap released the slice-set — the root cause found: the join never
  produces the evaluator-waking push) + the equip's roster REFUSED (the
  family-4 staging wiped the family-3 ladder — the reversed-order bug).
- BOOT H (the fixes A+B, 3a8dd9b): BOTH VERIFIED LIVE — the roster delivers
  in the reversed order (the equip_roster ok) + the tower's slice-set fires
  in the same instant as the in_world (the join's refresh; the boot-G's
  gap = 52.7 s). THE SHIP = back with the five still suppressed (the flag
  theory weakened). THE SUBCLASS EQUIP's display + the pop-ups = STILL the
  same despite the complete accepted delivery. THE ESCALATION = the
  user's call (FINDINGS 11.22).
- BOOT I (the stamp revert, 16105e8): the pop-ups = GONE (the stamp's
  mark-arm was their engine); the UI = unchanged; the dirty bits = STAY SET
  through the equip (the wipe = gone) — the rebuild = never read those
  markers. The stamp chain = only the boot's initial fire.
- BOOT J (the mark-only stamp, 75c3c2b): the pop-ups = still gone; the
  0xB74C provably changed (the harness: 0x55→0xE8) and the chain = STILL
  didn't fire at the equip → the ui_refresh = CONFIRMED not the key — the
  equip's apply never reaches the compare. The 702-push fallback = the
  agreed next.
- BOOT K (the channel census, 6037db4): the answer = the equip's frames DO
  take the WS WIRE (the lane's BAP inference refuted). THE TRAP = the
  ws_wire hook = the hot-path detour — the join's repush went missing, the
  tower black-screened (the boot-G's shape), the user's 801 released it.
  THE SHIP = the flake. PARKED (FINDINGS 12.1): the ws_wire hook = to be
  stripped (the boot L), the equip's kind question = the next lane.
- BOOT L (the ws_wire strip, 7ef2453 + the eqHash gate repair — the deploy
  ~11:30-11:45, FINDINGS 12.10): the server = clean (six domains match,
  build_data cache ok; PID 24840). THE FIRST BOOT ATTEMPT = the content_swap
  fail (the stale 09:36-era header eqHash vs the live gate — the gate compares
  the FULL identity incl. the DB-account configured hash) → the exact C++ port
  (bootL_eqhash_exact.py → 0x8653F8C71F8154E6) re-stamped → clean. THE TOUR =
  the user's, pending at the recording: (i) the tower re-observation (the gate);
  (ii) the halving (/restore 1376..3933, the B-side); (iii) the captures
  (P0-1/P0-2/P1-1).
- BOOT M (the fix-A item-only frame, 377ac5c): the equip's frame = objects=1
  bytes=188 (the wire confirmed); the census moved toward the 801's shape (no
  stamp fire, no fresh-pair evals, the poll alive) — the UI STILL stale. The
  boot-M census lane's re-anchor (12.19): the 12.18 anchors were artifacts; the
  equip = the quiet path (the content-identical frame → no dispatch).
- BOOT N (the serial port + the character-frame revert, 6 commits + b4cbabf):
  the serials LIVE + the walker DISPATCHED + the profile machinery ran (the
  rollback_apply + the full char_test walks) + the stamp never fired + the UI
  STILL stale. The lesson named: the serial model = the general-equipment
  grid's mechanism; the subclass panel = a different surface.
- BOOT O (216ca08 — the synthetic reset→select two-frame): THE WEASEL (the
  boot-13 nonce trap re-hit — the two frames sealed with the SAME nonce).
- BOOT P (7e94a2b the nonce fix): the two frames accepted, no kick — THE UI
  STILL THE SAME. THE FRONT = CUT HERE by the user (the escalation). THE
  COMPLETE FAILED LIST + the honest record = FINDINGS 12.25. THE RULING =
  FINDINGS 12.26 (the two gated surfaces — see "Where we are").

## THE 801 PORT (the landed implementation)

- The codec (middleware/web_service/messages/opcode801.*), the socket_entry_buckets
  domain (the per-entry destination buckets, the 14-row JSON), the
  stage_subclass_selection (the bucket-routed field update + the Attunement
  bundle handling) + the prepare/commit (the staleness-guarded), the web_service
  + the queuez staging branches (the commit → the persist → the restamp → the
  banner refresh), the loader's 6th domain.
- THE CATALOG: the stage-mirror enumeration = the 486 reachable selections (the
  54 per list × 9 lists); the kDefinitionCapacity = 512.
- THE FALLBACK: the apply_ability_buckets = the miss → the list's default
  selection (the roster/banner = the never-fail).

## THE KNOWN GAPS (post-RULING — the 12.26 state)

1. THE SUBCLASS EQUIP'S DISPLAY = THE ACTIVE FRONT (the post-Phase-1 state):
   THE MAP (FINDINGS 12.27): both candidate surfaces = dead for the equip (the
   item-side notify by the writer-level gate proof; the character-side chain by
   the reach map — tiles, not the panel); the panel's only known engine = the
   socket-node sink, unreachable. THE NEW LEAD = D1 (the promised reply
   version — all five boots never carried it; upstream's own comment: without
   it "the Client completes against the old store"). THE FIX (the upstream-
   exact 403, one variable = the delivery contract): the promised
   statusPair.value + the character upsert (8df11ab) + the +1 discipline + the
   clicked-row placement + the ability-bucket arms; the kind hook (built,
   649be1a, NOT deployed) rides as the census. THE BOOT = PENDING THE USER'S
   ARBITRATION (the scope + the two cheap zero-boot lanes: the sink's other
   callers + the mode-4/6 event trigger). THE FALSIFIABLE CLAIM: kind=1 at the
   equip, the transaction completes, the panel switches; the negative = the
   re-bind surface hunt. The pop-ups = DEAD (the stamp revert — the
   deliberate state).
2. THE VETERAN HUNT = the standing rider: NO recap in the last two boots → the
   trigger ∈ 47..953 (388 still-suppressed; the next fold = restore the second
   half → ~194 kept). The range has narrowed 3,887 → 388 across four folds.
3. THE VERB LAYER (parked, ready): the 1820 = VERIFIED live ×2 + the echo rule
   (every verb needs a real effect + push; the generic echo never suffices).
   The consume branches + the serial-model port = the foundation in the tree.
4. THE ENTITY FRONT (scoped, ready): days-scale for the one-entity smoke (the
   lane_entity_scope.md W1-W8 map; the build half = flag-OFF at master).
5. The bucket builder's strictness (parked); the P0-2 batch (untested); the
   P1-1 vendor open (blocked on entity rendering); the 12.18 anchor correction
   (the boot-M lane's re-anchor — recorded in 12.19).

## THE OPCODE FRONT (2026-08-19, the fusion day: B/C/D landed, E = resume-running)

- LANE D (vendor-verb inference) LANDED + VERIFIED: the 1200-1399 band has NO emitter IN THIS
  BUILD (whole-corpus scan, zero immediates, zero result-enum xrefs). The storefront verbs that
  DO exist = 1820/904/1901/801-804/403/601/701/702 + BAP purchased-offers. The 24-entry
  `_result_` enum at 0x141BDCD70 (index 1 = success) names the buy/sell/refund outcomes. The
  ranked boot list: P1-1 VENDOR OPEN = the next BOOT candidate after the swap front (settles
  GAP-4 of s1-datagen-spec: does the storefront round-trip; the fork already answers the right
  shape for free). Deliverable = claims/vendor-verb-inference.md.
- LANE B (svc-11 handler decompile) LANDED SILENT: THE OPCODE-SWITCH HYPOTHESIS DISPROVEN —
  FUN_140DFEC50 is already in the corpus (phase7) and is pure vtable dispatch (BAP type 11 →
  R19 0x141C3D2A8 → txnId correlation); NO centralized u16 opcode compare exists. The opcode
  semantics live in the per-opcode RESPONSE DECODERS. Deliverable = claims/opcode-decoder-map.md.
- LANE C (decoder-registry fill-order) LANDED (death-at-report-back, recovered): THE 237 EMPTY
  DECODER SLOTS ARE STRUCTURALLY IMPOSSIBLE — the registry DAT_14280E3E0 is written by ONE
  factory (FUN_140E75790) from a 71-entry static table at static-init; features cannot fill it.
  Closure of the decoder-runbook's "lazy population" premise. Deliverable =
  claims/decoder-registry-fill-order.md.
- LANE E (upstream codec diff) = LANDED (resume ses_fe6c39a59f): 9 opcodes NAMED by the
  upstream codecs (402 Dismantle / 403 Equip VERIFIED ×6 / 404 Unequip / 406 lock-favorite /
  801 subclass-socket VERIFIED ×6 / 901 vendor purchase w/ the clock rule / 903 socket-plug /
  1820 collections / 1901 shader apply). ALL 9 codec-level portable (zero code changes; the
  response shapes already correct — opcode_routes.cpp MD5-identical mod CRLF); the missing
  piece = the consume() branches + the state effect (the actions layer = census-gated fold-in).
  701/702 (the top boot opcodes, 42×/38×) = unnamed on BOTH trees — stays with lane B's
  R19/0x80528 decompile. THE NEXT = the codec MERGE (16 files, 3-way) + the P1-1 vendor-open
  boot (FINDINGS 12.7). Deliverable = claims/upstream-opcode-codec-diff.md.
- PROCESS CORRECTION (binding): provider errors are NOT a reliable run signal — on ANY errored
  lane, check the disk + opencode.db session_message BEFORE re-spawning (FINDINGS 12.6).

## THE FLAG MAP (the dictionary = audit-clean, the census = approved)

- The four layers (N1's table, N2's machinery, the consumer-trace's apply, N3's
  strings) + the correspondence verdict (the identity at the head, the growing
  per-block shift) + the U4b record bridge (the veteran = Record 190).
- THE DICTIONARY (audit-clean per the reviewer, 2026-08-18): the four spaces
  separated and labeled (the manifest/unlock registry vs the record-state vs the
  bank — the MoT cross proves the record space = definitively severed from the
  unlock registry); the shift map = 26 clean knots + the churn regime
  (21,512/21,569 resolved; the bank = the registry 0..12,299 exactly saturated);
  the record bridge = the objectiveValues bank (+0xA438) keyed by the manifest
  objective index (the 25/25 MoT map; record 190 = objective 1682, seeded
  complete); the string join = 72 HIGH / 50 MEDIUM / 41 NONE (the identity-join
  principle; the order test refuted); the elite-4 = the only bank-reachable
  client-inserted rows inside the veteran's range (bank 340/341/951/952). The
  machine table = RE_output/content/lane_dict_assembly/flag-dictionary.json +
  the deliverable = RE_output/claims/flag-dictionary.md.
- THE VETERAN HUNT (the plan change): the trigger = a flag byte in 47..3933.
  The ranked next test = flag[1682] + the elite-4, superseding the blind
  halving. THE BOOT-A RESOLVE STREAM: NO in-range (47..3933) resolutions — the
  recap's D1-family evaluation did not resolve through the vt+0x6F8 hook this
  boot; the fold direction = pending the user's recap observation (plays →
  veteran ∈ the reverted half; gone → ∈ the kept half). The DB = the staged
  fold (the first 1,549 suppressed, the second half reverted). The next
  zero-boot dictionary lane = the shift-map extension to the package-only
  hashes (the census's resolve-pair join feed).
- THE CENSUS (implemented, commit d0d1c73): five new detours per the spec (resolve
  0x50F4C0, expr_eval 0x548E00, stamp_consume 0xA42FD0, stamp_gate 0xE82AB0,
  ui_refresh 0xE80FC0; expr_vm NOT attached). THE SPEC'S 1.4 OVERLAP: the
  MARKER_POLL target (0xC8F1C0) = the ALREADY-DEPLOYED bit_prim observer — its
  line = renamed to stage=marker_poll (the hook untouched; nothing else consumed
  bit_poll). The batch = 12 specs; the install line carries count=12. The parse
  gates = the install count + the boot-7-shaped walk counts (char_test 8015 /
  flag_test 13874) before reading the new stages.

## Standing rules (unchanged, abbreviated)

Byte-exact settings copies (trap #18). No debuggers (trap #19). One destiny2.exe per
boot (trap #22). Never write the kind0 IV buffer before the game's ~+29s write (trap
#21). Contract-first; one variable per boot; flash-only subagents; main session = the
verification arm; hashes re-verified before every boot (incident.py + the re-hash of
the stamp-on-persist cache/settings). The boot-brief rule (every boot's response =
the purpose/payoff + what it does NOT test; AMENDED 2026-08-19 ~11:5x, FINDINGS
12.11: the launch-time recap = a plain-language 3-line purpose reminder — the main
event + the riders + the explicit non-goals — delivered the moment the user
launches). The deliverable rule + the lane death-safety rule. Findings in
the dated FINDINGS files (the new day = FINDINGS_2026-08-18.md); STATE = the snapshot.

## Milestones

- S0: DONE. S1: DONE. S2: the anchor close-out = DEPLOYED. THE SWAP =
  DONE — the ability swap COMMITS (the item upsert). THE EQUIP'S DISPLAY =
  the parked front: the panel trigger = NAMED (FUN_140a43300 + the trio),
  the two paths = proven disjoint, the equip = ON THE WIRE (the boot-K
  census) — the remaining question = the walker's kind classification (the
  next lane). The pop-ups = DEAD (the stamp revert). The tower = the fix B
  (the join's refresh) + the hot-path trap = the boot-K lesson. The 2100 =
  RETIRED. The flag map = the dictionary audit-clean + the correspondence
  CONFIRMED; the veteran hunt = the halving (the next boot's rider). The
  fork = clean (84acc9c → … → 75c3c2b → 6037db4).
