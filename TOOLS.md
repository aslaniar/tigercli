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
| RE_scripts/db_hygiene.sh | opencode DB report/vacuum guard | refuses while a session is live; dry-run default [caps: db-maintenance, vacuum-guard] |
| RE_scripts/build_index.py --root X | regenerate indexes for any checkout | entry count == grep '^## ' totals |
| RE_scripts/logindex.py | index ANY sunrise.log-shaped logs -> SQLite (ev/stage/kv per line) | --selftest; event count == parsed-line count [caps: log-indexing] |
| RE_scripts/logq.py | query a logindex: --ev/--stage/--grep/--source/--range/--tail; --aligned = cross-machine unified clock via merge_timeline drift | exit 1 = clean no-hits (a result, not silence) [caps: log-query, cross-machine-align] |
| RE_scripts/loggrep.sh | zero-infra locate (full-width, live-file warn, file:line cites) | warns when target modified <60s [caps: log-locate] |
| RE_scripts/bootstrap_check.sh | session-start instrument: budgets, STATUS lines, index liveness | always prints BOOTSTRAP OK last [caps: session-bootstrap, doc-budgets] |
| RE_scripts/gate_boot.py <brief> | mechanical pre-boot checklist gate | --literals fails loud on missing literal in deployed binary |
| RE_scripts/verify_hook_rvas.py | resolves EVERY client-hook RVA constant against .pdata and fails if it is not a function START. MANDATORY before any boot shipping a new or changed hook address. Born from p2(112): profile_harvest shipped 0x1A6040 for 0x1417A6040 (dropped digit); the bad value still sat inside the module so the observer's `module_range` check PASSED and the detour attached to an unrelated function - `install result=ok`, zero fires, through a Tower dwell + subclass swap + full character switch. A range check proves an address is IN the image, never that it is the RIGHT one | prints per-RVA verdicts; exit 1 on any FRAGMENT/MID-FUNCTION/UNRESOLVED. Addresses past their nearest .pdata entry are reported NOT-CODE (data constants) and listed for review, not failed [caps: hook-rva-verify] |
| RE_scripts/incident.py | incident digest: DB events + logs + procs + hashes | prints LIVENESS counts; exit 1 if root-bound sections all empty [caps: incident-digest] |
| RE_scripts/q.sh <term...> | one-name recall over indexes + raw archive | falls back to raw grep if index missing |

## Static-analysis core (destiny2_unpacked_full.exe)

