# MAC vs PC — architecture divergence reference

Single source of truth for everything that differs between the Windows/PC
rig setup and the macOS port, so a fix made on one side doesn't get applied
blindly to the other, and so neither side's tooling gets mistaken for the
other's. Read this before touching either tree. Written 2026-08-21 at the
end of the Mac-port-completion session; keep it updated as things change.

## 1. Source code changes — apply to BOTH platforms, keep the trees in sync

Everything in this section is a genuine bug fix, not a Mac-specific hack.
They were *found* via Mac testing (because the hybrid/external architecture
exercises code paths the PC rig's real-TLS setup never hits), but the code
itself has no `#ifdef MAC` or platform branching — it's the same fix either
way. All six are committed to the git-tracked `RE_build/Sunrise-fork` repo
(the canonical history both platforms should build from):

| Commit | File | What |
|---|---|---|
| `65df13f` | `src/client/hooks/network/http/http_descriptor_route.cpp` | Removed the external-mode branch that always forwarded HTTP traffic over the network without ever trying the in-process consumer first. |
| `9ba95c8` + `701c7d5` | `src/server/runtime/server_runtime.cpp` | Gated the client's own local BAP/gameplay listener bind behind `!external_server::enabled()` — it was binding unconditionally, and on this Mac a second bind on an already-owned port silently *succeeded* instead of failing, so the client was talking to itself. |
| `3935ca7` | `src/client/hooks/network/content_config/request/content_config_get_replacement.cpp` | The manifest-GET routing check (`is_manifest_url`) correctly recognized the external URL form, but the encode gate right below it still used the narrower `is_local_url` (embedded-marker only), so hybrid-mode manifest fetches fell through to an empty response instead of the real one. |
| `b84f8de` | `src/state/runtime/state_runtime.cpp` | `signOn.encryptionKey`/`authenticationKey` are now derived deterministically from the shared `bootstrap_token` (HMAC-SHA256, domain-separated labels) instead of pure `BCryptGenRandom`. Needed the moment SignOn is answered by a *different process* than the one running BAP (i.e. always, under the hybrid architecture) — two independently-random processes can never agree on a key neither one transmitted. `bap.nonce`/`sessionKey`/`envelopeIv` stay genuinely random per boot; only the two wrap keys had to become deterministic. |
| `6a63d9a` | `src/client/runtime/client_hook_activation.cpp` | Stopped installing the `ability_gate`/`gate_trace` research hooks by default (see §4 — this one's closer to a judgment call than the others; see the caveat there). |

**Whether the PC rig ever needs these**: only the first four matter if/when
the PC rig ever runs in `external_server` mode with something *other* than a
real, working TLS/SChannel path — which historically it hasn't needed,
since PC's wine-equivalent (native Windows) has a working SChannel. If PC
stays on real-TLS external mode (or embedded/in-process mode) forever, these
four fixes are dormant but harmless there. They do not change embedded-mode
behavior at all (embedded mode never took the branches these fixes touch).

## 2. Build system — completely separate toolchains, do not conflate

| | PC | Mac |
|---|---|---|
| Toolchain | MSVC / Visual Studio | llvm-mingw (`x86_64-w64-mingw32-clang`/`clang++`), cross-compiled on macOS |
| Project files | `Sunrise.sln`, `Sunrise/Sunrise.vcxproj` (client), `Sunrise/sunrise-server.vcxproj` (standalone server) | `RE_build/Sunrise-fork-inventory/Sunrise/CMakeLists.txt` — hand-written, not generated from the `.vcxproj` files |
| Repo | `RE_build/Sunrise-fork` (git-tracked, canonical) | `RE_build/Sunrise-fork-inventory` (**HAS its own `.git`, 170 commits — corrected 2026-08-22**; it, not `Sunrise-fork`, carries the real equip-front history. `Sunrise-fork` has 22 commits and its HEAD lacks the S2/equip work) |
| Server target | Exists natively in the `.vcxproj` | **Net-new as of today.** No standalone-server CMake target existed before this session; the previously-running `sunrise-server.exe` on this Mac was a pre-built Windows/MSVC binary with no Mac build path at all. |

**The CMakeLists.txt file list is hand-derived, not authoritative.** It was
built by taking the client DLL's own (proven, 565-file) list, excluding
`src/client/**`, `src/core/ui/**`, `src/core/runtime/**` (core_runtime.cpp —
the DLL's own `dllmain`-driven init sequence, wrong for a standalone `main()`),
`src/server/ui/**`, `src/steam/**` (the client's Steam-API-emulation surface,
meaningless for a headless server), `vendor/detours/**`, `vendor/imgui/**`,
plus adding ~15 server-exclusive files (`https_listener.cpp`, `tls.cpp`,
`persistence.cpp` + its test-mode siblings, `server_main.cpp`,
`discovery_listener.cpp`, `admin_http.cpp`, `content_loader.cpp`,
`vendor/sqlite/sqlite3.c`). **If a new file gets added anywhere in the
shared `src/server/**`/`src/state/**`/`src/middleware/**` trees on the PC
side, the Mac CMakeLists.txt needs the same file added by hand** or the
Mac build will fail to link (missing symbol) the next time someone rebuilds
there. There is no automation for this yet.

Two Mac-only build quirks, neither applicable to MSVC:
- `project(SunrisePort LANGUAGES CXX C RC)` needs the **C** language
  explicitly for `vendor/sqlite/sqlite3.c` to compile at all (CMake silently
  skipped it otherwise, with zero warning, and the link failed with dozens
  of missing `sqlite3_*` symbols).
- `target_link_options(sunrise-server ... -Wl,--stack,8388608)` — the
  client DLL rides `destiny2.exe`'s own generous host-process stack when
  loaded into it; the standalone Mac exe only gets whatever the linker
  defaults to, which stack-overflowed inside `state::initialize()`'s large
  stack-allocated `State` struct. MSVC's own default for the PC
  `sunrise-server.exe` has apparently always been sufficient — no equivalent
  setting exists in `sunrise-server.vcxproj`.

**Source-control debt to watch** (note: `Sunrise-fork-inventory` DOES have git —
see §2's table, corrected 2026-08-22): today's five (now six, see §1) source
fixes were iterated live in `Sunrise-fork-inventory` and had to be manually
copied + committed to `Sunrise-fork` afterward — one (`state_runtime.cpp`)
was missed until the very end of the session and nearly shipped only in the
untracked tree. **Habit going forward: every source edit made in
`Sunrise-fork-inventory` gets copied to `Sunrise-fork` and committed in the
same sitting, not batched for later.**

## 3. Runtime / launch environment — entirely Mac-specific, no PC equivalent

None of this exists or is meaningful on PC (native Windows has no wine
layer at all):

- **Client** runs inside a dedicated Whisky bottle named `Sunrise`
  (`whisky create Sunrise`), not the old hand-rolled
  `mac-port/launch-sunrise-macos.sh` script — that script's manually
  assembled wine environment was missing ~15 env vars Whisky's own launcher
  sets automatically (`WINEMSYNC` instead of just `WINEESYNC`, several
  `WINE_MACH_PORT_*`/`WINE_DISABLE_NTDLL_THREAD_REGS` Darwin-specific tuning
  vars) plus a per-app `DllOverrides` registry entry (`winemetal=b`,
  `d3d10core=n,b`) that Whisky auto-applies and the script never replicated.
  That gap was the actual cause of the original graphics-init crash, not a
  Metal/macOS-version regression as first suspected.
- **Server** runs under the separate GPTK cask's wine 7.7 (not Whisky), in
  its own dedicated prefix (`~/Library/Application Support/SunriseServer/pfx`),
  launched via `mac-port/launch-server-macos.sh`. This is deliberate — GPTK
  7.7 gets furthest of any tested engine on the TLS/SChannel front
  (`AcquireCredentialsHandle` succeeds there; Whisky's wine-11 fails
  credentials outright), and since it's a genuinely separate OS process from
  the client, **client and server do not need to share a wine engine or
  bottle at all** — they only need to agree on TCP ports (see §4).
- `launchctl setenv MTL_HUD_ENABLED 1` (Metal HUD / FPS counter) and
  `launchctl setenv MVK_CONFIG_SHADER_CACHE_PATH ...` (MoltenVK shader-cache
  persistence) are machine-wide, session-scoped environment variables.
  **Whisky.app must be fully quit and relaunched after either is set** — env
  vars are inherited at process launch, not dynamically, so an
  already-running Whisky never picks up a new value.
- `Game/bin/x64/Sunrise/logs/sunrise.log` — the client/server's own
  application-level log file (distinct from wine's own debug trace output).
  Controlled by `core.logging.file_sink`/`levels` in each side's
  `settings.json`. This was the single most useful diagnostic tool all
  session (far more informative than wine exception traces for anything
  past the graphics layer) — but leaving `file_sink=true` + `debug` levels
  on is a **real, measured performance cost** on this platform (see §4's
  `ability_gate`/`gate_trace` entry) in a way it may not be on PC's faster
  native disk I/O. Default should be `file_sink=false`, levels=`warn`;
  flip to `file_sink=true`+`info` only for an active debugging session, and
  revert afterward.

## 4. Config / settings — some differences are real requirements, some are just today's specific values

- **`bap_port` must be identical in both sides' `settings.json`.** This
  isn't a Mac-vs-PC thing — it's just a hand-edited value in two separate
  files that silently drifted (client had `30974`, server had `30975`) and
  cost a whole debugging pass. Whenever either file gets hand-edited, diff
  `bap_port`, `https_port`, and `config_guid` against the other side.
- **`config_guid` must equal the server's own *computed* content-manifest
  guid, never a hand-typed value.** The server's `config_guid` *setting* is
  only a validation override for logging — it is never actually injected
  into what the manifest route serves, which always uses
  `state::content_manifest`'s independently-computed hash. Clear the
  server's override (empty string) to force it to log its real computed
  value, then copy that into the client's `config_guid`. This value changes
  whenever the packages/content directory changes, so it needs
  re-synchronizing any time content moves (as it did mid-session here, when
  `Game/` moved from the old Downloads/depots path to the repo).
- **`client.region_private`** (`false` by default) — forces public
  destinations to load solo instead of waiting for a public activity host
  ("citizen join"). Confirmed necessary on Mac because no public-activity-
  host/matchmaking-advertisement machinery is wired up here at all; without
  it, any non-social-space destination hangs forever
  ("Citizen join... still waiting for session_id to be advertised"). **It
  is genuinely unknown whether the PC rig needs this** — nobody has checked
  whether PC's setup has working PAH advertisement. If it does, PC doesn't
  need this flag and gets full public-destination behavior for free; if it
  doesn't, PC has the exact same hang, `region_private` fixes it there too,
  and the two platforms are simply in the same boat. **Turning it on
  trades an infinite hang for a load that actually completes, but surfaces
  a real, separate, deeper gap**: complex multi-bubble destinations
  (Mercury freeroam) still fail to resolve a spawn point and the client
  self-terminates a few seconds after loading in. See STATE.md's "NEW BUG
  A" for the live investigation — the fork's own `ForcedDestination` system
  (`state/activity/forced/`) looks like the intended answer, not yet wired
  up.
- **`ability_gate`/`gate_trace` hook installation** (now disabled by
  default, `client_hook_activation.cpp`) — the one item in §1's table that's
  closer to a judgment call than a strict bug fix. These are pure research
  instrumentation for a past flag-mapping investigation with zero gameplay
  effect (verified: every hooked function calls the original unconditionally
  with the same arguments, then only logs). They fire on hot per-tick engine
  paths and generated 20k+ log lines in a single boot once `file_sink` was
  on, which was the dominant cost in several multi-second launch stalls.
  **Whether this matters on PC depends on whether PC's disk I/O is fast
  enough not to notice** — untested. Re-enabling is a two-line uncomment if
  that investigation ever resumes on either platform.

## 5. The `build_data.bin` identity re-stamp — needed on ANY platform after an exe rebuild, hit here because Mac had to build a new exe from scratch

Not Mac-specific in principle — any rebuild of `sunrise-server.exe` anywhere
changes its PE timestamp+size, which invalidates
`RE_output/s1_accept/Sunrise/cache/build_data.bin`'s stored identity header
and hard-fails `content_swap` on next boot (no live rescan-and-rebuild
fallback exists for this specific cache, unlike `content_manifest.bin`,
which does have one). This surfaced on Mac specifically because the
standalone-server CMake target (§2) is brand new here, so the exe actually
got rebuilt for the first time in a long while. **The PC rig's exe has
apparently been stable enough that nobody has hit this in a while** — but
the exact same fix applies there the next time it *is* rebuilt: patch bytes
12 (imageTimestamp, u32 LE) and 16 (imageSize, u32 LE) of the cache header
directly (`#pragma pack(push,1)`, `cache/records/format.h`), using the
values the server itself logs as "expected_ts"/"expected_size" on the boot
that fails. `cache_identity_patch.cpp`'s existing `restamp_equipment_hash`
is the wrong tool for this — it only ever touches the eq-hash at a fixed
offset and explicitly assumes ts/size are stable; there is no existing
tool that patches all three fields together yet.

## 6. Known permanent Mac-only limitation

**No wine build on macOS can complete a real inbound TLS/SChannel
handshake**, full stop — exhaustively tested across wine 7.7, Whisky's
wine-11, and CrossOver (32-bit-only under Rosetta, dead on arrival); no
macOS build of Proton-era wine-SChannel exists to try. This is why the
"hybrid" architecture in §1 exists at all: config-manifest GET and SignOn
POST are answered fully in-process by the client DLL (no TLS needed),
while BAP/discovery/admin stay genuinely external over the fork's own
AES-GCM (never used TLS to begin with). **This is permanent, not a
temporary workaround** — there is no path to "just fix wine's TLS" on this
platform. PC, running natively, has no equivalent problem and can use real
TLS for a real external server if it wants to; there is no reason to ever
port the hybrid architecture's *necessity* to PC, only its *code* (§1),
which is harmless there either way.

## 7. Quick-reference: Mac-only paths

| What | Path |
|---|---|
| Client wine bottle | `~/Library/Containers/com.franke.Whisky/Bottles/<uuid>` (name: `Sunrise`) |
| Client game files | `~/Documents/opencode/sunrise-fork/Game/` |
| Server wine prefix | `~/Library/Application Support/SunriseServer/pfx` |
| Server home (both platforms, not Mac-only) | `RE_output/s1_accept/` |
| Mac build tree (untracked) | `RE_build/Sunrise-fork-inventory/` |
| Canonical git repo (both platforms build from this) | `RE_build/Sunrise-fork/` |
| Client launch script (superseded, do not use) | `mac-port/launch-sunrise-macos.sh` |
| Server launch script (current) | `mac-port/launch-server-macos.sh` |
| MoltenVK shader cache | `~/Library/Caches/MoltenVK/Sunrise/moltenvk_cache.mvk` |
