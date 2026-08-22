# ANALYSIS: boot-time reduction opportunities (2026-08-21 evening)

Analysis-only deliverable from a secondary session (the pen belongs to the
live fork/game session). Nothing else was read-modify-written. All claims
grounded in `Game/bin/x64/Sunrise/logs/sunrise.log` ("run Y", the newest
boot, mtime 17:01) and `sunrise.log.old` ("run W"), plus FINDINGS 14.8/14.9
and MAC_VS_PC_DIVERGENCE.md. t values = ms after DLL attach, from the fork's
own logger.

## 1. Stack map (top-down)

- CLIENT: `Game/` (destiny2.exe + 92G `Game/packages`) launched through the
  dedicated Whisky bottle "Sunrise" (wine 7.7-era, DXMT d3d11->Metal,
  WINEMSYNC on). The fork rides in as `Game/bin/x64/steam_api64.dll`
  (16.6 MB, rebuilt several times today 16:41-16:53 by the pen session).
- SERVER: `RE_output/s1_accept/sunrise-server.exe`, separate GPTK wine 7.7
  prefix, launched by `mac-port/launch-server-macos.sh`. Server boot measured
  165 ms; NEVER a boot-time cost (FINDINGS 14.8).
- SOURCE: canonical git repo `RE_build/Sunrise-fork`; Mac build tree
  `RE_build/Sunrise-fork-inventory` (no git).
- LOGS: `Game/bin/x64/Sunrise/logs/sunrise.log` rotates to `.old` per launch
  (rename PRESERVES mtime - do not date a boot by its `.old` mtime; anchor by
  content. Two reads of "current" 40 minutes apart were different boots).

## 2. Where the time actually goes (run Y, fresh decomposition)

Phase boundaries from retail state_manager entries + fork events:

| Phase | t-range | Cost |
|---|---|---|
| click -> DLL attach | n/a (pre-log) | ~11 s (wine loader + Rosetta; FINDINGS 14.9) |
| attach -> egress hooks done | 0-318 | 0.3 s |
| graphics probe hole | 318-3338 | **3.0 s** (probe is BACK ON, see 3.5) |
| remaining hook installs | 3338-8877 | 5.5 s |
| activate main (= client init done) | 8877 | - |
| engine silence to STUN endpoint | 8877-15935 | 7.1 s |
| STUN DNS discovery + NAT report | 15935-16648 | 0.7 s |
| silence to bootflow:start | 16648-21531 | 4.9 s |
| bootflow:start -> platform_signin | 21531-24599 | 3.1 s (but see 3.4: can be MINUTES) |
| account_signin + content_check | 24761-25391 | ~0.6 s |
| package_registration | 25391-30359 | 5.0 s |
| bap_signin (total) | 30359-39328 | 9.0 s |
| investment_signin | 39328-43825 | 4.5 s |
| prepare_for_orbit | 43826-54818 | 11.0 s (incl. **6.07 s UPnP timeout**) |
| character:signin + cleanup | 54819-57532+ | ~2.7 s |

So "launch -> window visible" (the user's stated ideal target) is currently
~24-26 s: ~11 s pre-attach + ~13-15 s post-attach, of which ~3 s is the
re-enabled graphics probe. FINDINGS 14.9's floor verdict (~23 s, sub-10 s
unreachable) still holds EXCEPT the probe slice is back on the table.

The rest-of-boot stretch (platform_signin -> cleanup) is ~33 s in a clean
boot, with three named, attackable blocks (below).

## 3. Ranked levers

### 3.1 UPnP port-2003 timeout: ~6.1 s EVERY boot (highest certainty)
Measured identically in two independent boots:
- run W: t=253808 "Starting port collsion resolution ... port: [2003],
  max upnp attempts: [6]" -> t=259916 "Client completed with status: [2]"
  (= failure), "Unsuccessful UPnP reservation".
- run Y: t=43875 "Started UPnP client for port: [2003]" -> t=49949
  "completed with status: [2]". Exactly 6.07 s both times.
This is a pure deterministic dead wait: nothing on this setup will ever
answer UPnP. It sits INSIDE prepare_for_orbit (the state's other ~5 s is
world change to orbit_d2 + queuez seeding). The fork already installs 30
winsock/egress hooks; a hook that makes the UPnP client's discovery socket
traffic fail IMMEDIATELY (or answers it) reclaims the full ~6 s on every
boot forever. This matches the lever already named in FINDINGS 14.9 but
unbuilt.

### 3.2 Title/input gate idle: the largest VARIANCE source (observed once)
Run W sat ~214 s (t=21208 -> t=235181) between 'bootflow:start' and
'platform_signin' producing ZERO log lines, then proceeded normally and
fast. Run Y covered the same transition in 3.07 s. INFERRED mechanism: the
retail pre-signin title/prompt screen waiting for user input (engine renders
silently; the fork has no hook there yet). Consequence for BOOT TESTS:
any unattended (or slow-to-attend) boot can silently cost minutes. Lever:
auto-confirm the gate via the existing polled_input/cursor hook machinery
(both already installed at t=3338/3348), making boots fully hands-off and
variance-free. Even if the pen session considers it a non-issue when
attended, it is the difference between a 30 s test loop and a 4-minute one.

