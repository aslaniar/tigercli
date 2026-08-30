# ENVIRONMENTS - platform and tooling operations (the deep env layer)

STATUS: live (2026-08-26). Mixed-era document: blocks marked [PC-era] were the
2026-08-15..22 operating practice on the Windows rig; they remain authoritative
FOR THE RIG and historical reference for the Mac. The Mac (this machine, since
2026-08-22+) is noted per block. Loaded conditionally from AGENTS.md whenever a
session touches deployment, tooling invocation, Ghidra runs, or cross-machine ops.

## Machine map
- **This Mac** - primary analysis machine. destiny2 client can run here; the
  renderer compiles cold every launch (no persistent MoltenVK/DXMT shader cache)
  - see LESSONS #12 before any loadout-touching experiment.
- **The rig** `rasla@192.168.1.136` - ssh master ~/.ssh/cm-rig (may need to be
  reopened; needs the USER's password - FINDINGS_2026-08-24.md:1476). Rig game
  dir: `C:\Users\rasla\Downloads\destiny-preservation\dcv build\bin\x64\`.
  Client DLL deploys there via RE_scripts/deploy_client_dll.sh <mac|rig>.
- **Mac NIC map - THE INTERFACE IS NOT A CONSTANT, RESOLVE IT EVERY TIME.**
  en0 = Wi-Fi 192.168.1.164, en13 = ethernet 192.168.1.7. Which one carries
  rig-bound traffic depends on WHICH LINK IS ACTIVE: 2026-08-29 it was en0
  (Wi-Fi, 20.166); 2026-08-30 it is en13 (the user switched to ethernet, 20.196
  R6). A capture on the stale interface yields an EMPTY pcap that reads as a
  clean null. `arp -n 192.168.1.136` cannot disambiguate - it lists the rig on
  BOTH interfaces. Run `route -n get 192.168.1.136` at capture time, and prefer
  capturing BOTH: the server binds 192.168.1.164 (en0) while client->rig traffic
  egresses via the route, so one paired session can be split across two NICs. WATCH: `arp -a` carries a STATIC "permanent"
  entry 192.168.1.136 -> en0's own mac (self-referential) next to the correct
  dynamic one - prime suspect if paired DTLS establishment ever fails at L2.

## Deploy + build commands (current)
- Fork repo: RE_build/Sunrise-fork-inventory, branch upstream-gameplay-scoped.
  Build: cd RE_build/Sunrise-fork-inventory/build && make -j8 (src/steam/**
  compiles ONLY into steam_api64.dll).
- Deploy server: bash RE_scripts/deploy_p2d6_gameplay.sh (drops clients; gates
  inside; stages from build output and asserts deployed==built).
- Deploy client DLL: bash RE_scripts/deploy_client_dll.sh <mac|rig> "<literals...>"
  - hash assert + literal grep IN the deployed file; never skip.
- Log locations: server RE_output/s1_accept/Sunrise/logs/sunrise.log; each
  client <game>/Sunrise/logs/sunrise.log. Captures contain NUL bytes - grep
  them with `grep -a` (plain grep returns nothing and reads as a clean null).

## [PC-era] Shell layout (three layers)
A three-layer split, NOT a config change:
1. WINDOWS-NATIVE OPS = PowerShell (elevation, Get-NetTCPConnection port checks,
   process start/stop, server restarts, the file-form edits).
2. UNIX-SHAPED TOOLING = bash. THE INVOCATION: `bash` on PATH = the WSL stub,
   and WSL has NO distro installed. USE GIT BASH EXPLICITLY:
   `& "C:\Program Files\Git\bin\bash.exe" -lc "..."` from PowerShell.
   Gotchas: keep the whole bash command inside ONE single-quoted PowerShell
   string; multi-step pipelines work better written to a .sh file (run via
   `& "...\bash.exe" script.sh | Out-File out.txt`) because inline complex
   commands intermittently produce truncated/empty tool output.
3. EVERYTHING COMPLEX = a Python file: both shells are dumb glue; logic lives in
   the scripts.

## [Mac-current] Corpus greps
Use ripgrep (`rg`) for ALL corpus/file greps - ~5x+ faster than Select-String /
grep -r on the big dumps, and models know its flags cold. NUL-bearing captures
still need `-a`. If a fresh shell cannot find a tool, re-import PATH:
`export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"` (the PC form was
PowerShell Environment-variable re-import).

## [Mac-current] Python interpreters
DEFAULT for anything touching sqlite or installed tooling: `/usr/bin/python3`.
The default `python3` on PATH is miniconda's and its sqlite3 binding is broken
(`ImportError: dlopen _sqlite3 ... _sqlite3_enable_load_extension`); scripts
parse fine under it then fail at import time, so parse-checks do not catch it.
gate_boot/build_index work under either; incident.py needs /usr/bin/python3.

