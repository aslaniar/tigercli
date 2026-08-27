STATUS: historical - superseded by HANDOFF_OPENCODE_2026-08-25_EVENING.md and STATE.md (marked 2026-08-26). Kept for archaeology.

# HANDOFF TO CLAUDE - 2026-08-23 ~23:3x (fresh session, self-contained)

You are taking the pen on the Destiny/Sunrise private-server fork. This
document is self-contained; read it fully, then STATE.md, then the FINDINGS
sections named below.

## WHAT THIS PROJECT IS

A reimplementation of Bungie's backend (BAP protocol + activity host +
SignOn/content) that runs Destiny 2's Season-of-Arrivals build offline and
now multiplayer across a LAN. Two machines: this Mac (192.168.1.164) hosts
the standalone server under GPTK wine; a Windows gaming rig
(192.168.1.136) runs the game client. Tonight we got both clients signed on
SIMULTANEOUSLY as two different provisioned accounts for the first time -
identity, crypto keying and persistence isolation all verified green - and
then hit one named server defect that blocks the next step.

## READ IN THIS ORDER

1. STATE.md - living snapshot; headline + open item 3 are current.
2. FINDINGS_2026-08-23.md sections 20.14, 20.15, 20.16 (tonight's arc:
   Tower blocker found+fixed -> dual-client milestone -> the desync defect).
3. RE_output/claims/p2-landing-review-claude.md - tonight's earlier outside
   review; D3 and A2 items remain open.
4. ~/.opencode/plan/p2-tower-conn2-instrument.md - tonight's plan doc with
   the decision tables (mostly executed; section 4 has follow-ups).

## WHERE THINGS STAND

WORKING: solo play end to end on the private server; two provisioned
accounts; per-account channel keys; rig + Mac signed on simultaneously with
verified identity stamping (matched=slotN served=N on all four connections)
and zero signature failures; the rig reached the Tower twice tonight.

THE NAMED DEFECT (your front): when a second client signs on, the FIRST
client's presence-driven family-4 re-subscribe carries a CHANGED manifest
(55 -> 56 objects). stage_family4_snapshot() in
Sunrise/src/server/bap/encrypted/queuez/staging/queuez_family_staging.cpp
refuses it via the replay branch (before.family4Active &&
!same_manifest), while the caller in push/queuez/queuez_subscription.cpp
STILL SENDS THE FRAME ("a refused staging still sends the frame"). Result:
the client applies version-N+1 content while the server mirror stays at
version N. Mirror/client desync -> downstream kicks (PONY / black screen /
marionberry on either machine).

CORRECTED ATTRIBUTION you must not un-learn: the refused subscribes are the
MAC's (key=0, root ...0100100, objs=56, front=0x32D7B974) presence refresh,
NOT the rig's. The rig's own subscribe records fine (objects=49
recorded=1). Earlier tonight this was mis-attributed to the rig; the
stage=subscribe_in instrument lines corrected it.

ALSO EXONERATED TONIGHT: my re-staging of the rig's local soids into the
...110 band. The rig failed identically AFTER reverting those settings
(C4 boot), so resoid was never the cause. The revert is already applied;
rig is back on the legacy band. Backup of the ...110 variant exists on the
rig if you ever want it:
dcv build\bin\x64\Sunrise\settings.json.bak_m3g1_resoid

## YOUR TASK

Open the "queuez mirror desync" front:
1. Read the full queuez versioning history BEFORE designing anything: the
   comments in queuez_family_staging.cpp, queuez_subscription.cpp,
   queuez_deferred_push.cpp reference two prior incidents (skipped-increment
   crash, boot-G roster refusal). The staging policy you change interacts
   with both.
2. Decide what a changed-manifest re-subscribe SHOULD mean: accept as a new
   version? incremental update? explicit resync flow? Check what the real
   client does with each answer shape (its accept/reject behavior is
   observable via our handle_message observer + the stage=crypt/companion
   instruments).
3. Implement ONE policy as one surgical change. The instruments stay live
   until the front closes: stage=identity, stage=arm, stage=crypt,
   stage=family4_refusal, stage=subscribe_in.
4. Boot protocol to verify: Mac signs in first (user launches from Whisky
   UI), parks anywhere; rig second (user launches); rig picks a character.
   Success = no PONY/black screen, family4_refusal gone or handled, both
   sessions stable for minutes.

## STACK FACTS (all verified 23:30)

    server       UP pid 96159, exe 88935f8eedf76256, board empty
                 RE_output/s1_accept/sunrise-server.exe under
                 mac-port/launch-server-macos.sh (GPTK wine, own prefix)
    build tree   RE_build/Sunrise-fork-inventory (branch integration);
                 build dir Sunrise/build-mingw; deploy = copy exe ->
                 RE_scripts/restamp_build_data.py <cache> <exe> --apply ->
                 restart. NEVER skip the restamp after an exe rebuild.
    cache        ts 0x6A8BDAA2 size 0x2CFB000 eqHash 0xAC65559674A52DD8
                 (eqHash drift-check: run the exe --print-provisioned-hash;
                 note macOS has NO `timeout` command)
    clients      mac dll 83345d39 (llvm-mingw), rig dll 162972c7 (native
                 MSVC). DO NOT copy the Mac DLL to the rig.
    commits      a9d1cbc keepalive fix + crypto instruments; 41f754b
                 refusal branches; 69b5a91 subscribe_in. All diagnostic
                 fronts marked "strip when closed".
    backups      *.bak_p2b2_20260823_213659 (exe+cache),
                 settings.json.bak_m3g1_resoid on the rig
    harvest      RE_output/boots/20260823_p2c1_identity_crypt/,
                 .../20260823_m3_g1_dual_signon/,
                 .../20260823_m3_g1r_resoid_retry/

## RIG ACCESS

ssh -o ControlPath=~/.ssh/cm-rig rasla@192.168.1.136 '<cmd>'
Remote shell is cmd.exe (`cd /d` for paths). The user launches BOTH game
clients themselves now - Mac via Whisky UI (their preferred path; do NOT
fix or use mac-port launch scripts for them), rig by their own hand.
NEVER send inline multi-line PowerShell over ssh: write a .ps1, scp it,
run with -File, verify on disk.

## TRAPS THAT BIT TONIGHT - DO NOT REPEAT

- macOS has no `timeout` command: silent tool failures come from that.
- `$?` after a pipeline reports the LAST command; capture exit codes plain.
- In zsh, `echo ===X===` triggers equals-expansion; quote your separators.
- ps-grep pipelines can show phantom matches; re-read before concluding.
- Relative paths in compound commands break when workdir changes mid-chain;
  use absolute paths for cross-tree copies.
- Timestamps: several entries written tonight claimed times ~20 min AHEAD
  of their file mtimes (STATE "~21:0x" @20:52, brief "~21:0x" @20:49,
  20.11a "~21:1x"). Stamp from `date`, never from memory.
- DETAIL_COVERAGE invariant red is EXPECTED and inert (proven, FINDINGS
  20.11) - 17/18 is the healthy state.
- Do not chase the ship-render / black-screen-on-entry bug: parked as
  INTERMITTENT with two data points (FINDINGS 20.15).
- D3 (ensure_token config_guid branch) and A2 (bottle wipe cause) remain
  open from the landing review - noted, not yours unless asked.

## REPORTING

Record findings in FINDINGS_2026-08-23.md (or a new dated file) with exact
times from `date`. Update STATE.md headline/open-items when the picture
moves. Report-backs are pointers; the files are the deliverable.
