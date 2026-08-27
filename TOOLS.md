# TOOLS - the reusable instrument registry

STATUS: live (2026-08-26). Census-driven: every general-purpose tool in
RE_scripts, what it is FOR, and its self-test where one exists.

RULE: before any lane forks a scanner/dumper/parser, check this table first.
Generalize an existing tool instead of adding probe_NN.py - the forks that
motivated xref_scan.py (lane_svc43_xref_scan.py, hashtable_xref_scan.py,
iv_writer_hunt3+) are the cautionary record. A new CORE entry should carry a
self-test/oracle per the project's "give every reader an oracle it can fail
against" rule.

## Meta / workflow layer (this branch)

| Tool | For | Check |
|---|---|---|
| RE_scripts/db_hygiene.sh | opencode DB report/vacuum guard | refuses while a session is live; dry-run default |
| RE_scripts/build_index.py --root X | regenerate indexes for any checkout | entry count == grep '^## ' totals |
| RE_scripts/bootstrap_check.sh | session-start instrument: budgets, STATUS lines, index liveness | always prints BOOTSTRAP OK last |
| RE_scripts/gate_boot.py <brief> | mechanical pre-boot checklist gate | --literals fails loud on missing literal in deployed binary |
| RE_scripts/incident.py | incident digest: DB events + logs + procs + hashes | prints LIVENESS counts; exit 1 if root-bound sections all empty |
| RE_scripts/q.sh <term...> | one-name recall over indexes + raw archive | falls back to raw grep if index missing |

## Static-analysis core (destiny2_unpacked_full.exe)

| Tool | For | Oracle/self-test |
|---|---|---|
| RE_scripts/pe_reader.py | PE section map VA->file offset; imported by 8+ scripts | basis of every oracle below passing |
| RE_scripts/xref_scan.py lo hi | GENERAL rip-relative xref scanner (.text -> range), infers instruction starts | `xref_scan.py --self-test`: must find getter 0x1404DC070 -> table 0x141F91AD0 (VERIFIED PASS 2026-08-26) |
| RE_scripts/disasm_fn.py va | disassemble one function to heuristic end | output correctness = manual spot vs Ghidra project |
| RE_scripts/lane_svc43_disasm_range.py a b | LINEAR disassembly of a VA range, no early stop | n/a - use for raw ranges |
| RE_scripts/needle_scan.py | byte-pattern needle search across loaded image | run twice, stable output |
| RE_scripts/hash_table_dump.py / hashtable_xref_scan.py | hash->ptr table dump + refs into it (the generalized form is xref_scan.py) | known-entry check |

## Crash / runtime triage

| Tool | For |
|---|---|
| RE_scripts/minidump_parse.py | name faulting module from a Windows minidump |
| RE_scripts/diff_minidumps.py / diff_captured_tails.py | before/after artifact diffs |
| RE_scripts/merge_logs.py / merge_timeline.py | unified timeline across client+server logs |
| RE_scripts/live_console.py / retail_view.py | Layer-1 triage windows on live log streams |
| RE_scripts/rig_dll_helper.py | remote-thread memory reads on the rig client |

## Deploy / boot pipeline (canonical - do not fork deploys either)

| Tool | Gates inside |
|---|---|
| RE_scripts/deploy_p2d6_gameplay.sh | drops clients; stages from build; asserts deployed==built |
| RE_scripts/deploy_client_dll.sh <mac\|rig> "<literals>" | hash assert + literal grep IN deployed file |
| RE_scripts/restamp_build_data.py | identity restamp after server rebuild |
| RE_scripts/boot_record.py / boot_diff.py | boot artifact capture + cross-boot diff |
| RE_scripts/reset_lobby_claims.sh | clears the IN-MEMORY lobby-claim table (restarts the server) and re-verifies listeners/nat; run between ANY two runs from p2(67) on, or a stale pairing silently invalidates the test |
| RE_scripts/obf_fold.py | constant-folding helper for obfuscated code (self-test passed) |

## One-off probes (~172 files under RE_output/claims/*.py)
Deliberately NOT registered. Grouped automatically as PROBE FAMILIES by
build_index.py (INDEX_claims.md bottom); long families = U7 escalation fired
late. Archive candidates after refcount review.
