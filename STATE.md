# STATE - living snapshot (the single source of "where we are")

Updated: 2026-08-22 ~19:2x.

## HEADLINE: SHIPPABLE BASELINE + PUBLIC RELEASE COMPLETE

The Season-of-Arrivals fork boots and plays solo end to end on the private
server (destination loads, full inventory/equipment persistence, subclass +
ability swapping, preferences publishing). The documentation/community layer
is DONE and PUBLIC: aslaniar/Sunrise carries a complete docs set for building,
running, configuring and troubleshooting the server on Windows/Linux/macOS;
the unlock-index data package is published as its own CC0 repo; the knowledge
dump circulated via Discord as a PDF. Community-publication arc closed
(FINDINGS 18.1).

## THE DEPLOYED, WORKING STACK (verified 2026-08-22 ~19:2x)

  server exe  babeff605003104c   RE_output/s1_accept/sunrise-server.exe (pid 26388)
  client dll  a260ad3016ad6a6d   Game/bin/x64/steam_api64.dll
  cache       eqHash is LIVE state - compute, never assume (16.3); details=96;
              stored == computed == 0xE8683B305DA99CD7 at last verify
  flag bank   5,255 rows (curated baseline; account 4,931 / character 5 /
              profile 142 / char_obj 177) - saturation breaks the client
  configs     helmet_mode/text_size/reticle_color all at upstream defaults

Backups: state.db.bak_preflagrevert_20260822_140016 (saturated bank, bisect
input), .bak_preswap_/.bak_pretransplant_/.bak_preseed_, cache .bak_presplice_,
settings.json.bak_noloadout_, plus Sunrise-fork/.git_backup_20260822.

## OPEN ITEMS (ranked; none block solo play)

1. **Multiplayer P1 - bind-address rework** (code half of the shipped docs):
   five listeners bind loopback only (admin_http.cpp:481, discovery_listener
   :234/:268, https_listener.cpp:578, bap_listener.cpp) + TLS cert subject
   CN=127.0.0.1 (tls.cpp:17). Exit condition: remote client log shows clean
   domain loads.
2. **Guest accounts (P2)**: one global State / one initialAccount
   (runtime.h), seed_account_id() writes everything under one SOID
   (persistence.cpp:152). Schema already keys player tables by account_id -
   needs per-peer State views + per-account soid ranges, not schema rework.
3. **Release engineering**: adapt .github/workflows/build.yml to attach
   sunrise-server.exe per tagged release (+ checksums; NO pdb). Note:
   fresh installs self-generate caches; only upgraders need identity restamp
   (offsets 12/16; public tool now exists: scripts/restamp_build_data.py).
4. **Attribution bisect**: which saturated flag scope broke rendering (~3
   boots, zero graphics delta). The bisect input is preserved
   (.bak_preflagrevert). Closes OPEN-item attribution gap from 15.9.
5. **Entity front W1-W8** (static enemies): emission code deployed, flag OFF
   (`world_population`). W1 = settings-only boot; W2 receive-cluster observer;
   W3 live ground-truth capture. Prerequisite for multiplayer P4 peer
   visibility. Full ladder: RE_output/claims/lane_entity_scope.md.
6. **Upstream reconcile**: fork is ~115 commits behind stanuwu/Sunrise:master;
   policy pending. Divergence intentional until then.
7. **Research repo publish decision**: origin still points at tigercli.git
   (wrong project). Contents worth publishing someday: findings/, claims/
   (204 files incl. deadorbit-pipeline.md), RE_scripts tools.
8. **Shader-cache persistence** (Mac QoL): no MoltenVK/DXMT cache file
   persists; every launch compiles cold; new equipped models crash-prone at
   pick. Fixing makes all boots cheaper.
9. **Helmet front: RESOLVED-PARKED** (16.4): no consumer wired in this build
   for helmet visibility anywhere; control is vestigial; always-on-world /
   always-off-preview is DEFAULT behavior. Fixing = client feature build.
10. Parked unchanged: verb layer; vendor storefront loop; bucket-builder
    strictness; ForcedDestination wiring (complex multi-bubble destinations).

## WHAT IS PUBLIC VS INTERNAL

PUBLIC: github.com/aslaniar/Sunrise (source master @60a3fdd-line + six docs +
SERVER-SIDE-SPEC.md rev 2026-08-22 + scripts/{launch-server-macos.sh,
server-settings.template.json, restamp_build_data.py}); d2-unlock-index-
tables repo (CC0); knowledge dump as PDF via Discord.
INTERNAL ONLY: knowledge dump md/pdf sources + handbook digest & text
(RE_output/{community,dumps}), claims/ (204 files), RE_scripts tooling,
RE_output runtime artifacts (never ship: game-derived caches/DBs, live
tokens, oo2core proprietary DLL). Research repo origin misdirected to
tigercli.git - fix before ever publishing it.

## CORRECTIONS TO THE RECORD (supersede older text; do not re-derive)

- 14.17 "flags fully exonerated" INVALID (one-directional test) - superseded
  by 15.8/15.9; lesson binding: record the DIRECTION of every negative test.
