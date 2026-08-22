# STATE - living snapshot (the single source of "where we are")

Updated: 2026-08-22 ~16:0x.

## HEADLINE: THE TWO-BUG FRONT IS CLOSED. THE BASELINE IS SHIPPABLE.

User-confirmed on the 14:1x boot: weapons render enabled and the character
model loads. Everything base Sunrise does, PLUS a working private server,
PLUS subclass/ability swapping. This is the first shippable baseline.

Since then, same session: the helmet-off bug was opened, narrowed to the
inventory-preview surface only, and PARKED with its contenders ranked (open
item 6). It is cosmetic and does not touch the baseline.

THE CAUSE (FINDINGS 15.9): the blanket flag-bank saturation applied
08-16 18:17 -> 08-18 14:31 during the veteran-recap hunt. `character` went
5 -> ALL 256, `profile` 142 -> ALL 512, and the account bank was re-saturated
to 12,300 AFTER having already been reverted once on 08-16 for causing a
family-4 replication rejection (10.19/10.20).
THE FIX: revert the flags table to the 08-16 curated baseline - account 4,931
/ character 5 ({16,17,18,19,82}) / profile 142 / character_object 177 = 5,255
rows. Nothing else changed; items, cache and eqHash untouched.

WHY IT TOOK SIX DAYS AND AN OUTSIDE ESCALATION: 14.17 declared "THE FLAGS ARE
FULLY EXONERATED" from two probes that BOTH moved flags ON. Under the true
hypothesis (a SET flag breaks it) that is the maximally-broken state, so the
negative was the predicted result, not a refutation. That false exoneration
removed flags from the candidate set for 14.18-14.24, the escalation, and
15.1-15.7 - all of which correctly found the served data healthy, because it
always was. The user's own recollection ("this started during the veteran
hunt") is what reopened it.

## THE DEPLOYED, WORKING STACK

  server exe  babeff605003104c   RE_output/s1_accept/sunrise-server.exe
  client dll  a260ad3016ad6a6d   Game/bin/x64/steam_api64.dll
  cache       e3709166226f4a18   96 details, eqHash 0x1BF4E7F013021C0F
  server      pid 19680, clean boot (all domains match, build_data cache ok)
  flag bank   5,255 rows (curated baseline)
Backups: state.db.bak_preflagrevert_20260822_140016 (the saturated bank - keep,
it is the bisect input), plus .bak_preswap_/.bak_pretransplant_/.bak_preseed_,
cache .bak_presplice_20260822_133844, settings.json.bak_noloadout_20260822_122034.

## OPEN ITEMS (ranked; none block the baseline)

1. THE ATTRIBUTION GAP (do before shipping). The winning revert moved FOUR
   scopes at once; WHICH flag/scope/range is load-bearing is unproven (7,799
   added rows). Scopes are cleanly separable - ~3 boots to isolate (re-saturate
   one scope at a time until it re-breaks). Zero graphics delta, so cheap+safe.
2. THE VETERAN FOLD IS UNDONE by the revert (account rows in 47..953 back to
   522/907), so the recap returns. If that hunt resumes, re-derive the fold
   position from the backup chain. NOTE the hunt itself is what broke the
   game - resume it only with per-scope, reversible, one-variable folds.
3. THE S1 ITEM PICKER (FINDINGS 15.5): the curated upstream loadout was
   replaced at S1I-19 by items chosen from a table walk (consecutive rows
   1966/1967/2027-2029). Cosmetic now that weapons work, but the picker is
   still arbitrary. NOTE 15.5's proof that authored vs nativeDefaults socket
   policy produce IDENTICAL wire bytes - the policy is a no-op, do not revisit.