### 3.3 bap_signin task ENUM(2): 5.1 s single blocking task
run W: "Started task 'ENUM(2)'" at t=240887 alongside three siblings;
ENUM(0)/ENUM(1)/(14) complete in 148/498/33 ms, then ENUM(2) alone holds
"after '5126ms'" at t=246013. One task = one identifiable handler; naming it
(one instrumented boot correlating task index -> handler, or static read of
the task table) tells us whether it is a retry/backoff we can collapse.
Bounded upside ~5 s.

### 3.4 investment_signin ~4.5 s: server push shape (ours to change)
run W: ENUM(0) 4514 ms dominates; ENUM(2)/(4) ~2.0 s each overlap it.
The payloads are the fork's own BAP pushes (type=123 frames, len 2882/9178).
Options: serve the same contract with an earlier/parallel push (during
package_registration's 5 s window), or slim the initial frame set. Contract-
first: diff what the client actually consumes before trimming. Upside ~2-4 s.

### 3.5 Graphics probe: ~3.0 s of T0->T1, currently re-enabled
FINDINGS 14.8/14.9 landed `client.ui.enabled=false` to skip the probe
(probe = real D3D11 device + swapchain creation purely to read a vtable that
DXMT invalidates anyway; output consumed by NOTHING on Mac). Current
settings.json now has BOTH `client.ui.enabled=false` AND new keys
`graphics_probe: true`, `graphics_probe_warp: true`,
`renderer_hud_always: true`, `renderer_enabled: false` - and run Y shows the
probe running again (the 318->3338 hole, `ev=activate stage=graphics
result=ok` at 3348). The pen session evidently added a settings-gated probe
for the renderer/HUD work in flight (probeon/probeoff builds at 16:30/16:41).
NOT a criticism: if their renderer path needs the swapchain, keep it. But
T0->T1 will not return to the ~23 s floor while `graphics_probe=true`. If
their work settles and the probe is only needed at first-run, gating it to
run once (cache the vtable answer) recovers most of the 3 s permanently.

### 3.6 Logging posture during timed tests
Client settings.json is currently `file_sink=true` + levels `info` (and
`debugger_sink=true`). This exact posture was measured as "the dominant cost
in several multi-second boot stalls" when the research hooks were live
(STATE post-port cleanup; MAC_VS_PC_DIVERGENCE section 3 says default should
be file_sink=false/warn outside active debugging). Presumably intentional
for tonight's debugging; just re-revert before taking TIMED boot
measurements or the numbers will carry log I/O noise.

### 3.7 DnsQueryRaw egress hook fails every boot (minor)
`t=318 ev=hook stage=attach group=egress name=DnsQueryRaw result=fail`
(warn, every boot; egress_guard_exports.cpp treats absence as non-fatal).
Cost today ~0.7 s of STUN DNS discovery, plus the egress guard's DNS leg is
inert under wine. Cheap to fix whenever someone is in that file; low
priority for time alone.

### 3.8 Pre-attach ~11 s and engine silence: accepted floor
Wine itself is 0.76 s; the rest is Rosetta translating destiny2.exe + the
16.6 MB fork DLL + deps, then ~12 s engine bootstrap to first window (same
binary ~10-13 s native). No code we own touches these. Micro-experiments
only worth trying opportunistically: keep the bottle's wineserver warm
between tests (avoid cold start), verify no Whisky per-launch overhead
(compare WhiskyCmd CLI launch vs GUI click once). Expect single-digit-% at
best; do not sink time here.

### 3.9 package_registration ~5.0 s: leave alone
Client reading its own 92G packages dir at mmap speed; a leaner package set
is high-risk/low-certainty. Deprioritize (agrees with FINDINGS 14.9).

## 4. Expected total

Clean-boot platform_signin->cleanup currently ~33 s. Levers 3.1 + 3.3 + 3.4
= ~13-15 s recoverable with high confidence (UPnP alone certain at ~6 s);
3.5 returns ~3 s to T0->T1 when compatible; 3.2 removes minutes-scale tail
risk from unattended boots. Realistic end state: window ~21-22 s after
click, sign-in to character select ~15-18 s, fully hands-off.

## 5. Method notes for future boot timing

- Anchor on log CONTENT (state transitions, ev= stages), never file mtimes
  (.old rotation preserves mtime; two "latest" logs 40 min apart were
  different boots).
- Server-t <-> client-t offset math (FINDINGS 14.9) remains the reliable
  cross-clock tool; DXMT_LOG_PATH writes nothing (logging compiled out).
- One variable per measurement boot; logging posture fixed across the pair.