## [PC-era] GHIDRA TOOLING RULE (2026-08-16, hard)
All Ghidra automation runs in PYTHON (headless-analyzer scripts / PyGhidra),
never Java - the Java batch files in RE_scripts (CountRunFunctions.java,
ExportCorpus.java, etc.) are legacy and must not be the pattern for new lanes.
THE INVOCATION (2026-08-17, verified - all three gotchas):
`& "C:\Users\rasla\tools\ghidra_12.1.2_PUBLIC\support\pyghidraRun.bat" -H "RE_output\ghidra"
d2_full_cuib -process destiny2_unpacked_full.exe -noanalysis -scriptPath "RE_output\content"
-postScript <script.py> -log "RE_output\ghidra\<name>_run.log"`
Gotchas: (a) PLAIN analyzeHeadless fails ("Ghidra was not started with PyGhidra");
(b) WITHOUT -noanalysis the -process triggers FULL auto-analysis of the
38k-function program (hours); no-analysis runs take ~77 s; (c) shared-project
layout: RE_output\ghidra = location, program = /destiny2_unpacked_full.exe,
base 0x140000000; dump-side runtime base resolves per boot.
(On the Mac there is as yet no Ghidra project equivalent; reference-lane scripts
in RE_output/claims follow lane_sobject_ghidra*.py as the pattern.)

## [PC-era] THE LOCKED-DLL TRICK (the deploy toolbelt)
A crashed destiny2 zombie can hold steam_api64.dll with an unkillable handle
(access-denied taskkill + invisible in Task Manager). Fix WITHOUT reboot = the
rename trick: `Rename-Item steam_api64.dll steam_api64.dll.broken` (the zombie's
handle stays on the old name; the original path frees) -> copy replacement in ->
the zombie keeps its broken copy until it dies. Fallbacks: `wmic process
terminate` for killable-but-denied; reboot last. ALWAYS try rename first.

## Incident tooling
- `python -X utf8 RE_scripts/incident.py` digests session DB + logs + processes +
  listeners + acceptance-stack hashes into RE_output/incidents/INCIDENT_<ts>.md.
  [PC-era as of 2026-08-26: hardcoded Windows paths/commands and legacy opencode
  DB tables - output is PARTIAL on the Mac until the port lands.]

## Claude Code interop note
CLAUDE.md at this root imports AGENTS.md so both harnesses read one source of
truth. Model-tier mappings differ per harness (opencode ladder vs claude tiers) -
see AGENTS.md SPEND MAP.

## SHELL: two ways a tool-invoked command hangs after its work is done (2026-08-27)

Both cost minutes and look like a crash. Neither is one.

1. **A script that launches the server.** `mac-port/launch-server-macos.sh` (and anything
   wrapping it, e.g. `RE_scripts/reset_lobby_claims.sh`) starts a long-lived process that
   inherits the caller's stdout. A tool call waits for that pipe to close, so it hangs
   forever even though the server came up fine. WORSE: if the wrapper already KILLED the
   old server, an interrupt leaves NO server running at all - which then looks like the
   overnight "marionberry" symptom (20.98). Launch it as a background job instead, and
   verify with a separate short call (lsof + /lobby + nat probe).
2. **ssh over the ControlMaster.** `RE_scripts/deploy_client_dll.sh rig` prints
   `deployed to rig OK` and then hangs holding the multiplexed connection open. The
   deploy IS complete at that point - the script's own hash+literal asserts have already
   passed on the rig. Add `-o ServerAliveInterval=3 -o ServerAliveCountMax=2` when
   probing, and never chain a rig deploy with other work in one call: an interrupt then
   leaves the two machines on DIFFERENT builds.

RULE: one long-running or ssh-touching action per call, and re-verify state after any
interrupt rather than assuming the call did nothing.


