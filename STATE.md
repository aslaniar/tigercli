# STATE - living snapshot (the single source of "where we are")

Updated: 2026-08-22 ~23:3x.

## HEADLINE: SHIPPABLE BASELINE + PUBLIC RELEASE COMPLETE;
## OBSERVABILITY PROGRAM (5 LANES) IN FLIGHT

The Season-of-Arrivals fork boots and plays solo end to end on the private
server (destination loads, full inventory/equipment persistence, subclass +
ability swapping, preferences publishing). Docs/community layer is DONE and
PUBLIC. Since then: an MSVC build front closed (18.3, CI green), the vendor
front was scoped from the manifest (18.2), and a five-lane OBSERVABILITY
PROGRAM was dispatched to build the instruments the multiplayer saga needs.

## THE DEPLOYED, WORKING STACK (verified 2026-08-22 ~23:1x)

  server exe  04a3a1caf9fdc923   RE_output/s1_accept/sunrise-server.exe
              (Lane C dashboard + /events + seq ring + bind_address,
               + collector fixes: 3 compile breaks, SO_REUSEADDR on admin
               AND https, dashboard filter, /flags bounds clamp)
  client dll  67f3d0531a543b91   Game/bin/x64/steam_api64.dll
              (Lane E protocol tape, boot-validated; item_gate uninstalled)
  cache       build_data ts=0x6A8A90A5 size=0x02C4F000 (restamped per rebuild)
              eqHash 0xA8E1DA67DFA2118F - DRIFTED from 0xE8683B305DA99CD7 by
              the 22:46 play session (LIVE state; server self-restamps @20)
  flag bank   5,255 rows curated (account 4,931 / char 5 / profile 142 /
              char_obj 177); runtime bank lengths 12,300 / 256 / 512 / 4,096
  invariants  17/17 GREEN (RE_output/scripts/check_invariants.py)
  client log  core.logging.levels.client = "info" (retail + tape visible;
              item_gate still installed -> ~114k lines/boot)
  dashboard   http://127.0.0.1:8099/  (survives client death - proven)
  PRIOR ARTIFACTS backed up as *.bak_preobs_20260822_224433

## THE OBSERVABILITY PROGRAM - ALL 5 LANES LANDED + VERIFIED (2026-08-22)

Purpose: make system state legible to the USER, not only to an AI reading
8 MB of log; and a prerequisite for multiplayer, where nobody can read races
out of a static file. All five deliverables verified by the main session
against disk, not accepted from report-backs.

  A cockpit        DONE. lane_cockpit.md. Tools: live_console.py (Mac paths,
                   item_gate suppressed), live_client/server_tail.sh,
                   retail_view.py.
  B queryable boot DONE + VERIFIED. lane_boot_record.md. boot_diff(A4,B4)
                   names EXACTLY world_population_carrier 7->8, nothing
                   spurious; boot_diff(A4,R4) CLEAN. Records in
                   RE_output/boots/.
  C dashboard      DONE + FIXED. lane_dashboard.md. Landed 3 compile breaks
                   and 2 runtime bugs (below); all fixed and verified.
  D invariants     DONE + VERIFIED. lane_invariants.md. 17/17 green live;
                   RED at 12,549 on the saturated backup with char_obj
                   correctly staying green.
  E protocol tape  DONE + VERIFIED ON THE WIRE. lane_protocol_tape.md.

THE VALIDATION BOOT (2026-08-22 ~22:46, all four gates PASSED):
- Dashboard served during the boot AND after the client was force-quit.
- 114 tape=1 rows; predicted sign-on sequence reproduced exactly
  (svc=123 queue_update on PRIMARY session=0, then svc=9 activity_message
  on FAH session=1). Every kind named, zero unknowns, max type=54 inside
  the 0..58 registry.
- CROSS-CHECK: server and client type histograms IDENTICAL
  (58 auth_sense / 23 global_activity_state / 12x10 membership_replication /
  1 each bubble_host_table, join_result, entity_slot_notification), counts
  94 == 94, sizes differ by a CONSTANT 28 bytes (len=601 <-> size=573;
  len=234 <-> size=206) = the BAP frame header the server counts and the
  client dispatcher does not. => the handbook's p46 envelope layout is now
  INDEPENDENTLY CONFIRMED AGAINST LIVE TRAFFIC.
