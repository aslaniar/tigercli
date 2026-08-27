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
