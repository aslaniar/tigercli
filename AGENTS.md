# Workspace

Project directory for research into the Destiny preservation / reverse-engineering scene:
running Destiny 1 on PC, and re-opening vaulted Destiny 2 content. User has a CS
background but is new to game emulation and server RE — explain concepts, avoid jargon
without defining it, and record everything in dated `FINDINGS_*.md` files.

See root `~/Documents/opencode/AGENTS.md` for the model budget ladder and research loop
(research on flash tier, escalate to redteam/deep only on a named reasoning failure).

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
  inventory. Next big step = static enemies via the existing entity pipeline. EXISTENTIAL
  RISK: pinned to 2 Steam depot manifests that Valve could retire — archive them.
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
- Dated findings: `FINDINGS_YYYY-MM-DD.md` (see `FINDINGS_2026-08-07.md`).
- Distinguish VERIFIED facts (cited) from INFERRED mechanism (labeled).
- Record community links so sessions can pick up where the last left off.

## Where to start in this directory
- **GAME_PLAN_2026-08-07.md** — the consolidated strategy (4 tracks, priority order,
  guardrails). Read this first for "what should we do."
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
