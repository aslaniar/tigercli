# Plan: femu v2 - fold the pen session's workarounds into first-class features
(2026-08-31. Source: the pen session's pain-point breakdown + their scratch
implementations, which are the requirements spec AND the acceptance vectors.)

## VERDICT (why this happened)
femu v1 was certified against the easiest possible corner: a 28-byte pure
accessor over static file data. Every selftest positive lived in that corner.
The pen session's workload - the svc22 apply decoder - is the opposite corner:
heap-built runtime state, multi-call sequences, pointer-heavy .data. The tool
did not fail; it was SCOPED, and its tests certified the scope without
disclosing it. Fix: v2's acceptance test = the session's REAL workload.

The pivotal insight the session had (and v1 missed): the stale runtime
pointers in .data (0x7FF6AF7F0000-based - pe_reader now carries RUNTIME_BASE)
are not noise, they are REBASABLE. v1 treated them as a wall ("unusable
statically, dropped as oracle" - FINDINGS beacons work); the session rebased
64,095 qwords and unlocked the whole runtime-state class.

## LAYERS (reordered + refined after the 08-31 critique pass; each with
## selftest incl. negatives; acceptance = the real type24 workload)
## BUILD ORDER: L9 -> L5 -> L6 -> L8 -> L7 -> L10 (mapping sanity first:
## demand paging must trust its memory before it starts pulling pages).

### L9: mapping sanity (FIRST - demand paging must trust its memory)
- Real span = max(section ends); if SizeOfImage exceeds it, warn + map only
  real sections (+ headers page), leave the rest UNMAPPED.
- Crash hook classifies faults OUTSIDE real sections explicitly.
- NEW L1 NEGATIVE selftest: out-of-section access must fault (the blind
  spot that let the 4GB phantom mapping pass v1's suite).

### L5: dump-backed demand paging (generic; the big one)
- --graft-dump FILE: attach a minidump (minidump_reader.Minidump) as the
  backing store for unmapped memory.
- On crash:read-unmapped: map the faulting page, pull bytes from the dump at
  module-base-relative VA, resume - the session's 24-round loop becomes an
  internal mechanism (bounded rounds, count reported).
- graft_registry's manual page grafts become unnecessary; the registry
  chain-walk (schema-specific arithmetic, mirrors schema_walk) stays as a
  recipe module but rides on the generic machinery.
- PAGE PROVENANCE (new, the anti-L13 feature): every grafted page is tagged
  file|dump|hole. A page absent from the dump is a HOLE - reported in the
  result, never silently zero (the session's `if data: mem_write` produced
  confident zeros; that failure class is barred by construction).
- CRT WHITELIST (new, small, unlocks sequences): memcpy/memset/memmove/
  strlen implemented as stubs - demand-paged code calls CRT constantly and
  a purity abort there would kill legitimate sequences. Everything else
  still aborts loud.
- Acceptance: their type24 decode loop runs with NO hand scaffolding.

### L6: .data rebase (generic)
- --rebase: qword sweep over .data; any value in [RUNTIME_BASE,
  RUNTIME_BASE+0x8000000) -> imagebase + (v - RUNTIME_BASE). The session's
  64,095-qword pass, one flag. Report the count (liveness).
- DOCUMENTED LIMITATION: rebasing every in-range qword will occasionally
  shift a non-pointer that looks like one - silent, accepted, disclosed.
  Suspicious results get checked against an unrebased run. A
  pointer-analysis-accurate rebase is explicitly rejected as scope creep.

### L8: fault diagnostics
- Every result carries faulting RIP + last-N executed addresses (ring buffer
  code hook, always on).
- Fix hook coexistence so consumer hooks coexist with femu's (or make the
  ring buffer good enough that nobody needs their own).

### L7: sequence mode + reset-by-rederivation (SIMPLER than snapshots)
- Formalize the Rig API the session used by hand: map_region, write, call,
  read - documented, with the stack/state reset semantics stated. NO
  --script flag: the fix is the documented API, not a loader.
- State reset = REDERIVATION, not copying: the file image and dump are both
  immutable backing stores, so all mutable state is derived - drop grafted
  pages (re-pulled on demand) + restore dirty image bytes (DirtyGuard).
  Near-free, and the mental model is exact: the world is always
  (file image + dump); everything else is a cache.

### L10: analysis-tool fixes (from the same breakdown)
- lane_svc43_disasm_range: warn when start is not a spine-known boundary.
- disasm_fn: default to .pdata bounds (warn on heuristic end).
- field_xref: index-register forms + NEVER print a bare "no writers" without
  the form-list caveat (the false negative is the dangerous mode).
- pdata fragment families: group contiguous entries in the map (the
  donation-handler family, 30+ fragments).

### MAP INTEGRATION (small)
- femu results (verdicts, purity, behaviors) get a --record path into
  function_map.db (femu_results table); funcq shows them. Classification
  work must accumulate into the project's memory.
- Run provenance in every result: which dump, rebase count, paging rounds,
  holes touched (U14 applied to runs).

## PROCESS MITIGATIONS (the generalization answer)
1. Acceptance tests must include a REAL workload, not only planted corners.
2. Fold rule: consumer workarounds get harvested into the tool next session
   (lane template line: "workarounds created: list them for folding").
3. The registry/capability index (enforcement plan) covers find-the-tool;
   this case is extend-the-tool - the fold rule is its complement.
