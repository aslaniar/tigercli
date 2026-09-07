# GATE SEMANTICS - what each check reads, and what satisfies it (2026-09-06)

STATUS: live. Written because a session burned cycles GUESSING at
probe_audit's window rules instead of reading its logic ("the tool strips
comments before arm B, so a citation can never satisfy it"). Every gate
documents here: WHAT IT READS, WHAT SATISFIES IT, WHAT REFUSES. Read this
BEFORE writing citations - each check's rules are exact, and most were
tuned by a real-tree run that exposed a false positive.

## probe_audit.py - the instrument-source gate
Runs on the hook tree (RE_build/.../src/client/hooks, or --hooks-dir),
before every client deploy (deploy_client_dll.sh refuses on FAIL) and in
preflight. Exit 1 = findings; the record (verdict + hook-tree hash) is
RE_output/map/probe_audit.json.

Reads: each hooks .cpp TWICE - comment-STRIPPED (for code logic; a citation
in a comment can never satisfy an arm that runs on stripped text) and RAW
(waivers live in comments - they must be readable as text).

| Check | Refuses when | SATISFIED BY (exact) |
|---|---|---|
| A (R1) | an `emit_` function's code contains an alignment guard (`& 7`, `& 0x7`, `% 8`) near a `return` | a citation in the RAW text within 5 lines ABOVE the guard matching `ALIGN-CITED`, `alignment`, `misalign`, `&7=` or a `+0x...` field offset. NOTE: code-only citations are meaningless (comments stripped); the cite is a comment by design |
| B (R4) | a `*Sig* =` assignment whose RHS is a plain XOR of two fields | BOTH: (1) each operand individually transformed (`mix*(`, `rotl*(`, `<<`) and (2) a zero-guard `sig == 0` within +-2 lines. A `collision` comment alone is NOT enough - arm B runs on stripped text, so the GUARD must be real code (a zero signature aliases the change-gate's initial state; that guard is genuinely meaningful) |
| C (R6) | a lookup-class install row (name matches walk/lookup/find/map/cmp/compare/gate/sess/search/resolve) has no same-RVA leave coverage | (1) another row on the SAME RVA whose name matches leave/return/retwatch, or (2) an emit_ function pairing the row's stem with "leave" (e.g. walk_map -> emit_walkleave), or (3) the row's Probe kind is outcome-observing - `leave_capable_kinds` reads the Probe enum's OWN doc comments (any doc saying "On leave"/"returns"/"rax"), or (4) `no-leave: <reason>` in the raw text within 2 lines of the row |
| D (T3.1) | an `emit_` function whose body mentions `budget` but never names its exhaustion | a `budget_exhausted` line (or `exhaustedLogged` / the words "budget exhaust") INSIDE the same brace-matched function body |
| E (R8) | an emit_ function's `safe_read(`/read count GREW vs the git baseline (uncommitted/new files: no baseline, no check) | a `HOT-PATH-OK: <reason>` citation in the file's raw source |
| dup | two install rows targeting the same RVA (cross-table) | a `DUAL-OK: <reason>` in the raw text within 1 line of EITHER duplicate row |

Body/window mechanics (the parts a model must not guess):
- emit_ bodies are BRACE-MATCHED from the emit_ line (emit functions are
  interleaved with tables/dispatch code; a slice-to-next-emit once made six
  unrelated probes look budgeted).
- Arm A's citation search runs on RAW text (comments count); arms B/D/E run
  on STRIPPED text (what the compiler sees). A comment can therefore
  satisfy A but never B.
- Check C's pairing requires the leave row on the SAME RVA - a leave-named
  row on an unrelated function does not pair (the 09-06 walker shape).
- Waiver citations (`no-leave:`, `DUAL-OK:`) are read from RAW text within
  the span stated in each row above.

## hook_targets.py (used by verify_hook_rvas + preflight + probe_audit)
- Per-table: declared-size vs initializer count, null/rva-0 entries,
  unresolved RVA expressions.
- `duplicate_rva_problems`: cross-table duplicate RVAs; satisfied by
  `DUAL-OK:` in raw source within 1 line of either duplicate row.
- Rows now carry `kind` (the row's `Probe::X` token) - probe_audit reads it.

## gate_boot.py - the boot brief gate
- Required sections now include `NEGATIVE TEST`: content must contain
  either an arm-and-where-ran marker (`ran in/on/:`, `fixture`, `replay`,
  `rc=<n>`, `selftest`, `fails as designed`, `refused`) or an explicit
  `n/a (<reason>)` line. Template:
  RE_output/claims/boot-brief-template.md. Positive fixture:
  RE_output/map/boot_brief_v3_selftest.md (must GATE PASS); the negative
  arm (fixture minus the section) must NO-GO.
- MODEL REVIEW (third-branch streak >= 2) unchanged.

## boot_outcome.py - the outcome ledger
- `--close` (P5, wrong-question PM): requires `--verdict` and `--brief`;
  the verdict must share at least one content term (>4 chars, stop-worded)
  with the brief's PURPOSE section. Refusal names the PURPOSE terms - the
  fix is to restate the front's actual question in the verdict.

## negative_audit.py - scan-negative hygiene
- T2.3 (new): a scan-negative whose +-8-line evidence window cites a BARE
  `grep` (no `/usr/bin/grep`, `sgrep`, `logindex`, `logq`) is
  TOOL-BLIND = actionable (rc 1).
- The evidence window is CLIPPED TO THE ENTRY on both sides: it never
  crosses a `#` heading, so one entry's legitimate tool citation cannot
  sanitize another entry's bare grep (found by the T2.3 synthetic arm).
- The corpus keeps its 13 reviewed waivers; quoting-retraction text
  auto-waives visibly.

## deploy_client_dll.sh - the deploy refuse
- Runs probe_audit --quiet BEFORE the backup/copy; a FAIL copies nothing.
- The audit record (verdict + hook-tree hash + findings) is
  RE_output/map/probe_audit.json.

## THE STANDING FINDINGS at the last real run (the gate applying pressure)
- NONE as of 2026-09-06 evening: the pen's instrument session resolved the
  signature/lookup/duplicate findings (citations + guards in source), and
  the workflow session completed checks D (budget markers) and E (the R8
  cost arm, now CLI-reachable via git_baselines). The gate is binding at
  deploy time with an empty findings list - new violations will refuse the
  next deploy by themselves.
