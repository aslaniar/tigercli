# PC BOOTSTRAP — 2026-08-13 (read this first on the gaming PC)

You are a fresh session on the user's Windows gaming PC. The research moved here from macOS
via flash drive. Read order: this file → `GAME_PLAN_2026-08-07.md` → `FINDINGS_2026-08-07.md`
(skim; deep history) → `FINDINGS_2026-08-13.md` (the Sunrise deep-dive — current focus).

## Where we are
- Focus = **stanuwu/Sunrise** (D2 offline mod). Deep-dive done: it is a full in-process
  D2 private server (BAP/SignOn/families 0/3/4/5), not just map hooks. See FINDINGS_2026-08-13.
- Inventory persistence (PR #9, aspaleks) is CONFIRMED working (demo video on X, user-attested).
  Scope is officially expanding past "exploration only."
- The user now wants to do **actual RE work on this PC**, where the game can run.

## The plan (agreed 2026-08-13)
The Steam depot download = compiled artifacts (`bin\x64\destiny2.exe` ~100MB+, DLLs,
`packages\*.pkg`), NOT source. RE ladder, in order:
1. **Verify + document Sunrise's anchor points.** Ghidra headless on `destiny2.exe`; resolve
   every byte-signature in Sunrise's `src/client/patterns/`; decompile the hooked originals;
   write up the real function map. Nobody has published this. Directly useful to Sunrise
   (they admit docs are lacking).
2. **Extend the protocol map** past families 0/3/4/5 — decompile client handlers for the
   message families Sunrise didn't implement (missions, quests, combatant/entity updates).
   Output = protocol docs (legal-safe shape; NOT reconstructed client source — re3/reVC DMCA
   precedent, see FINDINGS_2026-08-07 legal notes).
3. **Enemy-feasibility spec**: what must a server emit (BAP activity messages/entity slots)
   to spawn a static combatant? Client is the oracle; Sunrise's entity_slots plumbing is the
   anchor.
4. **Content DB extraction** from the Arrivals `.pkg` files via tiger-pkg (Oodle on Windows
   = no friction here, borrow the game's own oo2core DLL like Sunrise does).

## First actions on this PC
- [ ] Confirm the depot download location (SunriseInstaller default, or wherever
      DepotDownloader put it). Note the exact path to `bin\x64\destiny2.exe`.
- [ ] Install: Git, Python 3, Ghidra (needs a JDK), VS Build Tools (v143 toolset builds
      Sunrise; the vcxproj asks for v145, override works per PR #6/#8 notes).
- [ ] Clone `github.com/stanuwu/Sunrise` here (or copy from the flash drive).
- [ ] Ghidra headless first pass: import `destiny2.exe`, run default analysis, dump
      strings + function count. Report binary size / any packing oddities before deeper work.
- [ ] Then start ladder step 1 (signature verification against Sunrise's patterns).

## Standing constraints (do not re-litigate)
- Legal shape: protocol/format/interop documentation = safe; publishing reconstructed game
  source = re3/reVC pattern = don't. Sunrise's own rules: no copyrighted data in PRs,
  everything extracted at runtime.
- Archive the two pinned depot manifests when convenient (1085661/7180122903232116872,
  1085662/2210332166360342287) — Valve could retire them; that's the project's existential
  risk.
- stan closed "enemy logic from captures" as not-planned (issue #4). Don't push mechanics
  in his repo; watch PR #9's reception as the scope signal.
- Model discipline per workspace AGENTS.md: flash tier for reading/summarizing; escalate
  only on a named reasoning failure.