- 15.2 "silently seeded nothing" WITHDRAWN -> 15.4: server REFUSES to boot
  with state.characters present (ordering defect; publisher is client-only).
- MAC_VS_PC_DIVERGENCE section 2 corrected twice 2026-08-22: ONE repository
  (RE_build/Sunrise-fork) with linked worktrees; inventory tree = worktree of
  it; publish final state = master-only line (references reverted).
- SocketPolicy authored==nativeDefaults byte-identical on wire (15.5);
  entryList=0 on gear correct (refuted x4); no equippability flag exists in
  the family-4 object (greyed = client derivation).
- helmetMode has NO consumer in this build (16.2-16.4): replicated record IS
  consumed (reticle/text probes applied) but helmet field dead everywhere;
  seed-version gates protect only motion-blur/grain/chromatic-aberration.
- Preferences are one-way (no write-back path); in-game changes die at boot.
- Deadorbit: local/embedded HTTP branch does NOT serve ticket_drop (op=1 vs
  op=2 union mismatch); external-mode URL rewrite intercepts it fine (dump
  section 12; tokens redacted).

## HARD-WON TRAPS (each cost a real failure; do not re-learn)

- DXMT cold-compile pick-crash: changing an EQUIPPED item's definition forces
  cold shader compiles at pick (no persistent shader cache on macOS) ->
  silent death, no SEH/minidump. State every experiment's GRAPHICS DELTA.
- Truncated log trap: build_data identity warn prints expected_eq SHORT with
  NUL+garbage mid-line. NEVER read expected values from logs; compute
  (RE_output/scripts/bootL_eqhash_exact.py, validated).
- eqHash is LIVE state: ability/equipment commits drift it; the server
  self-restamps offset 20 itself. Compute before comparing; never assume a
  recorded value.
- Use /usr/bin/python3 for sqlite3 work (miniconda python has broken _sqlite3).
- Cache surgery: details SORTED by definitionIndex; itemDetailCount u32 @36;
  payload checksum two-segment recipe (probe_cache_v24.checksum); eqHash @20
  OUTSIDE checksummed region.
- One-directional negative != exoneration. Record the test DIRECTION.
- NO settings write-back exists: published once from settings.json; DB stores
  none; in-game changes cannot survive a boot.
- Git EPERM curse (hit twice: research repo + source repo .git instances):
  reads via cat work, git gets EPERM on .git/config. FIX: copy .git to
  scratch, verify git reads it there, swap fresh copy into place at identical
  path (linked-worktree gitdir pointers resolve by path). Backups kept.
  Root cause never diagnosed - if instance #3 appears, budget a real
  diagnosis session instead of swap-by-pattern.
- Flag banks must stay CURATED: blanket saturation -> client discards part of
  the family-4 join snapshot (greyed weapons/unresolved model) while all
  server-side checks stay green.

## DEPLOY RULES (binding)

Kill old server first. Restamp build_data identity after any exe rebuild
(offsets 12/16; public script scripts/restamp_build_data.py in the fork).
Recompute eqHash after equipped items/levels/policy/plugs changes (flags do
NOT feed it). Content JSONs override cache at boot. Verify observer call
volume BEFORE deploying a hook. Verify THE WIRE changed before accepting a
negative. One destiny2.exe per boot. Byte-exact settings copies. No
debuggers. Restart the server before blaming state - session age is a real
artifact class. BOOT BRIEF RULE: purpose/payoff, falsifiable claim, what it
does NOT test, GRAPHICS DELTA.

## MAC PORT ESSENTIALS (stable)

Client rides Game/bin/x64/steam_api64.dll in Whisky bottle "Sunrise"
(DllOverrides winemetal=b, d3d10core=n,b per-app required - see public
docs/MACOS-CLIENT-SETUP.md). Server = llvm-mingw cross-compile under GPTK
wine 7.7, own prefix, mac-port/launch-server-macos.sh. Hybrid architecture:
config-manifest GET + SignOn answered IN-PROCESS by the client DLL (wine
inbound TLS impossible - permanent); BAP/discovery/admin external on
30975/3074/3075/8443/8099; gameplay ~30976 UDP even ports. Build -- -j 8.

## MILESTONES

S0 standalone-server extraction DONE (+Mac port). S1 persistence +
content-driven datagen DONE (+swap front). S2 static world population
STARTED (scoping done, emission deployed flag-off, W1-W8 ladder ready).
S3 combat / S4 missions / S5+ patrol-events-raids NOT STARTED (handbook +
playbook now exist externally; estimates revised down for early missions).
TWO-BUG FRONT DONE (2026-08-22) => FIRST SHIPPABLE BASELINE.
COMMUNITY PUBLICATION ARC DONE (2026-08-22, FINDINGS 18.1): docs layer,
spec, unlock tables, dump PDF all out the door.
Next natural fronts: multiplayer P1 bind-address -> guest accounts; or
entity front W1-W3 (feeds P4 later); attribution bisect as cheap warm-up.