4. THE SEED ORDERING BUG (FINDINGS 15.4, real and unfixed): the server seeds
   equipment in persistence::initialize BEFORE item definitions are published,
   and publish_item_definitions has its only caller in client/** which the
   server build excludes. Any server settings.json carrying state.characters
   therefore HARD-FAILS the boot. This is why no server config has ever had it.
5. THE SHADER CACHE never persists on this Mac (no MoltenVK/DXMT cache file
   exists). Every launch is fully cold, which is what makes new models
   crash-prone. Fixing it would make all future boots cheaper and safer.
6. THE HELMET BUG = PARKED, COSMETIC, CONTENDERS ROUNDED UP (15.10-15.12).
   The inventory-menu character preview renders helmet-off; the helmet DOES
   render in-world, so it is preview-surface-only and NOT a data fault (the
   same published dataset drives both). Retail D2 applies the helmet toggle to
   BOTH surfaces, so the split matches neither setting value. Ruled out:
   helmet_mode (flipped, no change), render-row data (correct + identical in
   shape to armor that renders), a slot-mapping off-by-one (ground truth:
   helmet=native slot 1, armor 2/4/5/6, slot 3 legitimately unused),
   previewMirrors (3-byte bool policy), overlays/unlockPairs (stubbed for ALL
   items), family-0 vs family-3 divergence (same build_shared, byte-identical
   Appearance block).
   NEXT AND FREE: contender 1 - test whether the whole account-preferences
   record is inert by changing an OBSERVABLE preference (show_fps is cleanest;
   also subtitles_mode / hud_opacity / reticle_color / text_size, all published
   at preferences_encoder.cpp:88-103). If none apply, helmet_mode could never
   have worked and the front becomes "wire up preferences consumption".
   Then: the 792 unmapped bytes sitting directly before previewMirrors + the
   Appearance block's unexplained banks; then unlockPairs; then client RE LAST.
   DO NOT start client RE before contender 1. DO NOT probe this by changing
   equipped items (15.7 cold-compile crash risk, zero information gain).
7. Parked, unchanged: the verb layer; the entity front (lane_entity_scope.md
   W1-W8); the vendor-open boot (P1-1); the bucket builder's strictness.

## CORRECTIONS TO THE RECORD (do not re-derive from the old text)

- 14.17's "flags fully exonerated" = INVALID (one-directional test). Superseded.
- 14.18-14.22's socket-entry-list front = CLOSED. `entryList=0` on gear is the
  CORRECT shape: the working 08-13 kinetic carried entryList=0 too (15.5).
- 14.19's proposed fix (b1) "flip socketEntryContentsResolved false" = UNSOUND;
  instance_encoder's valid() requires it true, so the item would never be
  pushed at all. Never run it.
- 15.2/15.3's "lost authored loadout" root-cause framing = WITHDRAWN by 15.5.
- MAC_VS_PC_DIVERGENCE.md says Sunrise-fork-inventory has no .git; it HAS one
  (170 commits) and is the real history. That doc needs a fix.

## HARD-WON TRAPS (all cost a real failure; do not re-learn)

- DXMT COLD-COMPILE PICK-CRASH (15.7): changing an EQUIPPED item's definition
  changes what the renderer compiles at character pick. Introducing
  never-before-rendered models crashed the game at pick. EVERY loadout
  experiment must state its GRAPHICS DELTA in the boot brief and minimise it.
- THE TRUNCATED LOG (15.6): the build_data identity line is truncated in the
  log FILE by a NUL + garbage. NEVER read expected_eq from the log. Compute it
  with RE_output/scripts/bootL_eqhash_exact.py (validated 2026-08-22: it
  reproduces the live known-good 0x1BF4E7F013021C0F exactly).
- USE /usr/bin/python3 for anything touching sqlite3; the miniconda python on
  this Mac has a broken _sqlite3 (missing _sqlite3_enable_load_extension).
- CACHE SURGERY (15.6, all verified working): details are SORTED by
  definitionIndex (insert in order, never append); itemDetailCount is the 3rd
  count field at offset 36; the eqHash is a u64 at offset 20 and is OUTSIDE the
  checksummed region; the payload checksum is probe_cache_v24.checksum's
  two-segment recipe. Splice + count + checksum + restamp all round-trip cleanly.
- A one-directional negative is not an exoneration. Record the DIRECTION.
- NO SETTINGS WRITE-BACK EXISTS (15.10): account settings are published
  one-way from settings.json (account_encoder.cpp:74); the DB stores none.
  Any in-game settings change is local UI state that cannot survive a boot.

## DEPLOY RULES (unchanged, still binding)

Kill the old server first. Restamp build_data identity after any exe rebuild
(RE_scripts/restamp_build_data.py, offsets 12/16). Recompute the eqHash after
any change to equipped items/levels/policy/plugs (flags do NOT feed it).
Content JSONs override cache at boot. Verify observer call volume BEFORE
deploying a hook. Verify THE WIRE changed before accepting a negative. One
destiny2.exe per boot. Byte-exact settings copies. No debuggers. Restart the
server before blaming state - session age is a real artifact class.
THE BOOT BRIEF RULE: every boot's response states purpose/payoff, the
falsifiable claim, what it does NOT test, and now also its GRAPHICS DELTA.

## MAC PORT ESSENTIALS (closed 2026-08-21, stable)

Client rides Game/bin/x64/steam_api64.dll in a dedicated Whisky bottle
("Sunrise"). Server is a MinGW/llvm-mingw cross-compile run under GPTK wine 7.7
in its own prefix, launched by mac-port/launch-server-macos.sh. Hybrid
architecture: config-manifest GET + SignOn answered in-process by the client
DLL; BAP/discovery/admin external on 30975/3074/3075/8443/8099. Wine on macOS
can never complete inbound TLS - that is permanent and is why the hybrid exists.
Build the server with `-- -j 8` (the serial build looks hung at ~90 min).
Full detail: MAC_VS_PC_DIVERGENCE.md.

## MILESTONES

S0 DONE. S1 DONE. S2 anchor close-out DEPLOYED. THE SWAP FRONT DONE (ability
swap commits; subclass equip panel updates live). THE MAC PORT DONE. THE
TWO-BUG FRONT DONE (2026-08-22) - weapons armed, character model loads.
=> FIRST SHIPPABLE BASELINE. Next natural fronts: the attribution bisect,
then the entity front (static enemies) or the vendor-open boot.
