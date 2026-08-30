# NIGHT RUNNER - setup and usage reference

STATUS: live (2026-08-30). The operational manual for the function-map /
night-lane toolchain. Tool details and oracle records live in TOOLS.md; the
design rationale lives in ~/.opencode/plan/night-runner.md; FINDINGS 20.126,
20.150, 20.186 hold the build history.

## WHAT THIS IS

A toolchain that converts the project's scattered function knowledge into one
queryable map (RE_output/map/function_map.db, 91,445-function spine), and a
night-lane queue that grows the map while you sleep. The scoreboard: how many
of the 91,445 functions are cited/named. Baseline at seed: 1,671 cited
(1.83%). The paying frontier: the ~250 big functions (12% cited) and the
2-5k protocol-relevant mid functions.

## THE TOOL INVENTORY (one line each; oracle records in TOOLS.md)

| Tool | Job |
|---|---|
| RE_scripts/reconcile.py | corpus <-> spine join -> function_map.db; incremental |
| RE_scripts/funcq.py | query the map: funcq.py ADDR / --coverage / --corpus TERM |
| RE_scripts/beacons.py | string census + .text xref sweep -> naming evidence |
| RE_scripts/femu.py | run ONE binary function in a Unicorn VM (pure compute) |
| RE_scripts/femu_batch.py | batch purity classification over the spine |
| RE_scripts/night_pull.py | pop N queue items -> night-lane brief; --done closes |

Interpreters: reconcile/funcq/beacons = /usr/bin/python3 (sqlite). femu* =
miniconda python3 (unicorn 2.1.4 + cryptography). beacons also wants capstone.

## THE NIGHTLY RITUAL (~1 minute of you)

```bash
cd ~/Documents/opencode/sunrise-fork
/usr/bin/python3 RE_scripts/reconcile.py                       # refresh map
/usr/bin/python3 RE_scripts/night_pull.py --n 10 \
    --claimant night-$(date +%m%d)                             # pull brief
```

Then spawn ONE background lane with the printed brief path
(RE_output/map/night_brief_<ts>.md) - submit-and-release, no polling.
The brief carries everything the lane needs: per-item questions, the
status-mark rule, the name-quarantine rule (inferred names are SUGGESTIONS,
never established - a wrong name poisons the map), DEATH SAFETY, and the
output contract (one claims block per item).

## THE MORNING RITUAL (~5 minutes)

```bash
# read the lane's claims doc, then close out finished items:
/usr/bin/python3 RE_scripts/night_pull.py --done 0xADDR1,0xADDR2
# fold the night's evidence into the map:
/usr/bin/python3 RE_scripts/reconcile.py
# the scoreboard:
/usr/bin/python3 RE_scripts/funcq.py --coverage
```

Triage is time-boxed ~15 minutes: promote verified names, flag discoveries
for the day's front, reseed the queue if a tier runs dry.

## THE KNOBS

- `night_pull.py --n N` - throughput. 10/night = steady; the 723-item seed
  queue at that rate is ~10 weeks, front-loaded (dark heavyweights first).
- `night_pull.py --claimant NAME` - who claimed the items; lets two lanes
  (or two harnesses) share one queue without collisions.
- `femu_batch.py --min-size/--max-size/--range/--sample` - classification
  sweeps by tier or address range.
- `femu.py --call ADDR --args a,b --max-insn N` - one-off execution of any
  pure function (--wmem ADDR=HEX to graft buffers/state).

## THE RULES (why it stays trustworthy)

1. **Quarantine**: night output is `inferred` until a verification pass or a
   confirming boot closes it. Never promote an auto-name silently.
2. **Yield to boots**: no heavy night compute while destiny2/sunrise-server
   is running (measurement noise on the sensitive instrument).
3. **Ghidra is single-tenant**: night headless runs need the window free or
   a COPY of the project directory.
4. **Fail loud**: every tool prints liveness counts and exits nonzero on a
   degenerate run - a null result is a result, never silence (L13).
5. **Read-only nights**: night lanes never boot, deploy, edit fork code, or
   write shared docs. New-paths-only, always.

## RESEEDING THE QUEUE

The seed (2026-08-29) was: P1 = big functions with zero citations AND zero
string refs (123 items); P2 = beacon-rich corpus-blind mids, >=4 distinct
strings (400); P3 = string-rich smalls (200). To reseed after coverage moves:

```bash
/usr/bin/python3 RE_scripts/beacons.py        # refresh strings/refs (35s)
/usr/bin/python3 RE_scripts/reconcile.py      # fold
# then re-run the seed queries against function_map.db (see git history:
# the 08-29 seed queries are in the night-runner commits), or ask any
# session to reseed - the queries are three SELECTs on the map.
```

## CURRENT STATE (2026-08-30)

- queue: 723 items seeded, none claimed yet.
- map: 9,748 citations / 1,671 cited functions / 488 names / 14,041 strings
  / 10,406 string refs / 3,669 string-referencing functions.
- known open lanes for the queue's later tiers: fork-symbol matching
  (fork source names -> binary addresses), constant-beacon sweep (decoded
  wire grammar as static identifiers), Ghidra decompile-all batch.