| Tool | For | Oracle/self-test |
|---|---|---|
| RE_scripts/pe_reader.py | PE section map VA->file offset; imported by 8+ scripts | basis of every oracle below passing [caps: pe-parse, section-map, pdata-bounds, static-read] |
| RE_scripts/xref_scan.py lo hi | **TRAP (20.291 R9.3): its `[unknown]` hits are UNJUDGED CANDIDATES, not references** - `mov qword [rcx+0xC00],0` was reported as a ref into the dispatch table because the immediate parsed as a rip-relative displacement; the tool says "judge by context" and that must actually be done. GENERAL xref scanner: rip-relative code refs (BOTH .text sections) + --ptrs data-pointer mode (vtables/callback tables) | `--self-test`: getter 0x1404DC070 -> table 0x141F91AD0 (re-verified PASS 08-31 post-fix); pen's hand-read ref 0x140B47D22 now found |
| RE_scripts/disasm_fn.py va | disassemble one function to heuristic end. **TRAP (20.291 R6): ANCHOR FIRST.** Passing an address that is not a function start produces a plausible-looking but FALSE instruction stream - the participant-image format spec was retracted because 0x1404f4740 is +0x40 inside 0x1404F4700 and the invented decode contained a `mov ebx,0x6c38` that is nowhere in the binary. Run pdata_bounds.py on every address before disassembling it | output correctness = manual spot vs Ghidra project |
| RE_scripts/lane_svc43_disasm_range.py a b | LINEAR disassembly of a VA range, no early stop | n/a - use for raw ranges |
| RE_scripts/needle_scan.py | byte-pattern needle search across loaded image | run twice, stable output [caps: needle-search, dump-sweep] |
| RE_scripts/hash_table_dump.py / hashtable_xref_scan.py | hash->ptr table dump + refs into it (the generalized form is xref_scan.py) | known-entry check |
| RE_scripts/field_xref.py <hex-disp> | STRUCT-FIELD xref: every .text access to `[reg + disp32]` AND `[reg + disp8]` (mod=01, added 08-31), classified read/WRITE/RMW. Answers "who touches field +N" — the complete x86-64 displacement coverage: disp32 (mod=10), disp8 (mod=01), --sib-scan (mod=00 SIB no-disp), and xref_scan (rip-relative). Disp8 hits are boundary-validated by linear disassembly of the enclosing function (pdata bounds) — the 0x1416F43F6 false-positive class is eliminated. REGISTRY caps: field-xref, sib-scan, disp8-scan. TRAP (20.276): scan the field under ALL its base aliases — a record field read via a sub-object base (+0xA8) spells a different displacement | `--selftest`: 3 known disp32 accesses + 3 known disp8 confirmed hits (0x1416E9CF0/0x1416EBD51/0x14171812A) + the 0x1416F43F6 false positive correctly rejected + negative displacement yielding 0 writes (PASS 08-31) |
| RE_scripts/callers.py <va> | DIRECT-caller enumeration: every E8/E9 rel32 in both .text sections targeting the VA, each site resolved to its owning function (fragment chains followed). Generalizes the ad-hoc caller scans of 20.271/20.273/20.276. Blind spots (stated in --help): indirect calls (vtables, function pointers — pair with xref_scan --ptrs), VMP regions | `--selftest`: must find the documented edge site 0x141769295 -> 0x1417692E0 owned by 0x141769230..2D4 (FINDINGS 20.271 R2) and classify it 'call' (PASS 2026-09-03) [caps: e8-callers, callgraph-enum] |
| RE_scripts/name_codec.py | THE PROFILE-BLOCK NAME CIPHER, BOTH DIRECTIONS (20.179 R1 / 20.195). Reader: plain[i] = key16(i) ^ ((wire[i]*0x7b4f)&0xFFFF); writer inverts the multiply with 0xBBAF. `--encode` builds wire words for a name, `--decode` reads them back, `--try-both` prints a captured buffer BOTH ways so a dump of unknown form (wire or stored) is told apart by which reading is legible. It lives outside the game so a name can be checked without a boot - p2(123)'s expected bytes were computed here and registered in the boot brief BEFORE booting, then matched exactly. TRAP: key16(0)=0 is a SPECIAL CASE, not a rotation result - at i=31 the rotation is by ZERO and key16(31)=0xB0C4. Names 31+ words long break if that is collapsed | `--selftest` 10/10: inverse is a true modular inverse, the index-0 special case is distinguished from the i=31 zero-rotation, 64-word round trip, empty-name-stores-zero, terminator-stores-key16(L), string round trip, and encoding is not the identity [caps: name-codec, encode-decode] |

## Crash / runtime triage

