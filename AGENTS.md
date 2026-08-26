# Workspace

Project directory for research into the Destiny preservation / reverse-engineering scene:
running Destiny 1 on PC, and re-opening vaulted Destiny 2 content. User has a CS
background but is new to game emulation and server RE — explain concepts, avoid jargon
without defining it, and record everything in dated `FINDINGS_*.md` files.

See root `~/Documents/opencode/AGENTS.md` for the model budget ladder and research loop
(research on flash tier, escalate to redteam/deep only on a named reasoning failure).
NOTE (2026-08-15): that root file no longer exists on this machine — the ladder and
loop are superseded by the rules in HANDOFF_2026-08-15.md (flash-only subagents,
delegate-don't-act, GLM only on explicit request). Treat the HANDOFF as authoritative
for model/escalation policy on this PC.

**CLAUDE CODE NOTE (2026-08-21, hard):** this project runs primarily on opencode;
the ladder above (deepseek-v4-flash/GLM/kimi) is opencode's own model routing and
does not exist inside Claude Code. When the main session is Claude Code, its
equivalent subagent tiers are: **haiku** for the cheap/bulk-delegation tier the
ladder calls "flash" (mechanical greps, boilerplate extraction, running a known
script and reporting output — no judgment calls), **sonnet** (the default, no
override needed) for anything needing real reasoning/judgment (this is what the
ladder's "redteam/deep" escalation maps to), and **opus** only on explicit user
request, mirroring "GLM only on explicit request." The delegate-don't-act
principle itself (main session verifies, doesn't hand-fix) carries over
unchanged — it's not opencode-specific. Whichever tool is driving, keep all
actual PROJECT knowledge (state, findings, incidents) in this repo's own plain
files (STATE.md, FINDINGS_*.md, AGENTS.md) — never in a tool-private memory
store one of the two can't see. That's the one rule that must never drift.

## Key projects (map)
- **V4NGUARD** — custom servers for Destiny 1. Lead dev: cohae (github.com/cohaereo).
  Discord is the main Destiny 1/2 RE hub (~7.7k members). Tooling is Rust.
  ⚠️ Server is PRIVATE/closed-source; cohae's RPCS3 fork stale since 2022-09-20; his energy
  has shifted to Marathon (Deimos-Public). Treat V4NGUARD's D1 server momentum as uncertain.
- **kallsyms (Nick Gregory)** — independent D1-on-PC via RPCS3; implements gameplay
  systems (char creation, inventory, quests), not just exploration. @kallsyms on X.
  Watch for V4NGUARD collaboration (moji_irl suggested it, 2026-08-06).
- **moji_irl / Project Sunrise** — Halo + Destiny server revival; shows a Dec 2013 Xbox 360
  D1 pre-alpha build (the Tower). ReXGlue recomp experiments. X-only, no public repo.
- **stanuwu / Sunrise** — "Destiny 2 Offline Exploration Mod" (RELEASED 2026-08-07,
  github.com/stanuwu/Sunrise, GPL-3.0, C++/Detours/ImGui). Loads vaulted maps in the
  Season of Arrivals build, fully offline, exploration only. **PRs explicitly welcome.**
  🔬 DEEP-DIVE: actually a full in-process reimplementation of Bungie's backend (BAP +
  activity host) — the thing V4NGUARD keeps closed. Community PR #9 adds persistent
  inventory. Next big step = static enemies via the existing entity pipeline.
  Also **d2-cui-explorer** documents the tag-hash-resolution methodology.
- **ReXGlue** (github.com/rexglue/rexglue-sdk) — Xbox 360 static recompiler (PPC→C++),
  an alternative to emulation for running X360 builds on PC. Early/immature.
  **XenonRecomp** (github.com/hedge-dev/XenonRecomp, 6.4k★) is the mature alternative —
  has a PPC_FUNC hook mechanism ideal for redirecting network calls; UNEXPLORED for D1.
- **Demonware ecosystem** — Destiny's networking lineage (Activision Demonware). Open-source
  reimplementations: open-bitdemon-emulator, demonware-companion (packet deserializer),
  Transformers-Demonware-Server (analogous dead-game revival). Blueprint for a D1 server.
- **Tiger engine tooling** — tiger-pkg, quicktag, tachyscope, alkahest, Charm, D2TagParser,
  DestinyUnpacker, etc. `.pkg` files compressed with Oodle. (Deimos-Public = Marathon tool,
  same Tiger format, active.)

## Conventions
- **Dated + time-stamped findings (2026-08-16, hard)**: every new recording carries the
  EXACT time, not just the date — `FINDINGS_YYYY-MM-DD.md` entries open with
  `## N.N TITLE (YYYY-MM-DD ~HH:MM)`; the STATE/claims file updates carry the same. The
  timeline matters: the newest timestamp = the source of truth when two recordings
  conflict. Never record a bare date again.
- Distinguish VERIFIED facts (cited) from INFERRED mechanism (labeled).
- Record community links so sessions can pick up where the last left off.
- **DELIVERABLE RULE (2026-08-16, hard)**: every subagent's report-back summary is a
  POINTER, never the source of truth. The full deliverable file is read END TO END at
  landing — the integration, the fixes, and the next lanes are built from the deliverable's
  claims (spot-verified against disk where load-bearing). Cost of the violation, observed:
  the L1 summary compressed "acquiredFlags = the gate" and omitted the family-5 evaluated-
  state propagation, the kNoDefinitionHash 2100 payload, and the FUN_140e051b0 commit-point
  open — the wrong fix (the all-2 bank) shipped from the summary alone.
- **LANE DEATH-SAFETY RULE (2026-08-16, hard)**: the observed lane deaths (the cuid
  TBD-shell case, the silent-cap pattern) = the analysis ran, the synthesis never landed.
  Five rules, carried in the lane-brief template's DEATH SAFETY section: (1) per-phase
  claims written the moment each phase's evidence lands, never end-of-run; (2) near-limit
  = stop-and-write (the rest becomes OPEN items with evidence pointers); (3) the priority
  order raw > per-phase claims > log > report-back (the report-back = optional, the files
  = not); (4) the collector fallback = assumed (the main session completes the deliverable
  from the raw if the lane dies mid-synthesis); (5) no sleep/poll loops — background the
  long runs, one spawn, one report, end the turn; the main session harvests via the
  artifact mtimes + the completion notification.
- **GHIDRA TOOLING RULE (2026-08-16, hard)**: all Ghidra automation runs in PYTHON
  (headless-analyzer scripts / PyGhidra), never Java — the Java batch files in RE_scripts
  (CountRunFunctions.java, ExportCorpus.java, etc.) are legacy and must not be the pattern
  for new lanes. The Python form maps better to the models' training data and is faster to
  iterate. The S2 lanes' lane_sobject_ghidra*.py = the reference pattern.
  THE INVOCATION (2026-08-17, verified — all three gotchas):
  `& "C:\Users\rasla\tools\ghidra_12.1.2_PUBLIC\support\pyghidraRun.bat" -H "RE_output\ghidra"
  d2_full_cuib -process destiny2_unpacked_full.exe -noanalysis -scriptPath "RE_output\content"
  -postScript <script.py> -log "RE_output\ghidra\<name>_run.log"` — (a) PLAIN analyzeHeadless
  fails: "Ghidra was not started with PyGhidra" (the .py provider = PyGhidra; use
  pyghidraRun.bat -H); (b) WITHOUT -noanalysis the -process triggers a FULL auto-analysis of
  the 38k-function program (hours; kill the java process and re-run with the flag — the lane
  logs show the no-analysis runs take ~77 s); (c) the project = a shared-project layout:
  RE_output\ghidra = the location, the program = /destiny2_unpacked_full.exe. The d2_full_cuib
  project = the analyzed image (base 0x140000000); the dump-side runtime image base resolves
  per boot.
- **SHELL LAYOUT RULE (2026-08-16)**: a three-layer split, NOT a config change (opencode's
  config-level shell stays as-is — the HANDOFF's reasons hold: elevation, ports, processes,
  service cycles stay PowerShell):
  1. WINDOWS-NATIVE OPS = PowerShell (elevation, Get-NetTCPConnection port checks, process
     start/stop, server restarts, the file-form edits).
  2. UNIX-SHAPED TOOLING = bash. THE INVOCATION (2026-08-17, verified): `bash` on the
     PATH = the WSL stub, and WSL has NO distro installed — it dies with "no installed
     distributions". USE GIT BASH EXPLICITLY: `& "C:\Program Files\Git\bin\bash.exe" -lc "..."`
     from PowerShell (bash 5.3.15, MINGW64; git/grep/sed present). Two gotchas: (a) keep
     the whole bash command inside ONE single-quoted PowerShell string — nested quotes
     break the capture; (b) multi-step bash pipelines (sed/grep chains, git log ranges)
     work better written to a .sh script file (C:\Users\rasla\AppData\Local\Temp\opencode\)
     and run via `& "...\bash.exe" script.sh | Out-File out.txt`, because inline complex
     commands intermittently produce truncated/empty tool output. cargo/cmake
     text pipelines, tigercli/quicktag runs, grep/sed-style streams, anything WSL-shaped.
     Terser, massively over-represented in the training data, fewer syntax fumbles.
     NOTE (2026-08-16): WSL has no distro on this machine — use `rg` (ripgrep, installed
     via winget) for ALL corpus/file greps: ~5x+ faster than Select-String on the big
     dumps and the model knows its flags cold. If a fresh shell can't find `rg`,
     re-import the PATH: `$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")`.
  3. EVERYTHING COMPLEX = a Python file (the existing WINDOWS SHELL RULE): both shells are
     dumb glue; the logic lives in the scripts.
  The shells are glue; Python owns the logic.
- **THE LOCKED-DLL TRICK (2026-08-16, the deploy toolbelt)**: a crashed destiny2 zombie can
  hold the dcv build's steam_api64.dll with an unkillable handle (access-denied taskkill +
  invisible in the Task Manager). The fix WITHOUT a reboot = the rename trick:
  `Rename-Item steam_api64.dll steam_api64.dll.broken` (the zombie's handle stays on the old
  name; the original path frees) → copy the replacement in → the zombie keeps its broken
  copy until it dies. The fallbacks: `wmic process terminate` for a killable-but-denied
  process (s1-3-swap-lane.md:224), and a reboot for a truly stuck one. ALWAYS try the
  rename before the reboot.
- **METHOD (2026-08-15, the contract-first principle)**: the in-process Sunrise DLL is the
  only proven-working server implementation for this client. Its behavior IS the spec —
  divergence from it is a bug until proven otherwise. Every new server capability starts
  with a DIVERGENCE CENSUS (grep every mode-gated branch + diff the in-process behavior
  end-to-end) BEFORE any implementation. The working contract lives in
  RE_output/claims/s1-accept-contract.md (the living spec, one section per milestone).
  Elimination-by-diff, never by-theory: a boot only happens when the diff names a
  candidate or says "nothing left."

## Session protocol (2026-08-15)

- **BOOT BRIEF RULE (2026-08-17, user-requested)**: every time a boot test is about to
  run, the response MUST include the boot's purpose/payoff summary — what we learn from
  THIS boot, win or lose, and what it explicitly does NOT test. Never launch without it.
- **`STATE.md` (root) = the living snapshot. Read it FIRST** — before HANDOFF or FINDINGS.
  After any restart/compaction, the first action of any session is to rewrite STATE.md
  from disk (distill, don't re-derive). FINDINGS stays the append-only archive.
- **Escalation contract**: invoke the outside-review session with "STATE + incident <ts>"
  only. Reviewer returns facts w/ evidence pointers, a ruling, bounded actions, and a
  DO-NOT list. The reviewer audits STATE against disk; the main session owns the pen.
- **Incidents**: `python -X utf8 RE_scripts\incident.py` digests the session DB + all
  server/client logs + processes/listeners + acceptance-stack hashes into
  `RE_output\incidents\INCIDENT_<ts>.md`. Run it when anything breaks live; it is the
  one-file catch-up for every party. Re-verify hashes before every game boot.

## THE UNIVERSAL LESSONS (2026-08-20, binding — what the equip front paid for)

The subclass-equip panel took five failed delivery-shape boots (16/C/M/N/P) and
closed in ONE boot once the discipline below applied. Every rule = a named
failure mode from this front. DO NOT re-learn them.

1. **THE REFERENCE IS THE ORACLE.** Fetch the upstream/community tree FRESH and
   check the history since the last fetch before ANY mechanism claim about it.
   A stale partial clone produces false lessons (the "upstream has no
   subclass-equip flow" lesson was refuted — the nine commits postdated the
   partial fetch). Read the reference's COMMENTS like documentation and quote
   them in claims — the fix's key ("or the Client completes against the old
   store") was sitting in an upstream comment the whole time.
2. **INSTRUMENT BEFORE INTERVENTION.** When a behavior is unexplained, the next
   move = the discriminator instrument (the kind hook), never another fix
   guess. Design the instrument the moment the question is named; NO fix rides
   a boot until the instrument deploys (the reviewer's DO-NOT #1).
3. **COMPLETE THE MAP BEFORE MOVING.** Every claim about a function = its full
   body read end to end + its xref census. Dumped-but-unanalyzed functions (the
   sink FUN_1412f3660 — dumped 08-17, analyzed 08-19) and un-priced gates (the
   inspected-def compare that killed boot P) are where the wrong fixes are born.
4. **THE COMPLETION VIEW.** In a client-server protocol, the reply envelope IS
   part of the contract: hunt the transaction-completion semantics (the
   promised revision, the ack token), not just the payload content. "The apply
   ran" ≠ "the transaction completed" — all five shapes delivered content; the
   missing piece was the completion token (D1).
5. **LOG ROUTING, NOT ACTIVITY.** Instrument the decision points (which
   kind/class each object resolves to), not just "machinery fired." Activity
   hooks read "alive" on every dead delivery — the polls/evals/dispatch fired
   on all five failed boots.
6. **PRE-NAME THE NEGATIVE.** Every boot = a falsifiable claim + a pre-mapped
   next step for the negative. A composed variable is acceptable ONLY if the
   negative stays decisive; record the attribution gap honestly (the winning
   boot's five components = one contract; which was load-bearing = unproven,
   recorded).
7. **ESCALATE AFTER N FAILURES.** Two consecutive failures on the same question
   = write the honest failure list + the outside review (STATE + incident).
   Never let the same session keep guessing — the reviewer's DO-NOT list is
   what broke the loop.
8. **THE DISK IS THE TRUTH.** The report-back = a pointer; the deliverable =
   read end to end; the load-bearing claims = spot-verified on disk. This
   caught the INT32_MIN correction, the drifted line cites, and the t=0 false
   alarm before any of them shipped a wrong fix.
9. **DOCUMENT EVERY GATE'S EXPECTED VALUE.** A verification that reads a log
   line without a documented expected value becomes its own hazard (the t=0
   empty-account identity warn nearly triggered a false fix — the expected
   value is now recorded in FINDINGS 13.4).
10. **THE CONTRACT IS THE VARIABLE.** One boot = one delivery contract with the
    census as the arbiter. The win came from the upstream-exact 403 as a single
    falsifiable unit — not from another shape theory.

11. **AN EXONERATION IS ONLY VALID IN THE DIRECTION IT WAS TESTED.**
    Record the DIRECTION of every negative test, and never generalise a
    one-directional negative into "X is exonerated." Cost of the violation
    (2026-08-22, FINDINGS 15.8/15.9): 14.17 declared the flags "fully
    exonerated" from two probes that BOTH turned flags ON. The true cause was
    a flag being ON, under which "still broken" was the PREDICTED result, not
    a refutation. That false exoneration removed flags from the candidate set
    for six days, nine findings entries, an outside escalation and two full
    sessions of server-side search that kept correctly concluding the data was
    healthy - because it always was.
12. **EVERY BOOT BRIEF STATES ITS GRAPHICS DELTA.** On this Mac the renderer
    compiles cold every launch (no persistent MoltenVK/DXMT shader cache), and
    character pick is the first heavy renderer work. Changing an EQUIPPED
    item's definition changes what must compile there. Cost of the violation
    (2026-08-22, FINDINGS 15.7): a data-correct loadout experiment introduced
    two never-before-rendered weapon models and crashed the game at pick - the
    brief had named an art-index hazard and missed the real one. State how
    many new models an experiment introduces, and minimise it.

13. **A NULL RESULT INDICTS THE INSTRUMENT BEFORE THE SYSTEM.**
    When an expected line does not appear, the FIRST hypothesis to eliminate is
    that the measurement never ran — not that the system lacks the behaviour.
    Prove liveness from the artifact itself, e.g.
    `grep -ac "<instrument literal>" <deployed binary>`, and design every
    instrument so it emits a line on the BORING path too. An instrument that can
    only fire on the interesting case turns silence into an unreadable result.
    Cost of the violation (2026-08-25, INCIDENT_2026-08-25_false-loops.md): two
    boots and a wrong strategic call — "the client publishes no descriptor,
    don't boot the rig" — from an instrument that was never deployed. Note this
    is a REPEAT: the deploy-script gate/restamp ordering bug was the same shape,
    a rig failure attributed to the subject.

14. **THE ARTIFACT UNDER TEST MUST BE PROVEN TO BE THE ARTIFACT YOU BUILT.**
    Never infer provenance from a script's success output. Assert it: the
    deployed hash equals the build hash, checked by the script, which fails loud
    on mismatch. A pipeline step that can silently consume a stale input will
    eventually consume one, and it will report success while doing it. Rule 8
    ("THE DISK IS THE TRUTH") governs claims and documents; this is its build-
    artifact half, and its absence is what made lesson 13 possible.

15. **EVERY SOURCE HAS A SCOPE OF AUTHORITY. NAME IT BEFORE CITING IT.**
    A committed tree is authoritative for "what does their committed code do"
    and for NOTHING ELSE — not for what they have demoed, not for what they know.
    Before any claim built on a source, state the question the source can
    actually answer, and never label a cross-scope inference "decisive."
    Cost of the violation (2026-08-25): called upstream's empty search result
    decisive proof about their fireteam demo and retracted it one turn later.
    The reading was CORRECT and the ref was CURRENT — the failure was scope, so
    do not mis-file this under lesson 1 (fetch freshness). Corollary: a fact the
    user has already supplied ("their demos lead their tree") is binding
    context, and re-deriving a conclusion that contradicts it is a bug.

16. **MARK EVERY LINK IN THE CHAIN, NOT THE INTERESTING ONE.**
    Before proposing any fix, enumerate the full chain and give every link an
    evidence mark: verified-by-execution / verified-by-reading / assumed /
    unknown. An unexamined link is NOT a passing link, and "assumed" must never
    be silently promoted to "verified" by repetition. Never say "one boot away"
    unless every other link carries a verified mark.
    Cost of the violation (2026-08-23..25): three consecutive "one boot away"
    claims, three failed boots. The chain walk that the user finally forced
    (FINDINGS 20.38) produced better information in one pass than all three
    guesses — four unverified links and a subsystem absent from both trees.

17. **NOTHING IN A SHIPPED PROTOCOL IS OPTIONAL.**
    A retail game does not carry decorative message types. Every entry in the
    client's own schema exists because something in the game requires it, so an
    UNIMPLEMENTED type is a missing REQUIREMENT we have not tripped over yet —
    never a deferred nicety. The same holds for a failure enum: if the client can
    name a rejection cause, some path produces it.
    Before building on any protocol, census the client's type table against our
    handlers and write the gaps down. Treat each gap as load-bearing until a
    positive test says otherwise; do not rank candidates by how cheap they are to
    test, which is what ranking on the wrong axis looks like.
    Cost of the violation (2026-08-25, FINDINGS 20.55): types 13/14
    `request_peer_reservation` / `release_peer_reservation` exist in our tree ONLY
    as strings in two log name-tables — no handler at all — while the client's
    failure vocabulary carries `no-reservation` and `no-ambassador-reservation`.
    We named a foreign peer in the roster without ever reserving a slot for them
    and the client froze hard. The lead was recorded in 20.53 and deprioritised
    for three boots of trailing-field guesses because those were cheaper to run.
    This is Universal Lesson 4 ("the reply envelope IS part of the contract")
    generalised, and it was re-learned the expensive way after already being
    written down once.

### THE PRE-BOOT CHECKLIST (binding — a boot costs the user real time)

Before asking for ANY boot test, all four must hold:

1. **Provenance** — the deployed artifact's hash equals the build's, asserted by
   the tooling, and any new instrument literal is confirmed present IN the
   deployed file.
2. **Liveness** — a named line that MUST appear if the instrument ran at all,
   independent of the outcome under test.
3. **Both negatives pre-named** — the CONTENT negative ("routable=0 means X")
   AND the ABSENCE negative ("zero lines means the instrument did not run, which
   means Y"). Lesson 6 requires the first; today proved the second is where the
   damage lives.
4. **Chain marks current** — the link this boot resolves is identified, and
   every other link's mark is written down (lesson 16).

Prefer, over all of the above, a change that makes the failure impossible to
express: a deleted overload, a deleted default argument, a compile error. The
moves that have actually paid on this project all convert runtime vigilance into
a compile-time or assert-time failure. Vigilance does not survive a long day.

## THE ANTI-RABBIT-HOLE RULES (2026-08-20, binding — the execution contract for lanes AND the main session)

The observed killer failure = the RABBIT HOLE: reacting to a symptom
turn-over-turn, fixing one thing, causing another, looping until someone has to
say "stop, breathe, get the facts straight, execute surgically." Every rule
below = that failure + its countermeasure. Every lane brief carries: THE
EVIDENCE ANCHORS, THE FALSIFIABLE QUESTION + THE EXPECTED VALUE, THE DEATH
SAFETY, THE DO-NOT.

1. **STOP → SEE IT END TO END → VERIFY → ONE SURGICAL ACTION.** When a symptom
   or a failure appears mid-work: (a) STOP — no immediate fix; (b) SEE the
   whole picture FIRST — the full chain, the expected values, the newest
   evidence — before touching anything. The canonical near-miss: the deploy's
   t=0 identity warn, where a deep hash-hunt nearly shipped a false fix
   because the end-to-end read (which pass logged the line) never happened
   first. (c) VERIFY the facts from disk — the newest timestamp wins; (d) ONE
   surgical action with a pre-named expected outcome. If the outcome ≠
   expected: STOP again — never a second guess in the same motion, never a
   cascading edit while the first one is unproven.
2. **A FIX MUST NOT MAKE NEW BUGS.** One variable per fix; the
   contract-preserving shape (the reference is the oracle); the harness gate
   before deploy; and the regression check of the previously-working behavior
   in the validation boot (e.g., the equip panel still switching).
3. **THE REFUTATION IS A DELIVERABLE.** Every brief names what would refute
   the expected answer, and the lane is instructed to write the refutation if
   it lands there. The lane's incentive = the truth, not the brief's
   confirmation. "A NEGATIVE is decisive" = uniform, not per-brief.
4. **THE 3-LINE REPORT-BACK.** The report-back = a fixed template (what
   landed / where / one-line verdict per question) — ≤3 lines, ≤10% of the
   budget. The budget belongs to the files. (The observed death mode: the
   report-back ate the budget — lanes C and T died at exactly this step.)
5. **PHASE-CONSISTENCY.** Each phase re-reads the PREVIOUS phase's claims
   before writing its own — the lane checks its own record, and the drift
   stops at the file. The per-phase claims = the required minimum deliverable;
   the consolidated file = OPTIONAL (the main session = the collector — the
   resume pattern that recovered lane T).
6. **THE LOAD-BEARING MARK.** The brief marks which claims are load-bearing;
   the lane writes those with full quotes + exact offsets (the main session's
   spot-verification reads them first — the verification arm exists for a
   reason).
7. **TWO DEAD-ENDS = A REWRITTEN BRIEF.** The same sub-question dead-ending
   twice → the brief gets rewritten with a corrected premise, never re-run
   verbatim (the escalation contract, applied to lanes).
8. **THE COLLECTOR IS ALWAYS ARMED.** The main session completes a dead lane's
   deliverable from the raw, or spawns a resume with a synthesis-only brief.
   Check disk + opencode.db session_message BEFORE any respawn (the 12.6
   correction — never re-spawn blind).

## THE NO-SYNTAX-TAX RULES (2026-08-20, binding)

Simple syntax errors are individually cheap but compound across a session.
Each rule costs seconds; the failed-run + debug cycle costs minutes. Apply
unconditionally.

1. **PARSE-CHECK BEFORE RUN.** Every new or modified script gets
   `python -m py_compile <file>` (or `bash -n`, or the equivalent) BEFORE its
   first real run. Never launch a script that has not parsed.
2. **SMOKE-RUN FIRST.** Every new script runs once against a trivial input or
   the scratch env and must exit 0 before the real run (the harness-scratch
   pattern, generalized to ALL scripts). The real run = the second run.
3. **ONE GHIDRA RUN = ONE SCRIPT.** The lane Ghidra scripts get the
   parse-check + the smoke pass BEFORE the ~77 s project run — a syntax error
   at the end of a Ghidra run wastes the whole run (the observed 3-6 debug-run
   iterations per script = exactly the tax this kills).
4. **VERIFY THE BYTES BEFORE CONCLUDING.** When console output looks mangled
   (missing "stage=", stray NULs, dropped characters), re-read the RAW bytes
   of the source (the file or the log) before drawing any conclusion — the
   t=0 near-miss's second face was a mangled log line nearly read as truth.
5. **NEVER GUESS THE TARGET TEXT.** The edit tool's oldString = copied from
   the file after a fresh read. A failed match = re-read the section, never
   re-guess (two failed-edit rounds this session alone).
6. **ASCII-ONLY COMMENTS.** No non-ASCII in source comments — the U+2014
   em-dash mojibake corrupted three comments this session; the fix cost more
   than the dash was worth.

## Where to start in this directory
- **HANDOFF_2026-08-15.md** — READ THIS SECOND (after this file). The conversational
  handoff: standing hard rules (flash-only subagents, delegate-don't-act, cost
  discipline), working agent-config gotchas, the broken-tools list, in-flight state,
  and the reasoning patterns. Written for a model switch; nothing in it exists
  anywhere else.
- **GAME_PLAN_2026-08-14.md** — the CURRENT strategy (goal: derive a FULL private server for
  the D2 Arrivals build — standalone server, persistence, static world, then combat/missions;
  honest scope: parity impossible, multi-year). Read this first for "what should we do."
- **GAME_PLAN_2026-08-07.md** — the original D1-centric strategy (4 tracks; D1 items are now
  standing watch only). Superseded for the D2/Sunrise track.
- **FINDINGS_2026-08-14.md** — PC RE results: destiny2.exe unpacked (VMProtect), 16-anchor
  function map, client-side contract CLOSED. The five specs in **RE_output/claims/** are the
  reference docs (dispatch map, spawn recipe, family-4 wire layout, signon, deadorbit).
- **FINDINGS_2026-08-07.md** — full research. Within it:
  - **Session handoff → watchlist & next steps** — time-boxed + standing watch items.
  - **Reference: D1 architecture & the emulation gap** — the educational state-of-the-art.
  - **Deep review** (V4 Pro) and **two Breadth reviews** (GLM 5.2) — independent verdicts.
  - **Frontier review** (Qwen 3.8 Max via @general) — verify/beyond/consolidate/plan;
    corrects the game plan (capture before XenonRecomp; D1 API key check = next step).
  - kimi K3 run (2026-08-07) FAILED to terminate: did a 13-step research loop (~$0.73) but
    never emitted a final answer (`finish:"unknown"`, 0 output tokens). Do not re-escalate
    to kimi for this topic unless the failure mode is addressed. Its useful residue: kallsyms'
    rpcs3-upstream fork has a branch `fix/nv0039-destiny-gather` (D1-specific RPCS3 fix).

## Skills/context for this research (vs the car project)
The user runs the separate VW CarPlay shim project in `../car-projects/` — do NOT mix the
two. It is only relevant here as a *transferable-skills analogy* (Ghidra + client-side
hooking skills transfer; the car project is self-contained, D1 has a remote authoritative
server that can't be scraped). Keep this research's files in THIS directory only.