## OPERATIONAL FACTS (moved from STATE.md 2026-08-28, doc-governance diet)
STATE's enforced shape is verdict + deployed + next gate + reading order; platform,
deploy, log and cross-machine specifics belong here per the AGENTS.md router.
  - Fork repo: RE_build/Sunrise-fork-inventory, branch upstream-gameplay-scoped.
    HISTORY NOTE: TWO COMMITS CLAIM p2(39) (f2d0995 Claude, 9639aa4 opencode).
    Next number continues upward; do not renumber. Deployed hashes live in
    DEPLOYED above, not here; build tree matches deployed.
  - Build: cd RE_build/Sunrise-fork-inventory/build && cmake . && make -j8. BOTH
    targets take EXPLICIT source lists in Sunrise/CMakeLists.txt, NOT globs - a new
    .cpp must be added there or it silently fails to link (bit c2764aa and p2(67)).
  - Deploy server: RE_scripts/deploy_p2d6_gameplay.sh (gates inside; asserts
    deployed==built; restamps cache - old exe+cache pairs are inseparable). Client:
    deploy_client_dll.sh <mac|rig> "<literals...>" - hash + literal assert, never skip.
  - NEVER launch the server or deploy to the rig chained with other work in one shell
    call: both hang holding a pipe AFTER succeeding, and an interrupt then leaves the
    server dead or the machines on different builds (ENVIRONMENTS.md "SHELL").
  - Server START (after deploy): nohup bash mac-port/launch-server-macos.sh (GPTK
    wine 7.7, SunriseServer prefix). Verify: lsof TCP 8443/30975/8099 + UDP 3074, and
    a crafted nat probe gets a 16B reply (snippet in HANDOFF_OPENCODE_TO_CLAUDE).
    8443 TLS is BROKEN (SEC_E_UNSUPPORTED_FUNCTION) - do not route anything new
    through it. SignOn rides in-process consume_http, which answers ONLY /SignOn;
    everything else that must reach the server uses the plaintext admin listener
    8099 (20.99). Presence store is IN-MEMORY: restart wipes stored keys.
  - CLIENT LAUNCH: user does it via WHISKY GUI (bottle D1FB4A66-...). A CLI launch
    does NOT wedge - it stops at bootflow:start task ENUM(0), which is the
    press-to-start gate, because nothing presses a key (20.99 item 5; a good boot
    shows ENUM(0) completing after ~15.7 s of human input). Nothing is wrong with
    the binary or the prefix. Autonomous boots would need synthesized input.
  - Logs: server RE_output/s1_accept/Sunrise/logs/sunrise.log; clients
    <game>/Sunrise/logs/sunrise.log. `bash RE_scripts/boot_verdict.sh` reads both
    machines + server and rules mechanically.
  - Log DIGGING (2026-08-27): index with `logindex.py --out <name> server=<path>
    mac=<path> rig=<path>`, query with `logq.py <db> --ev/--stage/--grep
    [--aligned]` (full-width, file:line-cited). Raw grep -a/sed = one-line
    peeks only; a frozen capture dir can be indexed as-is.
  - Rig: ssh master ~/.ssh/cm-rig to rasla@192.168.1.136 (password only to REOPEN);
    ICMP is firewalled so `ping` is NOT an aliveness test - the socket is. Sleep
    disabled on AC. Game dir C:\Users\rasla\...\destiny-preservation\dcv build\bin\x64\.
  - Identities: mac steamId ...861 / xuid ...ec5 (DEFAULT, no key in settings.json);
    rig ...862 / ...ec6 (authored). Member keys are BOOT-SCOPED; never hardcode.
  - Mac: /usr/bin/python3 for DB/sqlite (miniconda's is broken); plain `python3` for
    capstone. Static RE: destiny2_unpacked_full.exe, base 0x140000000, .text raw 0x600
    va 0x1000, .pdata raw 0x20B9A00 for exact function bounds. LOG STRINGS ARE NOT IN
    THE BINARY - use caller capture (LESSONS 18c), not string xrefs.

## [Mac-current] SERVER DIED AFTER AN INTERRUPTED SCRIPT - THE RECOVERY (2026-08-30)

STATE's hard rule says the long-running / ssh-touching scripts HANG AFTER SUCCEEDING and
that interrupting one can leave the server dead. `reset_lobby_claims.sh` did exactly that:
it restarted the server, then hung; the interrupt left NO sunrise-server process and ZERO
listeners. Recovery, verified 2026-08-30:

    nohup bash mac-port/launch-server-macos.sh > mac-port/launch.log 2>&1 &
    for _ in $(seq 1 40); do curl -s -m 2 http://192.168.1.164:8099/ladder >/dev/null && break; sleep 0.5; done
    curl -s -m 3 http://192.168.1.164:8099/ladder          # must return JSON
    netstat -an | grep -E "\.(30975|30976|3074|3075) "     # must list all four

This is step 6 of deploy_p2d6_gameplay.sh lifted verbatim - use it, do not improvise a
launch. A healthy restart also leaves `sessions:[]`, which IS the clean lobby-claim table
reset_lobby_claims.sh exists to produce, so an interrupted reset that you then recover from
has still achieved the reset. Verify the exe hash after recovery: a relaunch runs whatever
is on disk, and it must equal the hash the boot brief names.

## [BOTH MACHINES] TRAP 18 - NEVER ROUND-TRIP settings.json THROUGH A JSON SERIALISER

The client's settings parser is FORMAT-SENSITIVE. Rewriting settings.json with any
serialiser that reformats the whole file - `json.dump`, PowerShell `ConvertTo-Json`,
`jq` - makes the game fail at launch with Bungie's "problem reading game content".
Documented as TRAP 18 in FINDINGS_2026-08-15 (a byte-exact restore was the fix); hit
AGAIN on 2026-08-30 on the rig via `ConvertTo-Json -Depth 40`, which cost a launch during
a live paired-boot setup. It is recorded here because the operational doc is where anyone
about to edit a settings file actually looks.

THE PROCEDURE for changing a client setting:
1. Copy the file to a backup FIRST (`settings.json.bak_<who>_<what>`).
2. Edit it as TEXT with an exact-match insertion or replacement - not a parse/dump cycle.
   The on-disk style is 2-space indent, LF endings, no BOM, no trailing newline games.
3. Diff before writing: the ONLY changed lines must be the ones you intended.
4. For the rig, edit LOCALLY and scp the file up, then scp it back down and compare
   hashes. Editing in place over ssh hides formatting damage.
5. Parse the result once with a JSON reader to confirm validity - reading is safe, it is
   WRITING through a serialiser that breaks it.