| Tool | For |
|---|---|
| RE_scripts/log_archive.sh [--label ID] | BOOT-LOG CAPTURE + BACKUP: archives mac/rig/server logs into RE_output/logs/<ts>/ with sha256 + manifest (the fix for losing all-but-the-current boot's client logs). Rig fetch best-effort via ssh (loud on unreachable). Wired into boot_verdict + both deploy scripts as triggers | dedupe skips identical logs; LIVENESS line; exit 1 on degenerate [caps: log-archive, rig-fetch, dedupe] |
| RE_scripts/minidump_parse.py | CRASH TRIAGE ONLY - names the faulting module from a minidump. Does NOT read dump memory: for that use minidump_reader.py (or femu --graft-dump) [caps: minidump-parse] |
| RE_scripts/negative_audit.py | SCAN-NEGATIVE HYGIENE: flags corpus claims like 'zero static references'/'no writers' that lack an ENCODEDS declaration or predate an invalidating encoding fact (RUNTIME_BASE relocation). The 20.209 R2 class - a tool's coverage limit promoted to a world-fact | 9 corpus claims flagged on first run (2026-08-31) [caps: scan-negative-audit, invalidation-scan] |
| RE_scripts/minidump_reader.py | THE DUMP-MEMORY WORKHORSE: lazy seek-based reader for full dumps (6GB+ fine) - read_va/module/ranges, CLI: summary, `--read VA COUNT`, `--rva RVA COUNT` (RVA = static - 0x140000000). The engine under femu --graft-dump. Verified on dump_p2146.dmp (6.49GB, loads in 0.0s) [caps: dump-read, module-lookup, range-list] |
| RE_scripts/dump_search.py | SEARCH a full dump's memory for u64 values / byte patterns / ASCII across every committed range; hits reported as base-relative RVAs with optional hexdump context. Uses minidump_reader.py as its engine - it adds ONLY the scan, format handling stays there. THE ANSWER TO RUNTIME-BUILT STRUCTURES: found the single pointer to ent_recv in 6.49 GB (20.222), which proved 20.209 R2's "the entity chain is statically unreachable" WRONG. TRAP: destiny2_unpacked_full.exe stores RUNTIME-relocated pointers (base 0x7FF6AF7F0000), so a qword search for a static VA finds nothing - search 0x7FF6AF7F0000 + rva. Scenario-scoping applies: a dump only answers about states the process actually entered (20.221 R5). --selftest: must find "player_broadcast" AND land it at base+0x1CA1518, matching 20.209 R3's independently recorded static VA (PASS 2026-08-31) [caps: dump-search] |
| RE_scripts/diff_minidumps.py / diff_captured_tails.py | before/after artifact diffs |
| RE_scripts/merge_logs.py / merge_timeline.py | unified timeline across client+server logs; N-source (2026-08-27: typeless-client grammar fix, server-pivot default, size-window pairing w/ distinct-size guard) | --selftest: 20 checks incl. typeless-fixture phase |
| RE_scripts/live_console.py / retail_view.py | Layer-1 triage windows on live log streams |
| RE_scripts/rig_dll_helper.py | REMOTE-SIDE DEPLOY HELPER (run ON the rig): backup/verify a deployed DLL - SHA256 assert + literal presence. The remote half of deploy_client_dll.sh. NOT a memory reader - rig live-memory reads = run the live_read_*.py / dump_sunrise_memory.py scripts on the rig via ssh | backup makes .bak_<stamp>; verify asserts hash + literals, exits nonzero on failure [caps: deploy-backup, deploy-verify] |
| `tcpdump -i en0 -s0 -U -w X 'udp port 3097 or 3074 or 3075 or 30976'` | THE PEER-CHANNEL INSTRUMENT (20.144). Client-to-client traffic never reaches the server and the client log records only counts, so a pcap is the ONLY way to see it. No sudo: this user is in `access_bpf`. Capture ALL FOUR ports and CLASSIFY BY FLOW PAIR - the peer channel's mac-side port is NOT fixed (20.167: mac:30976<->rig:3097 carried all 2386 channel packets; a 3097-and-3097 filter matched ZERO). Steady state is DTLS-encrypted; read it by SIZE and CADENCE, not contents. LIVENESS (earned 20.166, hard): the "received by filter" counter is BOGUS on this mac (counts noise on empty nets) - prove an empty pcap is a real null by sending a probe packet (e.g. python socket to 127.0.0.1:3097) and confirming capture; and check `route -n get 192.168.1.136` for the rig-traffic egress interface FIRST (08-29: en0, not en13) |
| RE_scripts/capture_bap30975.sh <seconds> | THE BAP-WIRE INSTRUMENT (20.145). Captures tcp/30975 on BOTH en0 (rig client<->server) and lo0 (mac client<->server, loopback) into RE_output/captures/bap30975_<ts>/. No sudo. For a CLIENT-HOSTED fireteam, have the MAC client host (a rig-hosted session's client<->client stream never crosses the mac). Bodies may be session-sealed; framing/sizes still readable, and the fork's bap_listener framing is the decode reference |
| RE_scripts/bapdecode.py | pcap -> BAP-frame -> type-12 membership decode (tshark reassembly, svc25/26 key recovery, AES-GCM, region walk). Generalized from the GAH-REGION-DECODE lane's scratch decoders. Interpreter: miniconda python3 (needs `cryptography`) | --selftest (12 checks: planted-session positives + HMAC/tag/size negatives that must fail); --verify against the 224-body ground truth (RE_output/scratch/gah_en0) - 224/224 + full pcap run 2026-08-28 [caps: pcap-decode, bap-frame-decode, key-recovery, membership-decode] |
| RE_scripts/femu.py | FUNCTION EMULATION RIG v2 - THE BOOT-SAVER: execute one client function (or sequences via the Rig API) against the real binary + a dump of real client memory, WITHOUT a boot. Dump-backed demand paging, .data rebase + read-taint, CRT whitelist, mapping sanity, fault diagnostics (RIP + trace). Interpreter: miniconda python3 (`unicorn` installed 08-29) | --selftest 19 checks (no-dump + dump modes); ACCEPTANCE: the type24 decode loop ran the client's svc22 apply decoder against dump state with zero scaffolding (RE_output/scratch/femu_v2_acceptance.py) [caps: function-emulation, demand-paging, data-rebase, crt-whitelist, purity-classify, fault-diagnostics] |
| RE_scripts/femu_batch.py | batch purity/behavior classification over the 91k-function spine; verdict enum + DirtyGuard (image writes restored from file bytes) | --selftest 6/6; real run: 100 fns in 0.0s (9 pure / 10 import / 79 state-dependent / 2 exceptions) [caps: batch-classification, dirty-guard] |
| RE_scripts/reconcile.py | corpus <-> spine join -> RE_output/map/function_map.db: every hex/FUN_ citation in FINDINGS/claims/STATE mapped to its ENCLOSING function, names only from explicit patterns; incremental by file hash. Interpreter: /usr/bin/python3 | --selftest 9/9 (mid-func mapping, data classification, dedupe, negatives); real: 9,748 citations -> 1,671 functions, 488 names [caps: corpus-reconcile, function-map, incremental-scan] |
| RE_scripts/funcq.py | query the function map: what does the project know about function X (names/citations/neighbors); --coverage scoreboard; --corpus search. Interpreter: /usr/bin/python3 | cited baseline 1,671/91,445 (1.83%); big-tier 12%, mid 3.1%, small 1.4% [caps: function-query, coverage-report] |
| RE_scripts/beacons.py | string-beacon census: 14,041 ASCII/UTF-16 strings extracted, .text swept for rip-relative refs (10,406 refs -> 3,669 functions with naming evidence). Interpreter: /usr/bin/python3 | --selftest: POSITIVE client strings (privacy-mode, peer-creating, tried-to-join-self, managed-session-start) present once; NEGATIVE fork-side tags (ev=steamnet) absent; disasm spot-check 39/40 [caps: string-extraction, xref-sweep, naming-evidence] |
| RE_scripts/night_pull.py | pop N items from RE_output/map/queue.json -> night-lane brief (723 seeded: 123 dark heavyweights, 400 beacon-rich mids, 200 smalls) | morning --done marks; brief carries status-mark + quarantine rules [caps: queue-pull, brief-generation] |

### WHEN TO EMULATE VS BOOT (the femu accuracy contract - read before
### spending an hour on a paired boot for a question femu can answer)

femu executes the binary's REAL instructions, so fidelity depends only on
whether the function's WORLD is available:

- **EXACT (boot-grade - use femu, not a boot):** pure-compute functions.
  Hashes, codecs, bit-unpackers, crypto primitives, framing, enum lookups.
  Deterministic and identical to a boot; repeatable with no state pollution.
- **FAITHFUL-TO-DUMP (use femu, note the scope):** functions over captured
  runtime state. Execution is exact against the dump's snapshot; the answer
  is "against THIS state at that moment". Check the result flags:
  `rebase_reads` (answer depends on the rebase heuristic), `holes` (dump did
  not capture the memory), `pages_pulled` (provenance).
- **NOT EMULATABLE (fails loud, classified):** imports beyond the CRT
  whitelist (D3D/Steam/OS), threads/sync/exceptions, VMP-residual regions,
  state the dump did not capture. The abort reason IS the classification.
- **BOOT REQUIRED:** emergent behavior - state machines across systems,
  timing, live multi-client interaction, anything past the snapshot moment.

Rule of thumb: "what does this code COMPUTE" -> femu first (seconds).
"does the CLIENT do X in a live session" -> that is a boot.
Uncertain which tier? `femu_batch.py` classifies candidate functions cheaply
before you commit to either.

## Deploy / boot pipeline (canonical - do not fork deploys either)

| Tool | Gates inside |
|---|---|
| RE_scripts/deploy_p2d6_gameplay.sh | drops clients; stages from build; asserts deployed==built [caps: server-deploy] |
| RE_scripts/deploy_client_dll.sh <mac\|rig> "<literals>" | hash assert + literal grep IN deployed file |
| RE_scripts/restamp_build_data.py | identity restamp after server rebuild [caps: identity-restamp] |
| RE_scripts/boot_record.py / boot_diff.py | boot artifact capture + cross-boot diff |
| logged_empty.h (steam/interfaces/tables) | THE CENSUS INSTRUMENT: per-slot logging stub + argument registers, over a table sized PAST the interface. Any boot then returns the real ABI and its argument shapes for free. See LESSONS 18 |
| retail_log_enqueue_observer.cpp | CALLER CAPTURE: _ReturnAddress in the retail log funnel, reported as a module-relative RVA. Turns any log line into a code address (LESSONS 18c) |
| RE_scripts/pdata_bounds.py | resolves any address (RVA or static VA) to its OWNING FUNCTION, FOLLOWING UNW_FLAG_CHAININFO (a fragment entry's begin is NOT a function start - two of p2(74)'s six RVAs were fragments, 20.112) from .pdata RUNTIME_FUNCTION entries - the exact bounds source in a stripped image. The other half of caller capture: an RVA means nothing until it is resolved (LESSONS 18c) [caps: pdata-bounds, function-resolve] |
| RE_scripts/boot_verdict.sh | reads BOTH client logs + the server's and prints the lobby-lane verdict; compares Adding-player xuids MECHANICALLY (own vs peer) because the bare line fires every boot and proves nothing (20.101) [caps: boot-verdict] |
| RE_scripts/reset_lobby_claims.sh | clears the IN-MEMORY lobby-claim table (restarts the server) and re-verifies listeners/nat; run between ANY two runs from p2(67) on, or a stale pairing silently invalidates the test [caps: server-reset, lobby-claims] |
| RE_scripts/obf_fold.py | constant-folding helper for obfuscated code (self-test passed) [caps: obf-fold, chain-analysis] |

## One-off probes (~172 files under RE_output/claims/*.py)
Deliberately NOT registered. Grouped automatically as PROBE FAMILIES by
build_index.py (INDEX_claims.md bottom); long families = U7 escalation fired
late. Archive candidates after refcount review.

### state_hash_oracle.py (2026-08-30, PARTIAL - do not fork)
`RE_scripts/state_hash_oracle.py` - offline Python model of `lookup3::hash_bytes` and
`build_session_state`, for reproducing or searching a session-state hash without a boot.
The hash and state-model halves are transcribed from source and are correct by
construction. NOT YET USABLE END TO END: its self-test against a logged arm A hash fails
because a real body cannot be rebuilt from logs - `publish_snapshot` echoes each peer's
own 86-byte NetAddr blob byte-exact and the logs carry join descriptors instead.
Generalise this file (feed it a server-dumped replica or body) rather than writing a new
hash script. See RE_output/claims/session-state-profile-image.md OPEN (b).
