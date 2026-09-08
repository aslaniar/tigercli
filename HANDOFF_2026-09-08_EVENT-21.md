# HANDOFF 2026-09-08 (evening) — THE FRONT IS ONE MISSING MESSAGE

STATUS: live (2026-09-08, end of the Claude Code session). NEWEST HANDOFF —
read this first, then STATE.md's header, then FINDINGS 20.349-20.353.
Supersedes HANDOFF_2026-09-08_GATE-MACHINE.md as the newest (that one's
content stands; this continues it).

## THE ONE-PARAGRAPH STATE OF THE WORLD

The peer-render front has collapsed to a single missing input. p2-212
(paired, both machines in the tower, complete archive) measured it: the
client's world-change executor evaluates OUR session (sid=2, 0x4631748 —
p2-195's slot5), that session climbs 1→2→4 and stops, and the executor
idles 65,308 times a boot waiting for 6..9. The guard that gates the path
to 9 was called 9 times and returned TRUE every time on our session. So
the machinery is aimed at us and willing. What never happens is EVENT 21:
a complete enumeration of arriving event types (first-seen-per-value, 14
distinct ids, no truncation) shows only 8, 30 and 38 in the dispatcher's
valid 4..44 range. The fork already drives that pump — those three arrive
from our own traffic — so this is a message we do not send, not a locked
door. Separately, recv_root ran 12,258 times: the construction root IS
dispatched and bails, which kills the old "never dispatched" framing.

## *** UNCOMMITTED WORK — DO THIS FIRST ***

The client-side instrument changes are UNCOMMITTED in the worktree
`.claude/worktrees/fork-p2211` (branch `wt-p2211` of RE_build/Sunrise-fork).
The Claude Code session that made them was worktree-isolated and could not
run git in the client repo. One file, `milestone_trace_observer.cpp`:

    git -C .claude/worktrees/fork-p2211 diff --stat     # expect 1 file
    git -C .claude/worktrees/fork-p2211 commit -am "p2-212 instruments: evt_sub first-seen-per-event-type + sess_guard + exec_sess"

The change is also saved as a patch at repo root:
`0002-evtsub-first-seen-per-event-type.patch` (the evt_sub half only).

ALSO: that worktree lives under `.claude/worktrees/`, which the harness
treats as disposable scratch. Every other client tree is under RE_build.
Move it when convenient:

    git -C RE_build/Sunrise-fork worktree move ../../.claude/worktrees/fork-p2211 ../Sunrise-fork-p2211

## WHAT IS DEPLOYED RIGHT NOW

- Clients (mac + rig): `steam_api64.dll` = **ec96811586317a4f**, hash- and
  literal-asserted in the deployed file. 71 hook targets, VERIFY PASS.
- Server: **45acf511c6021990** (unchanged; the p2-211 server arm was
  already live). Running.
- **NETWORK: the rig/mac/server settings were re-pointed from
  192.168.1.7 (ethernet) to 192.168.1.164 (WiFi)** because the user moved
  to WiFi and the server could not bind (`transport stage=listen
  result=fail`). Backups: `*.bak_wifi_20260908` on all three. IF THE USER
  GOES BACK TO ETHERNET THIS MUST BE REVERTED or the server will not
  start. ENVIRONMENTS.md's "the interface is not a constant" warning is
  exactly this.

## THE THREE NEW INSTRUMENTS (all shipping, all fired)

| row | RVA | what it answers | p2-212 result |
|---|---|---|---|
| `evt_sub` (re-gated) | 0x16E3140 | every event type that arrives | 14 distinct; 8/30/38 in range; **no 21** |
| `sess_guard` | 0x176CE80 | does the C2 guard pass, on which session | 9 calls, **ret=1 every time**, our session |
| `exec_sess` | 0xC03F70 | which session the executor evaluates | **0x4631748 sid=2 (ours)**, state 1→2→4 |

`evt_sub`'s re-gating is the reusable lesson: a flat budget spent its 24
detail lines in a 16ms window in p2-211 and could not have seen event 21
even if it arrived. It now emits the first occurrence of each distinct
(dword-masked) out-param value, bounded by a 48-key table. That pattern
should be the default for any enumerating probe.

## NEXT STEPS (non-static, ordered so the plan can fail early)

1. **THE DIAGNOSTIC POKE — do this before building an emitter.** Force
   the fork's session to 9 (or mgr+0x8=1) for ONE boot, throwaway,
   reverted at boot end, per the AGENTS.md diagnostic allowance. It turns
   the whole inferred second half (attach → establish → queue producer →
   construction) into measurement in one boot. If the cascade does not
   fire, the emitter work was never the answer and R4's bailing root is
   the real front. This is the only step that can invalidate the plan, so
   it goes first.
2. **EMIT EVENT 21** (the user's call, and the obvious move). Find where
   the fork emits whatever produces 8/30/38 — OUR OWN SOURCE, not client
   disassembly — and add 21 behind a default-OFF setting. The deployed
   instruments report the outcome with no new work: `evt_sub` says whether
   id=0x15 arrived, `sess_guard` whether the guard passed on our body,
   `exec_sess` whether the state moved.
3. **TRACE THE WORKING CASE.** The client's own sessions 0x45A2C18 (sid=0)
   and 0x45DBD60 (sid=1) reach state 6 EVERY boot, beside ours at 4. That
   path has never been traced and is the cheapest lead left.
4. **recv_root bails** — independent live front now that "never
   dispatched" is dead.

## DO NOT

- Do not conclude anything about event 21 from p2-211's evt_sub lines —
  that budget was spent in a 16ms window (20.352 R3).
- Do not read the FIRST census line for a hook; counts are cumulative and
  the first ~75s read `calls=0` on instruments that later fired 8,000
  times. Read the LAST per fn.
- Do not treat 20.353 R7 (the 8/30/38 ↔ BAP RequestService numeric match)
  as a revival of the BAP link. 20.351 R2's two disproofs still stand. It
  is a coincidence worth ONE cheap test, not an adopted premise.
- Do not assert the guard would pass for an event-21 body: C2a is
  measured, C2b/C2c were measured only on other events' packets.
- The client is never modified as a delivered mechanism — the poke in
  step 1 is a throwaway diagnostic only.

## SESSION DEBT (small, named)

- `BOOT_BRIEF_p2-211.md` was NOT updated for these three arms and
  `gate_boot.py` did NOT run before p2-212 — the user chose speed. The
  instrument gates (verify_hook_rvas, duplicate-RVA, literal asserts) all
  passed; the brief-level gate did not run. Write the brief retroactively
  or start the next one clean.
- `verify_hook_rvas.py` crashes when `RE_HOOKS_DIR` points OUTSIDE the
  repo root (`path.relative_to(ROOT)` unguarded) — validate via a copy
  inside the tree, or fix the tool.
- `hook_targets.py` ignores `RE_HOOKS_DIR` entirely (only
  verify_hook_rvas passes the dir through), and
  `duplicate_rva_problems()` is DEFINED TWICE in it (the first is dead
  code). Calling it without `raw_reader` silently reports waived pairs as
  failures — that produced a false alarm this session.