- 352 ev=retail lines returned at client=info.
- 115,572-row two-sided record captured (closes Lane B's last open item).

## OPEN ITEMS (ranked; none block solo play)

1. ~~item_gate source fix~~ **CLOSED 23:2x**: install commented out
   (client_hook_activation.cpp, 6a63d9a treatment); DLL rebuilt + deployed
   (steam_api64 67f3d0531a543b91). Runtime confirmation = the NEXT client
   boot (expect the client log to fall from ~114k lines to ~1.2k with retail
   + tape intact). The f4dump diagnostics in family4_object_staging /
   roster_snapshot are the SAME closed-front class ("strip when the
   weapons/model front closes", 261 rows/boot) - not yet retired.
2. **Multiplayer P1 - bind-address rework**: five listeners bind loopback only
   (admin_http.cpp:481, discovery_listener :234/:268, https_listener.cpp:578,
   bap_listener.cpp) + TLS cert CN=127.0.0.1 (tls.cpp:17). Lane C is adding
   the admin-side bind_address as a rehearsal; P1 should reuse its key + fold
   helper (no shared host_address() helper exists yet - extract one).
3. **Guest accounts (P2)**: one global State / one initialAccount (runtime.h),
   seed_account_id() writes everything under one SOID (persistence.cpp:152).
   Schema already keys player tables by account_id - needs per-peer State
   views + per-account soid ranges, not schema rework.
4. **Release engineering**: adapt .github/workflows/build.yml to attach
   sunrise-server.exe per tagged release (+ checksums; NO pdb).
5. **Attribution bisect**: which saturated flag scope broke rendering (~3
   boots, zero graphics delta). Input preserved (.bak_preflagrevert, verified
   12,549 rows). Closes the 15.9 attribution gap.
6. **Entity front W1-W8** (static enemies): emission deployed, flag OFF
   (`world_population`). Prerequisite for multiplayer P4 peer visibility.
   Ladder: RE_output/claims/lane_entity_scope.md.
7. **Upstream reconcile**: fresh fetch 2026-08-22 22:0x = **45 behind, 98
   ahead** of stanuwu/Sunrise:master (upstream tip 0188841, 2026-08-21).
   Policy pending; divergence intentional until then.
8. ~~/flags response-budget overflow~~ **CLOSED 23:2x**: it was an
   out-of-bounds WRITE, not just an over-read - (kResponseCapacity - used)
   underflows as size_t once snprintf's would-be length pushes `used` past
   the buffer. Now clamped with a reserved tail and a "truncated" flag.
   Verified with a 1 KiB test build against the real 4 KB response: stayed
   in bounds, stayed VALID JSON, reported truncated=true + true run_count,
   server survived.
9. **Research repo publish decision**: origin still points at tigercli.git
   (wrong project).
10. **Shader-cache persistence** (Mac QoL): no MoltenVK/DXMT cache persists;
    every launch compiles cold; new equipped models crash-prone at pick.
11. Helmet front: RESOLVED-PARKED (16.4) - control is vestigial, no consumer.
12. Parked unchanged: verb layer; vendor storefront loop (scoped 18.2);
    bucket-builder strictness; ForcedDestination wiring.

## HAZARD: THE SHARED WORKTREE IS DIRTY (lanes C and E commit into it)

RE_build/Sunrise-fork-inventory (branch `integration`) carries UNCOMMITTED
work from 2026-08-21 ~22:15 that predates this program: CMakeLists.txt,
Sunrise.vcxproj, client_hook_activation.cpp, character_record_encoder.{cpp,h},
family4_object_staging.cpp (+40), roster_snapshot.cpp (+47), and the ENTIRE
UNTRACKED src/client/hooks/item_gate/ directory. A blanket `git add -A` in
that worktree sweeps ~100 lines of unrelated S2/datagen work into an
observability commit. Lane C confirmed it commits only its own files and does
NOT touch CMakeLists (headers only). Owner decision still outstanding: is the
08-21 work still wanted, or superseded by the 18.3 MSVC line?

## WHAT IS PUBLIC VS INTERNAL

PUBLIC: github.com/aslaniar/Sunrise, master @ **c30a72d** (docs set +
SERVER-SIDE-SPEC.md rev 2026-08-22 + scripts/{launch-server-macos.sh,
server-settings.template.json, restamp_build_data.py}; the 18.3 MSVC line:
windns_compat shipped in-tree, sln builds both targets, egress signatures
aligned to the Windows SDK; CI green). d2-unlock-index-tables repo (CC0).
Knowledge dump as PDF via Discord.
INTERNAL ONLY: knowledge dump md/pdf sources + handbook digest & text
(RE_output/{community,dumps}), claims/ (380+ files), RE_scripts tooling,
RE_output runtime artifacts (never ship: game-derived caches/DBs, live
tokens, oo2core proprietary DLL).

## CORRECTIONS TO THE RECORD (supersede older text; do not re-derive)

- UPSTREAM DELTA: STATE's earlier "~115 commits behind" was WRONG, and so was
  an intermediate "2 behind" read (taken from a STALE remote-tracking ref).
  Fresh fetch 2026-08-22 22:0x: **45 behind, 98 ahead**. Always fetch before
  quoting a divergence count.
- "Silencing item_gate leaves ~1-2k readable lines" is WRONG: retail is
  Level::info too, so client=warn leaves only the warn/error floor (~0-100
  lines this boot: 2 warn, 0 error). Corrected by Lane A.
- The BAP service names were NOT missing: src/middleware/bap/frame.h already
  carries RequestService/ResponseService/NotificationService enums, and Lane E
  verified they are NUMERICALLY IDENTICAL to the handbook registry (27/24/2,
  programmatic cross-check). They were simply never wired into the log line.
- handle_message_observer's `type=%u` column is the BAP SERVICE NUMBER, not
  the activity-message wire type (Lane E, verified against two incidents).
- 14.17 "flags fully exonerated" INVALID (one-directional test) - superseded
  by 15.8/15.9.
- 15.2 "silently seeded nothing" WITHDRAWN -> 15.4: server REFUSES to boot
  with state.characters present (ordering defect; publisher is client-only).
- ONE repository (RE_build/Sunrise-fork) with linked worktrees; inventory tree
  = worktree of it.
- SocketPolicy authored==nativeDefaults byte-identical on wire (15.5);
  entryList=0 on gear correct (refuted x4); no equippability flag exists in
  the family-4 object (greyed = client derivation).
- helmetMode has NO consumer in this build (16.2-16.4).
- Preferences are one-way (no write-back path); in-game changes die at boot.
- Deadorbit: local/embedded HTTP branch does NOT serve ticket_drop; external-
  mode URL rewrite intercepts it fine.

## HARD-WON TRAPS (each cost a real failure; do not re-learn)

- DXMT cold-compile pick-crash: changing an EQUIPPED item's definition forces
  cold shader compiles at pick (no persistent shader cache on macOS) ->
  silent death, no SEH/minidump. State every experiment's GRAPHICS DELTA.
- Truncated log trap: build_data identity warn prints expected_eq SHORT with
  NUL+garbage mid-line. NEVER read expected values from logs; compute
  (RE_output/scripts/bootL_eqhash_exact.py, validated).
- eqHash is LIVE state: ability/equipment commits drift it; the server
  self-restamps offset 20 itself. Compute before comparing.
- CROSS-PROCESS ANCHOR TRAP (new, Lane B): same-name core events on the two
  sides are NOT the same real moment - the client's core lines come from the
  in-process DLL, the server's from the standalone wine server that booted
  minutes earlier (observed disagreement ~5.3 s). Only WIRE events (transport
  accept / bap) are true shared moments. merge_logs.py's PRIMARY anchor has
  ZERO client-side hits on every capture currently on disk.
- SNAPSHOT IS A VALUE TYPE (new, Lane C): core::log::snapshot::Snapshot is
  std::array<Entry,128> (~134 KB) returned BY VALUE. Enlarging the ring to
  4096 makes it ~4.3 MB in any caller's frame - the admin thread's default
  1 MB stack cannot hold it. Gate capacity per-target and raise the thread
  stack before enlarging.
- STALE CONFIG DECOY (new, Lane C): RE_output/s1_accept/settings.json (root
  level, https_port 443, Windows paths) is IGNORED. The live file is
  RE_output/s1_accept/Sunrise/settings.json. Do not read the decoy as config.
- Use /usr/bin/python3 for sqlite3 work (miniconda python has broken _sqlite3).
  Sandbox also cannot open state.db.bak_* in place - copy to scratch first.
- Cache surgery: details SORTED by definitionIndex; itemDetailCount u32 @36;
  payload checksum two-segment recipe; eqHash @20 OUTSIDE checksummed region.
- One-directional negative != exoneration. Record the test DIRECTION.
- NO settings write-back exists: published once from settings.json; in-game
  changes cannot survive a boot.
- Git EPERM curse (hit twice): reads via cat work, git gets EPERM on
  .git/config. FIX: copy .git to scratch, verify, swap fresh copy into place
  at identical path. If instance #3 appears, budget a real diagnosis session.
- ADMIN PORT / TIME_WAIT (new, 2026-08-22): the dashboard polls 8099 every
  second, so its own just-closed connections sit in TIME_WAIT and a quick
  server restart could not rebind - and admin bind failure is FATAL
  (ev=admin result=fail reason=bind -> initialize stage=admin result=fail ->
  server exits). FIXED by setting SO_REUSEADDR on the admin listener,
  matching bap_listener.cpp. Verified with 9 TIME_WAIT sockets present at
  relaunch. https_listener now carries the same option (the client holds
  8443 for a whole session and would fail identically once it has live
  connections; not reproducible on THIS Mac because the hybrid architecture
  answers config/SignOn in-process so 8443 never sees client traffic).
  discovery_listener is UDP - TIME_WAIT is TCP-only, so it is not exposed.
- Flag banks must stay CURATED: blanket saturation -> client discards part of
  the family-4 join snapshot while all server-side checks stay green.

## DEPLOY RULES (binding)

Kill old server first. Restamp build_data identity after any exe rebuild
(offsets 12/16; scripts/restamp_build_data.py). Recompute eqHash after
equipped items/levels/policy/plugs changes (flags do NOT feed it). Content
JSONs override cache at boot. Verify observer call volume BEFORE deploying a
hook. Verify THE WIRE changed before accepting a negative. One destiny2.exe
per boot. Byte-exact settings copies. No debuggers. Restart the server before
blaming state. BOOT BRIEF RULE: purpose/payoff, falsifiable claim, what it
does NOT test, GRAPHICS DELTA. NEW: run check_invariants.py before and after
a boot - it seeds the monotonic baselines and catches the saturation class.

## MAC PORT ESSENTIALS (stable)

Client rides Game/bin/x64/steam_api64.dll in Whisky bottle "Sunrise"
(DllOverrides winemetal=b, d3d10core=n,b per-app required). Server =
llvm-mingw cross-compile under GPTK wine 7.7, own prefix,
mac-port/launch-server-macos.sh. Hybrid architecture: config-manifest GET +
SignOn answered IN-PROCESS by the client DLL (wine inbound TLS impossible -
permanent); BAP/discovery/admin external on 30975/3074/3075/8443/8099;
gameplay ~30976 UDP even ports. Build -- -j 8.

## MILESTONES

S0 standalone-server extraction DONE (+Mac port). S1 persistence +
content-driven datagen DONE (+swap front). S2 static world population
STARTED (scoping done, emission deployed flag-off, W1-W8 ladder ready).
S3 combat / S4 missions / S5+ NOT STARTED (handbook + playbook now exist
externally; estimates revised down for early missions).
TWO-BUG FRONT DONE (2026-08-22) => FIRST SHIPPABLE BASELINE.
COMMUNITY PUBLICATION ARC DONE (2026-08-22, FINDINGS 18.1).
MSVC BUILD FRONT DONE (2026-08-22, FINDINGS 18.3, CI green on c30a72d).
OBSERVABILITY PROGRAM IN FLIGHT (2026-08-22 ~21:3x, lanes A-E; D verified).
Next natural fronts: finish A-E -> multiplayer P1 bind-address -> guest
accounts; entity front W1-W3; attribution bisect as a cheap warm-up.
