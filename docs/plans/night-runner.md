# Plan: the function map + night runner (consolidated, 2026-08-29)

Combines three discussion turns: the night-runner idea, the reconcile-job spec,
and the surface taxonomy. Status: planning; another session holds the pen.

## GOAL
A queryable map of the 91,445-function binary (RE_output/export/functions.csv
is the existing spine: addr/size/auto-name, exported 08-14, stale but complete),
filled by night lanes and queried by one command - so boot-triggered static
scrambles collapse to lookups, and "how mapped are we" is a number.

Key calibration: coverage is automatable and reachable; comprehension of the
protocol-relevant slice is the paying subset. The boot loop remains - it gets
cheap. Expected: protocol surface well-covered in ~3-6 weeks of nights
(2-3 lane-hours/night); whole-binary *classified* in ~2-3 months, front-loaded.

## THE THREE PLANES (taxonomy)
1. CODE-PROTOCOL: wire-observable or gates/serves served content. BAP/secure
   channel, activity/membership, matchmaking/lobby, admissions, inventory/
   profile/persistence, vendors, content serving. <- deep semantics target.
2. DATA-CONTENT: pkg/tags/manifests (Tiger engine). Missions/campaign live
   HERE mostly - data-shaped, own census (pkg tooling exists), not functions.
3. CODE-ENGINE: renderer, UI rendering, audio, physics (no wire output),
   scheduler, platform. <- classification-only target.
BOUNDARY IS POROUS (both directions, precedented): engine job stall gated road
C (+20s hitch assert, network_send 'peer-creating'); protocol gap now blocks
render (L9: family-0/3 records unreplicated). Therefore classification records
ADJACENCY (callers/callees/cluster), never a fence.

## PART 1: reconcile job (the map's foundation) - 1-2 nights
- Spine: functions.csv sorted -> interval map (cited addrs often point INSIDE
  a function; bisect to enclosing).
- Corpus scan: FINDINGS + claims/*.md + STATE + HANDOFFs + boot briefs.
  Extract: hex addrs in image range (code vs .data by sub-range), FUN_ names,
  fork symbols. For every hit capture: enclosing function, source file,
  entry id/date, +/-2 lines context (the context sentence IS the payload).
- classify: function-start / inside-function / data / out-of-range.
- names table: harvested ONLY from explicit patterns; status
  verified|inferred|auto. Conflicts kept, never silently resolved (supersession
  convention: display newest, keep all).
- verification per U8: sample ~20 citations, re-read sources, confirm context.
  Coverage report #1: how many of 91k have >=1 citation (baseline for nights).
- incremental: file mtime/hash tracking -> re-run = seconds (maintenance job).
- Output: RE_output/map/function_map.db (sqlite): functions (spine), citations,
  names, later strings/xrefs/features. Plus funcq.py query CLI.

## PART 2: funcq.py - the query surface
`funcq.py <addr-or-name>` -> everything known: names+status, every citation
(dated), decompile path (if archived), xrefs, strings, cluster, neighbors.
Also `--coverage` (the scoreboard: % named, % with census, % cited),
`--cluster <addr>`, `--corpus <term>` (prose search via the index).

## PART 3: night lanes (the filling mechanism)
- Queue: RE_output/map/queue.md (or .json) - targets with status: unswept
  ranges, un-xref'd tables, unnamed clusters, fork-symbol candidates.
- Nightly spawn: 1-2 background lanes, flash tier, using existing lane infra
  verbatim (brief, per-phase claims as they land, near-limit stop-and-write,
  3-line report-back, DEATH SAFETY).
- Spawn mechanics: NO new scheduling infra - the established submit-and-release
  pattern (spawn last thing at night, morning harvest) IS the night runner.
- Job ladder (by cost tier, from the real distribution):
  T1 small fns (71k, <256B = thunks/wrappers): auto-classify from features.
     ~2 compute nights.
  T2 big fns (250, >=4KB, 3.8MB = 17% of code): individually read. 1-2 nights.
  T3 mid protocol-relevant slice (est. 2-5k of 20k): LLM read + confidence
     marks + verification sampling, ~150-300/night. 2-5 weeks.
  T4 mid remainder: classification-only, opportunistic, low priority.
- Job priority order: (1) reconcile+funcq, (2) fork-symbol matching
  (fork = seed ground truth; expand frontier transitively via xrefs),
  (3) string-beacon census (Bungie's own asserts/errors name consumers),
  (4) constant beacons (decoded wire grammar identifies protocol fns
  statically), (5) LLM decompile reading with corpus priors.
- ALL night output marked `inferred`, quarantined until a verification pass or
  confirming boot closes it. A wrong name poisons every future chain - worse
  than no name.

## PART 4: safety envelope (pen held by another session)
- Branch meta/nightmap-v1. New paths only: RE_scripts/{funcq,reconcile}.py,
  night lane briefs, RE_output/map/*. Zero contact with fork code, deploys,
  boots, settings; never write STATE/FINDINGS/FRONT.
- Doc registration (TOOLS.md rows, router trigger, FINDINGS entry) staged,
  folded when pen frees - same discipline as 08-27/28 fold-ins.
- Read-only on: functions.csv, Ghidra project, corpus, dumps, logs.
- Ghidra single-tenancy: night headless runs only in the scheduled window, or
  against a COPY of the project directory.
- Compute-noise rule: heavy night work yields to active boots (check for
  running destiny2/sunrise-server first; or schedule for non-boot windows).
- Morning triage: time-boxed ~15 min (harvest report, update queue, promote
  any verified names). This box is the guard against the known failure mode:
  night output becoming a daytime reading burden.

## PART 5: execution tier - answering behavior questions without a boot
Three tiers, honestly bounded:
- T-A FUNCTION EMULATION (new capability, ~1-2 evenings): Unicorn-class
  harness loading the unpacked binary; execute individual functions with
  crafted inputs; observe outputs = ground truth for pure-compute functions
  (hashes, scramblers, unpackers - a large slice of the 71k small fns).
  Purity heuristic: imports/D3D/engine-globals -> fail loud, classify
  "not emulatable" (also useful output). VMP-residual functions: flag, do
  not fight. Integrates as a night-agent tie-breaker: questions static
  reading cannot close get executed instead of deferred to a boot.
- T-B PYTHON MICRO-REPLICAS (already the house pattern - bapdecode IS one):
  when a function is simple+important, the night lane writes the Python
  replica + test vectors and registers it. Each replica = permanent
  oracle-bearing asset; the binary becomes progressively queryable without
  running it. Micro-scale version of the fork effort itself.
- T-C LIVE-CLIENT SCRIPTED PROBING (pen-owned, NOT a night capability):
  the in-process Sunrise DLL could expose a query console (call fn X with
  args Y, log result) so one boot answers a batch of scripted questions.
  Powerful; requires fork code + boots. QUEUED for the pen-holder as an
  instrument idea, per the U17/instrument philosophy.
Full-client emulation: rejected - redundant (a real client already runs on
mac+rig) and infeasible (engine/GPU/services/anti-tamper). The scarce
resource is unattended cheap execution, which T-A addresses for the
executable slice; emergent/state-machine behavior stays with boots.

## ACCEPTANCE
1. funcq on a known address (e.g. 0x1416E1620) returns citations + neighbors
   in one command; spot-check 20 reconciled citations vs sources (U8).
2. Coverage baseline report exists and numbers the gap.
3. First night lane runs clean under the envelope: new-paths-only (git status
   proof), yields to a boot, produces queue progress + claims per phase.
4. All scripts parse-checked, selftested, negatives tested (house standard).
